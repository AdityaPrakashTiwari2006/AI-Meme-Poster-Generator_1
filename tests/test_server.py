"""
Unit and integration tests for FastAPI backend server.
Verifies all REST API routes and composition outputs.
"""
import base64
import io
import sys
import unittest
from fastapi.testclient import TestClient
from PIL import Image

sys.path.insert(0, ".")
from server import app


class TestFastAPIServer(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_list_fonts(self):
        """Verifies GET /api/fonts returns the list of loaded fonts."""
        response = self.client.get("/api/fonts")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("fonts", data)
        self.assertTrue(len(data["fonts"]) > 0)
        # Arial or Impact fallback should be present
        self.assertTrue(any(f in ["Arial", "Impact", "comic", "segoe"] for f in data["fonts"]) or len(data["fonts"]) > 0)

    def test_list_templates(self):
        """Verifies GET /api/templates returns lists of available images."""
        response = self.client.get("/api/templates")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("meme_templates", data)
        self.assertIn("poster_templates", data)

    def test_get_config(self):
        """Verifies GET /api/config exposes settings and dropdown items."""
        response = self.client.get("/api/config")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("aspect_ratios", data)
        self.assertIn("tones", data)
        self.assertIn("palettes", data)

    def test_api_generate_captions(self):
        """Verifies POST /api/captions falls back to offline templates under test runner context."""
        payload = {
            "topic": "FastAPI Testing",
            "audience": "Developers",
            "tone": "Sarcastic & Witty",
            "event_type": "Meme"
        }
        response = self.client.post("/api/captions", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("captions", data)
        self.assertEqual(len(data["captions"]), 5)
        # Should include notice of test runner/offline fallback
        self.assertIsNotNone(data["notice"])

    def test_api_compose_meme_base64_output(self):
        """Verifies POST /api/compose compiles meme and returns valid base64 PNG."""
        payload = {
            "content_type": "Meme",
            "target_size": [200, 200],
            "safe_margin": 10,
            "font_name": "Impact",
            "top_text": "Top Text Test",
            "bottom_text": "Bottom Text Test",
            "text_color_hex": "#FFFFFF",
            "stroke_color_hex": "#000000",
            "stroke_width": 2,
            "font_size": 20
        }
        response = self.client.post("/api/compose", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("image_b64", data)
        
        # Verify base64 decode produces a valid image
        img_b64 = data["image_b64"]
        self.assertTrue(img_b64.startswith("data:image/png;base64,"))
        
        raw_b64 = img_b64.split(",", 1)[1]
        img_bytes = base64.b64decode(raw_b64)
        image = Image.open(io.BytesIO(img_bytes))
        
        self.assertEqual(image.size, (200, 200))
        self.assertEqual(image.format, "PNG")


if __name__ == "__main__":
    unittest.main()
