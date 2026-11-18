"""Regression checks for dropped, blank or overwritten figure panels."""
import importlib.util
from pathlib import Path
import tempfile
import unittest

from PIL import Image
from figure_compositor import compose_figure as fc


class IntegrityTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.paths = []
        for name, color in (("red", "red"), ("blue", "blue")):
            path = self.root / (name + ".png")
            Image.new("RGB", (100, 30), color).save(path)
            self.paths.append(str(path))
        self.kw = dict(grid=(1, 2), width_mm=60, height_mm=40, dpi=60,
                       output=str(self.root / "figure"), dark_mode=False,
                       standardize_bg=False)

    def test_no_vector_really_skips_pdf_and_svg(self):
        fc.compose(self.paths, vector_output=False, **self.kw)
        self.assertTrue((self.root / "figure.png").exists())
        self.assertFalse((self.root / "figure.pdf").exists())
        self.assertFalse((self.root / "figure.svg").exists())

    def test_grid_cannot_silently_drop_panels(self):
        self.kw["grid"] = (1, 1)
        with self.assertRaises(ValueError):
            fc.compose(self.paths, vector_output=False, **self.kw)
        self.assertFalse((self.root / "figure.png").exists())

    def test_missing_or_corrupt_input_fails(self):
        with self.assertRaises(FileNotFoundError):
            fc.compose(self.paths + [str(self.root / "missing.png")], **self.kw)
        bad = self.root / "bad.png"; bad.write_bytes(b"not an image")
        with self.assertRaises(ValueError):
            fc.compose([self.paths[0], str(bad)], vector_output=False, **self.kw)

    def test_source_panels_cannot_be_overwritten(self):
        self.kw["output"] = str(self.root / "red")
        original = (self.root / "red.png").read_bytes()
        with self.assertRaises(ValueError):
            fc.compose(self.paths, vector_output=False, **self.kw)
        self.assertEqual((self.root / "red.png").read_bytes(), original)

    @unittest.skipUnless(importlib.util.find_spec("fitz"), "PyMuPDF optional dependency")
    def test_raster_and_mixed_pdf_keep_all_panels(self):
        import fitz
        fc.compose(self.paths, **self.kw)
        with fitz.open(self.root / "figure.pdf") as doc:
            self.assertEqual(len(doc[0].get_images()), 2)
            self.assertAlmostEqual(doc[0].rect.width, 60 / 25.4 * 72, places=3)
        pdf = self.root / "source.pdf"
        with fitz.open() as doc:
            page = doc.new_page(width=100, height=50)
            page.draw_rect(page.rect, color=(0, 1, 0), fill=(0, 1, 0))
            page.insert_text((10, 20), "PDF panel")
            doc.save(pdf)
        fc.compose([self.paths[0], str(pdf)], **self.kw)
        with fitz.open(self.root / "figure.pdf") as doc:
            self.assertEqual(len(doc[0].get_images()), 2)

    @unittest.skipUnless(importlib.util.find_spec("fitz"), "PyMuPDF optional dependency")
    def test_all_pdf_input_retains_original_vector_text(self):
        import fitz
        paths = []
        for text in ("FIRST", "SECOND"):
            path = self.root / (text + ".pdf")
            with fitz.open() as doc:
                page = doc.new_page(width=100, height=50)
                page.insert_text((10, 20), text)
                doc.save(path)
            paths.append(str(path))
        fc.compose(paths, **self.kw)
        with fitz.open(self.root / "figure.pdf") as doc:
            self.assertIn("FIRST", doc[0].get_text())
            self.assertIn("SECOND", doc[0].get_text())
            self.assertFalse(doc[0].get_images())

    @unittest.skipUnless(importlib.util.find_spec("fitz"), "PyMuPDF optional dependency")
    def test_hybrid_export_letterboxes_instead_of_stretching(self):
        import fitz
        import numpy as np
        positions = fc.compose(self.paths, **self.kw)
        png = np.asarray(Image.open(self.root / "figure.png").convert("RGB"))
        with fitz.open(self.root / "figure.pdf") as doc:
            pix = doc[0].get_pixmap(matrix=fitz.Matrix(60 / 72, 60 / 72), alpha=False)
            pdf = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, 3)
        heights = []
        for pixels in (png, pdf):
            red = (pixels[:, :, 0] > 180) & (pixels[:, :, 1] < 80) & (pixels[:, :, 2] < 80)
            ys = np.where(red)[0]
            self.assertGreater(len(ys), 0)
            heights.append(int(ys.max() - ys.min() + 1))
        self.assertLess(heights[1], positions[0][3] / 2)
        self.assertLessEqual(abs(heights[0] - heights[1]), 3)

    def test_hero_left_layout_is_left_not_top(self):
        self.kw.pop("grid")
        positions = fc.compose(self.paths, layout="hero-left", vector_output=False, **self.kw)
        self.assertGreater(positions[1][0], positions[0][0])

    def test_single_panel_hero_does_not_divide_by_zero(self):
        self.kw.pop("grid")
        positions = fc.compose(self.paths[:1], layout="hero-top", vector_output=False, **self.kw)
        self.assertEqual(len(positions), 1)
