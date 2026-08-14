"""
Helper utilities for image conversions, resizing, and buffer handling.
"""
import io
import math
from PIL import Image, ImageDraw


def image_to_bytes(image: Image.Image, format: str = "PNG", quality: int = 95) -> bytes:
    """
    Converts a PIL Image object to bytes for download.
    """
    buffer = io.BytesIO()
    save_format = format.upper()
    if save_format in ["JPG", "JPEG"]:
        if image.mode in ("RGBA", "P"):
            image = image.convert("RGB")
        image.save(buffer, format="JPEG", quality=quality)
    else:
        image.save(buffer, format="PNG", optimize=True)
    buffer.seek(0)
    return buffer.getvalue()


def fit_image_to_aspect_ratio(
    image: Image.Image,
    target_width: int,
    target_height: int,
    fit_mode: str = "cover"
) -> Image.Image:
    """
    Resizes and crops/pads an image to fit target dimensions.
    fit_mode: 'cover' (crop excess) or 'contain' (add background padding)
    """
    img_w, img_h = image.size
    target_ratio = target_width / target_height
    img_ratio = img_w / img_h

    if fit_mode == "cover":
        if img_ratio > target_ratio:
            # Source is wider, scale by height and crop width
            new_height = target_height
            new_width = int(img_w * (target_height / img_h))
        else:
            # Source is taller, scale by width and crop height
            new_width = target_width
            new_height = int(img_h * (target_width / img_w))

        resized = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # Center crop
        left = (new_width - target_width) // 2
        top = (new_height - target_height) // 2
        return resized.crop((left, top, left + target_width, top + target_height))

    else:  # contain
        if img_ratio > target_ratio:
            new_width = target_width
            new_height = int(img_h * (target_width / img_w))
        else:
            new_height = target_height
            new_width = int(img_w * (target_height / img_h))

        resized = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        canvas = Image.new("RGBA", (target_width, target_height), (15, 15, 20, 255))
        paste_x = (target_width - new_width) // 2
        paste_y = (target_height - new_height) // 2
        canvas.paste(resized, (paste_x, paste_y))
        return canvas


def create_gradient_background(
    width: int,
    height: int,
    start_color: tuple[int, int, int] = (20, 24, 38),
    end_color: tuple[int, int, int] = (10, 12, 18),
    direction: str = "vertical"
) -> Image.Image:
    """
    Generates a smooth linear gradient background image.
    """
    base = Image.new("RGB", (width, height), start_color)
    draw = ImageDraw.Draw(base)

    if direction == "vertical":
        for y in range(height):
            ratio = y / height
            r = int(start_color[0] * (1 - ratio) + end_color[0] * ratio)
            g = int(start_color[1] * (1 - ratio) + end_color[1] * ratio)
            b = int(start_color[2] * (1 - ratio) + end_color[2] * ratio)
            draw.line([(0, y), (width, y)], fill=(r, g, b))
    else:  # horizontal
        for x in range(width):
            ratio = x / width
            r = int(start_color[0] * (1 - ratio) + end_color[0] * ratio)
            g = int(start_color[1] * (1 - ratio) + end_color[1] * ratio)
            b = int(start_color[2] * (1 - ratio) + end_color[2] * ratio)
            draw.line([(x, 0), (x, height)], fill=(r, g, b))

    return base


def hex_to_rgb(hex_str: str) -> tuple[int, int, int]:
    """Converts a hex color string (e.g. #FFFFFF or FFFFFF) to RGB tuple."""
    hex_clean = hex_str.lstrip("#")
    if len(hex_clean) == 3:
        hex_clean = "".join([c * 2 for c in hex_clean])
    return tuple(int(hex_clean[i:i + 2], 16) for i in (0, 2, 4))
