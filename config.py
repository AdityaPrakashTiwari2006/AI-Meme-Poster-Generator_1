"""
Configuration and constants for AI Meme & Poster Creator.
"""
from pathlib import Path
from dotenv import load_dotenv

# Paths
BASE_DIR = Path(__file__).resolve().parent

# Automatically load environment variables from project .env
load_dotenv(dotenv_path=BASE_DIR / ".env", override=True)

ASSETS_DIR = BASE_DIR / "assets"
FONTS_DIR = ASSETS_DIR / "fonts"
MEME_TEMPLATES_DIR = ASSETS_DIR / "meme_templates"
POSTER_TEMPLATES_DIR = ASSETS_DIR / "poster_templates"

# Ensure directories exist
for directory in [ASSETS_DIR, FONTS_DIR, MEME_TEMPLATES_DIR, POSTER_TEMPLATES_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# Aspect Ratios (width x height)
ASPECT_RATIOS = {
    "1:1 Square (Instagram / Twitter)": (1080, 1080),
    "4:5 Portrait (Instagram Feed)": (1080, 1350),
    "9:16 Story (TikTok / Reels / Status)": (1080, 1920),
    "16:9 Landscape (Twitter / Presentation)": (1920, 1080),
    "3:2 Standard Poster": (1200, 800),
}

# Supported Tone Options
TONE_PRESETS = [
    "Sarcastic & Witty",
    "Relatable & Casual",
    "Gen-Z & Trendy",
    "Tech & Programmer Humor",
    "Corporate & Professional",
    "Hype & Energetic",
    "Dark & Ironical",
    "Wholesome & Cute",
    "Inspirational & Dramatic"
]

# Color Palettes for Posters & Overlays
COLOR_PALETTES = {
    "Neon Cyberpunk": {
        "primary": "#00F0FF",
        "secondary": "#FF0055",
        "accent": "#FFE600",
        "background": "#0D0E15",
        "text": "#FFFFFF",
    },
    "Clean Minimalist": {
        "primary": "#1A1A1A",
        "secondary": "#666666",
        "accent": "#E63946",
        "background": "#F8F9FA",
        "text": "#111111",
    },
    "Sunset Warmth": {
        "primary": "#FF5964",
        "secondary": "#FEE180",
        "accent": "#35A7FF",
        "background": "#2E1F27",
        "text": "#FFFFFF",
    },
    "Midnight Blue": {
        "primary": "#4CC9F0",
        "secondary": "#4361EE",
        "accent": "#7209B7",
        "background": "#0B132B",
        "text": "#FFFFFF",
    },
    "Forest Emerald": {
        "primary": "#52B788",
        "secondary": "#74C69D",
        "accent": "#D8F3DC",
        "background": "#081C15",
        "text": "#FFFFFF",
    },
}
