# AI Meme & Poster Studio 🎨

An interactive web application built with **Python**, **Streamlit**, and **Pillow (PIL)** for creating high-impact memes, event flyers, and promotional posters using AI.

---

## 🌟 Features

- **🎭 Meme Studio**: Top/bottom text rendering with dynamic auto-wrapping, bold stroke outlines, custom typography, and viral templates.
- **📢 Poster & Flyer Studio**: Structured layout hierarchy with badges, titles, subtitles, date/time chips, call-to-actions, and dark gradient scrims for maximum legibility.
- **✨ Multiple Image Sources**:
  - AI Image generation via text prompts
  - Built-in curated stock template library
  - Procedural aesthetic gradient generation
  - User image upload (PNG, JPG, WEBP)
- **📐 Aspect Ratio Presets**:
  - `1:1` Square (Instagram / Twitter)
  - `4:5` Portrait (Instagram Feed)
  - `9:16` Story (Reels / TikTok / Status)
  - `16:9` Landscape (Banners / Slides)
  - `3:2` Classic Poster
- **🎛️ Real-Time Fine Tuning**: Adjust font size, text/stroke colors, opacity, alignment, and vertical offsets with live instant preview.
- **💾 High-Res Export**: 1-click download as PNG or JPEG.

---

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Generate Starter Assets (Optional)
```bash
python assets/generate_starter_templates.py
```

### 3. Run the Streamlit App
```bash
streamlit run app.py
```

---

## 📁 Project Structure

```text
├── app.py                      # Main Streamlit web application
├── requirements.txt            # Python dependencies
├── config.py                   # Global constants, palettes & aspect ratios
├── core/
│   ├── composer.py             # Pillow rendering engine (strokes, overlays, auto-wrap)
│   ├── llm_service.py          # AI Caption generation interface
│   └── image_gen_service.py    # AI image generation & procedural backdrops
├── assets/
│   ├── fonts/                  # TrueType / OpenType font files
│   ├── meme_templates/         # Stock meme templates
│   ├── poster_templates/       # Stock poster backdrops
│   └── generate_starter_templates.py # Asset generator
└── utils/
    ├── font_loader.py          # Font discovery and system fallbacks
    └── helpers.py              # Image conversion, cropping, and bytes streaming
```

---

## 🌐 Public Cloud Deployment Guide

You can deploy this application for free on **Streamlit Community Cloud** using the following steps:

### 1. Host the Code on GitHub
- Create a new public or private repository on GitHub (e.g., `ai-meme-poster-studio`).
- Commit and push all files in this project to the main branch.
- **Ensure that your `.env` file is NOT committed** (it is already protected by `.gitignore`).

### 2. Configure Streamlit Community Cloud
1. Go to [share.streamlit.io](https://share.streamlit.io/) and log in with your GitHub account.
2. Click the **"New app"** button.
3. Select your repository, branch (usually `main`), and set the Main file path to **`app.py`**.
4. Click the **"Advanced settings..."** button *before* deploying.

### 3. Add API Keys / Secrets
In the **Secrets** text area, paste your keys using TOML format:
```toml
GEMINI_API_KEY = "your_actual_gemini_api_key"
# Optional:
OPENAI_API_KEY = "your_openai_api_key_if_using_dalle"
```
5. Click **"Save"** and then **"Deploy!"**.

Within a couple of minutes, Streamlit will install the dependencies from `requirements.txt`, build the container, and provide a shareable public URL (e.g. `https://your-app-name.streamlit.app`).

