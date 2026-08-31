# AI Meme & Poster Studio 🎨

An interactive AI-powered web application built with **Python**, **Streamlit**, **FastAPI**, and **Pillow (PIL)** for creating high-impact viral memes, event flyers, and promotional posters in seconds.

---

### 🌐 **Live Demo**
👉 **[Launch AI Meme & Poster Creator on Streamlit Cloud](https://ai-meme-poster-generator1-epn49vdpkjnntjg9rz5y2t.streamlit.app/)**

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://ai-meme-poster-generator1-epn49vdpkjnntjg9rz5y2t.streamlit.app/)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## 🌟 Key Features

- **🎭 Meme Studio**: Top/bottom punchline text rendering with dynamic auto-wrapping, bold stroke outlines, custom typography, and viral templates.
- **📢 Poster & Flyer Studio**: Structured layout hierarchy with badges, headlines, subtitles, date/time chips, call-to-actions, and dual-zone dark gradient scrims for maximum legibility.
- **🧠 Generative AI Copywriting**: Powered by **Google Gemini** with an automated multi-candidate failover chain (`gemini-3.5-flash-lite` $\rightarrow$ `gemini-flash-latest` $\rightarrow$ `gemini-3.5-flash`) and smart offline template heuristics.
- **✨ Multiple Image Sources**:
  - **AI Image Generation**: Instant free generation via **Pollinations.ai** & **Google Imagen**
  - **Stock Template Library**: Curated high-resolution templates
  - **Procedural Backdrops**: Mathematical aesthetic gradient generator
  - **Custom Image Upload**: Upload your own PNG, JPG, or WEBP backgrounds
- **📐 Universal Aspect Ratio Presets**:
  - `1:1` Square (Instagram Feed / Twitter)
  - `4:5` Portrait (Instagram Feeds / Flyers)
  - `9:16` Story (Reels / TikTok / WhatsApp Status)
  - `16:9` Landscape (Banners / Slides / YouTube)
  - `3:2` Classic Poster
- **🎛️ Typography & Styling Engine**: Adjust font family, dynamic font size scaling, text/stroke colors, dark scrim opacity, alignment, and vertical offsets with live instant preview.
- **💾 High-Res Export**: 1-click download as publication-ready PNG ($1080 \times 1350\text{px}$).

---

## 🚀 Quick Start (Local Setup)

### 1. Clone the Repository
```bash
git clone https://github.com/AdityaPrakashTiwari2006/AI-Meme-Poster-Generator.git
cd AI-Meme-Poster-Generator
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure API Key (Optional)
Create a `.env` file in the project root:
```env
GEMINI_API_KEY=your_gemini_api_key_here
```
*(If no API key is configured, the app automatically switches to smart offline templates and free Pollinations AI image generation).*

### 4. Run the Streamlit Application
```bash
streamlit run app.py
```
Open **[http://localhost:8501](http://localhost:8501)** in your browser.

---

## ⚡ Alternative: Run FastAPI Backend & Web App

You can also run the modular FastAPI server:
```bash
python server.py
# or
uvicorn server:app --host 0.0.0.0 --port 8000 --reload
```
Open **[http://localhost:8000](http://localhost:8000)** for the modern single-page web interface.

---

## 📁 Project Structure

```text
├── app.py                      # Main Streamlit web application
├── server.py                   # FastAPI REST API backend & static file server
├── requirements.txt            # Python dependencies
├── config.py                   # Global constants, palettes & aspect ratios
├── core/
│   ├── composer.py             # Pillow rendering engine (auto-fit, scrims, strokes)
│   ├── caption_generator.py    # Gemini LLM copy generator with candidate model failover
│   ├── llm_service.py          # Unified LLM & offline template service
│   └── image_generator.py      # AI image generator (Pollinations, Imagen, DALL-E)
├── frontend/                   # Modern Vanilla JS / CSS web client for FastAPI
│   ├── index.html
│   ├── style.css
│   └── app.js
├── assets/
│   ├── fonts/                  # Bundled TrueType fonts (Impact, Arial-Bold, Segoe UI)
│   ├── meme_templates/         # Stock meme template images
│   └── poster_templates/       # Stock poster backdrops
├── utils/
│   ├── font_loader.py          # Cross-platform font discovery and fallbacks
│   └── helpers.py              # Aspect-ratio cropping, color conversion, image bytes
└── tests/                      # 44 Automated Unit & Integration Tests
```

---

## 🧪 Running Automated Tests

Run the full test suite (44 unit and integration tests):
```bash
python -m unittest discover tests -v
```

---

## 🌐 Deployment

### Streamlit Community Cloud
1. Fork or push this repository to GitHub.
2. Go to **[share.streamlit.io](https://share.streamlit.io/)** and create a new app from your repo with main file **`app.py`**.
3. Under **Settings → Secrets**, add:
   ```toml
   GEMINI_API_KEY = "your_actual_gemini_api_key"
   ```
4. Deploy! Live link: **[ai-meme-poster-generator1-epn49vdpkjnntjg9rz5y2t.streamlit.app](https://ai-meme-poster-generator1-epn49vdpkjnntjg9rz5y2t.streamlit.app/)**

---

## 📄 License
This project is open-source under the **MIT License**.
