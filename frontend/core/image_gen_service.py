"""
Image Generation Service Facade.
Provides procedural gradient backdrops, prompt generation, and AI image provider dispatch.
"""
from core.image_generator import (
    generate_image_prompt,
    generate_image,
    generate_image_pollinations,
    generate_image_gemini_imagen,
    generate_image_openai_dalle,
    ImageGenerationError,
    ImageGenAuthError,
    ImageGenNetworkError,
    ImageGenEmptyResponseError,
    PROMPT_STYLE_MODIFIERS
)
from utils.helpers import create_gradient_background, hex_to_rgb
from config import COLOR_PALETTES
from PIL import Image, ImageDraw


def create_procedural_backdrop(
    palette_name: str = "Neon Cyberpunk",
    width: int = 1080,
    height: int = 1080
) -> Image.Image:
    """
    Generates a stylish procedural background with smooth gradients and geometric accents.
    """
    palette = COLOR_PALETTES.get(palette_name, COLOR_PALETTES["Midnight Blue"])
    bg_rgb = hex_to_rgb(palette["background"])
    accent_rgb = hex_to_rgb(palette["primary"])

    base = create_gradient_background(
        width, height,
        start_color=bg_rgb,
        end_color=(max(0, bg_rgb[0] - 10), max(0, bg_rgb[1] - 10), max(0, bg_rgb[2] - 10)),
        direction="vertical"
    )
    base = base.convert("RGBA")

    overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    # Top right glow
    draw.ellipse(
        [(int(width * 0.6), -int(height * 0.2)), (int(width * 1.3), int(height * 0.5))],
        fill=(*accent_rgb, 35)
    )
    # Bottom left glow
    sec_rgb = hex_to_rgb(palette["secondary"])
    draw.ellipse(
        [(-int(width * 0.2), int(height * 0.6)), (int(width * 0.5), int(height * 1.2))],
        fill=(*sec_rgb, 25)
    )

    combined = Image.alpha_composite(base, overlay)
    return combined.convert("RGB")


def fetch_pollinations_image(
    prompt: str,
    width: int = 1080,
    height: int = 1080,
    seed: int = 42
) -> Image.Image:
    """Convenience wrapper for Pollinations image generation with procedural fallback."""
    try:
        return generate_image_pollinations(prompt, width=width, height=height, seed=seed)
    except Exception:
        return create_procedural_backdrop("Midnight Blue", width, height)
