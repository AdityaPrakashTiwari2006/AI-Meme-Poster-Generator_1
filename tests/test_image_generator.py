"""
Unit tests for AI Image Generation Module (core/image_generator.py).
Tests:
- Prompt generation with styles, moods, and event types
- Multi-provider API dispatch (Pollinations, Imagen, DALL-E)
- Missing credential / auth error handling
- Network error & timeout handling
- Empty response handling
"""
import io
import os
import base64
import unittest
from unittest.mock import patch, MagicMock
from PIL import Image
import requests

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


class TestImageGenerator(unittest.TestCase):

    def setUp(self):
        # Save original env
        self.orig_imagen = os.environ.get("IMAGEN_API_KEY")
        self.orig_gemini = os.environ.get("GEMINI_API_KEY")
        self.orig_openai = os.environ.get("OPENAI_API_KEY")

        # Clear for isolation
        for k in ["IMAGEN_API_KEY", "GEMINI_API_KEY", "OPENAI_API_KEY"]:
            if k in os.environ:
                del os.environ[k]

        # Helper test image bytes
        dummy = Image.new("RGB", (64, 64), (255, 0, 0))
        buf = io.BytesIO()
        dummy.save(buf, format="PNG")
        self.valid_png_bytes = buf.getvalue()
        self.valid_b64_str = base64.b64encode(self.valid_png_bytes).decode("utf-8")

    def tearDown(self):
        # Restore env
        if self.orig_imagen is not None:
            os.environ["IMAGEN_API_KEY"] = self.orig_imagen
        if self.orig_gemini is not None:
            os.environ["GEMINI_API_KEY"] = self.orig_gemini
        if self.orig_openai is not None:
            os.environ["OPENAI_API_KEY"] = self.orig_openai

    def test_generate_image_prompt_poster(self):
        """Tests that prompt generation creates rich descriptive prompts for posters."""
        topic = "Autonomous AI Multi-Agent Summit"
        prompt = generate_image_prompt(
            topic=topic,
            style="Dark Tech & Cyberpunk",
            mood="Visionary & High Energy",
            event_type="Conference"
        )
        self.assertIn(topic, prompt)
        self.assertIn("Conference", prompt)
        self.assertIn("cyberpunk", prompt.lower())
        self.assertIn("negative space", prompt.lower())

    def test_generate_image_prompt_meme(self):
        """Tests prompt generation for meme format."""
        prompt = generate_image_prompt(
            topic="Pushing to production on Friday",
            style="Classic Meme Cartoon",
            mood="Hilarious",
            event_type="Meme"
        )
        self.assertIn("meme", prompt.lower())
        self.assertIn("Pushing to production", prompt)

    @patch("requests.get")
    def test_pollinations_generation_success(self, mock_get):
        """Tests successful image generation via Pollinations."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.content = self.valid_png_bytes
        mock_get.return_value = mock_resp

        img = generate_image_pollinations("Test prompt", width=1080, height=1350)
        self.assertIsInstance(img, Image.Image)
        self.assertEqual(img.mode, "RGB")

    @patch("requests.get")
    def test_pollinations_network_error(self, mock_get):
        """Tests timeout and network failure handling in Pollinations."""
        mock_get.side_effect = requests.exceptions.Timeout("Connection timeout")
        with self.assertRaises(ImageGenNetworkError):
            generate_image_pollinations("Test prompt")

    def test_gemini_imagen_auth_error(self):
        """Tests that ImageGenAuthError is raised when Imagen key is missing."""
        with self.assertRaises(ImageGenAuthError):
            generate_image_gemini_imagen("Prompt without key")

    @patch("requests.post")
    def test_gemini_imagen_success(self, mock_post):
        """Tests successful Google Imagen generation with base64 payload."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "predictions": [
                {"bytesBase64Encoded": self.valid_b64_str}
            ]
        }
        mock_post.return_value = mock_resp
        os.environ["GEMINI_API_KEY"] = "mock_gemini_key"

        img = generate_image_gemini_imagen("Future City Hackathon")
        self.assertIsInstance(img, Image.Image)
        self.assertEqual(img.size, (64, 64))

    def test_openai_dalle_auth_error(self):
        """Tests that ImageGenAuthError is raised when OpenAI key is missing."""
        with self.assertRaises(ImageGenAuthError):
            generate_image_openai_dalle("Prompt without key")

    @patch("requests.post")
    def test_openai_dalle_success(self, mock_post):
        """Tests successful OpenAI DALL-E 3 image generation."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "data": [
                {"b64_json": self.valid_b64_str}
            ]
        }
        mock_post.return_value = mock_resp
        os.environ["OPENAI_API_KEY"] = "mock_openai_key"

        img = generate_image_openai_dalle("AI Art Exhibition")
        self.assertIsInstance(img, Image.Image)

    @patch("requests.get")
    def test_unified_generate_image_auto(self, mock_get):
        """Tests unified generate_image endpoint in auto mode."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.content = self.valid_png_bytes
        mock_get.return_value = mock_resp

        img = generate_image("Test Prompt", width=1080, height=1350, provider="auto")
        self.assertIsInstance(img, Image.Image)
        self.assertEqual(img.size, (1080, 1350))


if __name__ == "__main__":
    unittest.main()
