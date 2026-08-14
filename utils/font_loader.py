"""
Font Loader Module.
Discovers bundled fonts, common Windows system fonts, and handles graceful fallbacks.
"""
import os
from pathlib import Path
from PIL import ImageFont
from config import FONTS_DIR

# Common Windows system font locations
SYSTEM_FONT_PATHS = [
    Path(r"C:\Windows\Fonts"),
    Path(r"C:\WINNT\Fonts"),
    Path.home() / "AppData" / "Local" / "Microsoft" / "Windows" / "Fonts",
]

# Preferred fonts for Memes and Posters
PREFERRED_FONTS = {
    "Impact": ["impact.ttf", "Impact.ttf"],
    "Arial Bold": ["arialbd.ttf", "ARIALBD.TTF", "arial.ttf"],
    "Montserrat Bold": ["Montserrat-Bold.ttf", "montserrat-bold.ttf"],
    "Bebas Neue": ["BebasNeue-Regular.ttf", "bebasneue.ttf"],
    "Anton": ["Anton-Regular.ttf", "anton.ttf"],
    "Comic Sans": ["comic.ttf", "comicbd.ttf"],
    "Segoe UI Bold": ["segoeuib.ttf", "segoeui.ttf"],
    "Trebuchet MS": ["trebuc.ttf", "trebucbd.ttf"],
    "Verdana Bold": ["verdanab.ttf", "verdana.ttf"],
    "Courier New Bold": ["courbd.ttf", "cour.ttf"],
}


def get_available_fonts() -> dict[str, str | None]:
    """
    Returns a dictionary mapping human-readable font names to their file paths.
    """
    available = {}

    # 1. Search in local project assets/fonts directory
    if FONTS_DIR.exists():
        for font_file in FONTS_DIR.glob("*.[tT][tT][fF]"):
            clean_name = font_file.stem.replace("-", " ").title()
            available[clean_name] = str(font_file)
        for font_file in FONTS_DIR.glob("*.[oO][tT][fF]"):
            clean_name = font_file.stem.replace("-", " ").title()
            available[clean_name] = str(font_file)

    # 2. Check system font locations for preferred fonts
    for font_name, candidate_filenames in PREFERRED_FONTS.items():
        if font_name in available:
            continue
        for sys_dir in SYSTEM_FONT_PATHS:
            if not sys_dir.exists():
                continue
            for fname in candidate_filenames:
                fpath = sys_dir / fname
                if fpath.exists():
                    available[font_name] = str(fpath)
                    break
            if font_name in available:
                break

    # 3. Always include default system fallback
    if "Default (System)" not in available:
        available["Default (System)"] = None

    return available


def load_font(font_path_or_name: str | None, size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    """
    Safely loads a PIL ImageFont given a file path or font name with fallback.
    """
    if font_path_or_name and os.path.exists(font_path_or_name):
        try:
            return ImageFont.truetype(font_path_or_name, size=size)
        except Exception:
            pass

    # Try finding in available fonts
    all_fonts = get_available_fonts()
    if font_path_or_name in all_fonts and all_fonts[font_path_or_name]:
        target_path = all_fonts[font_path_or_name]
        try:
            return ImageFont.truetype(target_path, size=size)
        except Exception:
            pass

    # Try common system fallbacks directly
    for sys_dir in SYSTEM_FONT_PATHS:
        for fallback in ["arial.ttf", "impact.ttf", "segoeui.ttf", "tahoma.ttf"]:
            p = sys_dir / fallback
            if p.exists():
                try:
                    return ImageFont.truetype(str(p), size=size)
                except Exception:
                    pass

    return ImageFont.load_default()
