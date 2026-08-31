"""
Font Loader Module.
Discovers bundled fonts, common Windows system fonts, and handles graceful fallbacks.
"""
import os
from pathlib import Path
from PIL import ImageFont
from config import FONTS_DIR

# Common font locations across Windows, Linux (Streamlit Cloud/Docker/Render), and macOS
SYSTEM_FONT_PATHS = [
    FONTS_DIR,
    Path(r"C:\Windows\Fonts"),
    Path(r"C:\WINNT\Fonts"),
    Path.home() / "AppData" / "Local" / "Microsoft" / "Windows" / "Fonts",
    Path("/usr/share/fonts"),
    Path("/usr/share/fonts/truetype"),
    Path("/usr/share/fonts/opentype"),
    Path("/usr/local/share/fonts"),
    Path.home() / ".fonts",
    Path.home() / ".local" / "share" / "fonts",
    Path("/System/Library/Fonts"),
    Path("/Library/Fonts"),
]

# Preferred font names and their common filenames
PREFERRED_FONTS = {
    "Impact": ["Impact.ttf", "impact.ttf"],
    "Arial Bold": ["Arial-Bold.ttf", "arialbd.ttf", "ARIALBD.TTF", "DejaVuSans-Bold.ttf", "LiberationSans-Bold.ttf"],
    "Arial": ["Arial.ttf", "arial.ttf", "DejaVuSans.ttf", "LiberationSans-Regular.ttf"],
    "Segoe UI Bold": ["SegoeUI-Bold.ttf", "segoeuib.ttf", "segoeui.ttf", "Arial-Bold.ttf", "DejaVuSans-Bold.ttf"],
    "Segoe UI": ["SegoeUI.ttf", "segoeui.ttf", "Arial.ttf", "DejaVuSans.ttf"],
    "Verdana Bold": ["Verdana-Bold.ttf", "verdanab.ttf", "DejaVuSans-Bold.ttf"],
    "Verdana": ["Verdana.ttf", "verdana.ttf", "DejaVuSans.ttf"],
    "Montserrat Bold": ["Montserrat-Bold.ttf", "montserrat-bold.ttf", "SegoeUI-Bold.ttf", "Arial-Bold.ttf"],
    "Trebuchet MS": ["trebuc.ttf", "trebucbd.ttf"],
}


def get_available_fonts() -> dict[str, str | None]:
    """
    Returns a dictionary mapping human-readable font names to their file paths.
    """
    available = {}

    # 1. Search in local project assets/fonts directory first
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
                # Also try recursive search in subdirectories (common in Linux)
                matches = list(sys_dir.rglob(fname))
                if matches:
                    available[font_name] = str(matches[0])
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
    Guarantees returning a scalable font wherever possible.
    """
    # Direct path provided
    if font_path_or_name and os.path.exists(font_path_or_name):
        try:
            return ImageFont.truetype(font_path_or_name, size=size)
        except Exception:
            pass

    # Check bundled assets/fonts directory directly
    if font_path_or_name and FONTS_DIR.exists():
        # Exact or close filename match
        for ext in [".ttf", ".TTF", ".otf", ".OTF"]:
            candidate = FONTS_DIR / f"{font_path_or_name}{ext}"
            if candidate.exists():
                try:
                    return ImageFont.truetype(str(candidate), size=size)
                except Exception:
                    pass
            candidate_hyphen = FONTS_DIR / f"{font_path_or_name.replace(' ', '-')}{ext}"
            if candidate_hyphen.exists():
                try:
                    return ImageFont.truetype(str(candidate_hyphen), size=size)
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

    # Try any available bundled font in assets/fonts
    if FONTS_DIR.exists():
        bundled_files = list(FONTS_DIR.glob("*.[tT][tT][fF]")) + list(FONTS_DIR.glob("*.[oO][tT][fF]"))
        for bf in bundled_files:
            try:
                return ImageFont.truetype(str(bf), size=size)
            except Exception:
                pass

    # Try common system fallbacks directly
    for sys_dir in SYSTEM_FONT_PATHS:
        if not sys_dir.exists():
            continue
        for fallback in ["arial.ttf", "arialbd.ttf", "DejaVuSans.ttf", "DejaVuSans-Bold.ttf", "LiberationSans-Regular.ttf", "impact.ttf", "segoeui.ttf"]:
            p = sys_dir / fallback
            if p.exists():
                try:
                    return ImageFont.truetype(str(p), size=size)
                except Exception:
                    pass
            matches = list(sys_dir.rglob(fallback))
            if matches:
                try:
                    return ImageFont.truetype(str(matches[0]), size=size)
                except Exception:
                    pass

    # Pillow 10.1+ supports load_default with size
    try:
        return ImageFont.load_default(size=size)
    except TypeError:
        return ImageFont.load_default()
