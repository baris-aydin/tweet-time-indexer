Tweet-Time-Indexer (v1.0)

Find tweet screenshots that match a specific time.
This Streamlit app OCRs the timestamp line from Twitter/X screenshots, converts it to UTC, and lets you search for matches at an exact minute or within a tolerance window.

✨ What it does

Indexes a folder of .png/.jpg/.jpeg/.webp screenshots.

Uses PaddleOCR + OpenCV to read the timestamp row (e.g., 4:05 PM · Aug 17, 2022 or 11:30 PM · 21/03/2030).

Parses the text with dateparser, attaches the chosen timezone (default America/Toronto), and stores it as UTC.

Lets you query a target date/time and a match window (Exact, ±1/2/5/10 min) to see all matching screenshots.

Everything runs locally; no screenshots are uploaded.

🖼️ Supported timestamp styles (examples)

4:05 PM · Aug 17, 2022

9:04 PM · Nov 26, 2022

11:30 PM · 21/03/2030

Variants with minor punctuation/spacing differences are handled.

Tip: For consistent testing, set X/Twitter Display language: English (US) and your OS/browser timezone to Eastern (Toronto).

🗂️ Project layout
app/
  ui_streamlit.py      # Streamlit UI + OCR/index/search logic
data/
  screenshots/         # Default folder the app points to (you can change it in the UI)

🚀 Quick start

Recommended: Python 3.11 on Windows (works on macOS/Linux too).

# 1) Create & activate a venv
py -3.11 -m venv .venv
.\.venv\Scripts\activate

# 2) Install deps (CPU-only)
pip install -r requirements.txt
pip install paddlepaddle==2.6.1  # CPU build of PaddlePaddle

# 3) Run the app
streamlit run app/ui_streamlit.py


The first OCR run will download model files to ~/.paddleocr.

🧭 How to use

Put a few tweet screenshots in a folder (default: data/screenshots/).

In the app:

Set Screenshots folder (or accept default).

Click Index folder (OCR timestamps).
You’ll see how many images produced a parseable timestamp.

Choose the date/time you’re looking for and a match window.

Click Find matches to list any screenshots within the window (UTC is shown for each match).

⚙️ Configuration

Default timezone: America/Toronto (edit DEFAULT_TZ in ui_streamlit.py).

OCR crop strategy: tries several candidate bands near the bottom of the image (adjust CANDIDATE_BANDS if your screenshots differ).

Caching:

@st.cache_resource for the OCR engine.

@st.cache_data for the per-folder index.

🧪 Generating reliable test screenshots

Force X/Twitter to English (US) and set OS/browser timezone to Eastern.

Capture the tweet detail page (click the timestamp) so the timestamp line appears clearly.

Test both light and dark themes.

Include edge cases:

12:00 AM / 11:59 PM

DST transition days (March/November)

Different years and numeric vs month-name formats.

🛠️ Troubleshooting

ImportError: numpy.core.multiarray failed to import
Ensure NumPy is compatible with OpenCV 4.6 wheels. A safe combo used in dev:

opencv-contrib-python==4.6.0.66

numpy==1.26.x

Python 3.11

PaddleOCR missing extras
If you installed paddleocr with --no-deps, also install:

pip install opencv-contrib-python==4.6.0.66 scikit-image attrdict beautifulsoup4 lxml fire


(The app doesn’t need PyMuPDF/pdf2docx/premailer/openpyxl.)

ModuleNotFoundError: No module named 'paddle'
Install CPU PaddlePaddle: pip install paddlepaddle==2.6.1

Streamlit:
If you see set_page_config() can only be called once, make sure it’s only called at the top of the script.

🧹 Dev tooling

Optional but recommended:

pip install pre-commit black ruff
pre-commit install
# Format / lint:
black .
ruff check .

🗺️ Roadmap ideas

Add a file picker widget and drag-drop.

Show confidence and bounding boxes for the OCR’d timestamp.

Support additional locales explicitly (e.g., Turkish, German) with format hints.

Export index to a CSV for offline search.

Batch-rename or move matched screenshots.

📄 License

TBD 

🙏 Acknowledgements

PaddleOCR

PaddlePaddle

OpenCV

Streamlit

dateparser
