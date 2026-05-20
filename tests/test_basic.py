"""Basic smoke tests for figure-compositor."""

import subprocess
import sys


def test_cli_help():
    """CLI --help should exit 0."""
    result = subprocess.run(
        [sys.executable, "-m", "figure_compositor.compose_figure", "--help"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "Figure Compositor" in result.stdout or "usage:" in result.stdout


def test_import():
    """Package should import without error."""
    import figure_compositor  # noqa: F401
