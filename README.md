# Tweet-Time-Indexer (v2.0)

Find the **original posting time** of X/Twitter screenshots by OCR’ing the timestamp line and converting it to UTC — now with **auto-copy of matched screenshots** into a `matches/` folder.

> v1.0 indexed folders and let you search by Exact/±N minutes in the UI; v2.0 keeps all that and also **writes matched files to disk** for easy export. 

---

## ✨ What’s new in v2.0

* ✅ **Matched-file export:** when results are found, the app copies the matching screenshots to `data/matches/` (or your configured folder).
* 🧹 **No CSV index file:** the on-disk CSV index has been removed. We still cache OCR results in memory between runs for speed.

---

## 🧭 What it does

* **Indexes a folder** of screenshots and extracts the tweet timestamp via OCR.
* Supports both **dark/light themes** and multiple timestamp styles (e.g., `4:05 PM · Aug 17, 2022`, `09:04 PM · 26/11/2022`).
* Converts parsed time to **UTC** and finds screenshots that match an input time with **Exact / ±1/2/5/10 min** windows.
* **Caches** OCR results per folder for fast re-runs.
* **Copies** matched screenshots into a `matches/` folder for quick sharing or archival.

---

## 📦 Requirements

* **Python 3.11** (recommended for dependency compatibility)
* Windows, macOS, or Linux
* Internet access on first run (OCR models auto-download)

---

## 🔧 Install & Run

```powershell
# 1) Clone
git clone https://github.com/<you>/tweet-time-indexer.git
cd tweet-time-indexer

# 2) Create & activate a Python 3.11 venv
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1  # (Windows PowerShell)
# source .venv/bin/activate   # (macOS/Linux)

# 3) Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# If PaddleOCR asks for extras (Windows/CPU):
pip install paddlepaddle==2.6.1 opencv-contrib-python==4.6.0.66

# 4) Run the app
streamlit run app/ui_streamlit.py
```

The first launch will download PaddleOCR model files to your user cache (e.g., `~/.paddleocr/...`).

---

## 🧪 Create test screenshots

For consistent tests, set X/Twitter to **English (US)** and your system/browser timezone to **America/Toronto (Eastern)**.

* Twitter (web): **More → Settings and privacy → Accessibility, display, and languages → Languages → Display language: English (US)**
* Windows: **Settings → Time & language → Date & time → Time zone: (UTC-05:00) Eastern Time**
* Browser: set UI language to **English (United States)** and hard-refresh

Open a tweet’s **permalink** so you can see a timestamp like:

* `4:05 PM · Aug 17, 2022`
* `9:04 PM · 26/11/2022`

Save screenshots into:

```
data/
  screenshots/
    your-file-1.png
    your-file-2.jpg
```

---

## ▶️ Usage

1. **Folder path:** In the app, confirm the screenshots folder (defaults to `data/screenshots`).
2. **Index:** Click **“Index folder (OCR timestamps)”** to OCR timestamps and cache them.
3. **Query:** Choose date/time + matching window and click **“Find matches”**.
4. **Result:**

   * The UI lists matches and previews images.
   * **Matched files are copied to** `data/matches/` (created automatically).

> Tip: If you change the screenshots folder, re-run **Index** before searching.

---

## 🗂 Project structure

```
app/
  ui_streamlit.py    # Streamlit UI + OCR/indexing/matching
data/
  screenshots/       # Put your test images here
  matches/           # <-- v2.0: matched results are copied here
```

---

## 🧠 How it works

1. **Crop candidates** in the lower region of each image (where X/Twitter timestamps usually appear).
2. **Preprocess** (grayscale, median blur, adaptive threshold + inverse).
3. **OCR** with PaddleOCR; merge detected lines to a single text blob per candidate.
4. **Parse** with `dateparser` (timezone-aware, converted to UTC).
5. **Cache** results per folder (`@st.cache_data`).
6. **Match** by exact minute or ±N minutes and **copy** matches to `data/matches/`.

---

## 🛠 Troubleshooting

* **“`set_page_config()` can only be called once…”**
  Ensure it’s at the very top (already correct in this repo).
* **`ImageMixin.image() got an unexpected keyword argument 'use_container_width'`**
  You’re on an older Streamlit; remove that kwarg or upgrade Streamlit.
* **NumPy / OpenCV ABI errors**
  Use Python 3.11; keep `numpy==1.26.x` and `opencv-contrib-python==4.6.0.66` with `paddleocr==2.7.0.3`.
* **`ModuleNotFoundError: No module named 'paddle'`**
  Install PaddlePaddle (CPU): `pip install paddlepaddle==2.6.1`.

---

## 🔒 Privacy

All OCR runs **locally**. The app only reads the folder you choose and writes matched images to `data/matches/`.

---

## 🗺 Roadmap

* Drag-and-drop single image mode
* Batch export of results metadata (optional CSV/JSON toggle)
* More robust region detection & multi-language support
* Optional local model cache controls

---

## 📜 License

MIT (see `LICENSE` if added).


