"""
Pillow Composition Engine.
Provides robust graphic rendering, multi-tier typography layout,
dynamic text wrapping, safe margin constraint enforcement, and PNG export.
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter
from utils.font_loader import load_font
from utils.helpers import fit_image_to_aspect_ratio, hex_to_rgb, create_gradient_background


def wrap_text(text: str, font, max_width: int, draw: ImageDraw.ImageDraw) -> list[str]:
    """
    Wraps text into multiple lines such that each line fits strictly within max_width.
    Handles long words, existing newlines, and empty inputs gracefully.
    """
    if not text or not text.strip():
        return []

    lines = []
    # Preserve explicit newlines from input first
    raw_paragraphs = text.split("\n")

    for paragraph in raw_paragraphs:
        words = paragraph.split()
        if not words:
            continue

        current_line = []
        for word in words:
            test_line = " ".join(current_line + [word])
            bbox = draw.textbbox((0, 0), test_line, font=font)
            line_width = bbox[2] - bbox[0]

            if line_width <= max_width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(" ".join(current_line))
                    current_line = [word]
                else:
                    # Single word is wider than max_width: split character by character
                    accumulated = ""
                    for char in word:
                        test_accum = accumulated + char
                        char_bbox = draw.textbbox((0, 0), test_accum, font=font)
                        if (char_bbox[2] - char_bbox[0]) <= max_width:
                            accumulated = test_accum
                        else:
                            if accumulated:
                                lines.append(accumulated)
                            accumulated = char
                    if accumulated:
                        current_line = [accumulated]

        if current_line:
            lines.append(" ".join(current_line))

    return lines


def calculate_text_block_dimensions(
    lines: list[str],
    font,
    draw: ImageDraw.ImageDraw,
    line_spacing: int | None = None
) -> tuple[int, int]:
    """
    Calculates total width and height of a block of wrapped lines.
    """
    if not lines:
        return 0, 0

    if line_spacing is None:
        font_sz = getattr(font, "size", 20)
        line_spacing = max(4, int(font_sz * 0.2))

    max_w = 0
    total_h = 0
    for i, line in enumerate(lines):
        bbox = draw.textbbox((0, 0), line, font=font)
        w = bbox[2] - bbox[0]
        h = bbox[3] - bbox[1]
        max_w = max(max_w, w)
        total_h += h
        if i < len(lines) - 1:
            total_h += line_spacing

    return max_w, total_h


def auto_fit_font(
    text: str,
    font_name: str | None,
    max_width: int,
    max_height: int,
    initial_size: int = 72,
    min_size: int = 16,
    draw: ImageDraw.ImageDraw = None
) -> tuple[any, list[str]]:
    """
    Dynamically scales font size downwards until the wrapped text strictly fits
    within both max_width and max_height bounds.
    """
    size = initial_size
    dummy_img = Image.new("RGBA", (1, 1))
    if draw is None:
        draw = ImageDraw.Draw(dummy_img)

    while size >= min_size:
        font = load_font(font_name, size)
        lines = wrap_text(text, font, max_width, draw)
        if not lines:
            return font, []

        line_spacing = int(size * 0.2)
        block_w, block_h = calculate_text_block_dimensions(lines, font, draw, line_spacing)

        if block_w <= max_width and block_h <= max_height:
            return font, lines

        size -= 2

    # If min_size is reached but still slightly exceeds max_height, step down further if allowed
    while size >= 10:
        font = load_font(font_name, size)
        lines = wrap_text(text, font, max_width, draw)
        line_spacing = int(size * 0.2)
        block_w, block_h = calculate_text_block_dimensions(lines, font, draw, line_spacing)
        if block_w <= max_width and block_h <= max_height:
            return font, lines
        size -= 2

    font = load_font(font_name, max(8, size))
    lines = wrap_text(text, font, max_width, draw)
    return font, lines


def draw_text_with_outline(
    draw: ImageDraw.ImageDraw,
    xy: tuple[int, int],
    text: str,
    font,
    text_color: tuple[int, int, int] | str,
    stroke_color: tuple[int, int, int] | str = (0, 0, 0),
    stroke_width: int = 4,
    align: str = "center"
):
    """
    Draws text with a thick outer stroke/outline for high-contrast meme readability.
    """
    draw.text(
        xy,
        text,
        font=font,
        fill=text_color,
        stroke_width=stroke_width,
        stroke_fill=stroke_color,
        align=align
    )


def compose_meme(
    base_image: Image.Image,
    top_text: str = "",
    bottom_text: str = "",
    target_size: tuple[int, int] = (1080, 1080),
    safe_margin: int = 40,
    font_name: str = "Impact",
    text_color_hex: str = "#FFFFFF",
    stroke_color_hex: str = "#000000",
    stroke_width: int = 5,
    font_size: int = 64,
    uppercase: bool = True,
    vertical_offset: int = 0,
    darken_overlay: float = 0.0
) -> Image.Image:
    """
    Composes a meme image with top and bottom captions constrained within safe margins.
    """
    canvas = fit_image_to_aspect_ratio(base_image, target_size[0], target_size[1], fit_mode="cover")
    canvas = canvas.convert("RGBA")

    if darken_overlay > 0:
        overlay = Image.new("RGBA", canvas.size, (0, 0, 0, int(255 * darken_overlay)))
        canvas = Image.alpha_composite(canvas, overlay)

    draw = ImageDraw.Draw(canvas)
    w, h = canvas.size
    max_w = w - (safe_margin * 2)
    # Give each text zone enough height to comfortably fit the chosen font size
    # (at least 3 lines worth at the chosen size), instead of hard-capping at h//3
    line_h_estimate = int(font_size * 1.4)
    max_h_each = max(h // 3, line_h_estimate * 3)

    text_rgb = hex_to_rgb(text_color_hex)
    stroke_rgb = hex_to_rgb(stroke_color_hex)

    # Render Top Text
    if top_text.strip():
        txt = top_text.upper() if uppercase else top_text
        font, lines = auto_fit_font(txt, font_name, max_w, max_h_each, initial_size=font_size, draw=draw)
        line_spacing = int(font.size * 0.2) if hasattr(font, "size") else 10

        curr_y = safe_margin + vertical_offset
        for line in lines:
            bbox = draw.textbbox((0, 0), line, font=font, stroke_width=stroke_width)
            line_w = bbox[2] - bbox[0]
            line_h = bbox[3] - bbox[1]
            pos_x = (w - line_w) // 2
            draw_text_with_outline(
                draw, (pos_x, curr_y), line, font,
                text_color=text_rgb, stroke_color=stroke_rgb, stroke_width=stroke_width
            )
            curr_y += line_h + line_spacing

    # Render Bottom Text
    if bottom_text.strip():
        txt = bottom_text.upper() if uppercase else bottom_text
        font, lines = auto_fit_font(txt, font_name, max_w, max_h_each, initial_size=font_size, draw=draw)
        line_spacing = int(font.size * 0.2) if hasattr(font, "size") else 10

        _, total_h = calculate_text_block_dimensions(lines, font, draw, line_spacing)
        curr_y = h - safe_margin - total_h + vertical_offset

        for line in lines:
            bbox = draw.textbbox((0, 0), line, font=font, stroke_width=stroke_width)
            line_w = bbox[2] - bbox[0]
            line_h = bbox[3] - bbox[1]
            pos_x = (w - line_w) // 2
            draw_text_with_outline(
                draw, (pos_x, curr_y), line, font,
                text_color=text_rgb, stroke_color=stroke_rgb, stroke_width=stroke_width
            )
            curr_y += line_h + line_spacing

    return canvas.convert("RGB")


def compose_poster(
    base_image: Image.Image | None = None,
    title: str = "ANNUAL TECH SUMMIT",
    subtitle: str = "Pioneering the Next Generation of AI Systems",
    caption: str = "",
    badge_text: str = "FEATURED CONFERENCE",
    date_time: str = "OCTOBER 24, 2026 • 6:00 PM EST",
    location_cta: str = "SAN FRANCISCO, CA • GET TICKETS AT SUMMIT.DEV",
    target_size: tuple[int, int] = (1080, 1350),
    safe_margin: int = 80,
    font_name: str = "Montserrat Bold",
    title_color_hex: str = "#FFFFFF",
    subtitle_color_hex: str = "#F0F0F0",
    caption_color_hex: str = "#CCCCCC",
    accent_color_hex: str = "#00F0FF",
    overlay_opacity: float = 0.60,
    layout_align: str = "center",
    show_border: bool = True
) -> Image.Image:
    """
    Composes a 1080x1350 (or custom dimensions) Instagram poster with multi-tier typography:
    - Safe margins strictly enforced around all edges
    - Contrast-enhancing dark scrim gradient overlay
    - Category / Announcement badge pill
    - High-impact Title with dynamic auto-wrapping and auto-fit
    - Accent divider bar
    - Subtitle / Tagline
    - Body Caption / Description
    - Footer Date/Time and Location/CTA chips
    """
    target_w, target_h = target_size

    # 1. Base Image or Procedural Gradient
    if base_image is None:
        canvas = create_gradient_background(
            target_w, target_h,
            start_color=(15, 20, 32),
            end_color=(8, 10, 18),
            direction="vertical"
        )
    else:
        canvas = fit_image_to_aspect_ratio(base_image, target_w, target_h, fit_mode="cover")

    canvas = canvas.convert("RGBA")
    w, h = canvas.size

    # 2. Dark Scrim Gradient Overlay for Text Readability
    overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    overlay_draw = ImageDraw.Draw(overlay)
    alpha_base = int(255 * overlay_opacity)

    for y in range(h):
        progress = y / h
        # Smooth curve: darker at top/bottom, strong legibility everywhere
        alpha = int(alpha_base * (0.65 + 0.45 * progress))
        alpha = min(245, max(30, alpha))
        overlay_draw.line([(0, y), (w, y)], fill=(8, 10, 16, alpha))

    canvas = Image.alpha_composite(canvas, overlay)
    draw = ImageDraw.Draw(canvas)

    # Convert color codes
    title_rgb = hex_to_rgb(title_color_hex)
    sub_rgb = hex_to_rgb(subtitle_color_hex)
    cap_rgb = hex_to_rgb(caption_color_hex)
    accent_rgb = hex_to_rgb(accent_color_hex)

    # 3. Outer Safe Margin Bounds
    safe_left = safe_margin
    safe_right = w - safe_margin
    safe_top = safe_margin
    safe_bottom = h - safe_margin
    content_w = safe_right - safe_left

    # 4. Optional Outer Accent Framing Border
    if show_border:
        border_offset = max(20, safe_margin // 2)
        draw.rectangle(
            [(border_offset, border_offset), (w - border_offset, h - border_offset)],
            outline=(*accent_rgb, 100),
            width=2
        )

    # 5. Header / Category Badge Pill
    current_y = safe_top + int(h * 0.02)

    if badge_text and badge_text.strip():
        badge_font = load_font(font_name, int(w * 0.026))
        badge_str = badge_text.strip().upper()
        b_box = draw.textbbox((0, 0), badge_str, font=badge_font)
        bw = b_box[2] - b_box[0]
        bh = b_box[3] - b_box[1]
        
        pad_x, pad_y = 20, 8
        pill_w = bw + pad_x * 2
        pill_h = bh + pad_y * 2

        if layout_align == "center":
            bx = (w - pill_w) // 2
        else:
            bx = safe_left

        # Pill background
        draw.rounded_rectangle(
            [(bx, current_y), (bx + pill_w, current_y + pill_h)],
            radius=12,
            fill=(*accent_rgb, 230)
        )
        # Badge Text
        draw.text((bx + pad_x, current_y + pad_y), badge_str, font=badge_font, fill=(10, 12, 18, 255))
        current_y += pill_h + int(h * 0.035)

    # 6. Main Event / Poster Title
    if title and title.strip():
        title_str = title.strip().upper()
        max_title_h = int(h * 0.28)
        title_font, title_lines = auto_fit_font(
            title_str, font_name, content_w, max_title_h,
            initial_size=int(w * 0.082), min_size=24, draw=draw
        )
        t_spacing = int(title_font.size * 0.15) if hasattr(title_font, "size") else 12

        for line in title_lines:
            bbox = draw.textbbox((0, 0), line, font=title_font)
            lw = bbox[2] - bbox[0]
            lh = bbox[3] - bbox[1]
            lx = (w - lw) // 2 if layout_align == "center" else safe_left
            draw.text((lx, current_y), line, font=title_font, fill=(*title_rgb, 255))
            current_y += lh + t_spacing

        current_y += int(h * 0.015)

    # 7. Accent Divider Bar
    bar_w = int(w * 0.16)
    bar_x = (w - bar_w) // 2 if layout_align == "center" else safe_left
    draw.line([(bar_x, current_y), (bar_x + bar_w, current_y)], fill=(*accent_rgb, 240), width=4)
    current_y += int(h * 0.03)

    # 8. Subtitle / Tagline
    if subtitle and subtitle.strip():
        sub_str = subtitle.strip()
        max_sub_h = int(h * 0.15)
        sub_font, sub_lines = auto_fit_font(
            sub_str, "Segoe UI Bold", content_w, max_sub_h,
            initial_size=int(w * 0.036), min_size=18, draw=draw
        )
        s_spacing = int(sub_font.size * 0.2) if hasattr(sub_font, "size") else 8

        for line in sub_lines:
            bbox = draw.textbbox((0, 0), line, font=sub_font)
            lw = bbox[2] - bbox[0]
            lh = bbox[3] - bbox[1]
            lx = (w - lw) // 2 if layout_align == "center" else safe_left
            draw.text((lx, current_y), line, font=sub_font, fill=(*sub_rgb, 245))
            current_y += lh + s_spacing

        current_y += int(h * 0.02)

    # 9. Additional Caption / Body Description
    if caption and caption.strip():
        cap_str = caption.strip()
        max_cap_h = int(h * 0.12)
        cap_font, cap_lines = auto_fit_font(
            cap_str, "Segoe UI Bold", content_w, max_cap_h,
            initial_size=int(w * 0.028), min_size=15, draw=draw
        )
        c_spacing = int(cap_font.size * 0.2) if hasattr(cap_font, "size") else 6

        for line in cap_lines:
            bbox = draw.textbbox((0, 0), line, font=cap_font)
            lw = bbox[2] - bbox[0]
            lh = bbox[3] - bbox[1]
            lx = (w - lw) // 2 if layout_align == "center" else safe_left
            draw.text((lx, current_y), line, font=cap_font, fill=(*cap_rgb, 220))
            current_y += lh + c_spacing

    # 10. Footer Event Information (Date/Time & Location/CTA)
    # Anchor to safe bottom margin
    footer_font = load_font(font_name, int(w * 0.032))
    cta_font = load_font("Segoe UI Bold", int(w * 0.028))

    dt_lines = wrap_text(date_time.strip(), footer_font, content_w, draw) if date_time.strip() else []
    cta_lines = wrap_text(location_cta.strip(), cta_font, content_w, draw) if location_cta.strip() else []

    dt_w, dt_h = calculate_text_block_dimensions(dt_lines, footer_font, draw, line_spacing=6)
    cta_w, cta_h = calculate_text_block_dimensions(cta_lines, cta_font, draw, line_spacing=6)

    total_footer_h = dt_h + (16 if dt_lines and cta_lines else 0) + cta_h
    start_footer_y = safe_bottom - total_footer_h

    # Render Date/Time
    curr_foot_y = start_footer_y
    for line in dt_lines:
        bbox = draw.textbbox((0, 0), line, font=footer_font)
        lw = bbox[2] - bbox[0]
        lh = bbox[3] - bbox[1]
        lx = (w - lw) // 2 if layout_align == "center" else safe_left
        draw.text((lx, curr_foot_y), line, font=footer_font, fill=(*accent_rgb, 255))
        curr_foot_y += lh + 6

    if dt_lines and cta_lines:
        curr_foot_y += 10

    # Render Location / CTA
    for line in cta_lines:
        bbox = draw.textbbox((0, 0), line, font=cta_font)
        lw = bbox[2] - bbox[0]
        lh = bbox[3] - bbox[1]
        lx = (w - lw) // 2 if layout_align == "center" else safe_left
        draw.text((lx, curr_foot_y), line, font=cta_font, fill=(*title_rgb, 230))
        curr_foot_y += lh + 6

    return canvas.convert("RGB")


def save_poster(image: Image.Image, output_path: str | Path) -> str:
    """
    Saves a generated poster image as PNG.
    Creates parent directories if necessary and returns absolute file path.
    """
    out_file = Path(output_path).resolve()
    out_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Ensure saved as RGB PNG
    if image.mode in ("RGBA", "P"):
        image = image.convert("RGB")
    image.save(out_file, format="PNG", optimize=True)
    return str(out_file)
