"""
Unit tests for Gemini API Configuration, Environment Variable Loading,
Security / Redaction, and Offline Fallback Preservation.
"""
import io
import os
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock
from dotenv import load_dotenv

from core.caption_generator import (
    get_api_key,
    generate_ai_captions,
    sanitize_message,
    MissingAPIKeyError,
    APIFailureError
)
from core.llm_service import generate_captions_flexible, get_offline_captions


class TestGeminiAPIConfiguration(unittest.TestCase):

    def setUp(self):
        self.orig_gemini = os.environ.get("GEMINI_API_KEY")
        self.orig_llm = os.environ.get("LLM_API_KEY")
        self.orig_google = os.environ.get("GOOGLE_API_KEY")

        for k in ["GEMINI_API_KEY", "LLM_API_KEY", "GOOGLE_API_KEY"]:
            if k in os.environ:
                del os.environ[k]

    def tearDown(self):
        if self.orig_gemini is not None:
            os.environ["GEMINI_API_KEY"] = self.orig_gemini
        if self.orig_llm is not None:
            os.environ["LLM_API_KEY"] = self.orig_llm
        if self.orig_google is not None:
            os.environ["GOOGLE_API_KEY"] = self.orig_google

    def test_dotenv_in_requirements(self):
        """Verifies python-dotenv is declared in requirements.txt."""
        req_file = Path("requirements.txt")
        self.assertTrue(req_file.exists())
        content = req_file.read_text(encoding="utf-8")
        self.assertIn("python-dotenv", content)

    def test_dotenv_in_gitignore(self):
        """Verifies .env is listed in .gitignore to prevent committing secrets."""
        git_ignore = Path(".gitignore")
        self.assertTrue(git_ignore.exists())
        content = git_ignore.read_text(encoding="utf-8")
        self.assertIn(".env", content)

    def test_no_hardcoded_keys_in_source_code(self):
        """Verifies that no actual API keys are hardcoded in python source files."""
        for py_file in Path(".").rglob("*.py"):
            if "venv" in str(py_file) or ".venv" in str(py_file) or "tests" in str(py_file):
                continue
            code = py_file.read_text(encoding="utf-8")
            self.assertNotIn("AIzaSy", code, f"Potential hardcoded Google API key in {py_file}")
            self.assertNotIn("sk-proj-", code, f"Potential hardcoded OpenAI key in {py_file}")

    def test_load_api_key_from_env(self):
        """Verifies get_api_key reads GEMINI_API_KEY from environment."""
        os.environ["GEMINI_API_KEY"] = "gemini_secure_test_key_abc123"
        key = get_api_key()
        self.assertEqual(key, "gemini_secure_test_key_abc123")

    @patch("requests.post")
    def test_gemini_client_receives_key_correctly(self, mock_post):
        """Verifies that the Gemini REST request receives the API key in the endpoint."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "candidates": [
                {
                    "content": {
                        "parts": [
                            {
                                "text": """[
                                    {"title": "T1", "top_text": "TOP 1", "bottom_text": "BOT 1", "subtitle": "SUB 1", "caption": "CAP 1", "badge": "B1", "full_caption": "F1"},
                                    {"title": "T2", "top_text": "TOP 2", "bottom_text": "BOT 2", "subtitle": "SUB 2", "caption": "CAP 2", "badge": "B2", "full_caption": "F2"},
                                    {"title": "T3", "top_text": "TOP 3", "bottom_text": "BOT 3", "subtitle": "SUB 3", "caption": "CAP 3", "badge": "B3", "full_caption": "F3"},
                                    {"title": "T4", "top_text": "TOP 4", "bottom_text": "BOT 4", "subtitle": "SUB 4", "caption": "CAP 4", "badge": "B4", "full_caption": "F4"},
                                    {"title": "T5", "top_text": "TOP 5", "bottom_text": "BOT 5", "subtitle": "SUB 5", "caption": "CAP 5", "badge": "B5", "full_caption": "F5"}
                                ]"""
                            }
                        ]
                    }
                }
            ]
        }
        mock_post.return_value = mock_response
        test_key = "test_gemini_key_789"
        os.environ["GEMINI_API_KEY"] = test_key

        results = generate_ai_captions(
            topic="Next Gen Robotics",
            audience="Engineers",
            tone="Visionary",
            event_type="Poster"
        )

        self.assertEqual(len(results), 5)
        # Check that mock_post was called with URL containing the key
        called_url = mock_post.call_args[0][0]
        self.assertIn(f"key={test_key}", called_url)

    def test_offline_fallback_preserved_on_missing_key(self):
        """Verifies that missing API key returns 5 offline template suggestions and an informative notice."""
        # Ensure no key in environment
        caps, notice = generate_captions_flexible(
            topic="Debugging at Midnight",
            audience="Developers",
            tone="Sarcastic & Witty",
            event_type="Meme"
        )

        self.assertEqual(len(caps), 5)
        self.assertIsNotNone(notice)
        self.assertIn("API key is missing", notice)
        self.assertIn("offline templates", notice)

    @patch("requests.post")
    def test_notice_disappears_when_valid_key_configured(self, mock_post):
        """Verifies that when a valid key is configured and API succeeds, notice is None."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "candidates": [
                {
                    "content": {
                        "parts": [
                            {
                                "text": """[
                                    {"title": "AI 1", "top_text": "T1", "bottom_text": "B1", "subtitle": "S1", "caption": "C1", "badge": "B1", "full_caption": "F1"},
                                    {"title": "AI 2", "top_text": "T2", "bottom_text": "B2", "subtitle": "S2", "caption": "C2", "badge": "B2", "full_caption": "F2"},
                                    {"title": "AI 3", "top_text": "T3", "bottom_text": "B3", "subtitle": "S3", "caption": "C3", "badge": "B3", "full_caption": "F3"},
                                    {"title": "AI 4", "top_text": "T4", "bottom_text": "B4", "subtitle": "S4", "caption": "C4", "badge": "B4", "full_caption": "F4"},
                                    {"title": "AI 5", "top_text": "T5", "bottom_text": "B5", "subtitle": "S5", "caption": "C5", "badge": "B5", "full_caption": "F5"}
                                ]"""
                            }
                        ]
                    }
                }
            ]
        }
        mock_post.return_value = mock_response
        os.environ["GEMINI_API_KEY"] = "valid_live_key"

        caps, notice = generate_captions_flexible(
            topic="Developer Conference",
            audience="Software Engineers",
            tone="Hype",
            event_type="Poster"
        )

        self.assertEqual(len(caps), 5)
        self.assertIsNone(notice, "Notice/warning must be None when a valid key succeeds!")

    def test_api_key_redaction_in_sanitization(self):
        """Verifies that API keys are completely stripped and redacted from error strings."""
        sensitive_key = "AIzaSySecretApiKey123456789"
        raw_error = f"Error connecting to https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={sensitive_key}: HTTP 403 Forbidden"
        
        sanitized = sanitize_message(raw_error, key=sensitive_key)
        self.assertNotIn(sensitive_key, sanitized)
        self.assertIn("[REDACTED]", sanitized)


if __name__ == "__main__":
    unittest.main()
