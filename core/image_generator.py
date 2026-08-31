"""
Standalone AI Image Generation Module.
Provides prompt expansion, multi-provider AI image generation (Pollinations, Google Imagen, OpenAI DALL-E),
and complete pipeline orchestration independent from any UI.
"""
import io
import json
import os
import re
import base64
from pathlib import Path
from typing import Literal
import requests
from PIL import Image
from dotenv import load_dotenv

from utils.helpers import fit_image_to_aspect_ratio, create_gradient_background, hex_to_rgb
from config import COLOR_PALETTES

# Ensure .env from project root is explicitly loaded
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(dotenv_path=BASE_DIR / ".env", override=True)


class ImageGenerationError(Exception):
    """Base exception for image generation errors."""
    pass


class ImageGenAuthError(ImageGenerationError):
    """Raised when authentication / API key for image provider is invalid or missing."""
    pass


class ImageGenNetworkError(ImageGenerationError):
    """Raised on network timeouts or connection failures during image generation."""
    pass


class ImageGenEmptyResponseError(ImageGenerationError):
    """Raised when image generation returns empty or unreadable image bytes."""
    pass


def sanitize_image_error(msg: str, key: str | None = None) -> str:
    """Strips API keys from error outputs."""
    if not msg:
        return ""
    res = msg
    if key and key.strip():
        res = res.replace(key.strip(), "[REDACTED]")
    res = re.sub(r'key=[a-zA-Z0-9_\-]+', 'key=[REDACTED]', res)
    return res


# Preset Prompt Style Modifiers for high-impact poster backdrops
PROMPT_STYLE_MODIFIERS = {
    "Cinematic & Neon": "cinematic lighting, vibrant neon accents, high contrast, clean negative space for typography, octane render, 8k resolution",
    "Minimalist & Modern": "minimalist abstract aesthetic, smooth matte textures, subtle geometric shadows, elegant editorial composition, studio lighting",
    "Dark Tech & Cyberpunk": "futuristic dark cyberpunk atmosphere, glowing cyan and magenta circuitry, holographic depth, sleek digital art",
    "Warm Sunset Ambient": "warm golden hour lighting, soft gradient sunset tones, dramatic rim lighting, aesthetic bokeh, cinematic depth of field",
    "Bold Abstract 3D": "abstract 3D floating shapes, iridescent glassmorphism, dynamic fluid wave composition, modern graphic design backdrop",
    "Classic Meme Cartoon": "funny relatable illustration, vibrant comic art style, expressive characters, bold colors, clean background"
}


def generate_image_prompt(
    topic: str,
    style: str = "Cinematic & Neon",
    mood: str = "Energetic",
    event_type: str = "Poster",
    additional_details: str = ""
) -> str:
    """
    Generates an optimized, visually descriptive image generation prompt from user inputs.
    Crafted to ensure clean composition with room for typography overlays.
    """
    topic_clean = topic.strip() if topic and topic.strip() else "Modern Technology Summit"
    modifier = PROMPT_STYLE_MODIFIERS.get(style, PROMPT_STYLE_MODIFIERS["Cinematic & Neon"])
    
    details_clause = f", featuring {additional_details.strip()}" if additional_details and additional_details.strip() else ""

    if event_type.lower() == "meme":
        prompt = (
            f"A funny, expressive, viral meme illustration about {topic_clean}{details_clause}. "
            f"Style: {modifier}, mood: {mood}, clear focal point, vibrant colors, uncluttered layout."
        )
    else:
        prompt = (
            f"A stunning, professional visual background for a {event_type} about {topic_clean}{details_clause}. "
            f"Mood: {mood}. Aesthetic: {modifier}. "
            f"High visual impact, centered composition with balanced negative space for text overlay, no embedded text or letters."
        )

    return prompt


def generate_image_pollinations(
    prompt: str,
    width: int = 1080,
    height: int = 1350,
    seed: int = 42,
    timeout: int = 30
) -> Image.Image:
    """
    Generates an image via the Pollinations API (fast, reliable, zero-config).
    """
    if not prompt or not prompt.strip():
        prompt = "Vibrant abstract graphic design poster backdrop"

    encoded_prompt = requests.utils.quote(prompt.strip())
    url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width={width}&height={height}&seed={seed}&nologo=true"

    try:
        response = requests.get(url, timeout=timeout)
    except requests.exceptions.Timeout:
        raise ImageGenNetworkError(f"Pollinations image generation timed out after {timeout} seconds.")
    except requests.exceptions.RequestException as e:
        raise ImageGenNetworkError(f"Network error during image generation: {str(e)}")

    if response.status_code != 200:
        raise ImageGenerationError(f"Pollinations API returned status {response.status_code}: {response.text[:200]}")

    if not response.content:
        raise ImageGenEmptyResponseError("Pollinations API returned empty image content.")

    try:
        image = Image.open(io.BytesIO(response.content)).convert("RGB")
        return fit_image_to_aspect_ratio(image, width, height, fit_mode="cover")
    except Exception as e:
        raise ImageGenEmptyResponseError(f"Failed to decode image from API response: {str(e)}")


def generate_image_gemini_imagen(
    prompt: str,
    api_key: str | None = None,
    aspect_ratio: str = "4:5",
    timeout: int = 40
) -> Image.Image:
    """
    Generates an image via Google Imagen API using GEMINI_API_KEY.
    Tries candidate model versions (imagen-3.0-generate-002, imagen-3.0-generate-001).
    """
    key = api_key
    if not key:
        try:
            import streamlit as st
            key = st.secrets.get("IMAGEN_API_KEY") or st.secrets.get("GEMINI_API_KEY") or st.secrets.get("GOOGLE_API_KEY")
        except Exception:
            pass
    if not key:
        key = os.getenv("IMAGEN_API_KEY") or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")

    if not key:
        raise ImageGenAuthError("Gemini / Imagen API key is missing. Set GEMINI_API_KEY in .env, streamlit secrets, or environment.")

    candidate_models = ["imagen-3.0-generate-002", "imagen-3.0-generate-001", "image-generation-001"]
    last_error = None

    for model_id in candidate_models:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_id}:predict?key={key}"
        headers = {"Content-Type": "application/json"}
        payload = {
            "instances": [
                {"prompt": prompt}
            ],
            "parameters": {
                "sampleCount": 1,
                "aspectRatio": aspect_ratio,
                "outputMimeType": "image/jpeg"
            }
        }

        try:
            response = requests.post(url, headers=headers, json=payload, timeout=timeout)
        except requests.exceptions.RequestException as e:
            last_error = f"Network error: {str(e)}"
            continue

        if response.status_code == 200:
            try:
                data = response.json()
                predictions = data.get("predictions", [])
                if predictions and "bytesBase64Encoded" in predictions[0]:
                    img_b64 = predictions[0]["bytesBase64Encoded"]
                    img_bytes = base64.b64decode(img_b64)
                    return Image.open(io.BytesIO(img_bytes)).convert("RGB")
            except Exception as e:
                last_error = str(e)
                continue
        else:
            last_error = f"Imagen API Error (HTTP {response.status_code}): {response.text[:250]}"

    raise ImageGenerationError(last_error or "Imagen API model not available for this API key.")


def generate_image_openai_dalle(
    prompt: str,
    api_key: str | None = None,
    size: str = "1024x1024",
    timeout: int = 45
) -> Image.Image:
    """
    Generates an image via OpenAI DALL-E 3 API using OPENAI_API_KEY.
    """
    key = api_key
    if not key:
        try:
            import streamlit as st
            key = st.secrets.get("OPENAI_API_KEY")
        except Exception:
            pass
    if not key:
        key = os.getenv("OPENAI_API_KEY")

    if not key:
        raise ImageGenAuthError("OpenAI API key is missing. Set OPENAI_API_KEY in .env, streamlit secrets, or environment.")

    url = "https://api.openai.com/v1/images/generations"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {key}"
    }
    payload = {
        "model": "dall-e-3",
        "prompt": prompt,
        "n": 1,
        "size": size,
        "response_format": "b64_json"
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=timeout)
    except requests.exceptions.RequestException as e:
        raise ImageGenNetworkError(f"Network error connecting to OpenAI DALL-E API: {str(e)}")

    if response.status_code != 200:
        raise ImageGenerationError(f"OpenAI DALL-E Error (HTTP {response.status_code}): {response.text[:250]}")

    try:
        data = response.json()
        img_data = data.get("data", [])
        if not img_data or "b64_json" not in img_data[0]:
            raise ImageGenEmptyResponseError("OpenAI DALL-E returned no image data.")
        
        img_bytes = base64.b64decode(img_data[0]["b64_json"])
        return Image.open(io.BytesIO(img_bytes)).convert("RGB")
    except Exception as e:
        raise ImageGenEmptyResponseError(f"Failed to parse DALL-E image response: {str(e)}")


def generate_image(
    prompt: str,
    width: int = 1080,
    height: int = 1350,
    provider: Literal["auto", "pollinations", "gemini", "openai"] = "auto",
    api_key: str | None = None,
    seed: int = 42,
    timeout: int = 30
) -> Image.Image:
    """
    Unified entry point for AI image generation with automatic fallback.
    If Gemini or OpenAI fail (e.g. HTTP 404, subscription limits), gracefully falls back to Pollinations.
    """
    if provider == "gemini":
        try:
            img = generate_image_gemini_imagen(prompt, api_key=api_key, timeout=timeout)
            return fit_image_to_aspect_ratio(img, width, height, fit_mode="cover")
        except Exception:
            # Graceful fallback to Pollinations if Imagen is not enabled on the key
            return generate_image_pollinations(prompt, width=width, height=height, seed=seed, timeout=timeout)

    elif provider == "openai":
        try:
            img = generate_image_openai_dalle(prompt, api_key=api_key, timeout=timeout)
            return fit_image_to_aspect_ratio(img, width, height, fit_mode="cover")
        except Exception:
            return generate_image_pollinations(prompt, width=width, height=height, seed=seed, timeout=timeout)

    elif provider == "pollinations":
        return generate_image_pollinations(prompt, width=width, height=height, seed=seed, timeout=timeout)

    else:  # "auto"
        # 1. Try Gemini if key is provided or present in environment
        gemini_key = api_key or os.getenv("IMAGEN_API_KEY") or os.getenv("GEMINI_API_KEY")
        if gemini_key:
            try:
                img = generate_image_gemini_imagen(prompt, api_key=gemini_key, timeout=timeout)
                return fit_image_to_aspect_ratio(img, width, height, fit_mode="cover")
            except Exception:
                pass  # Fallthrough to next provider

        # 2. Try OpenAI if key is present in environment
        openai_key = os.getenv("OPENAI_API_KEY")
        if openai_key:
            try:
                img = generate_image_openai_dalle(prompt, api_key=openai_key, timeout=timeout)
                return fit_image_to_aspect_ratio(img, width, height, fit_mode="cover")
            except Exception:
                pass

        # 3. Default to Pollinations (free, instant, 100% reliable)
        return generate_image_pollinations(prompt, width=width, height=height, seed=seed, timeout=timeout)
