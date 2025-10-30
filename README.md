# Tweet-Time-Indexer (v1.0)

Find the **original posting time** of X/Twitter screenshots by OCR’ing the timestamp line and converting it to UTC.
Built with **Streamlit + PaddleOCR + OpenCV**.

---

## ✨ What it does

* **Indexes a folder** of screenshots and extracts the tweet timestamp via OCR
* Supports both **dark/light themes** and multiple timestamp styles
  (e.g., `4:05 PM · Aug 17, 2022`, `09:04 PM · 26/11/2022`)
* Converts the parsed time to **UTC**, then finds screenshots that match an input time with **Exact / ±1/2/5/10 min** windows
* **Caches** OCR results per folder for fast re-runs

---

## 📦 Requirements

* **Python 3.11** (recommended for easiest dependency compatibility)
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

# (Windows note) If PaddleOCR asks for extra deps, install:
pip install paddlepaddle==2.6.1 opencv-contrib-python==4.6.0.66

# 4) Run the app
streamlit run app/ui_streamlit.py
```

First launch will download PaddleOCR model files to your user cache (e.g., `~/.paddleocr/...`).

---

## 🧪 Create Test Screenshots

For reliable tests, set X/Twitter to **English (US)** and your system/browser timezone to **America/Toronto (Eastern)**.

* Twitter (web): **More → Settings and privacy → Accessibility, display, and languages → Languages → Display language: English (US)**
* Windows: **Settings → Time & language → Date & time → Time zone: (UTC-05:00) Eastern Time**
* Chrome/Edge: set UI language to English (United States) and hard-refresh

Now open a tweet’s **permalink** so you see a line like:

* `4:05 PM · Aug 17, 2022` (common)
* `9:04 PM · 26/11/2022` (numeric day-first, some clients)

Take screenshots and place them in:

```
data/
  screenshots/
    your-file-1.png
    your-file-2.jpg
```

In the app:

1. Enter the folder path (defaults to `data/screenshots`)
2. Click **Index folder (OCR timestamps)**
3. Choose a date/time + window and click **Find matches**

---

## 🗂 Project Structure

```
app/
  ui_streamlit.py   # Streamlit UI + OCR/indexing logic
data/
  screenshots/      # Put your test images here
```

---

## 🧠 How it works (quick)

1. **Crop candidates** at the lower part of the image (where timestamps live on X/Twitter)
2. **Preprocess** (grayscale, median blur, adaptive threshold + inverse)
3. **OCR** with PaddleOCR on each variant, merge lines to a text blob
4. **Parse** with `dateparser` (timezone-aware, converted to UTC)
5. **Cache** results per folder (`@st.cache_data`)
6. **Match** by exact minute or ±N minutes

---

## ⚠️ Troubleshooting

* **“`set_page_config()` can only be called once…”**
  Ensure it’s called at the very top of the script (this repo already does).

* **`ImageMixin.image() got an unexpected keyword argument 'use_container_width'`**
  If you hit this on older Streamlit, remove that keyword or upgrade Streamlit.
  (This repo falls back to `st.image(img)` if needed.)

* **NumPy / OpenCV ABI errors**
  Use Python 3.11 and keep `numpy==1.26.x` with `opencv-contrib-python==4.6.0.66` when using PaddleOCR 2.7.0.3.

* **`ModuleNotFoundError: No module named 'paddle'`**
  Install PaddlePaddle (CPU): `pip install paddlepaddle==2.6.1`.

* **`PyMuPDF` build errors**
  Not required by the app unless you enable PDF input; it’s safe to omit.

---

## 🔒 Privacy

All OCR runs **locally** on your machine. The app only reads images from the folder you choose.

---

## 🗺 Roadmap

* Drag-and-drop single image mode
* Batch export of matched results (CSV/JSON)
* More robust region detection & language packs
* Optional local model caching controls

---

## 🤝 Acknowledgements

* [PaddleOCR](https://github.com/PaddlePaddle/PaddleOCR)
* [Streamlit](https://streamlit.io)
* [OpenCV](https://opencv.org)
* [dateparser](https://dateparser.readthedocs.io/)

---

## 📜 License

MIT (see `LICENSE` if added).
