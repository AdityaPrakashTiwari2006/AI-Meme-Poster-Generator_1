"""
FastAPI Backend Server for AI Meme & Poster Studio.
Provides unified REST API endpoints for composition, caption generation,
image generation, and serving static assets.
"""
import base64
import io
import os
import sys

# Setup folder paths and add project root to sys.path for Render deployment
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from config import ASPECT_RATIOS, TONE_PRESETS, COLOR_PALETTES, MEME_TEMPLATES_DIR, POSTER_TEMPLATES_DIR
from utils.font_loader import get_available_fonts
from utils.helpers import create_gradient_background
from core.composer import compose_meme, compose_poster
from core.llm_service import generate_captions_flexible
from core.image_generator import generate_image, generate_image_prompt

app = FastAPI(title="AI Meme & Poster Studio API")

# Setup folder paths
BASE_DIR = Path(__file__).resolve().parent
FRONTEND_DIR = BASE_DIR / "frontend"
FRONTEND_DIR.mkdir(parents=True, exist_ok=True)
ASSETS_DIR = BASE_DIR / "assets"

# Request Models
class CaptionRequest(BaseModel):
    topic: str
    audience: str = "General Audience"
    tone: str = "Sarcastic & Witty"
    event_type: str = "Meme"
    api_key: Optional[str] = None

class ImageGenRequest(BaseModel):
    prompt: str
    width: int = 1080
    height: int = 1080
    provider: str = "auto"
    api_key: Optional[str] = None

class ImagePromptRequest(BaseModel):
    topic: str
    style: str
    mood: str
    event_type: str

class ComposeRequest(BaseModel):
    content_type: str  # "Meme" or "Poster"
    base_image_b64: Optional[str] = None
    template_name: Optional[str] = None
    gradient_palette: Optional[str] = None  # name of palette from COLOR_PALETTES
    target_size: List[int] = [1080, 1080]
    safe_margin: int = 80
    font_name: str = "Impact"
    
    # Meme Config
    top_text: str = ""
    bottom_text: str = ""
    text_color_hex: str = "#FFFFFF"
    stroke_color_hex: str = "#000000"
    stroke_width: int = 5
    font_size: int = 64
    uppercase: bool = True
    vertical_offset: int = 0
    darken_overlay: float = 0.0
    
    # Poster Config
    title: str = ""
    subtitle: str = ""
    caption: str = ""
    badge_text: str = ""
    date_time: str = ""
    location_cta: str = ""
    title_color_hex: str = "#FFFFFF"
    subtitle_color_hex: str = "#F0F0F0"
    caption_color_hex: str = "#CCCCCC"
    accent_color_hex: str = "#00F0FF"
    overlay_opacity: float = 0.60
    layout_align: str = "center"
    show_border: bool = True

def get_template_map(directory: Path) -> dict[str, Path]:
    templates = {}
    if directory.exists():
        for f in directory.glob("*.*"):
            if f.suffix.lower() in [".png", ".jpg", ".jpeg", ".webp"]:
                clean_label = f.stem.replace("_", " ").title()
                templates[clean_label] = f
    return templates

@app.get("/api/fonts")
def list_fonts():
    """Returns list of available TrueType/OpenType font names."""
    try:
        fonts = list(get_available_fonts().keys())
        return {"fonts": fonts}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/templates")
def list_templates():
    """Returns list of available meme and poster templates."""
    try:
        memes = list(get_template_map(MEME_TEMPLATES_DIR).keys())
        posters = list(get_template_map(POSTER_TEMPLATES_DIR).keys())
        return {
            "meme_templates": memes,
            "poster_templates": posters
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/config")
def get_global_config():
    """Returns core aspect ratio mapping and tone lists for frontend drop-downs."""
    return {
        "aspect_ratios": ASPECT_RATIOS,
        "tones": TONE_PRESETS,
        "palettes": COLOR_PALETTES
    }

@app.post("/api/captions")
def api_generate_captions(req: CaptionRequest):
    """Generates 5 AI captions with standard fallback."""
    try:
        caps, notice = generate_captions_flexible(
            topic=req.topic,
            audience=req.audience,
            tone=req.tone,
            event_type=req.event_type,
            api_key=req.api_key
        )
        return {"captions": caps, "notice": notice}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/generate-image")
def api_generate_image(req: ImageGenRequest):
    """Triggers prompt expansion and image generator pipeline."""
    try:
        image = generate_image(
            prompt=req.prompt,
            width=req.width,
            height=req.height,
            provider=req.provider,
            api_key=req.api_key
        )
        
        # Save to base64 string
        buffered = io.BytesIO()
        image.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
        return {"image_b64": f"data:image/png;base64,{img_str}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/generate-prompt")
def api_generate_prompt(req: ImagePromptRequest):
    """Generates a typography-optimized image prompt based on parameters."""
    try:
        prompt = generate_image_prompt(
            topic=req.topic,
            style=req.style,
            mood=req.mood,
            event_type=req.event_type
        )
        return {"prompt": prompt}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/compose")
def api_compose(req: ComposeRequest):
    """Composes the final poster or meme from visual settings."""
    try:
        w, h = req.target_size
        
        # 1. Resolve Background Image Source
        base_img = None
        if req.base_image_b64:
            # Load user-uploaded base64 image
            try:
                header, base64_data = req.base_image_b64.split(",", 1) if "," in req.base_image_b64 else ("", req.base_image_b64)
                img_data = base64.b64decode(base64_data)
                base_img = Image.open(io.BytesIO(img_data)).convert("RGB")
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"Failed to parse base_image_b64: {str(e)}")
        
        elif req.template_name:
            # Load stock template
            templates = {**get_template_map(MEME_TEMPLATES_DIR), **get_template_map(POSTER_TEMPLATES_DIR)}
            fpath = templates.get(req.template_name)
            if fpath and fpath.exists():
                try:
                    base_img = Image.open(fpath).convert("RGB")
                except Exception as e:
                    raise HTTPException(status_code=500, detail=f"Failed to open template file: {str(e)}")
            else:
                raise HTTPException(status_code=404, detail=f"Template '{req.template_name}' not found.")
        
        elif req.gradient_palette:
            # Procedural Gradient Backdrop
            palette = COLOR_PALETTES.get(req.gradient_palette)
            if palette:
                bg_hex = palette["background"]
                # Convert hex to RGB values
                from utils.helpers import hex_to_rgb
                bg_rgb = hex_to_rgb(bg_hex)
                # Create gradient from background color to a darker tone
                darker_rgb = (max(0, bg_rgb[0]-30), max(0, bg_rgb[1]-30), max(0, bg_rgb[2]-30))
                base_img = create_gradient_background(w, h, start_color=bg_rgb, end_color=darker_rgb, direction="vertical")
            else:
                base_img = create_gradient_background(w, h, start_color=(20, 24, 38), end_color=(8, 10, 16), direction="vertical")

        # 2. Trigger Graphic Compositions
        if req.content_type == "Meme":
            if base_img is None:
                # Memes require a fallback plain canvas if none specified
                base_img = Image.new("RGB", (w, h), (0, 0, 0))
            
            composed = compose_meme(
                base_image=base_img,
                top_text=req.top_text,
                bottom_text=req.bottom_text,
                target_size=(w, h),
                safe_margin=req.safe_margin,
                font_name=req.font_name,
                text_color_hex=req.text_color_hex,
                stroke_color_hex=req.stroke_color_hex,
                stroke_width=req.stroke_width,
                font_size=req.font_size,
                uppercase=req.uppercase,
                vertical_offset=req.vertical_offset,
                darken_overlay=req.darken_overlay
            )
        else:
            # Poster mode
            composed = compose_poster(
                base_image=base_img,
                title=req.title,
                subtitle=req.subtitle,
                caption=req.caption,
                badge_text=req.badge_text,
                date_time=req.date_time,
                location_cta=req.location_cta,
                target_size=(w, h),
                safe_margin=req.safe_margin,
                font_name=req.font_name,
                title_color_hex=req.title_color_hex,
                subtitle_color_hex=req.subtitle_color_hex,
                caption_color_hex=req.caption_color_hex,
                accent_color_hex=req.accent_color_hex,
                overlay_opacity=req.overlay_opacity,
                layout_align=req.layout_align,
                show_border=req.show_border
            )

        # 3. Stream back composed image as base64 PNG
        buffered = io.BytesIO()
        composed.save(buffered, format="PNG")
        composed_b64 = base64.b64encode(buffered.getvalue()).decode("utf-8")
        return {"image_b64": f"data:image/png;base64,{composed_b64}"}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Mount static asset folders for templates/fonts retrieval
if ASSETS_DIR.exists():
    app.mount("/assets", StaticFiles(directory=str(ASSETS_DIR)), name="assets")

# Route handler for index.html serving
@app.get("/")
def serve_index():
    idx_path = FRONTEND_DIR / "index.html"
    if idx_path.exists():
        return FileResponse(idx_path)
    return {"message": "AI Meme & Poster Studio Backend running. Frontend folder empty."}

# Mount static frontend serving after all API paths are defined
app.mount("/", StaticFiles(directory=str(FRONTEND_DIR)), name="frontend")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)
