"""
AI Meme & Poster Creator - Streamlit User Interface.
Orchestrates inputs, LLM caption generation, template selection, Pillow composition,
live visual preview, and high-resolution PNG export.
"""
import os
from pathlib import Path
import streamlit as st
from PIL import Image
from dotenv import load_dotenv

import sys

# Ensure .env is explicitly loaded and project root is in sys.path
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

load_dotenv(dotenv_path=BASE_DIR / ".env", override=True)

from config import (
    ASPECT_RATIOS,
    TONE_PRESETS,
    COLOR_PALETTES,
    MEME_TEMPLATES_DIR,
    POSTER_TEMPLATES_DIR
)
from utils.font_loader import get_available_fonts
from utils.helpers import image_to_bytes
from core.composer import compose_meme, compose_poster
from core.llm_service import generate_captions_flexible
from core.image_gen_service import create_procedural_backdrop, fetch_pollinations_image

# Streamlit Page Setup
st.set_page_config(
    page_title="AI Meme & Poster Creator",
    page_icon="🎨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Clean CSS Styling
st.markdown("""
<style>
    .block-container {
        padding-top: 1.8rem;
        padding-bottom: 2.5rem;
    }
    .main-title {
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        font-weight: 800;
        font-size: 2.1rem;
        margin-bottom: 0.2rem;
    }
    .main-subtitle {
        font-size: 1.0rem;
        color: #8b949e;
        margin-bottom: 1.2rem;
    }
    .section-box {
        background: rgba(255, 255, 255, 0.02);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 10px;
        padding: 1.2rem;
        margin-bottom: 1.2rem;
    }
    .suggestion-box {
        background: rgba(0, 240, 255, 0.04);
        border: 1px solid rgba(0, 240, 255, 0.15);
        border-radius: 8px;
        padding: 0.75rem;
        margin-bottom: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)


def load_templates(directory: Path) -> dict[str, Path]:
    """Loads all image files from template folder into a dictionary."""
    templates = {}
    if directory.exists():
        for f in directory.glob("*.*"):
            if f.suffix.lower() in [".png", ".jpg", ".jpeg", ".webp"]:
                clean_label = f.stem.replace("_", " ").title()
                templates[clean_label] = f
    return templates


def main():
    # Sidebar - Global Config & Dimensions
    st.sidebar.markdown("## ⚙️ Canvas & API Settings")
    
    aspect_choice = st.sidebar.selectbox(
        "Canvas Aspect Ratio:",
        list(ASPECT_RATIOS.keys()),
        index=1  # Default to 4:5 Instagram Portrait (1080x1350)
    )
    target_dimensions = ASPECT_RATIOS[aspect_choice]

    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🔑 API Configuration")
    
    env_gemini_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY") or os.getenv("LLM_API_KEY")
    if env_gemini_key and env_gemini_key.strip():
        st.sidebar.success("✅ `GEMINI_API_KEY` loaded from `.env`")
        user_api_key = st.sidebar.text_input(
            "Gemini API Key (Optional override):",
            type="password",
            help="Key is loaded from your .env file. Enter a key here only if you wish to override it."
        )
    else:
        st.sidebar.info("ℹ️ No `GEMINI_API_KEY` in `.env` (using offline templates).")
        user_api_key = st.sidebar.text_input(
            "Gemini API Key:",
            type="password",
            help="Enter your Gemini API key or add GEMINI_API_KEY=your_key in .env"
        )

    available_fonts = get_available_fonts()
    font_names = list(available_fonts.keys())

    # Header
    st.markdown('<div class="main-title">🎨 AI Meme & Poster Creator</div>', unsafe_allow_html=True)
    st.markdown('<div class="main-subtitle">Generate AI captions, select templates, compose high-res visual designs, and export as PNG.</div>', unsafe_allow_html=True)

    # Initialize Session States
    if "content_type" not in st.session_state:
        st.session_state["content_type"] = "Poster"
    if "topic" not in st.session_state:
        st.session_state["topic"] = "AI Hackathon 2026"
    if "event_name" not in st.session_state:
        st.session_state["event_name"] = "GLOBAL AI AGENTS HACKATHON"
    if "date" not in st.session_state:
        st.session_state["date"] = "OCTOBER 24-26, 2026 • 6:00 PM EST"
    if "location" not in st.session_state:
        st.session_state["location"] = "SAN FRANCISCO & VIRTUAL • REGISTER AT HACK.IO"
    if "subtitle" not in st.session_state:
        st.session_state["subtitle"] = "Build autonomous multi-agent systems and win $50,000 in prizes."
    if "caption_text" not in st.session_state:
        st.session_state["caption_text"] = "Open to developers, designers, and AI creators worldwide."
    if "badge" not in st.session_state:
        st.session_state["badge"] = "FEATURED HACKATHON"
    if "meme_top_text" not in st.session_state:
        st.session_state["meme_top_text"] = "WHEN YOU DEPLOY CODE ON FRIDAY"
    if "meme_bottom_text" not in st.session_state:
        st.session_state["meme_bottom_text"] = "AND THE WHOLE DATABASE SHUTS DOWN"
    if "rendered_poster" not in st.session_state:
        st.session_state["rendered_poster"] = None
    if "current_image" not in st.session_state:
        st.session_state["current_image"] = None

    # Dual Column Interface
    col_form, col_view = st.columns([1.15, 1.0], gap="large")

    with col_form:
        # 1. Content Type Selector
        st.markdown("### 1. Project Configuration")
        content_type = st.radio(
            "Content Type:",
            ["Poster", "Meme"],
            horizontal=True,
            index=0 if st.session_state["content_type"] == "Poster" else 1
        )
        st.session_state["content_type"] = content_type

        # 2. Topic, Event Details & Tone
        c_t1, c_t2 = st.columns(2)
        with c_t1:
            topic_val = st.text_input(
                "Topic / Theme:",
                value=st.session_state["topic"],
                placeholder="e.g. AI Agents, Startup Launch, Gym Motivation, Debugging"
            )
            st.session_state["topic"] = topic_val
        with c_t2:
            tone_val = st.selectbox(
                "Tone:",
                TONE_PRESETS,
                index=0 if content_type == "Meme" else 5
            )

        if content_type == "Poster":
            event_name_val = st.text_input(
                "Event Name / Title:",
                value=st.session_state["event_name"],
                placeholder="e.g. ANNUAL TECH SUMMIT"
            )
            st.session_state["event_name"] = event_name_val

            c_d1, c_d2 = st.columns(2)
            with c_d1:
                date_val = st.text_input(
                    "Date & Time:",
                    value=st.session_state["date"],
                    placeholder="e.g. OCT 24, 2026 • 7:00 PM"
                )
                st.session_state["date"] = date_val
            with c_d2:
                loc_val = st.text_input(
                    "Location / CTA:",
                    value=st.session_state["location"],
                    placeholder="e.g. MAIN AUDITORIUM • RSVP NOW"
                )
                st.session_state["location"] = loc_val

        # 3. AI Caption Generator & Selection
        st.markdown("---")
        st.markdown("### 2. AI Copywriting & Captions")
        
        c_btn_gen, _ = st.columns([1.2, 1.0])
        with c_btn_gen:
            gen_captions_btn = st.button("✨ Generate Captions", use_container_width=True)

        if gen_captions_btn:
            with st.spinner("Generating 5 AI caption suggestions..."):
                caps, notice = generate_captions_flexible(
                    topic=st.session_state["topic"],
                    audience="General Audience / Tech Enthusiasts",
                    tone=tone_val,
                    event_type=content_type,
                    api_key=user_api_key if user_api_key.strip() else None
                )
                st.session_state["captions_cache"] = caps
                st.session_state["caption_notice"] = notice

        if st.session_state.get("caption_notice"):
            st.info(st.session_state["caption_notice"])

        # Caption Selection Dropdown / Selector
        captions_list = st.session_state.get("captions_cache", [])
        if captions_list:
            caption_labels = []
            for i, c in enumerate(captions_list):
                if content_type == "Meme":
                    caption_labels.append(f"Option {i+1}: \"{c['top_text']}\" / \"{c['bottom_text']}\"")
                else:
                    caption_labels.append(f"Option {i+1}: {c['title']} - {c.get('subtitle', '')[:35]}...")

            selected_caption_idx = st.selectbox(
                "Caption Selection (Choose from 5 AI Suggestions):",
                range(len(caption_labels)),
                format_func=lambda idx: caption_labels[idx]
            )

            # Apply selected caption button
            if st.button("📥 Apply Selected Caption to Form", use_container_width=True):
                chosen = captions_list[selected_caption_idx]
                if content_type == "Meme":
                    st.session_state["meme_top_text"] = chosen["top_text"]
                    st.session_state["meme_bottom_text"] = chosen["bottom_text"]
                else:
                    st.session_state["badge"] = chosen.get("badge", "FEATURED")
                    st.session_state["event_name"] = chosen.get("title", st.session_state["topic"].upper())
                    st.session_state["subtitle"] = chosen.get("subtitle", "")
                    st.session_state["caption_text"] = chosen.get("caption", "")
                st.rerun()

        # Editable Text Fields
        if content_type == "Meme":
            st.session_state["meme_top_text"] = st.text_area(
                "Top Text (Header):",
                value=st.session_state["meme_top_text"],
                height=65
            )
            st.session_state["meme_bottom_text"] = st.text_area(
                "Bottom Text (Punchline):",
                value=st.session_state["meme_bottom_text"],
                height=65
            )
        else:
            c_p1, c_p2 = st.columns([1, 2])
            with c_p1:
                st.session_state["badge"] = st.text_input("Badge / Category:", value=st.session_state["badge"])
            with c_p2:
                st.session_state["subtitle"] = st.text_input("Subtitle / Tagline:", value=st.session_state["subtitle"])
            
            st.session_state["caption_text"] = st.text_area(
                "Caption / Description:",
                value=st.session_state["caption_text"],
                height=65
            )

        # 4. Template & Background Selector
        st.markdown("---")
        st.markdown("### 3. Template & Background Source")
        
        bg_source = st.radio(
            "Select Background Type:",
            ["📂 Template Library", "✨ AI Generated Image", "🎨 Procedural Gradient", "📁 Upload Image"],
            horizontal=True
        )

        if bg_source == "📂 Template Library":
            tpl_dir = MEME_TEMPLATES_DIR if content_type == "Meme" else POSTER_TEMPLATES_DIR
            templates_dict = load_templates(tpl_dir)
            if templates_dict:
                selected_tpl_name = st.selectbox("Template Selector:", list(templates_dict.keys()))
                tpl_path = templates_dict[selected_tpl_name]
                st.session_state["current_image"] = Image.open(tpl_path)
            else:
                st.session_state["current_image"] = create_procedural_backdrop("Neon Cyberpunk", *target_dimensions)

        elif bg_source == "✨ AI Generated Image":
            from core.image_generator import (
                generate_image_prompt,
                generate_image,
                PROMPT_STYLE_MODIFIERS,
                ImageGenerationError
            )

            # 1. Prompt Settings & Auto-Craft
            st.markdown("##### Step A: Generate Image Prompt")
            c_stl, c_mood = st.columns(2)
            with c_stl:
                chosen_style = st.selectbox("Visual Style:", list(PROMPT_STYLE_MODIFIERS.keys()), index=0)
            with c_mood:
                chosen_mood = st.selectbox("Mood / Atmosphere:", ["Energetic", "Visionary & Epic", "Dramatic & Moody", "Playful & Fun", "Sophisticated & Clean"], index=0)

            if "ai_img_prompt" not in st.session_state or st.button("🪄 Auto-Craft Image Prompt", use_container_width=True):
                st.session_state["ai_img_prompt"] = generate_image_prompt(
                    topic=st.session_state["topic"],
                    style=chosen_style,
                    mood=chosen_mood,
                    event_type=content_type
                )

            ai_img_prompt = st.text_area(
                "Image Generation Prompt:",
                value=st.session_state.get("ai_img_prompt", ""),
                height=75
            )
            st.session_state["ai_img_prompt"] = ai_img_prompt

            # 2. Provider Selection & Generation
            st.markdown("##### Step B: Generate Image via API")
            c_prov, c_gen_btn = st.columns([1.2, 1.0])
            with c_prov:
                chosen_provider = st.selectbox(
                    "Image Provider:",
                    ["auto", "pollinations", "gemini", "openai"],
                    format_func=lambda p: {
                        "auto": "⚡ Auto (Gemini / OpenAI / Pollinations)",
                        "pollinations": "🌐 Pollinations.ai (Instant Free)",
                        "gemini": "✨ Google Imagen (GEMINI_API_KEY)",
                        "openai": "🎨 OpenAI DALL-E (OPENAI_API_KEY)"
                    }.get(p, p),
                    index=0
                )
            with c_gen_btn:
                st.write("")
                st.write("")
                trigger_ai_img = st.button("🚀 Generate AI Image", use_container_width=True, type="secondary")

            if trigger_ai_img:
                with st.spinner("Generating background with AI..."):
                    try:
                        fetched_img = generate_image(
                            prompt=ai_img_prompt,
                            width=target_dimensions[0],
                            height=target_dimensions[1],
                            provider=chosen_provider,
                            api_key=user_api_key if user_api_key.strip() else None
                        )
                        st.session_state["current_image"] = fetched_img
                        st.session_state["img_gen_error"] = None
                        st.success("✅ AI Background generated successfully!")
                    except Exception as e:
                        st.session_state["img_gen_error"] = str(e)

            # Fallback upload option if generation fails
            if st.session_state.get("img_gen_error"):
                st.error(f"⚠️ Image generation failed: {st.session_state['img_gen_error']}")
                st.info("💡 You can upload your own background image instead below:")
                fallback_upload = st.file_uploader("Upload Image Fallback:", type=["png", "jpg", "jpeg", "webp"], key="img_gen_fallback_upload")
                if fallback_upload is not None:
                    st.session_state["current_image"] = Image.open(fallback_upload)
                    st.success("Custom background image uploaded!")

        elif bg_source == "🎨 Procedural Gradient":
            chosen_pal = st.selectbox("Palette:", list(COLOR_PALETTES.keys()))
            if st.button("Generate Gradient Backdrop", use_container_width=True) or st.session_state["current_image"] is None:
                st.session_state["current_image"] = create_procedural_backdrop(
                    chosen_pal, target_dimensions[0], target_dimensions[1]
                )

        elif bg_source == "📁 Upload Image":
            up_file = st.file_uploader("Upload Image:", type=["png", "jpg", "jpeg", "webp"], key="main_custom_upload")
            if up_file is not None:
                st.session_state["current_image"] = Image.open(up_file)
            elif st.session_state["current_image"] is None:
                st.session_state["current_image"] = create_procedural_backdrop("Midnight Blue", *target_dimensions)

        # Fallback image safety
        if st.session_state["current_image"] is None:
            st.session_state["current_image"] = create_procedural_backdrop("Midnight Blue", *target_dimensions)

        # 5. Styling Customizer
        with st.expander("🎛️ Advanced Typography & Styling Options", expanded=False):
            st_f1, st_f2 = st.columns(2)
            with st_f1:
                selected_font = st.selectbox(
                    "Font Family:",
                    font_names,
                    index=font_names.index("Impact") if (content_type == "Meme" and "Impact" in font_names) else 0
                )
            with st_f2:
                font_sz = st.slider("Font Size Scale:", min_value=24, max_value=120, value=68, step=2)

            if content_type == "Meme":
                m_c1, m_c2, m_c3 = st.columns(3)
                with m_c1:
                    meme_text_color = st.color_picker("Text Color:", "#FFFFFF")
                with m_c2:
                    meme_stroke_color = st.color_picker("Stroke Color:", "#000000")
                with m_c3:
                    meme_stroke_w = st.slider("Stroke Width:", 0, 12, 5)

                uppercase_mode = st.checkbox("Uppercase Text", value=True)
                v_offset = st.slider("Vertical Offset (px):", -100, 100, 0, step=5)
            else:
                p_c1, p_c2, p_c3 = st.columns(3)
                with p_c1:
                    title_col = st.color_picker("Title Color:", "#FFFFFF")
                with p_c2:
                    sub_col = st.color_picker("Subtitle Color:", "#F0F0F0")
                with p_c3:
                    accent_col = st.color_picker("Accent Color:", "#00F0FF")

                overlay_val = st.slider("Dark Scrim Overlay:", 0.0, 0.95, 0.60, step=0.05)
                show_border_val = st.checkbox("Framing Border", value=True)
                align_val = st.selectbox("Text Alignment:", ["center", "left"], index=0)

        # 6. Generate Poster / Meme Button
        st.markdown("---")
        generate_action_label = "🎨 Generate Meme" if content_type == "Meme" else "🎨 Generate Poster"
        if st.button(generate_action_label, use_container_width=True, type="primary") or st.session_state["rendered_poster"] is None:
            base_bg = st.session_state["current_image"]
            if content_type == "Meme":
                st.session_state["rendered_poster"] = compose_meme(
                    base_image=base_bg,
                    top_text=st.session_state["meme_top_text"],
                    bottom_text=st.session_state["meme_bottom_text"],
                    target_size=target_dimensions,
                    font_name=selected_font,
                    text_color_hex=meme_text_color if 'meme_text_color' in locals() else "#FFFFFF",
                    stroke_color_hex=meme_stroke_color if 'meme_stroke_color' in locals() else "#000000",
                    stroke_width=meme_stroke_w if 'meme_stroke_w' in locals() else 5,
                    font_size=font_sz,
                    uppercase=uppercase_mode if 'uppercase_mode' in locals() else True,
                    vertical_offset=v_offset if 'v_offset' in locals() else 0
                )
            else:
                st.session_state["rendered_poster"] = compose_poster(
                    base_image=base_bg,
                    title=st.session_state["event_name"],
                    subtitle=st.session_state["subtitle"],
                    caption=st.session_state["caption_text"],
                    badge_text=st.session_state["badge"],
                    date_time=st.session_state["date"],
                    location_cta=st.session_state["location"],
                    target_size=target_dimensions,
                    font_name=selected_font,
                    title_color_hex=title_col if 'title_col' in locals() else "#FFFFFF",
                    subtitle_color_hex=sub_col if 'sub_col' in locals() else "#F0F0F0",
                    accent_color_hex=accent_col if 'accent_col' in locals() else "#00F0FF",
                    overlay_opacity=overlay_val if 'overlay_val' in locals() else 0.60,
                    layout_align=align_val if 'align_val' in locals() else "center",
                    show_border=show_border_val if 'show_border_val' in locals() else True
                )
            st.success(f"{content_type} generated successfully!")

    # Right Column: Preview & Download PNG
    with col_view:
        st.markdown("### 👁️ Live Canvas Preview")
        
        rendered_result = st.session_state.get("rendered_poster")
        if rendered_result is not None:
            st.image(
                rendered_result,
                use_container_width=True,
                caption=f"{content_type} Output • Resolution: {target_dimensions[0]}x{target_dimensions[1]}px"
            )

            # High Resolution PNG Export
            st.markdown("#### 💾 Export Design")
            export_filename = st.text_input(
                "Export Filename:",
                value=f"{content_type.lower()}_design"
            )

            png_bytes = image_to_bytes(rendered_result, format="PNG")

            st.download_button(
                label=f"⬇️ Download PNG ({len(png_bytes) // 1024} KB)",
                data=png_bytes,
                file_name=f"{export_filename}.png",
                mime="image/png",
                use_container_width=True,
                type="primary"
            )
        else:
            st.info("Click 'Generate Poster' to compose your design.")


if __name__ == "__main__":
    main()
