"""
Generates starter meme and poster template images for local offline testing.
"""
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
MEME_DIR = BASE_DIR / "meme_templates"
POSTER_DIR = BASE_DIR / "poster_templates"

MEME_DIR.mkdir(parents=True, exist_ok=True)
POSTER_DIR.mkdir(parents=True, exist_ok=True)


def create_starter_assets():
    # 1. Classic Two-Panel Comparison Meme Template
    img1 = Image.new("RGB", (1080, 1080), (240, 240, 245))
    draw = ImageDraw.Draw(img1)
    # Split line
    draw.line([(0, 540), (1080, 540)], fill=(30, 30, 30), width=6)
    draw.line([(540, 0), (540, 1080)], fill=(30, 30, 30), width=6)
    # Left panels color badges
    draw.rectangle([(0, 0), (540, 540)], fill=(255, 180, 180))
    draw.rectangle([(0, 540), (540, 1080)], fill=(180, 255, 200))
    # Emojis/Symbols
    draw.text((230, 230), "❌", fill=(180, 40, 40))
    draw.text((230, 770), "✅", fill=(40, 160, 60))
    img1.save(MEME_DIR / "comparison_choice.png")

    # 2. Dramatic Reaction Backdrop
    img2 = Image.new("RGB", (1080, 1080), (18, 20, 28))
    draw2 = ImageDraw.Draw(img2)
    for r in range(400, 50, -30):
        alpha = int(255 * (1 - r / 400))
        draw2.ellipse([(540 - r, 540 - r), (540 + r, 540 + r)], outline=(255, 75, 43), width=4)
    img2.save(MEME_DIR / "dramatic_shock.png")

    # 3. Modern Cyberpunk Poster Backdrop
    img3 = Image.new("RGB", (1080, 1350), (12, 14, 22))
    draw3 = ImageDraw.Draw(img3)
    # Neon gradients / geometric lines
    draw3.polygon([(0, 0), (1080, 0), (1080, 450), (0, 700)], fill=(20, 28, 48))
    draw3.line([(0, 700), (1080, 450)], fill=(0, 240, 255), width=4)
    draw3.line([(0, 730), (1080, 480)], fill=(255, 0, 128), width=3)
    img3.save(POSTER_DIR / "cyberpunk_event.png")

    # 4. Minimalist Elegant Poster Backdrop
    img4 = Image.new("RGB", (1080, 1350), (245, 246, 248))
    draw4 = ImageDraw.Draw(img4)
    draw4.rectangle([(60, 60), (1020, 1290)], outline=(210, 215, 225), width=3)
    draw4.ellipse([(340, 300), (740, 700)], fill=(230, 235, 245))
    img4.save(POSTER_DIR / "minimalist_editorial.png")

    # 5. Sunset Ambient Poster Backdrop
    img5 = Image.new("RGB", (1080, 1350), (35, 20, 45))
    draw5 = ImageDraw.Draw(img5)
    for y in range(1350):
        ratio = y / 1350
        r = int(255 * (1 - ratio) + 30 * ratio)
        g = int(80 * (1 - ratio) + 20 * ratio)
        b = int(120 * (1 - ratio) + 60 * ratio)
        draw5.line([(0, y), (1080, y)], fill=(r, g, b))
    img5.save(POSTER_DIR / "sunset_vibes.png")

    print("Starter assets created successfully.")


if __name__ == "__main__":
    create_starter_assets()
