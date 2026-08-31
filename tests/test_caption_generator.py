"""
Unit tests for AI Caption Generator Module (core/caption_generator.py).
Tests:
- Missing API Key handling
- API failure / HTTP error handling
- Empty / malformed response handling
- Output format (5 caption suggestions)
- Input parameters integration (topic, audience, tone, event type)
"""
import os
import unittest
from unittest.mock import patch, MagicMock
import requests

from core.caption_generator import (
    generate_ai_captions,
    get_api_key,
    build_prompt,
    parse_llm_json_response,
    MissingAPIKeyError,
    APIFailureError,
    EmptyResponseError
)


class TestCaptionGenerator(unittest.TestCase):

    def setUp(self):
        # Save original env vars
        self.orig_gemini = os.environ.get("GEMINI_API_KEY")
        self.orig_llm = os.environ.get("LLM_API_KEY")
        self.orig_google = os.environ.get("GOOGLE_API_KEY")

        # Clear env vars for isolated tests
        for k in ["GEMINI_API_KEY", "LLM_API_KEY", "GOOGLE_API_KEY"]:
            if k in os.environ:
                del os.environ[k]

    def tearDown(self):
        # Restore env vars
        if self.orig_gemini is not None:
            os.environ["GEMINI_API_KEY"] = self.orig_gemini
        if self.orig_llm is not None:
            os.environ["LLM_API_KEY"] = self.orig_llm
        if self.orig_google is not None:
            os.environ["GOOGLE_API_KEY"] = self.orig_google

    def test_missing_api_key_error(self):
        """Tests that MissingAPIKeyError is raised when no API key is provided or found in env."""
        with self.assertRaises(MissingAPIKeyError):
            get_api_key()

        with self.assertRaises(MissingAPIKeyError):
            generate_ai_captions(
                topic="AI Innovation",
                audience="Developers",
                tone="Witty",
                event_type="Hackathon"
            )

    def test_read_api_key_from_env(self):
        """Tests that API key is correctly read from environment variable."""
        os.environ["GEMINI_API_KEY"] = "test_env_key_123"
        self.assertEqual(get_api_key(), "test_env_key_123")

        # Custom argument overrides env
        self.assertEqual(get_api_key(custom_key="custom_param_key"), "custom_param_key")

    def test_build_prompt_inputs(self):
        """Tests that all 4 input parameters are injected into the prompt."""
        topic = "Quantum Computing Workshop"
        audience = "Physics Students"
        tone = "Inspirational & Dramatic"
        event_type = "Conference"

        prompt = build_prompt(topic, audience, tone, event_type)
        self.assertIn(topic, prompt)
        self.assertIn(audience, prompt)
        self.assertIn(tone, prompt)
        self.assertIn(event_type, prompt)
        self.assertIn("5", prompt)

    def test_parse_llm_json_response_success(self):
        """Tests parsing a valid JSON response into exactly 5 caption suggestions."""
        mock_json_str = """
        [
            {
                "title": "Option 1",
                "top_text": "TOP 1",
                "bottom_text": "BOTTOM 1",
                "subtitle": "SUB 1",
                "caption": "CAP 1",
                "badge": "BADGE 1",
                "full_caption": "FULL 1"
            },
            {
                "title": "Option 2",
                "top_text": "TOP 2",
                "bottom_text": "BOTTOM 2",
                "subtitle": "SUB 2",
                "caption": "CAP 2",
                "badge": "BADGE 2",
                "full_caption": "FULL 2"
            },
            {
                "title": "Option 3",
                "top_text": "TOP 3",
                "bottom_text": "BOTTOM 3",
                "subtitle": "SUB 3",
                "caption": "CAP 3",
                "badge": "BADGE 3",
                "full_caption": "FULL 3"
            },
            {
                "title": "Option 4",
                "top_text": "TOP 4",
                "bottom_text": "BOTTOM 4",
                "subtitle": "SUB 4",
                "caption": "CAP 4",
                "badge": "BADGE 4",
                "full_caption": "FULL 4"
            },
            {
                "title": "Option 5",
                "top_text": "TOP 5",
                "bottom_text": "BOTTOM 5",
                "subtitle": "SUB 5",
                "caption": "CAP 5",
                "badge": "BADGE 5",
                "full_caption": "FULL 5"
            }
        ]
        """
        suggestions = parse_llm_json_response(mock_json_str)
        self.assertEqual(len(suggestions), 5)
        self.assertEqual(suggestions[0]["title"], "Option 1")
        self.assertEqual(suggestions[4]["bottom_text"], "BOTTOM 5")

    def test_empty_response_error(self):
        """Tests that EmptyResponseError is raised on empty or blank responses."""
        with self.assertRaises(EmptyResponseError):
            parse_llm_json_response("")

        with self.assertRaises(EmptyResponseError):
            parse_llm_json_response("   \n\t   ")

    @patch("requests.post")
    def test_api_failure_network_error(self, mock_post):
        """Tests that APIFailureError is raised on network error / timeout."""
        mock_post.side_effect = requests.exceptions.ConnectionError("Connection refused")
        os.environ["GEMINI_API_KEY"] = "fake_key"

        with self.assertRaises(APIFailureError) as ctx:
            generate_ai_captions("Topic", "Audience", "Tone", "Event")

        self.assertIn("Network error", str(ctx.exception))

    @patch("requests.post")
    def test_api_failure_http_status_error(self, mock_post):
        """Tests that APIFailureError is raised on 401/403/500 HTTP errors."""
        mock_response = MagicMock()
        mock_response.status_code = 403
        mock_response.json.return_value = {
            "error": {"message": "API key not valid. Please pass a valid API key."}
        }
        mock_post.return_value = mock_response
        os.environ["GEMINI_API_KEY"] = "invalid_key"

        with self.assertRaises(APIFailureError) as ctx:
            generate_ai_captions("Topic", "Audience", "Tone", "Event")

        self.assertIn("403", str(ctx.exception))
        self.assertIn("API key not valid", str(ctx.exception))

    @patch("requests.post")
    def test_successful_api_generation_flow(self, mock_post):
        """Tests complete end-to-end flow with mocked 200 OK Gemini response."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "candidates": [
                {
                    "content": {
                        "parts": [
                            {
                                "text": """[
                                    {"title": "M1", "top_text": "T1", "bottom_text": "B1", "subtitle": "S1", "caption": "C1", "badge": "TAG1", "full_caption": "F1"},
                                    {"title": "M2", "top_text": "T2", "bottom_text": "B2", "subtitle": "S2", "caption": "C2", "badge": "TAG2", "full_caption": "F2"},
                                    {"title": "M3", "top_text": "T3", "bottom_text": "B3", "subtitle": "S3", "caption": "C3", "badge": "TAG3", "full_caption": "F3"},
                                    {"title": "M4", "top_text": "T4", "bottom_text": "B4", "subtitle": "S4", "caption": "C4", "badge": "TAG4", "full_caption": "F4"},
                                    {"title": "M5", "top_text": "T5", "bottom_text": "B5", "subtitle": "S5", "caption": "C5", "badge": "TAG5", "full_caption": "F5"}
                                ]"""
                            }
                        ]
                    }
                }
            ]
        }
        mock_post.return_value = mock_response
        os.environ["GEMINI_API_KEY"] = "valid_mock_key"

        results = generate_ai_captions(
            topic="Hackathon 2026",
            audience="College Coders",
            tone="Hype & Energetic",
            event_type="Competition"
        )

        self.assertEqual(len(results), 5)
        self.assertEqual(results[0]["title"], "M1")
        self.assertEqual(results[4]["badge"], "TAG5")


if __name__ == "__main__":
    unittest.main()
