"""
Unit tests for the Pillow Poster Composition Engine.
Tests text wrapping, dynamic scaling, 1080x1350 dimensions, safe margin constraints, and PNG export.
"""
import os
import unittest
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

from core.composer import (
    wrap_text,
    calculate_text_block_dimensions,
    auto_fit_font,
    compose_poster,
    save_poster
)
from utils.font_loader import load_font


class TestPosterEngine(unittest.TestCase):

    def setUp(self):
        self.test_dir = Path("test_output")
        self.test_dir.mkdir(exist_ok=True)
        self.dummy_img = Image.new("RGBA", (100, 100))
        self.draw = ImageDraw.Draw(self.dummy_img)
        self.font = load_font("Arial Bold", 32)

    def tearDown(self):
        # Clean up temporary test files
        for test_file in self.test_dir.glob("*.png"):
            try:
                test_file.unlink()
            except Exception:
                pass
        if self.test_dir.exists():
            try:
                self.test_dir.rmdir()
            except Exception:
                pass

    def test_wrap_text_basic(self):
        """Tests standard word wrapping for normal and long text."""
        text = "This is a short line"
        lines = wrap_text(text, self.font, max_width=500, draw=self.draw)
        self.assertEqual(len(lines), 1)
        self.assertEqual(lines[0], text)

        long_text = "The quick brown fox jumps over the lazy dog multiple times across the sunny field"
        lines_wrapped = wrap_text(long_text, self.font, max_width=200, draw=self.draw)
        self.assertGreater(len(lines_wrapped), 1)

        # Verify every line width is <= max_width
        for line in lines_wrapped:
            bbox = self.draw.textbbox((0, 0), line, font=self.font)
            w = bbox[2] - bbox[0]
            self.assertLessEqual(w, 200)

    def test_wrap_text_edge_cases(self):
        """Tests empty, whitespace, and very long single word splitting."""
        self.assertEqual(wrap_text("", self.font, 300, self.draw), [])
        self.assertEqual(wrap_text("   \n\t  ", self.font, 300, self.draw), [])

        # Super long unbroken word
        unbroken_word = "SUPERLONGUNBROKENWORDTHATEXCEEDSMAXWIDTHBYFAR"
        split_lines = wrap_text(unbroken_word, self.font, max_width=100, draw=self.draw)
        self.assertGreater(len(split_lines), 1)
        for line in split_lines:
            bbox = self.draw.textbbox((0, 0), line, font=self.font)
            self.assertLessEqual(bbox[2] - bbox[0], 100)

    def test_calculate_text_block_dimensions(self):
        """Tests block width and height calculation."""
        lines = ["LINE ONE", "LINE TWO IS LONGER", "LINE THREE"]
        w, h = calculate_text_block_dimensions(lines, self.font, self.draw, line_spacing=10)
        self.assertGreater(w, 0)
        self.assertGreater(h, 0)

    def test_auto_fit_font_scaling(self):
        """Tests that auto_fit_font scales down font to fit boundaries."""
        long_paragraph = "A very extensive title that needs to fit inside a bounded rectangular box without overflowing"
        fitted_font, fitted_lines = auto_fit_font(
            long_paragraph,
            font_name="Arial Bold",
            max_width=400,
            max_height=120,
            initial_size=80,
            min_size=16,
            draw=self.draw
        )
        self.assertTrue(len(fitted_lines) > 0)
        w, h = calculate_text_block_dimensions(fitted_lines, fitted_font, self.draw)
        self.assertLessEqual(w, 400)
        self.assertLessEqual(h, 120)

    def test_compose_poster_instagram_dimensions(self):
        """Tests poster composition output format and Instagram 1080x1350 dimensions."""
        poster = compose_poster(
            base_image=None,
            title="GLOBAL DESIGN HACKATHON 2026",
            subtitle="Build the future of intelligent agents with global leaders",
            caption="Over $50,000 in prizes, mentorship, and live workshops.",
            badge_text="WORLD CHAMPIONSHIP",
            date_time="OCTOBER 15-18, 2026",
            location_cta="VIRTUAL & HYBRID • REGISTER AT HACK.IO",
            target_size=(1080, 1350),
            safe_margin=80
        )

        self.assertIsInstance(poster, Image.Image)
        self.assertEqual(poster.size, (1080, 1350))
        self.assertEqual(poster.mode, "RGB")

    def test_compose_poster_with_custom_background(self):
        """Tests poster rendering over an existing image."""
        bg = Image.new("RGB", (800, 600), (200, 100, 50))
        poster = compose_poster(
            base_image=bg,
            title="PRODUCT LAUNCH EVENT",
            subtitle="Introducing our revolutionary AI toolset",
            target_size=(1080, 1350),
            safe_margin=80,
            overlay_opacity=0.7
        )
        self.assertEqual(poster.size, (1080, 1350))

    def test_save_poster_as_png(self):
        """Tests saving generated poster to PNG on disk."""
        poster = compose_poster(
            base_image=None,
            title="EXCLUSIVE TECH WEBINAR",
            target_size=(1080, 1350)
        )
        out_path = self.test_dir / "test_instagram_poster.png"
        saved_file = save_poster(poster, out_path)

        self.assertTrue(os.path.exists(saved_file))
        with Image.open(saved_file) as reloaded:
            self.assertEqual(reloaded.format, "PNG")
            self.assertEqual(reloaded.size, (1080, 1350))

    def test_poster_safe_margin_bounds(self):
        """Tests that posters render properly with custom safe margins without crashing."""
        for margin in [40, 80, 120]:
            poster = compose_poster(
                base_image=None,
                title="VERY EXTENSIVE HEADLINE TESTING SAFE MARGINS " * 3,
                subtitle="Detailed subtitle testing boundary limits " * 3,
                caption="Extended caption testing vertical space inside bounds " * 4,
                date_time="SATURDAY, NOVEMBER 14 • 8:00 PM",
                location_cta="METROPOLITAN CONVENTION HALL • RSVP AT EVENT.COM",
                target_size=(1080, 1350),
                safe_margin=margin
            )
            self.assertEqual(poster.size, (1080, 1350))

    def test_create_procedural_backdrop(self):
        """Tests procedural gradient backdrop generation."""
        from core.image_gen_service import create_procedural_backdrop
        backdrop = create_procedural_backdrop(palette_name="Neon Cyberpunk", width=1080, height=1350)
        self.assertIsInstance(backdrop, Image.Image)
        self.assertEqual(backdrop.size, (1080, 1350))
        self.assertEqual(backdrop.mode, "RGB")

    def test_fit_image_to_aspect_ratio_cover(self):
        """Tests image aspect ratio resizing and center cropping to 1080x1350."""
        from utils.helpers import fit_image_to_aspect_ratio
        orig_img = Image.new("RGB", (1920, 1080), (100, 150, 200))
        fitted = fit_image_to_aspect_ratio(orig_img, 1080, 1350, fit_mode="cover")
        self.assertEqual(fitted.size, (1080, 1350))

    def test_create_gradient_background(self):
        """Tests linear gradient background generation."""
        from utils.helpers import create_gradient_background
        grad = create_gradient_background(1080, 1350, start_color=(20, 30, 40), end_color=(5, 10, 15))
        self.assertEqual(grad.size, (1080, 1350))


if __name__ == "__main__":
    unittest.main()
