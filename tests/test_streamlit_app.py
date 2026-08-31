"""
Automated UI interaction tests for app.py using streamlit.testing.v1.AppTest.
Verifies that the entire application loads, session states initialize,
and user interactions execute without runtime exceptions.
"""
from pathlib import Path
import unittest
from streamlit.testing.v1 import AppTest

APP_PATH = str(Path(__file__).resolve().parent.parent / "app.py")


class TestStreamlitAppIntegration(unittest.TestCase):

    def test_app_loads_and_initializes_without_errors(self):
        """Tests that app.py runs from top to bottom without exceptions."""
        at = AppTest.from_file(APP_PATH)
        at.run()
        self.assertFalse(at.exception, f"App threw an exception on initial load: {at.exception}")

    def test_app_generate_captions_action(self):
        """Tests clicking the Generate Captions button in Poster mode."""
        at = AppTest.from_file(APP_PATH)
        at.run(timeout=15)
        self.assertFalse(at.exception)

        # Find and click Generate Captions button
        gen_caps_buttons = [b for b in at.button if "Generate Captions" in b.label]
        if gen_caps_buttons:
            gen_caps_buttons[0].click().run(timeout=15)
            self.assertFalse(at.exception, f"Exception clicking Generate Captions: {at.exception}")

    def test_app_switch_to_meme_mode(self):
        """Tests switching mode to Meme and rendering."""
        at = AppTest.from_file(APP_PATH)
        at.run()
        self.assertFalse(at.exception)

        # Toggle radio to Meme
        content_type_radio = at.radio[0]
        content_type_radio.set_value("Meme").run()
        self.assertFalse(at.exception, f"Exception switching to Meme mode: {at.exception}")


if __name__ == "__main__":
    unittest.main()
