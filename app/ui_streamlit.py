# app/ui_streamlit.py
import io
import os
from pathlib import Path
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import cv2
import numpy as np
import streamlit as st
from paddleocr import PaddleOCR
from PIL import Image
import dateparser

import re

# -----------------------------
# Config
# -----------------------------
APP_TITLE = "Twitter/X Timestamp Finder"
DEFAULT_TZ = ZoneInfo("America/Toronto")  # your default timezone
IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp"}
CANDIDATE_BANDS = [(0.75, 1.00, 0.00, 1.00),  # bottom third: y1..y2, x1..x2 (fractions)
                   (0.65, 0.92, 0.00, 1.00),  # mid-lower wide band
                   (0.85, 1.00, 0.10, 0.90)]  # centered bottom strip
CLEAN_PAT = re.compile(r"(views?|retweets?|quotes?|likes?|bookmarks?)", re.I)
TS_HINT = re.compile(r"(\d{1,2}:\d{2})|([0-3]?\d[./-][0-1]?\d[./-]\d{2,4})|"
                     r"(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)", re.I)
TIME_RE = re.compile(r"\b\d{1,2}:\d{2}\b")  # must contain a time like 11:30

# Init OCR once (English UI text is most common; adjust 'lang' if needed)
st.set_page_config(page_title=APP_TITLE, layout="wide")
@st.cache_resource
def get_ocr():
    # use_angle_cls helps with minor rotations; det + rec default models are fine
    return PaddleOCR(use_angle_cls=True, lang="en")


# -----------------------------
# Utility functions
# -----------------------------
def load_image_cv(path: Path) -> np.ndarray | None:
    img = cv2.imdecode(np.fromfile(str(path), dtype=np.uint8), cv2.IMREAD_COLOR)
    return img

def clean_timestamp_text(text: str) -> str:
    # Common separators/garbage
    t = text.replace("·", " ").replace("|", " ")
    t = CLEAN_PAT.sub(" ", t)
    # Fix missing spaces around AM/PM
    t = re.sub(r"(\d)([AP]M)\b", r"\1 \2", t, flags=re.I)   # 11:30PM -> 11:30 PM
    t = re.sub(r"\b([AP]M)(\d)", r"\1 \2", t, flags=re.I)   # PM21 -> PM 21
    t = re.sub(r"\s{2,}", " ", t).strip()
    return t

def candidate_crops(img: np.ndarray) -> list[np.ndarray]:
    h, w = img.shape[:2]
    crops = []
    for (y1f, y2f, x1f, x2f) in CANDIDATE_BANDS:
        y1, y2 = int(h * y1f), int(h * y2f)
        x1, x2 = int(w * x1f), int(w * x2f)
        band = img[y1:y2, x1:x2]
        if band.size > 0:
            crops.append(band)
    return crops

def preprocess(img: np.ndarray) -> list[np.ndarray]:
    """Return a few preprocessed variants to try (light/dark, thresholded, scaled)."""
    # Upscale to help OCR on tiny UI fonts
    h, w = img.shape[:2]
    scale = 2.0 if min(h, w) < 1200 else 1.5
    img_big = cv2.resize(img, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)

    g = cv2.cvtColor(img_big, cv2.COLOR_BGR2GRAY)

    # Contrast boost for grey-on-dark
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    g = clahe.apply(g)

    g = cv2.medianBlur(g, 3)

    thr = cv2.adaptiveThreshold(
        g, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 31, 5
    )
    inv = cv2.bitwise_not(thr)

    # A “soft” binarization, sometimes cleaner than adaptive
    _, otsu = cv2.threshold(g, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    return [thr, inv, otsu]



def ocr_texts(cv_img: np.ndarray) -> list[str]:
    """Run OCR on multiple variants and return likely timestamp lines only."""
    ocr = get_ocr()
    candidates = []
    for variant in preprocess(cv_img):
        rgb = cv2.cvtColor(variant, cv2.COLOR_GRAY2RGB)
        result = ocr.ocr(rgb, cls=True)
        if not result or not result[0]:
            continue
        for rec in result[0]:
            if not rec or not rec[1]:
                continue
            line = " ".join(rec[1][0].split())
            if line and TIME_RE.search(line):   # <-- require a time
                candidates.append(line)

    # dedupe
    seen, out = set(), []
    for t in candidates:
        if t not in seen:
            seen.add(t)
            out.append(t)
    return out

def parse_datetime_from_text(text: str, base_tz: ZoneInfo) -> datetime | None:
    import re
    t = clean_timestamp_text(text)

    # 1) Try dateparser first
    dt = dateparser.parse(
        t,
        settings={
            "RETURN_AS_TIMEZONE_AWARE": True,
            "TIMEZONE": str(base_tz),
            "TO_TIMEZONE": "UTC",
        },
    )
    if dt:
        return dt if dt.tzinfo else dt.replace(tzinfo=base_tz).astimezone(ZoneInfo("UTC"))

    # 2) Regex fallback for DD/MM/YYYY with or without AM/PM
    m = re.search(
        r"\b(?P<h>\d{1,2}):(?P<m>\d{2})\s*(?P<ampm>[AP]M)?\b.*?"
        r"\b(?P<d>\d{1,2})[\/\.\-](?P<mo>\d{1,2})[\/\.\-](?P<y>\d{2,4})\b",
        t, flags=re.I
    )
    if not m:
        # Also support "Aug 21, 2025" styles
        m2 = re.search(
            r"\b(?P<h>\d{1,2}):(?P<m>\d{2})\s*(?P<ampm>[AP]M)?\b.*?"
            r"\b(?P<mon>[A-Za-z]{3,})\s*(?P<d2>\d{1,2}),\s*(?P<y2>\d{2,4})\b",
            t, flags=re.I
        )
        if m2:
            h = int(m2.group("h")); mi = int(m2.group("m"))
            ampm = (m2.group("ampm") or "").upper()
            mon = m2.group("mon"); d = int(m2.group("d2")); y = int(m2.group("y2"))
            if y < 100: y += 2000
            from calendar import month_abbr, month_name
            mon_map = {m.lower(): i for i, m in enumerate(month_abbr) if m}
            mon_map.update({m.lower(): i for i, m in enumerate(month_name) if m})
            mo = mon_map.get(mon.lower())
            if not mo: return None
        else:
            return None
    if m:
        h = int(m.group("h")); mi = int(m.group("m"))
        ampm = (m.group("ampm") or "").upper()
        d = int(m.group("d")); mo = int(m.group("mo")); y = int(m.group("y"))
        if y < 100: y += 2000
    try:
        if ampm == "PM" and h != 12: h += 12
        if ampm == "AM" and h == 12: h = 0
        dt_local = datetime(y, mo, d, h, mi, tzinfo=base_tz)
        return dt_local.astimezone(ZoneInfo("UTC"))
    except Exception:
        return None


def index_folder(folder: Path, base_tz: ZoneInfo) -> list[dict]:
    """
    Build an in-memory index: [{'path': Path, 'dt_utc': datetime, 'raw': str}]
    """
    index = []
    for p in sorted(folder.glob("*")):
        if p.suffix.lower() not in IMAGE_EXTS:
            continue
        img = load_image_cv(p)
        if img is None:
            continue

        found_dt = None
        best_text = None

        for crop in candidate_crops(img):
            for txt in ocr_texts(crop):
                parsed = parse_datetime_from_text(txt, base_tz)
                if parsed:
                    found_dt = parsed
                    best_text = txt
                    break
            if found_dt:
                break

        # fallback: try whole image if bands failed
        if not found_dt:
            for txt in ocr_texts(img):
                parsed = parse_datetime_from_text(txt, base_tz)
                if parsed:
                    found_dt = parsed
                    best_text = txt
                    break

        if found_dt:
            index.append({"path": p, "dt_utc": found_dt, "raw": best_text})
    return index

def build_query_dt(year, month, day, hour, minute, ampm, base_tz: ZoneInfo) -> datetime:
    # Convert 12h → 24h
    h = hour % 12
    if ampm == "PM":
        h += 12
    dt_local = datetime(year, month, day, h, minute, tzinfo=base_tz)
    return dt_local.astimezone(ZoneInfo("UTC"))

def within_window(target_utc: datetime, candidate_utc: datetime, minutes: int) -> bool:
    if minutes <= 0:
        # exact minute match (ignore seconds)
        t = target_utc.replace(second=0, microsecond=0)
        c = candidate_utc.replace(second=0, microsecond=0)
        return t == c
    delta = abs(candidate_utc - target_utc)
    return delta <= timedelta(minutes=minutes)

# -----------------------------
# Streamlit UI
# -----------------------------
#st.set_page_config(page_title=APP_TITLE, layout="wide")
st.title(APP_TITLE)
st.caption("Pick a screenshots folder, choose a date/time, and find matching Twitter/X posts.")

# Folder picker (simple text input to a path)
default_screens_dir = str(Path.cwd() / "data" / "screenshots")
folder_str = st.text_input("Screenshots folder", value=default_screens_dir)
folder = Path(folder_str)

colA, colB, colC = st.columns(3)
with colA:
    year = st.number_input("Year", min_value=2006, max_value=2100, value=2025, step=1)
    month = st.selectbox("Month", list(range(1, 13)), index=7)  # August as example
    day = st.number_input("Day", min_value=1, max_value=31, value=21, step=1)
with colB:
    hour_12 = st.selectbox("Hour", list(range(1, 13)), index=1)  # 1..12
    minute = st.selectbox("Minute", [0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55], index=6)
    ampm = st.selectbox("AM / PM", ["AM", "PM"], index=1)
with colC:
    mode = st.selectbox(
        "Match mode",
        ["Exact", "±1 min", "±2 min", "±5 min", "±10 min"],
        index=0,
        help="Exact: same minute (seconds ignored). Ranges allow ±N minutes.",
    )

match_window_map = {"Exact": 0, "±1 min": 1, "±2 min": 2, "±5 min": 5, "±10 min": 10}
window_minutes = match_window_map[mode]

# Caching index per folder path to avoid repeated OCR each run
@st.cache_data(show_spinner=True)
def cached_index(folder_path_str: str, tz_name: str):
    fpath = Path(folder_path_str)
    tz = ZoneInfo(tz_name)
    return index_folder(fpath, tz)

st.write(f"Using timezone: **America/Toronto** (converted to UTC internally).")

do_index = st.button("Index folder (OCR timestamps)")
show_debug = st.checkbox("Show OCR debug (parsed vs raw)", value=False)

if do_index:
    if not folder.exists():
        st.error("Folder does not exist.")
    else:
        with st.spinner("Running OCR and indexing screenshots..."):
            idx = cached_index(folder_str, "America/Toronto")
        st.success(f"Indexed {len(idx)} image(s) with recognizable timestamps.")
        if show_debug:
            for rec in idx:
                st.write(
                    f"- **{rec['path'].name}**  \n"
                    f"  OCR raw: `{rec['raw']}`  \n"
                    f"  UTC: `{rec['dt_utc'].isoformat(timespec='minutes')}`"
                )
#show_debug = st.checkbox("Show OCR debug (parsed vs raw)", value=False)

st.divider()
if st.button("Find matches"):
    if not folder.exists():
        st.error("Folder does not exist.")
    else:
        # Ensure we have an index
        idx = cached_index(folder_str, "America/Toronto")
        if not idx:
            st.warning("No indexed timestamps yet. Click 'Index folder' first.")
        else:
            query_dt_utc = build_query_dt(
                int(year), int(month), int(day), int(hour_12), int(minute), ampm, DEFAULT_TZ
            )
            st.write(f"Query (UTC): `{query_dt_utc.isoformat(timespec='minutes')}`  | Window: **{mode}**")

            # Filter by window
            matches = [
                rec for rec in idx
                if within_window(query_dt_utc, rec["dt_utc"], window_minutes)
            ]

            if not matches:
                st.info("No matches found.")
            else:
                st.success(f"Found {len(matches)} match(es):")
                for rec in matches:
                    p: Path = rec["path"]
                    st.write(f"**{p.name}**  —  OCR: `{rec['raw']}`  —  UTC: `{rec['dt_utc'].isoformat(timespec='minutes')}`")
                    # Show preview
                    img = load_image_cv(p)
                    if img is not None:
                        # convert BGR->RGB for display
                        rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                        st.image(rgb, use_column_width=True)
