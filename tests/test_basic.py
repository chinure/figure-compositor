"""Basic CLI smoke tests runnable with the standard library."""
import subprocess
import sys
import unittest


class BasicTests(unittest.TestCase):
    def test_cli_help(self):
        result = subprocess.run([sys.executable, "-m", "figure_compositor.compose_figure", "--help"],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0)
        self.assertIn("usage:", result.stdout)

    def test_import(self):
        import figure_compositor
        self.assertTrue(figure_compositor.__version__)
