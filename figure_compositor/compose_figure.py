#!/usr/bin/env python3
"""
Figure Compositor — publication-ready multi-panel figure assembly script.

Supports PNG, JPG, TIFF, PDF, SVG inputs. Outputs PNG, TIFF, SVG, and PDF.
Handles regular grids, custom layouts (hero+support), dark image plates,
transparent backgrounds, and journal-specific formatting.

Usage:
    # Regular grid
    python compose_figure.py --panels a.png b.png c.png d.png --grid 2 2

    # Custom layout via config JSON
    python compose_figure.py --config figure_2_config.json

    # Audit only
    python compose_figure.py --panels *.png --audit-only
"""

import argparse
import json
import os
import sys
import io
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    print("ERROR: Pillow is required. Install: pip install Pillow")
    sys.exit(1)

# ═══════════════════════════════════════════════════════════════════
# JOURNAL DEFAULTS
# ═══════════════════════════════════════════════════════════════════

JOURNAL_DEFAULTS = {
    'nature': {
        'label_case': 'lower',
        'label_size_pt': 8,
        'full_width_mm': 183,
        'font_family': 'Arial',
        'single_col_mm': 89,
        'min_dpi_photo': 300,
        'min_dpi_line_art': 1000,
        'label_weight': 'bold',
    },
    'cell': {
        'label_case': 'lower',
        'label_size_pt': 8,
        'full_width_mm': 174,
        'font_family': 'Arial',
        'single_col_mm': 85,
        'min_dpi_photo': 300,
        'min_dpi_line_art': 1000,
        'label_weight': 'bold',
    },
    'science': {
        'label_case': 'upper',
        'label_size_pt': 10,
        'full_width_mm': 174,
        'font_family': 'Helvetica',
        'single_col_mm': 85,
        'min_dpi_photo': 300,
        'min_dpi_line_art': 1200,
        'label_weight': 'bold',
    },
    'pnas': {
        'label_case': 'lower',
        'label_size_pt': 8,
        'full_width_mm': 178,
        'font_family': 'Arial',
        'single_col_mm': 87,
        'min_dpi_photo': 300,
        'min_dpi_line_art': 600,
        'label_weight': 'bold',
    },
    'embo': {
        'label_case': 'lower',
        'label_size_pt': 10,
        'full_width_mm': 180,
        'font_family': 'Arial',
        'single_col_mm': 88,
        'min_dpi_photo': 300,
        'min_dpi_line_art': 600,
        'label_weight': 'bold',
    },
    'elife': {
        'label_case': 'lower',
        'label_size_pt': 8,
        'full_width_mm': 180,
        'font_family': 'sans-serif',
        'single_col_mm': 88,
        'min_dpi_photo': 300,
        'min_dpi_line_art': 600,
        'label_weight': 'bold',
    },
    'ieee': {
        'label_case': 'lower',
        'label_size_pt': 8,
        'full_width_mm': 252,  # double-column
        'font_family': 'Times',
        'single_col_mm': 88,
        'min_dpi_photo': 300,
        'min_dpi_line_art': 600,
        'label_weight': 'bold',
    },
}

DPI_DEFAULT = 300
MARGIN_MM = 3
GAP_MM = 2.5

# A4 canvas constraint — all figures must fit within A4 page dimensions
A4_WIDTH_MM = 210   # A4 page width
A4_HEIGHT_MM = 297  # A4 page height
A4_SAFE_MARGIN_MM = 15  # typical print margin on A4
A4_MAX_FIGURE_W_MM = A4_WIDTH_MM - 2 * A4_SAFE_MARGIN_MM   # 180 mm
A4_MAX_FIGURE_H_MM = A4_HEIGHT_MM - 2 * A4_SAFE_MARGIN_MM  # 267 mm


def enforce_a4_limits(width_mm, height_mm, journal='nature'):
    """
    Ensure figure dimensions fit within an A4 page.
    All composite figures are assembled on an A4 canvas.

    Returns (clamped_width_mm, clamped_height_mm, warnings).
    """
    warnings = []
    spec = JOURNAL_DEFAULTS.get(journal, JOURNAL_DEFAULTS['nature'])
    journal_width = spec['full_width_mm']

    # Clamp width to A4-safe limit
    if width_mm is None:
        width_mm = journal_width

    if width_mm > A4_MAX_FIGURE_W_MM:
        warnings.append(
            f"Requested width {width_mm} mm exceeds A4 safe limit "
            f"({A4_MAX_FIGURE_W_MM} mm). Clamped to {A4_MAX_FIGURE_W_MM} mm."
        )
        width_mm = A4_MAX_FIGURE_W_MM

    # Clamp height to A4-safe limit
    if height_mm is None:
        height_mm = width_mm * 0.65

    if height_mm > A4_MAX_FIGURE_H_MM:
        warnings.append(
            f"Computed height {int(height_mm)} mm exceeds A4 safe limit "
            f"({A4_MAX_FIGURE_H_MM} mm). Clamped to {A4_MAX_FIGURE_H_MM} mm."
        )
        height_mm = A4_MAX_FIGURE_H_MM

    return width_mm, height_mm, warnings


# ═══════════════════════════════════════════════════════════════════
# FONT LOADING
# ═══════════════════════════════════════════════════════════════════

def load_font(size_pt, bold=True, prefer_font=None):
    """
    Load a publication-quality font with robust fallback chain.
    Returns a PIL ImageFont object.
    """
    # User-specified override
    if prefer_font and os.path.exists(prefer_font):
        try:
            return ImageFont.truetype(prefer_font, size_pt)
        except Exception:
            pass

    # Platform-specific candidates ordered by preference
    candidates = []

    if bold:
        candidates += [
            '/home/chinure/.local/share/fonts/arial/arialbd.ttf',
            '/usr/share/fonts/truetype/msttcorefonts/Arial_Bold.ttf',
            '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
            '/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf',
            '/usr/share/fonts/truetype/freefont/FreeSansBold.ttf',
            '/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf',
            '/System/Library/Fonts/Helvetica.ttc',
            '/Library/Fonts/Arial Bold.ttf',
            '/Library/Fonts/HelveticaBold.ttf',
            'C:/Windows/Fonts/arialbd.ttf',
            'C:/Windows/Fonts/verdanab.ttf',
            'C:/Windows/Fonts/tahomabd.ttf',
        ]
    else:
        candidates += [
            '/home/chinure/.local/share/fonts/arial/arial.ttf',
            '/usr/share/fonts/truetype/msttcorefonts/Arial.ttf',
            '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
            '/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf',
            '/usr/share/fonts/truetype/freefont/FreeSans.ttf',
            '/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf',
            '/System/Library/Fonts/Helvetica.ttc',
            '/Library/Fonts/Arial.ttf',
            '/Library/Fonts/Helvetica.ttf',
            'C:/Windows/Fonts/arial.ttf',
            'C:/Windows/Fonts/verdana.ttf',
            'C:/Windows/Fonts/tahoma.ttf',
        ]

    for path in candidates:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size_pt)
            except Exception:
                continue

    # Final fallback — warn user
    import warnings
    warnings.warn(
        f"Could not load any publication-quality font. Using PIL default. "
        f"Consider installing Arial, DejaVu, or Liberation fonts. "
        f"You can also use --font-path to specify a font file.",
        RuntimeWarning
    )
    return ImageFont.load_default()


# ═══════════════════════════════════════════════════════════════════
# IMAGE LOADING & PROCESSING
# ═══════════════════════════════════════════════════════════════════

def load_image_any_format(path, dpi=300):
    """Load an image file, handling PDF and SVG if possible."""
    ext = Path(path).suffix.lower()

    if ext == '.pdf':
        # Try pymupdf (fitz) first — no external dependencies
        try:
            import fitz
            doc = fitz.open(path)
            page = doc[0]
            # Render at high resolution for quality
            mat = fitz.Matrix(dpi/72, dpi/72)
            pix = page.get_pixmap(matrix=mat)
            img = Image.open(io.BytesIO(pix.tobytes("png")))
            doc.close()
            return img
        except ImportError:
            pass
        # Fallback to pdf2image (requires poppler)
        try:
            from pdf2image import convert_from_path
            images = convert_from_path(path, dpi=dpi)
            return images[0]
        except ImportError:
            raise RuntimeError(
                f"PDF input requires pymupdf (pip install pymupdf) or pdf2image (pip install pdf2image)"
            )

    elif ext == '.svg':
        try:
            import cairosvg
            png_data = cairosvg.svg2png(url=path, dpi=dpi)
            return Image.open(io.BytesIO(png_data))
        except ImportError:
            raise RuntimeError(
                f"SVG input requires cairosvg. Install: pip install cairosvg"
            )

    else:
        return Image.open(path)


def estimate_image_brightness(img):
    """
    Estimate average brightness of an image (0-255).
    Returns a float. Lower values indicate darker images.
    """
    # Convert to small grayscale for speed
    small = img.convert('L').resize((100, 100), Image.LANCZOS)
    arr = list(small.getdata())
    return sum(arr) / len(arr)


def trim_image_content(img, bg_color=(255, 255, 255), tolerance=5):
    """
    Remove empty/blank border regions from an image.

    Detects the bounding box of non-background pixels and crops to it.
    This is useful before layout analysis so that whitespace padding
    does not inflate the apparent panel size.

    Parameters
    ----------
    img : PIL.Image
        Input image (any mode).
    bg_color : tuple
        RGB value to treat as "background". Default white.
    tolerance : int
        Pixels differing from bg_color by more than this per channel
        are considered content.

    Returns
    -------
    PIL.Image
        Cropped image (or original if no content found).
    (left, top, right, bottom)
        Crop box coordinates in original image.
    """
    try:
        import numpy as np
        rgb = img.convert('RGB')
        arr = np.array(rgb)

        # Create mask: True where pixel differs from bg_color by > tolerance
        diff = np.abs(arr.astype(int) - np.array(bg_color, dtype=int))
        mask = np.any(diff > tolerance, axis=2)

        # Find bounding box of non-background pixels
        rows = np.any(mask, axis=1)
        cols = np.any(mask, axis=0)

        if not np.any(rows) or not np.any(cols):
            # Entirely blank — return original
            return img, (0, 0, img.width, img.height)

        top = int(np.argmax(rows))
        bottom = int(len(rows) - np.argmax(rows[::-1]))
        left = int(np.argmax(cols))
        right = int(len(cols) - np.argmax(cols[::-1]))

        # Safety margin: leave a small border (1% or 2px)
        margin_x = max(2, img.width // 100)
        margin_y = max(2, img.height // 100)
        left = max(0, left - margin_x)
        top = max(0, top - margin_y)
        right = min(img.width, right + margin_x)
        bottom = min(img.height, bottom + margin_y)

        return rgb.crop((left, top, right, bottom)), (left, top, right, bottom)
    except Exception:
        return img, (0, 0, img.width, img.height)


def fit_image(img, target_w, target_h, fit_mode='fit', bg_color=(255, 255, 255),
              v_align='center', h_align='center'):
    """
    Resize image into target dimensions.

    Parameters
    ----------
    fit_mode : str
        'fit'    — preserve aspect ratio, letterbox on bg_color (default)
        'fill'   — preserve aspect ratio, crop to fill entire target
        'original' — no resize, center original image (clip if too large)
        'stretch'— distort to fill (NOT recommended for publication)
    v_align, h_align : str
        For fit_mode='fit': where to place the image within the letterbox.
        'center' (default), 'top'/'left', 'bottom'/'right'.
        Use 'top' + 'left' for strict row/column alignment.
    """
    if target_w <= 0 or target_h <= 0:
        return Image.new('RGBA', (1, 1), bg_color)

    # Handle alpha channel: if image has transparency, composite onto bg_color
    if img.mode in ('RGBA', 'LA', 'P'):
        # Convert palette with transparency
        if img.mode == 'P':
            img = img.convert('RGBA')
        # Create background
        bg = Image.new('RGBA', img.size, bg_color + (255,))
        img = Image.alpha_composite(bg, img.convert('RGBA'))
    else:
        img = img.convert('RGBA')

    img_ratio = img.width / max(img.height, 1)
    target_ratio = target_w / max(target_h, 1)

    if fit_mode == 'fit':
        if img_ratio > target_ratio:
            new_w = target_w
            new_h = max(1, int(target_w / img_ratio))
        else:
            new_h = target_h
            new_w = max(1, int(target_h * img_ratio))
        resized = img.resize((new_w, new_h), Image.LANCZOS)
        canvas = Image.new('RGBA', (target_w, target_h), bg_color + (255,))

        # Horizontal alignment
        if h_align == 'left':
            paste_x = 0
        elif h_align == 'right':
            paste_x = target_w - new_w
        else:
            paste_x = (target_w - new_w) // 2

        # Vertical alignment
        if v_align == 'top':
            paste_y = 0
        elif v_align == 'bottom':
            paste_y = target_h - new_h
        else:
            paste_y = (target_h - new_h) // 2

        canvas.paste(resized, (paste_x, paste_y))
        return canvas

    elif fit_mode == 'fill':
        if img_ratio > target_ratio:
            new_h = target_h
            new_w = max(1, int(target_h * img_ratio))
        else:
            new_w = target_w
            new_h = max(1, int(target_w / img_ratio))
        resized = img.resize((new_w, new_h), Image.LANCZOS)
        # Center-crop to target
        left = (new_w - target_w) // 2
        top = (new_h - target_h) // 2
        return resized.crop((left, top, left + target_w, top + target_h))

    elif fit_mode == 'original':
        canvas = Image.new('RGBA', (target_w, target_h), bg_color + (255,))
        ow, oh = img.size
        if ow > target_w or oh > target_h:
            # Scale down to fit while preserving aspect
            scale = min(target_w / ow, target_h / oh)
            ow, oh = int(ow * scale), int(oh * scale)
            img = img.resize((ow, oh), Image.LANCZOS)
        paste_x = max(0, (target_w - ow) // 2)
        paste_y = max(0, (target_h - oh) // 2)
        canvas.paste(img, (paste_x, paste_y))
        return canvas

    elif fit_mode == 'stretch':
        return img.resize((target_w, target_h), Image.LANCZOS)

    else:
        raise ValueError(f"Unknown fit_mode: {fit_mode}")


def standardize_background(img, target_bg=(255, 255, 255), tolerance=20):
    """
    Replace near-white backgrounds with exact target color using numpy.
    Much faster than pixel-by-pixel iteration.
    """
    try:
        import numpy as np
        # Handle alpha
        if img.mode in ('RGBA', 'LA'):
            arr = np.array(img.convert('RGBA'))
            # Only standardize fully opaque near-white pixels
            white_mask = (
                (arr[:, :, 0] > 255 - tolerance) &
                (arr[:, :, 1] > 255 - tolerance) &
                (arr[:, :, 2] > 255 - tolerance) &
                (arr[:, :, 3] > 250)
            )
            arr[white_mask, :3] = target_bg
            return Image.fromarray(arr, 'RGBA')
        else:
            arr = np.array(img.convert('RGB'))
            white_mask = (
                (arr[:, :, 0] > 255 - tolerance) &
                (arr[:, :, 1] > 255 - tolerance) &
                (arr[:, :, 2] > 255 - tolerance)
            )
            arr[white_mask] = target_bg
            return Image.fromarray(arr, 'RGB')
    except ImportError:
        # Numpy fallback: slow pixel-by-pixel
        img = img.convert('RGB')
        pixels = img.load()
        for y in range(img.height):
            for x in range(img.width):
                r, g, b = pixels[x, y]
                if (abs(r - 255) < tolerance and
                    abs(g - 255) < tolerance and
                    abs(b - 255) < tolerance):
                    pixels[x, y] = target_bg
        return img


# ═══════════════════════════════════════════════════════════════════
# LAYOUT COMPUTATION
# ═══════════════════════════════════════════════════════════════════

def compute_grid_positions(n_panels, grid_rows, grid_cols,
                           canvas_w, canvas_h, margin, gap):
    """Compute (x, y, w, h) for each panel in a regular grid."""
    usable_w = canvas_w - 2 * margin - (grid_cols - 1) * gap
    usable_h = canvas_h - 2 * margin - (grid_rows - 1) * gap
    panel_w = usable_w // grid_cols
    panel_h = usable_h // grid_rows

    positions = []
    for i in range(n_panels):
        row = i // grid_cols
        col = i % grid_cols
        if row >= grid_rows:
            break
        x = margin + col * (panel_w + gap)
        y = margin + row * (panel_h + gap)
        positions.append((x, y, panel_w, panel_h))
    return positions


def compute_custom_positions(layout_specs, canvas_w, canvas_h, margin, gap):
    """
    Compute positions from custom layout specs.

    layout_specs: list of dicts with keys:
        - row, col: starting grid cell
        - rowspan, colspan: how many cells to span (default 1)

    Returns list of (x, y, w, h).
    """
    # Determine grid dimensions from specs
    max_row = max(s.get('row', 0) + s.get('rowspan', 1) for s in layout_specs)
    max_col = max(s.get('col', 0) + s.get('colspan', 1) for s in layout_specs)
    grid_rows = max_row
    grid_cols = max_col

    usable_w = canvas_w - 2 * margin - (grid_cols - 1) * gap
    usable_h = canvas_h - 2 * margin - (grid_rows - 1) * gap
    cell_w = usable_w // grid_cols
    cell_h = usable_h // grid_rows

    positions = []
    for spec in layout_specs:
        r = spec.get('row', 0)
        c = spec.get('col', 0)
        rs = spec.get('rowspan', 1)
        cs = spec.get('colspan', 1)

        x = margin + c * (cell_w + gap)
        y = margin + r * (cell_h + gap)
        w = cs * cell_w + (cs - 1) * gap
        h = rs * cell_h + (rs - 1) * gap
        positions.append((x, y, w, h))

    return positions


def compute_hero_support_positions(n_panels, hero_index, hero_ratio,
                                   canvas_w, canvas_h, margin, gap,
                                   hero_side='top'):
    """
    Compute positions for hero + support layout.

    hero_index: which panel (0-based) is the hero
    hero_ratio: fraction of canvas for hero (0.4-0.7)
    hero_side: 'top', 'left', 'center'
    """
    # Simplified: hero on top or left, rest in grid below/right
    n_support = n_panels - 1
    positions = [None] * n_panels

    if hero_side == 'top':
        hero_h = int((canvas_h - 2 * margin - gap) * hero_ratio)
        support_h = canvas_h - 2 * margin - gap - hero_h
        positions[hero_index] = (margin, margin, canvas_w - 2 * margin, hero_h)

        # Support panels in a row below
        cols = min(n_support, 4)
        rows = (n_support + cols - 1) // cols
        support_positions = compute_grid_positions(
            n_support, rows, cols,
            canvas_w, support_h, margin, gap
        )
        support_idx = 0
        for i in range(n_panels):
            if i == hero_index:
                continue
            sx, sy, sw, sh = support_positions[support_idx]
            positions[i] = (sx, margin + hero_h + gap + sy, sw, sh)
            support_idx += 1

    elif hero_side == 'left':
        hero_w = int((canvas_w - 2 * margin - gap) * hero_ratio)
        support_w = canvas_w - 2 * margin - gap - hero_w
        positions[hero_index] = (margin, margin, hero_w, canvas_h - 2 * margin)

        # Support panels stacked vertically on right
        rows = min(n_support, 5)
        cols = (n_support + rows - 1) // rows
        support_positions = compute_grid_positions(
            n_support, rows, cols,
            support_w, canvas_h, margin, gap
        )
        support_idx = 0
        for i in range(n_panels):
            if i == hero_index:
                continue
            sx, sy, sw, sh = support_positions[support_idx]
            positions[i] = (margin + hero_w + gap + sx, sy, sw, sh)
            support_idx += 1

    return positions


# ═══════════════════════════════════════════════════════════════════
# CONTENT-AWARE PANEL SIZING
# ═══════════════════════════════════════════════════════════════════

def estimate_min_text_height(img):
    """
    Roughly estimate the minimum text stroke height in an image (in pixels).
    Uses edge-density analysis on a downsampled grayscale version.
    Returns estimated text height in original-image pixels.
    """
    try:
        import numpy as np
        # Downsample for speed
        gray = np.array(img.convert('L').resize((400, int(400 * img.height / img.width)),
                                                  Image.LANCZOS))
        # Vertical gradient — text produces strong vertical edges
        vgrad = np.abs(np.diff(gray.astype(float), axis=0))
        # Find columns with consistent edge density (text columns)
        edge_cols = np.sum(vgrad > 25, axis=0)
        text_regions = edge_cols[edge_cols > np.percentile(edge_cols, 70)]
        if len(text_regions) == 0:
            return 12.0  # default guess
        # Estimate character height from edge density pattern
        # Typical text has ~8-30 px character height at 400px width
        est_h_400 = max(8.0, np.median(text_regions) * 0.6)
        # Scale back to original image pixels
        scale_back = img.width / 400.0
        return est_h_400 * scale_back
    except Exception:
        return 12.0


SUBREGION_NAMES = [
    ['top-left', 'top-center', 'top-right'],
    ['mid-left', 'mid-center', 'mid-right'],
    ['bottom-left', 'bottom-center', 'bottom-right'],
]


def audit_subregion_text(img, min_text_px=3.0, grid=3):
    """
    Divide img into a grid x grid subregion matrix and estimate text readability
    in each subregion independently.

    Returns list of (region_name, estimated_text_px, status) tuples for regions
    where text is below the threshold. Status is 'OK', 'WARNING', or 'CRITICAL'.
    """
    try:
        import numpy as np
        w, h = img.size
        if w < grid * 50 or h < grid * 50:
            return []  # too small to subdivide meaningfully

        cell_w = w // grid
        cell_h = h // grid
        problems = []

        for row in range(grid):
            for col in range(grid):
                left = col * cell_w
                upper = row * cell_h
                right = left + cell_w if col < grid - 1 else w
                lower = upper + cell_h if row < grid - 1 else h
                region = img.crop((left, upper, right, lower))

                # Estimate text height in this subregion
                est_h = estimate_min_text_height(region)
                # Scale to original image reference (already in original px)
                # estimate_min_text_height returns px in original scale

                if est_h < min_text_px:
                    status = 'CRITICAL' if est_h < 2.0 else 'WARNING'
                    region_name = SUBREGION_NAMES[row][col]
                    problems.append((region_name, est_h, status))

        return problems
    except Exception:
        return []


def auto_detect_grid(panels, target_width_mm=183, gap_mm=2.5, dpi=300,
                     max_cols=4, min_cols=1):
    """
    Automatically determine the best row×col grid for a set of panels.

    Strategy:
    1. Trim whitespace from each panel.
    2. Compute trimmed aspect ratios.
    3. Try every plausible column count and pick the one that minimises
       the total "wasted" letterbox area (i.e. panels are closest to their
       natural proportions after fitting).

    Parameters
    ----------
    panels : list[str]
        File paths.
    target_width_mm : float
        Figure width in mm.
    gap_mm : float
        Inter-panel gap in mm.
    dpi : int
    max_cols : int
        Upper bound on columns.
    min_cols : int
        Lower bound on columns.

    Returns
    -------
    (rows, cols) : tuple[int, int]
    """
    import math

    trimmed_ars = []
    for path in panels:
        if not os.path.exists(path):
            trimmed_ars.append(1.0)
            continue
        try:
            img = load_image_any_format(path)
            trimmed, _ = trim_image_content(img)
            ar = trimmed.width / max(trimmed.height, 1)
            trimmed_ars.append(ar)
        except Exception:
            trimmed_ars.append(1.0)

    n = len(panels)
    target_width_px = int(target_width_mm / 25.4 * dpi)
    margin_px = int(MARGIN_MM / 25.4 * dpi)
    gap_px = int(gap_mm / 25.4 * dpi)

    best_cols = max(1, min(max_cols, int(math.sqrt(n))))
    best_score = float('inf')

    for cols in range(min_cols, min(max_cols, n) + 1):
        rows = math.ceil(n / cols)
        usable_w = target_width_px - 2 * margin_px - (cols - 1) * gap_px
        cell_w = usable_w / cols
        usable_h = target_width_px - 2 * margin_px - (rows - 1) * gap_px
        cell_h = usable_h / rows  # rough, we will recompute height later

        score = 0.0
        for ar in trimmed_ars:
            # natural size at this cell width
            natural_h = cell_w / ar
            # waste = |natural_h - cell_h| (absolute misfit)
            # Panels that naturally fill the cell well score low
            if natural_h > cell_h * 1.5:
                score += (natural_h - cell_h) / cell_h
            elif natural_h < cell_h * 0.5:
                score += (cell_h - natural_h) / cell_h

        # Slight preference for fewer rows (more compact)
        score += rows * 0.1

        if score < best_score:
            best_score = score
            best_cols = cols

    best_rows = math.ceil(n / best_cols)
    return (best_rows, best_cols)


def analyze_panel_proportions(panels, journal='nature', grid_cols=2, dpi=300,
                              use_trimmed=True):
    """
    Analyze each panel's original dimensions and estimate readability
    if placed into a standard grid.

    Parameters
    ----------
    use_trimmed : bool
        If True (default), trim whitespace borders before computing
        aspect ratio and scale factor. This prevents excess padding
        from distorting the layout decision.

    Returns list of dicts with keys:
        file, orig_w, orig_h, trimmed_w, trimmed_h, aspect_ratio, estimated_text_px,
        target_panel_w_px, target_panel_h_px, scale_factor,
        scaled_text_px, is_readable, strategy
    """
    spec = JOURNAL_DEFAULTS.get(journal, JOURNAL_DEFAULTS['nature'])
    full_width_mm = spec['full_width_mm']

    # Compute target panel size (uniform grid assumption)
    full_width_px = int(full_width_mm / 25.4 * dpi)
    margin_px = int(MARGIN_MM / 25.4 * dpi)
    gap_px = int(GAP_MM / 25.4 * dpi)
    usable_w = full_width_px - 2 * margin_px - (grid_cols - 1) * gap_px
    target_panel_w = usable_w // grid_cols
    # Assume square-ish panel for height estimate
    target_panel_h = target_panel_w * 3 // 4

    MIN_READABLE_TEXT_PX = 18  # ~5pt at 300dpi (conservative)

    results = []
    for path in panels:
        if not os.path.exists(path):
            results.append({
                'file': path, 'exists': False,
                'strategy': 'MISSING'
            })
            continue

        try:
            img = load_image_any_format(path)
            raw_w, raw_h = img.size

            # Trim whitespace for accurate content sizing
            if use_trimmed:
                trimmed_img, _ = trim_image_content(img)
                w, h = trimmed_img.size
            else:
                w, h = raw_w, raw_h

            ar = w / max(h, 1)
            est_text = estimate_min_text_height(img)

            # Scale factor if fit into target panel width
            scale_w = target_panel_w / w
            scale_h = target_panel_h / h
            # For fit_mode='fit', the limiting dimension determines scale
            scale_factor = min(scale_w, scale_h)
            scaled_text = est_text * scale_factor

            # Determine strategy
            if scaled_text >= MIN_READABLE_TEXT_PX:
                strategy = 'OK'
            elif ar > 2.5:
                strategy = 'WIDE_ALLOCATE'
            elif ar < 0.4:
                strategy = 'TALL_ALLOCATE'
            elif scaled_text >= 10:
                strategy = 'MARGINAL'
            else:
                strategy = 'REGENERATE'

            results.append({
                'file': path,
                'exists': True,
                'orig_w': raw_w,
                'orig_h': raw_h,
                'trimmed_w': w,
                'trimmed_h': h,
                'aspect_ratio': ar,
                'estimated_text_px': est_text,
                'target_panel_w': target_panel_w,
                'target_panel_h': target_panel_h,
                'scale_factor': scale_factor,
                'scaled_text_px': scaled_text,
                'is_readable': scaled_text >= MIN_READABLE_TEXT_PX,
                'strategy': strategy,
            })
        except Exception as e:
            results.append({
                'file': path, 'exists': True,
                'strategy': f'ERROR: {e}'
            })

    return results


def compute_smart_layout_specs(panel_analysis, max_cols=4):
    """
    Generate custom layout_specs from panel proportion analysis.

    Strategy mapping:
        OK          → normal 1×1 cell
        WIDE_ALLOCATE → colspan=2 (or more if very wide)
        TALL_ALLOCATE → rowspan=2
        MARGINAL    → colspan=1, but suggest user verify
        REGENERATE  → colspan=1, but flag for user attention

    Returns (layout_specs, grid_cols, grid_rows, suggested_height_mm)
    """
    n = len(panel_analysis)

    # Determine per-panel colspan
    colspans = []
    for pa in panel_analysis:
        if not pa.get('exists'):
            colspans.append(1)
            continue
        strat = pa.get('strategy', 'OK')
        if strat == 'WIDE_ALLOCATE':
            ar = pa.get('aspect_ratio', 1.0)
            if ar > 4.0:
                colspans.append(min(3, max_cols))
            else:
                colspans.append(min(2, max_cols))
        elif strat == 'TALL_ALLOCATE':
            colspans.append(1)
        else:
            colspans.append(1)

    # Determine grid columns: enough to accommodate the widest panel
    grid_cols = max(max(colspans), min(max_cols, n))
    if n <= 3:
        grid_cols = max(grid_cols, n)

    # Place panels greedily left-to-right, top-to-bottom
    layout_specs = []
    current_col = 0
    current_row = 0
    rowspans = [1] * n  # default

    for i, pa in enumerate(panel_analysis):
        cs = colspans[i]
        rs = rowspans[i]

        # If doesn't fit in current row, move to next row
        if current_col + cs > grid_cols:
            current_row += 1
            current_col = 0

        layout_specs.append({
            'row': current_row,
            'col': current_col,
            'rowspan': rs,
            'colspan': cs,
        })
        current_col += cs

    grid_rows = current_row + 1

    # Suggest figure height based on row count and panel aspect ratios
    # Base height: ~70% of width per row, adjusted for tall panels
    base_height_mm = 60 * grid_rows
    tall_count = sum(1 for pa in panel_analysis if pa.get('strategy') == 'TALL_ALLOCATE')
    if tall_count > 0:
        base_height_mm += 30 * tall_count

    return layout_specs, grid_cols, grid_rows, max(base_height_mm, 80)


def print_proportion_report(panel_analysis):
    """Print a readable proportion analysis report."""
    print("\n" + "=" * 75)
    print(" Content-Aware Panel Sizing Report")
    print("=" * 75)
    print(f" {'Panel':<8} {'Size':>14} {'AR':>6} {'Text(px)':>10} "
          f"{'Scale':>8} {'Scaled':>8} {'Strategy'}")
    print("-" * 75)

    for i, pa in enumerate(panel_analysis):
        label = chr(97 + i)
        if not pa.get('exists'):
            print(f" {label:<8} {'MISSING':>14} {'—':>6} {'—':>10} {'—':>8} {'—':>8} MISSING")
            continue

        raw_str = f"{pa['orig_w']}x{pa['orig_h']}"
        # Show trimmed size if different
        if 'trimmed_w' in pa and (pa['trimmed_w'] != pa['orig_w'] or pa['trimmed_h'] != pa['orig_h']):
            size_str = f"{raw_str} → {pa['trimmed_w']}x{pa['trimmed_h']}"
        else:
            size_str = raw_str
        ar_str = f"{pa['aspect_ratio']:.2f}"
        text_str = f"{pa['estimated_text_px']:.1f}"
        scale_str = f"{pa['scale_factor']:.3f}"
        scaled_str = f"{pa['scaled_text_px']:.1f}"
        strat = pa['strategy']

        # Color-code strategy
        if strat == 'OK':
            flag = "✅"
        elif strat in ('WIDE_ALLOCATE', 'TALL_ALLOCATE'):
            flag = "🔧"
        elif strat == 'MARGINAL':
            flag = "⚠️"
        elif strat == 'REGENERATE':
            flag = "❌"
        else:
            flag = "?"

        print(f" {label:<8} {size_str:>14} {ar_str:>6} {text_str:>10} "
              f"{scale_str:>8} {scaled_str:>8} {flag} {strat}")

    print("-" * 75)
    print(" Legend:")
    print("   ✅ OK        — Text remains readable after scaling")
    print("   🔧 ALLOCATE  — Panel will receive extra space (colspan/rowspan)")
    print("   ⚠️ MARGINAL  — Text is small but may be acceptable; verify visually")
    print("   ❌ REGENERATE — Text will be unreadable; return to plotting code")
    print("   Size format: raw_w×raw_h → trimmed_w×trimmed_h (whitespace removed)")
    print("=" * 75 + "\n")


# ═══════════════════════════════════════════════════════════════════
# PANEL LABELING
# ═══════════════════════════════════════════════════════════════════

def estimate_region_content_density(img_region):
    """
    Estimate content density in an image region by edge detection.
    Returns a float 0.0–1.0 (higher = more edges/content).
    """
    try:
        import numpy as np
        gray = np.array(img_region.convert('L'), dtype=np.float32)
        # Sobel-like edge detection
        gy, gx = np.gradient(gray)
        edge_mag = np.sqrt(gx**2 + gy**2)
        # Normalize: count pixels with significant gradient
        threshold = edge_mag.mean() + edge_mag.std()
        dense_ratio = (edge_mag > threshold).sum() / edge_mag.size
        return float(dense_ratio)
    except Exception:
        return 0.0


def find_label_safe_zone(panel_img, label_w, label_h, offset, max_scan_x_ratio=0.6):
    """
    Scan the top row of panel_img to find a low-content zone for the label.

    Returns a tuple: (best_x_offset, best_position_name, density_at_best).
    best_position_name is one of 'top-left', 'top-right', 'top-left-shifted'.
    """
    try:
        import numpy as np
        pw, ph = panel_img.size
        if pw < label_w + offset * 2 or ph < label_h + offset * 2:
            return (offset, 'top-left', 0.0)

        # Region to scan: top strip tall enough for label + offset
        strip_h = min(label_h + offset * 2, ph // 4)
        top_strip = panel_img.crop((0, 0, pw, strip_h))
        strip_np = np.array(top_strip.convert('L'))

        # Compute edge density in sliding windows
        window_w = label_w + offset * 2
        max_x = int(pw * max_scan_x_ratio)
        positions = []
        step = max(1, window_w // 4)

        for scan_x in range(0, max_x - window_w + 1, step):
            window = strip_np[:, scan_x:scan_x + window_w]
            gy, gx = np.gradient(window.astype(np.float32))
            edge_mag = np.sqrt(gx**2 + gy**2)
            density = float((edge_mag > (edge_mag.mean() + edge_mag.std())).sum() / edge_mag.size)
            positions.append((scan_x, density))

        if not positions:
            return (offset, 'top-left', 0.0)

        # Sort by density (lowest first)
        positions.sort(key=lambda t: t[1])
        best_x, best_density = positions[0]

        # Thresholds
        LOW_DENSITY = 0.08   # ~8% edge pixels = fairly clean
        HIGH_DENSITY = 0.20  # ~20% edge pixels = quite busy

        if best_density < LOW_DENSITY and best_x < window_w:
            # Default top-left is clean enough
            return (offset, 'top-left', best_density)
        elif best_density < HIGH_DENSITY:
            # Shift to the best low-density zone
            return (best_x + offset, 'top-left-shifted', best_density)
        else:
            # Everything is busy; try top-right as last resort
            return (offset, 'top-right', best_density)
    except Exception:
        return (offset, 'top-left', 0.0)


PANEL_TYPE_OFFSETS = {
    'plot': 4,
    'heatmap': 8,      # larger offset for heatmap titles/colorbars
    'table': 8,        # larger offset for table headers
    'microscopy': 6,   # moderate offset for dark images
    'unknown': 4,
}


def detect_panel_type(img):
    """
    Heuristically classify a panel image by content type.
    Returns one of: 'plot', 'heatmap', 'table', 'microscopy', 'unknown'.
    """
    try:
        import numpy as np
        gray = np.array(img.convert('L'))
        h, w = gray.shape
        brightness = gray.mean()

        # Microscopy: very dark
        if brightness < 60:
            return 'microscopy'

        # Analyze top strip (where titles/headers live)
        top_strip = gray[:max(h // 4, 50), :]
        gy, gx = np.gradient(top_strip.astype(float))
        edge_mag = np.sqrt(gx**2 + gy**2)
        top_density = (edge_mag > (edge_mag.mean() + edge_mag.std())).sum() / edge_mag.size

        # Heatmap: top strip has moderate-high density (colorbar, column labels)
        # and the image has lots of local color variation
        if top_density > 0.12:
            # Distinguish heatmap from table: heatmap has smooth gradients,
            # table has sharp grid lines
            mid_region = gray[h//4:3*h//4, w//4:3*w//4]
            gy_mid, gx_mid = np.gradient(mid_region.astype(float))
            edge_mid = np.sqrt(gx_mid**2 + gy_mid**2)
            # Count very strong edges (grid lines)
            strong_edges = (edge_mid > np.percentile(edge_mid, 95)).sum()
            total = edge_mid.size
            if strong_edges / total > 0.05:
                return 'table'
            else:
                return 'heatmap'

        return 'plot'
    except Exception:
        return 'unknown'


def add_panel_label(draw, label, x, y, w, h, font, position='top-left',
                    color=(0, 0, 0), offset_px=4, dark_mode=False,
                    panel_img=None, avoidance='off', panel_type='unknown'):
    """
    Add a panel label to the canvas.

    position: 'top-left', 'top-right', 'outside-top-left'
    avoidance: 'off', 'auto', 'strict'
        When 'auto' or 'strict', scans panel_img top row for low-content
        zones and shifts the label to avoid overlapping heatmap titles,
        colorbars, or dense plot elements.
    """
    label_color = (255, 255, 255) if dark_mode else color

    # Adaptive offset: heatmap/table need more headroom for titles/colorbars
    if panel_type in PANEL_TYPE_OFFSETS:
        offset_px = PANEL_TYPE_OFFSETS[panel_type]

    # Smart avoidance: detect content in label area and shift if needed
    if avoidance in ('auto', 'strict') and panel_img is not None:
        # Estimate label dimensions
        bbox = draw.textbbox((0, 0), label, font=font)
        label_w = bbox[2] - bbox[0]
        label_h = bbox[3] - bbox[1]

        safe_x, resolved_pos, density = find_label_safe_zone(
            panel_img, label_w, label_h, offset_px,
            max_scan_x_ratio=0.5 if avoidance == 'auto' else 0.35
        )

        if resolved_pos == 'top-left':
            label_x = x + safe_x
            label_y = y + offset_px
        elif resolved_pos == 'top-left-shifted':
            label_x = x + safe_x
            label_y = y + offset_px
            if density > 0.05:
                # If we had to shift, add a subtle visual cue: small background
                # (not implemented here; just position shift)
                pass
        elif resolved_pos == 'top-right':
            bbox = draw.textbbox((0, 0), label, font=font)
            tw = bbox[2] - bbox[0]
            label_x = x + w - tw - offset_px
            label_y = y + offset_px
        else:
            label_x = x + offset_px
            label_y = y + offset_px
    else:
        # Original logic (no avoidance)
        if position == 'top-left':
            label_x = x + offset_px
            label_y = y + offset_px
        elif position == 'top-right':
            bbox = draw.textbbox((0, 0), label, font=font)
            tw = bbox[2] - bbox[0]
            label_x = x + w - tw - offset_px
            label_y = y + offset_px
        elif position == 'outside-top-left':
            label_x = x + offset_px
            label_y = y - 20
        else:
            label_x = x + offset_px
            label_y = y + offset_px

    # Ensure label stays within panel for inside positions
    if position != 'outside-top-left':
        label_x = max(x + 2, label_x)
        label_y = max(y + 2, label_y)
        # Also keep within right/bottom bounds
        bbox = draw.textbbox((0, 0), label, font=font)
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]
        label_x = min(label_x, x + w - tw - 2)
        label_y = min(label_y, y + h - th - 2)

    draw.text((label_x, label_y), label, font=font, fill=label_color)


# ═══════════════════════════════════════════════════════════════════
# CONSISTENCY AUDIT — HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════════

def detect_scale_bar(img, brightness):
    """
    Heuristic detection of scale bars in microscopy images.
    Returns (detected: bool, confidence: str).
    """
    try:
        import numpy as np
        gray = np.array(img.convert('L'))
        h, w = gray.shape

        # Scale bars are typically in bottom 20% of image, near edges
        bottom_region = gray[int(h * 0.75):, :]

        # Look for high-contrast horizontal lines (white bar on dark, or black bar on light)
        # Compute horizontal edge strength
        hgrad = np.abs(np.diff(bottom_region.astype(float), axis=1))

        # Threshold for strong edges
        strong_edges = hgrad > 80

        # Count rows with continuous strong horizontal edges
        row_edge_counts = np.sum(strong_edges, axis=1)
        max_edge_row = np.max(row_edge_counts) if len(row_edge_counts) > 0 else 0

        # Scale bars typically have edge length 30-200 pixels
        if 20 <= max_edge_row <= min(w, 300):
            return True, 'probable'

        # Also check for vertical bars (some scale bars are vertical)
        vgrad = np.abs(np.diff(bottom_region.astype(float), axis=0))
        strong_v_edges = vgrad > 80
        col_edge_counts = np.sum(strong_v_edges, axis=0)
        max_edge_col = np.max(col_edge_counts) if len(col_edge_counts) > 0 else 0

        if 20 <= max_edge_col <= min(h, 300):
            return True, 'possible'

        # If image is very dark (microscopy), and no edges found, likely missing scale bar
        if brightness < 80 and max_edge_row < 10:
            return False, 'likely_missing'

        return False, 'not_detected'
    except Exception:
        return False, 'error'


def check_contrast_ratio(img):
    """
    Estimate text-to-background contrast ratio for accessibility.
    Returns ratio (≥ 4.5 recommended for WCAG AA).
    """
    try:
        import numpy as np
        gray = np.array(img.convert('L'))

        # Find dark and light regions
        dark_mask = gray < 50
        light_mask = gray > 200

        dark_mean = np.mean(gray[dark_mask]) if np.any(dark_mask) else 0
        light_mean = np.mean(gray[light_mask]) if np.any(light_mask) else 255

        # Relative luminance (simplified for grayscale)
        L1 = (light_mean + 0.05) / 255
        L2 = (dark_mean + 0.05) / 255

        ratio = max(L1, L2) / min(L1, L2)
        return ratio
    except Exception:
        return 0.0


def check_local_contrast_regions(img, min_region_ratio=4.5):
    """
    Check contrast in subregions of the image (top, middle, bottom thirds).
    Returns list of (region_name, contrast_ratio) for regions below threshold.
    """
    try:
        import numpy as np
        gray = np.array(img.convert('L'))
        h, w = gray.shape
        regions = []
        region_names = ['top', 'middle', 'bottom']
        for i, name in enumerate(region_names):
            y0 = i * h // 3
            y1 = (i + 1) * h // 3 if i < 2 else h
            region = gray[y0:y1, :]
            dark_mask = region < 50
            light_mask = region > 200
            dark_mean = np.mean(region[dark_mask]) if np.any(dark_mask) else 0
            light_mean = np.mean(region[light_mask]) if np.any(light_mask) else 255
            L1 = (light_mean + 0.05) / 255
            L2 = (dark_mean + 0.05) / 255
            ratio = max(L1, L2) / min(L1, L2) if min(L1, L2) > 0 else 0
            if ratio < min_region_ratio and ratio > 0:
                regions.append((name, float(ratio)))
        return regions
    except Exception:
        return []


def check_grayscale_distinguishability(img, n_colors=5):
    """
    Check if distinct colors remain distinguishable when converted to grayscale.
    Returns (is_safe: bool, min_separation: float).
    """
    try:
        import numpy as np
        # Extract dominant colors
        rgb = np.array(img.convert('RGB').resize((100, 100), Image.LANCZOS))
        pixels = rgb.reshape(-1, 3)

        # Simple k-means for dominant colors
        from sklearn.cluster import KMeans
        kmeans = KMeans(n_clusters=min(n_colors, len(pixels)), random_state=42, n_init=10)
        kmeans.fit(pixels)
        colors = kmeans.cluster_centers_.astype(int)

        # Convert to grayscale luminance
        luminances = [0.299 * r + 0.587 * g + 0.114 * b for r, g, b in colors]

        # Find minimum separation
        min_sep = float('inf')
        for i in range(len(luminances)):
            for j in range(i + 1, len(luminances)):
                sep = abs(luminances[i] - luminances[j])
                if sep < min_sep:
                    min_sep = sep

        # Threshold: 30 luminance units (out of 255) is a safe minimum
        is_safe = min_sep > 25
        return is_safe, min_sep
    except Exception:
        return True, 255.0  # assume safe if can't analyze


def extract_image_metadata(path):
    """
    Extract EXIF/IPTC metadata from image file.
    Returns dict with metadata keys, or None if no metadata.
    """
    try:
        img = Image.open(path)
        metadata = {}

        # EXIF data
        if hasattr(img, '_getexif') and img._getexif():
            exif = img._getexif()
            metadata['exif'] = {str(k): str(v) for k, v in exif.items()}
        elif hasattr(img, 'info') and 'exif' in img.info:
            metadata['exif_present'] = True

        # Check for common microscopy metadata hints
        info = img.info
        if 'dpi' in info:
            metadata['dpi'] = info['dpi']

        return metadata if metadata else None
    except Exception:
        return None


# ═══════════════════════════════════════════════════════════════════
# CONSISTENCY AUDIT
# ═══════════════════════════════════════════════════════════════════

def audit_panels(panel_files):
    """Run comprehensive consistency checks on input files."""
    results = []
    for path in panel_files:
        if not os.path.exists(path):
            results.append({'file': path, 'exists': False, 'error': 'File not found'})
            continue

        result = {'file': path, 'exists': True, 'issues': []}

        try:
            img = load_image_any_format(path)
            w, h = img.size
            result['size'] = (w, h)
            result['format'] = img.format
            result['mode'] = img.mode

            # DPI check
            dpi_info = img.info.get('dpi', (None, None))
            estimated_dpi = dpi_info[0] if dpi_info[0] else w / 3.5
            result['dpi'] = dpi_info[0] if dpi_info[0] else None
            result['estimated_dpi'] = estimated_dpi

            if estimated_dpi < 150:
                result['issues'].append(('CRITICAL', f'DPI {estimated_dpi:.0f} < 150'))
            elif estimated_dpi < 300:
                result['issues'].append(('WARNING', f'Low DPI {estimated_dpi:.0f} (< 300)'))

            # Aspect ratio
            ar = w / max(h, 1)
            result['aspect_ratio'] = ar
            if ar > 3.5 or ar < 0.28:
                result['issues'].append(('WARNING', f'Extreme aspect ratio {ar:.2f}'))

            # Background color
            try:
                corner = img.crop((0, 0, min(20, w), min(20, h)))
                if corner.mode in ('RGBA', 'P'):
                    corner = corner.convert('RGBA')
                    # Use opaque version for analysis
                    bg = Image.new('RGBA', corner.size, (255, 255, 255, 255))
                    corner = Image.alpha_composite(bg, corner)
                corner_rgb = corner.convert('RGB')
                pixels = list(corner_rgb.getdata())
                avg_bg = tuple(int(sum(c[i] for c in pixels) / len(pixels)) for i in range(3))
                result['avg_background'] = avg_bg
            except Exception as e:
                result['avg_background'] = None
                result['issues'].append(('INFO', f'BG analysis failed: {e}'))

            # Brightness (for dark mode detection)
            try:
                result['brightness'] = estimate_image_brightness(img)
            except Exception:
                result['brightness'] = 128

            # Text readability check (rough estimate)
            # Estimate minimum text height by looking for vertical edges
            try:
                import numpy as np
                gray = np.array(img.convert('L').resize((400, 400), Image.LANCZOS))
                # Compute vertical gradient
                vgrad = np.abs(np.diff(gray, axis=0))
                # Count strong vertical edges per column
                edge_cols = np.sum(vgrad > 30, axis=0)
                # Estimate text as regions with consistent edge density
                if np.max(edge_cols) > 0:
                    # Rough heuristic: at 400px width, text characters are ~8-30px tall
                    text_height_estimate = 400 * 8 / w  # approximate minimum at original scale
                    result['estimated_min_text_px'] = text_height_estimate
                    if text_height_estimate < 3:  # would be < 5pt at 300dpi
                        result['issues'].append(
                            ('WARNING', 'Text may be too small at print size')
                        )
            except ImportError:
                pass

            # Subregion text readability check (detects small text in dense areas)
            try:
                subregion_problems = audit_subregion_text(img, min_text_px=3.0, grid=3)
                result['subregion_text_issues'] = subregion_problems
                for region_name, est_h, status in subregion_problems:
                    if status == 'CRITICAL':
                        result['issues'].append(
                            ('WARNING', f'Subregion "{region_name}": text ~{est_h:.1f}px may be unreadable at print size')
                        )
                    else:
                        result['issues'].append(
                            ('INFO', f'Subregion "{region_name}": text marginal ({est_h:.1f}px)')
                        )
            except Exception:
                pass

            # Compression artifact check (JPG only)
            if img.format and img.format.upper() in ('JPEG', 'JPG'):
                try:
                    import numpy as np
                    arr = np.array(img.convert('L'))
                    # Compute blockiness metric (DCT artifact detection)
                    h, w = arr.shape
                    block_scores = []
                    for by in range(0, min(h - 8, 200), 8):
                        for bx in range(0, min(w - 8, 200), 8):
                            block = arr[by:by+8, bx:bx+8].astype(float)
                            # Variance within 8x8 block
                            block_scores.append(np.var(block))
                    if block_scores and np.mean(block_scores) < 5:
                        result['issues'].append(
                            ('WARNING', 'Possible heavy JPG compression artifacts')
                        )
                except Exception:
                    pass

            # Scale bar detection (microscopy images)
            try:
                brightness = result.get('brightness', 128)
                detected, confidence = detect_scale_bar(img, brightness)
                result['scale_bar_detected'] = detected
                result['scale_bar_confidence'] = confidence

                # Flag if dark/microscopy-like and no scale bar detected
                if brightness < 100 and not detected and confidence in ('likely_missing', 'not_detected'):
                    result['issues'].append(
                        ('WARNING', 'No scale bar detected — Cell Press requires scale bars on all microscopy images')
                    )
            except Exception:
                pass

            # Contrast ratio check (accessibility)
            try:
                contrast = check_contrast_ratio(img)
                result['contrast_ratio'] = contrast
                if contrast > 0 and contrast < 4.5:
                    result['issues'].append(
                        ('WARNING', f'Low contrast ratio ({contrast:.1f}:1) — aim for ≥ 4.5:1')
                    )

                # Local contrast: check specific regions for low contrast
                local_issues = check_local_contrast_regions(img, min_region_ratio=4.5)
                for region_name, region_contrast in local_issues:
                    result['issues'].append(
                        ('INFO', f'{region_name} region contrast {region_contrast:.1f}:1 — may affect text readability')
                    )
            except Exception:
                pass

            # Grayscale distinguishability (print compatibility)
            try:
                gray_safe, min_sep = check_grayscale_distinguishability(img)
                result['grayscale_safe'] = gray_safe
                result['grayscale_min_sep'] = min_sep
                if not gray_safe:
                    result['issues'].append(
                        ('WARNING', f'Colors may be indistinguishable in grayscale print (min separation: {min_sep:.1f})')
                    )
            except Exception:
                pass

            # Image metadata (microscopy parameters)
            try:
                meta = extract_image_metadata(path)
                result['metadata'] = meta
                if meta is None:
                    result['issues'].append(
                        ('INFO', 'No EXIF/metadata found — consider embedding microscopy parameters')
                    )
            except Exception:
                pass

        except Exception as e:
            result['error'] = str(e)
            result['issues'].append(('CRITICAL', f'Failed to load: {e}'))

        results.append(result)
    return results


def _check_shared_legend(results):
    """
    Detect if multiple panels share similar dominant colors,
    suggesting a shared legend could reduce visual clutter.
    """
    try:
        from sklearn.cluster import KMeans
    except ImportError:
        return  # skip if sklearn not available

    panel_colors = []
    for r in results:
        if not r.get('exists'):
            continue
        path = r['file']
        try:
            img = load_image_any_format(path)
            # Downsample for speed
            small = img.convert('RGB').resize((100, 100))
            arr = np.array(small).reshape(-1, 3)
            # K-means to find dominant colors
            km = KMeans(n_clusters=3, n_init=1, max_iter=50, random_state=42)
            km.fit(arr)
            centers = km.cluster_centers_.astype(int)
            panel_colors.append((os.path.basename(path), centers))
        except Exception:
            continue

    if len(panel_colors) < 3:
        return

    # Count how many panels share at least one similar color
    shared_count = 0
    threshold = 30  # RGB distance
    for i in range(len(panel_colors)):
        for j in range(i + 1, len(panel_colors)):
            name1, cols1 = panel_colors[i]
            name2, cols2 = panel_colors[j]
            for c1 in cols1:
                for c2 in cols2:
                    dist = np.linalg.norm(c1 - c2)
                    if dist < threshold:
                        shared_count += 1
                        break

    # Heuristic: if many panel pairs share colors, suggest legend consolidation
    max_pairs = len(panel_colors) * (len(panel_colors) - 1) // 2
    if shared_count >= max_pairs * 0.4 and len(panel_colors) >= 3:
        print(f"\n ℹ️  {len(panel_colors)} panels appear to share similar color palettes. "
              f"Consider consolidating repeated legends into one shared legend strip "
              f"to reduce visual clutter and save panel space.")


def print_audit_report(results, journal='nature'):
    """Print formatted audit report."""
    spec = JOURNAL_DEFAULTS.get(journal, JOURNAL_DEFAULTS['nature'])
    min_dpi = spec['min_dpi_photo']

    print("\n" + "=" * 75)
    print(" Figure Consistency Audit Report")
    print("=" * 75)
    print(f"  Target: {journal.upper()}")
    print(f"  Min DPI: {min_dpi} (photos)")
    print("-" * 75)
    print(f" {'Panel':<8} {'File':<22} {'Size':>12} {'DPI':>7} {'BG':>8} {'Status'}")
    print("-" * 75)

    backgrounds = []
    for r in results:
        fname = os.path.basename(r['file'])[:20]
        if not r.get('exists'):
            print(f" {fname:<22} {'MISSING':>12} {'—':>7} {'—':>8} FAIL")
            continue
        if 'error' in r and not r.get('size'):
            print(f" {fname:<22} {'ERROR':>12} {'—':>7} {'—':>8} FAIL")
            continue

        size_str = f"{r['size'][0]}x{r['size'][1]}" if 'size' in r else '—'
        dpi_str = f"{r.get('estimated_dpi', 0):.0f}" if r.get('estimated_dpi') else "—"
        bg = r.get('avg_background')
        bg_str = f"#{bg[0]:02x}{bg[1]:02x}{bg[2]:02x}" if bg else "—"
        if bg:
            backgrounds.append(bg)

        critical = [i for i in r.get('issues', []) if i[0] == 'CRITICAL']
        warnings = [i for i in r.get('issues', []) if i[0] == 'WARNING']
        info = [i for i in r.get('issues', []) if i[0] == 'INFO']

        if critical:
            status = f"❌ {', '.join(i[1] for i in critical[:2])}"
        elif warnings:
            status = f"⚠️  {', '.join(i[1] for i in warnings[:2])}"
        elif info:
            status = f"ℹ️  {', '.join(i[1] for i in info[:1])}"
        else:
            status = "✅ OK"

        print(f" {fname:<22} {size_str:>12} {dpi_str:>7} {bg_str:>8} {status}")

    # Background consistency
    if len(backgrounds) >= 2:
        bg_variance = max(
            max(abs(b1[i] - b2[i]) for i in range(3))
            for b1 in backgrounds for b2 in backgrounds
        )
        if bg_variance > 15:
            print(f"\n ⚠️  Background colors vary by {bg_variance} across panels. "
                  f"Standardize recommended.")

    # Dark mode suggestion
    dark_count = sum(1 for r in results if r.get('brightness', 128) < 80)
    if dark_count >= 2:
        print(f"\n ℹ️  {dark_count} panels appear dark (brightness < 80). "
              f"Consider using dark_mode='true'.")

    # Scale bar summary (microscopy panels)
    missing_scale = [r for r in results
                     if any('scale bar' in i[1].lower() for i in r.get('issues', []))]
    if missing_scale:
        print(f"\n ⚠️  {len(missing_scale)} panel(s) lack detected scale bars. "
              f"Cell Press requires scale bars on all microscopy images.")

    # Shared legend detection (color consistency across panels)
    try:
        _check_shared_legend(results)
    except Exception:
        pass

    # Contrast summary
    low_contrast = [r for r in results if r.get('contrast_ratio', 10) < 4.5]
    if low_contrast:
        print(f"\n ⚠️  {len(low_contrast)} panel(s) have low contrast ratio (< 4.5:1). "
              f"May fail accessibility standards.")

    # Grayscale compatibility summary
    gray_issues = [r for r in results if r.get('grayscale_safe') is False]
    if gray_issues:
        print(f"\n ⚠️  {len(gray_issues)} panel(s) have colors that may be "
              f"indistinguishable in grayscale print. Consider adding patterns or labels.")

    # Metadata summary
    no_meta = [r for r in results if r.get('metadata') is None]
    if no_meta and any(r.get('brightness', 128) < 100 for r in no_meta):
        print(f"\n ℹ️  {len(no_meta)} panel(s) lack EXIF/metadata. "
              f"Consider embedding microscopy parameters (instrument, objective, etc.).")

    # Input panel quality grades (P2-9)
    print("\n Panel Quality Grades:")
    print("-" * 40)
    for r in results:
        if not r.get('exists'):
            grade = 'F'
        else:
            issues = r.get('issues', [])
            critical = sum(1 for i in issues if i[0] == 'CRITICAL')
            warnings = sum(1 for i in issues if i[0] == 'WARNING')
            if critical > 0:
                grade = 'D'
            elif warnings >= 3:
                grade = 'C'
            elif warnings >= 1:
                grade = 'B'
            else:
                grade = 'A'
        fname = os.path.basename(r['file'])
        print(f"   {fname:<30} {grade}")
    print("   (A=excellent, B=minor issues, C=needs attention, D=critical)")

    print("\n" + "=" * 75 + "\n")


# ═══════════════════════════════════════════════════════════════════
# RASTER COMPOSITION (PIL)
# ═══════════════════════════════════════════════════════════════════

def compose_raster(panels, labels, positions, journal='nature',
                   width_mm=None, height_mm=None, dpi=DPI_DEFAULT,
                   output='./figures/composite',
                   standardize_bg=True, dark_mode=False,
                   fit_mode='fit', label_position='top-left',
                   bg_color=None, font_path=None,
                   label_avoidance='off',
                   align='loose',
                   strip_top_pct=0):
    """
    Compose panels into a raster image using PIL.

    Parameters
    ----------
    positions : list of (x, y, w, h) in pixels
        Pre-computed panel positions.
    dark_mode : bool
        If True, use dark background and white labels.
    fit_mode : str
        'fit', 'fill', 'original', 'stretch'
    """
    spec = JOURNAL_DEFAULTS.get(journal, JOURNAL_DEFAULTS['nature'])

    if width_mm is None:
        width_mm = spec['full_width_mm']
    if height_mm is None:
        # Auto-estimate from positions
        max_x = max(x + w for x, y, w, h in positions)
        max_y = max(y + h for x, y, w, h in positions)
        # Convert back to mm approximately (already in pixels, convert)
        height_mm = int(max_y / dpi * 25.4 + MARGIN_MM)

    # Enforce A4 canvas constraint
    width_mm, height_mm, a4_warnings = enforce_a4_limits(width_mm, height_mm, journal)
    for w in a4_warnings:
        print(f"  ⚠️  {w}")

    W = int(width_mm / 25.4 * dpi)
    H = int(height_mm / 25.4 * dpi)

    if bg_color is None:
        bg_color = (0, 0, 0) if dark_mode else (255, 255, 255)

    canvas = Image.new('RGBA', (W, H), bg_color + (255,))
    draw = ImageDraw.Draw(canvas)
    # PIL uses pixels, spec gives points. Convert: px = pt * dpi / 72
    label_px = max(8, int(spec['label_size_pt'] * dpi / 72))
    label_font = load_font(label_px, bold=True, prefer_font=font_path)

    for i, (panel_path, label, (px, py, pw, ph)) in enumerate(zip(panels, labels, positions)):
        print(f"  [{i+1}/{len(panels)}] Processing: {os.path.basename(panel_path)}")

        # Format label
        if spec['label_case'] == 'upper':
            label = label.upper()
        else:
            label = label.lower()

        if not os.path.exists(panel_path):
            print(f"     ⚠️  File not found: {panel_path}")
            draw.rectangle([px, py, px + pw, py + ph], outline=(255, 0, 0), width=3)
            draw.text((px + 10, py + 10), f"MISSING:\n{panel_path}",
                      font=label_font, fill=(255, 0, 0))
            continue

        try:
            img = load_image_any_format(panel_path, dpi=dpi)
            # Strip top portion if requested (e.g., to remove embedded titles)
            if strip_top_pct > 0:
                w, h = img.size
                crop_y = int(h * strip_top_pct / 100)
                if crop_y > 0 and crop_y < h * 0.25:
                    img = img.crop((0, crop_y, w, h))
            if standardize_bg and not dark_mode:
                img = standardize_background(img, target_bg=bg_color)
            v_a = 'top' if align == 'strict' else 'center'
            h_a = 'left' if align == 'strict' else 'center'
            fitted = fit_image(img, pw, ph, fit_mode=fit_mode, bg_color=bg_color,
                               v_align=v_a, h_align=h_a)
            canvas.paste(fitted, (px, py))
        except Exception as e:
            print(f"     ❌ Error: {e}")
            draw.rectangle([px, py, px + pw, py + ph], outline=(255, 0, 0), width=3)
            draw.text((px + 10, py + 10), f"ERROR:\n{str(e)[:50]}",
                      font=label_font, fill=(255, 0, 0))

        # Detect panel type for adaptive offset
        ptype = detect_panel_type(fitted)

        # Add label (with smart avoidance if enabled)
        add_panel_label(draw, label, px, py, pw, ph, label_font,
                        position=label_position, dark_mode=dark_mode,
                        panel_img=fitted, avoidance=label_avoidance,
                        panel_type=ptype)

    # Convert to RGB for saving (most formats don't support RGBA)
    if bg_color == (0, 0, 0):
        final = Image.new('RGB', (W, H), (0, 0, 0))
        final.paste(canvas, (0, 0), canvas)
    else:
        final = canvas.convert('RGB')

    # Save
    os.makedirs(os.path.dirname(output) if os.path.dirname(output) else '.', exist_ok=True)
    final.save(f"{output}.png", dpi=(dpi, dpi))
    final.save(f"{output}.tiff", dpi=(dpi, dpi))
    print(f"  Saved raster: {output}.png, {output}.tiff")

    return final


# ═══════════════════════════════════════════════════════════════════
# VECTOR COMPOSITION (matplotlib)
# ═══════════════════════════════════════════════════════════════════

def compose_vector(panels, labels, positions, journal='nature',
                   width_mm=None, height_mm=None, dpi=DPI_DEFAULT,
                   output='./figures/composite',
                   fit_mode='fit', label_position='top-left',
                   dark_mode=False, font_path=None,
                   label_avoidance='off',
                   align='loose'):
    """
    Compose panels using matplotlib gridspec.
    Output is vector (SVG/PDF) with raster-embedded images.
    The frame, labels, and spines are vector; panel images are raster.
    """
    try:
        import matplotlib
        matplotlib.use('Agg')  # non-interactive backend
        import matplotlib.pyplot as plt
        import matplotlib.gridspec as gridspec
        import numpy as np
    except ImportError:
        print("WARNING: matplotlib not available. Cannot generate vector output.")
        return None

    spec = JOURNAL_DEFAULTS.get(journal, JOURNAL_DEFAULTS['nature'])

    if width_mm is None:
        width_mm = spec['full_width_mm']
    if height_mm is None:
        max_y = max(y + h for x, y, w, h in positions)
        height_mm = int(max_y / dpi * 25.4 + MARGIN_MM)

    # Enforce A4 canvas constraint
    width_mm, height_mm, a4_warnings = enforce_a4_limits(width_mm, height_mm, journal)
    for w in a4_warnings:
        print(f"  ⚠️  {w}")

    fig_w = width_mm / 25.4
    fig_h = height_mm / 25.4

    # Set matplotlib rcParams for editable text
    plt.rcParams['font.family'] = 'sans-serif'
    plt.rcParams['font.sans-serif'] = ['Arial', 'Helvetica', 'DejaVu Sans', 'Liberation Sans']
    plt.rcParams['svg.fonttype'] = 'none'
    plt.rcParams['pdf.fonttype'] = 42

    fig = plt.figure(figsize=(fig_w, fig_h), dpi=dpi)
    fig.patch.set_facecolor('black' if dark_mode else 'white')

    # Create axes for each panel based on positions
    W_px = fig_w * dpi
    H_px = fig_h * dpi

    for i, (panel_path, label, (px, py, pw, ph)) in enumerate(zip(panels, labels, positions)):
        # Convert pixel positions to figure-relative coordinates
        left = px / W_px
        bottom = 1 - (py + ph) / H_px  # matplotlib uses bottom-left origin
        width = pw / W_px
        height = ph / H_px

        ax = fig.add_axes([left, bottom, width, height])
        ax.set_xticks([])
        ax.set_yticks([])
        for spine in ax.spines.values():
            spine.set_visible(False)
        ax.set_facecolor('black' if dark_mode else 'white')

        # Load and display image
        if os.path.exists(panel_path):
            try:
                img = load_image_any_format(panel_path, dpi=dpi)
                # Handle alpha
                if img.mode in ('RGBA', 'LA', 'P'):
                    img_array = np.array(img)
                else:
                    img_array = np.array(img.convert('RGB'))
                ax.imshow(img_array, aspect='auto',
                          interpolation='nearest',
                          extent=[0, 1, 0, 1])
            except Exception as e:
                ax.text(0.5, 0.5, f'Error:\n{str(e)[:50]}',
                        ha='center', va='center', transform=ax.transAxes,
                        color='red', fontsize=8)
        else:
            ax.text(0.5, 0.5, f'Missing:\n{panel_path}',
                    ha='center', va='center', transform=ax.transAxes,
                    color='red', fontsize=8)

        # Label (with smart avoidance)
        if spec['label_case'] == 'upper':
            label = label.upper()
        else:
            label = label.lower()

        label_color = 'white' if dark_mode else 'black'

        # Adaptive offset based on panel type (matplotlib axes coords)
        ptype = 'unknown'
        if os.path.exists(panel_path):
            try:
                pimg = load_image_any_format(panel_path, dpi=dpi)
                ptype = detect_panel_type(pimg)
            except Exception:
                pass
        offset_map = {'plot': (0.02, 0.98), 'heatmap': (0.04, 0.96),
                      'table': (0.04, 0.96), 'microscopy': (0.03, 0.97),
                      'unknown': (0.02, 0.98)}
        base_x, base_y = offset_map.get(ptype, (0.02, 0.98))

        # Determine label position with avoidance
        resolved_pos = label_position
        text_x, text_y = base_x, base_y
        ha, va = 'left', 'top'

        if label_avoidance in ('auto', 'strict') and os.path.exists(panel_path):
            try:
                img = load_image_any_format(panel_path, dpi=dpi)
                safe_x_px, resolved_pos_vec, _ = find_label_safe_zone(
                    img,
                    label_w=int(spec['label_size_pt'] * 2),  # approximate width in px
                    label_h=int(spec['label_size_pt'] * 1.5),
                    offset=int(spec['label_size_pt']),
                    max_scan_x_ratio=0.5 if label_avoidance == 'auto' else 0.35
                )
                # Convert pixel offset back to axes fraction
                img_w = img.size[0]
                shift_frac = safe_x_px / max(img_w, 1)
                if resolved_pos_vec == 'top-right':
                    text_x, text_y = 0.98, 0.98
                    ha = 'right'
                elif resolved_pos_vec == 'top-left-shifted' and shift_frac > 0.05:
                    text_x = 0.02 + shift_frac
                    text_y = 0.98
                else:
                    text_x, text_y = 0.02, 0.98
            except Exception:
                pass  # fallback to default

        if resolved_pos == 'top-right' or (label_position == 'top-right' and label_avoidance == 'off'):
            text_x, text_y = 0.98, 0.98
            ha = 'right'

        ax.text(text_x, text_y, label, transform=ax.transAxes,
                fontsize=spec['label_size_pt'], fontweight='bold',
                va=va, ha=ha, color=label_color)

    # Save vector formats
    os.makedirs(os.path.dirname(output) if os.path.dirname(output) else '.', exist_ok=True)
    fig.savefig(f"{output}.svg", bbox_inches='tight', facecolor=fig.get_facecolor())
    fig.savefig(f"{output}.pdf", bbox_inches='tight', facecolor=fig.get_facecolor())
    print(f"  Saved vector: {output}.svg, {output}.pdf")

    plt.close(fig)
    return fig


# ═══════════════════════════════════════════════════════════════════
# NATIVE VECTOR PDF (pymupdf — editable in Illustrator)
# ═══════════════════════════════════════════════════════════════════

def compose_pdf_native(panels, labels, positions, journal='nature',
                       width_mm=None, height_mm=None, dpi=DPI_DEFAULT,
                       output='./figures/composite',
                       dark_mode=False, label_position='top-left',
                       label_avoidance='off',
                       align='loose',
                       strip_top_pct=0):
    """
    Compose panels directly from PDF sources into a single editable PDF.
    Uses pymupdf to embed original PDF pages as vector objects.
    Panel content (text, lines, shapes) remains fully editable in Illustrator.
    Labels are added as native vector text.
    """
    try:
        import fitz
    except ImportError:
        print("  WARNING: pymupdf not available. Cannot generate native vector PDF.")
        return None

    spec = JOURNAL_DEFAULTS.get(journal, JOURNAL_DEFAULTS['nature'])

    if width_mm is None:
        width_mm = spec['full_width_mm']
    if height_mm is None:
        max_y = max(y + h for x, y, w, h in positions)
        height_mm = int(max_y / dpi * 25.4 + MARGIN_MM)

    # Enforce A4 canvas constraint
    width_mm, height_mm, a4_warnings = enforce_a4_limits(width_mm, height_mm, journal)
    for w in a4_warnings:
        print(f"  ⚠️  {w}")

    PT_PER_MM = 72.0 / 25.4
    page_w_pt = width_mm * PT_PER_MM
    page_h_pt = height_mm * PT_PER_MM

    doc = fitz.open()
    page = doc.new_page(width=page_w_pt, height=page_h_pt)

    # White/black background
    bg = (0, 0, 0) if dark_mode else (1, 1, 1)
    page.draw_rect(fitz.Rect(0, 0, page_w_pt, page_h_pt), color=bg, fill=bg)

    # Load Arial Bold from file for vector labels
    arial_font_path = '/home/chinure/.local/share/fonts/arial/arialbd.ttf'
    arial_font_name = "ArialBold"
    try:
        with open(arial_font_path, "rb") as f:
            fontbuffer = f.read()
        page.insert_font(fontname=arial_font_name, fontbuffer=fontbuffer)
    except Exception:
        arial_font_name = "helv"  # fallback

    for i, (panel_path, label, (px, py, pw, ph)) in enumerate(zip(panels, labels, positions)):
        if not panel_path.lower().endswith('.pdf'):
            print(f"  Panel {label}: non-PDF input, skipped in native PDF")
            continue
        if not os.path.exists(panel_path):
            print(f"  Panel {label}: file not found")
            continue

        try:
            src = fitz.open(panel_path)
            # Apply top strip if requested
            if strip_top_pct > 0 and strip_top_pct <= 20:
                src_page = src[0]
                rect = src_page.rect
                crop_y = rect.y0 + rect.height * strip_top_pct / 100.0
                src_page.set_cropbox(fitz.Rect(rect.x0, crop_y, rect.x1, rect.y1))
            # Convert pixel coords → PDF points
            x_pt = px / dpi * 72.0
            y_pt = py / dpi * 72.0
            w_pt = pw / dpi * 72.0
            h_pt = ph / dpi * 72.0
            target_rect = fitz.Rect(x_pt, y_pt, x_pt + w_pt, y_pt + h_pt)
            page.show_pdf_page(target_rect, src, 0)
            src.close()
        except Exception as e:
            print(f"  Panel {label}: embedding error — {e}")
            continue

        # Vector label
        label_color = (1, 1, 1) if dark_mode else (0, 0, 0)
        label_size_pt = spec['label_size_pt']
        display_label = label.upper() if spec['label_case'] == 'upper' else label.lower()

        offset_pt = 2.5 * PT_PER_MM
        label_x = x_pt + offset_pt
        label_y = y_pt + offset_pt + label_size_pt * 0.35

        try:
            page.insert_text((label_x, label_y), display_label,
                             fontsize=label_size_pt,
                             fontname=arial_font_name,
                             color=label_color)
        except Exception as e:
            print(f"  Panel {label}: label insertion error — {e}")

    os.makedirs(os.path.dirname(output) if os.path.dirname(output) else '.', exist_ok=True)
    pdf_path = f"{output}.pdf"
    doc.save(pdf_path)
    doc.close()
    print(f"  Saved native vector PDF: {pdf_path}")
    return pdf_path


# ═══════════════════════════════════════════════════════════════════
# MAIN COMPOSITION (orchestrates raster + vector)
# ═══════════════════════════════════════════════════════════════════

def compose(panels, labels=None, layout='grid', layout_specs=None,
            grid=None, hero_index=None, hero_ratio=0.55, hero_side='top',
            journal='nature', width_mm=None, height_mm=None, dpi=DPI_DEFAULT,
            output='./figures/composite',
            standardize_bg=True, dark_mode='auto',
            fit_mode='fit', label_position='top-left',
            bg_color=None, font_path=None,
            vector_output=True, smart_layout=False,
            label_avoidance='off',
            align='loose',
            strip_top_pct=0,
            figure_type='main'):
    """
    Main composition function. Orchestrates layout, audit, raster, and vector.

    Parameters
    ----------
    panels : list[str]
        File paths to panel images.
    labels : list[str] or None
        Panel labels. Auto-generated as a, b, c, ... if None.
    layout : str
        'grid', 'custom', 'hero-top', 'hero-left'.
    layout_specs : list[dict] or None
        For 'custom' layout: list of {row, col, rowspan, colspan} dicts.
    grid : tuple(int, int) or None
        For 'grid' layout: (rows, cols).
    hero_index : int or None
        For hero layouts: which panel (0-based) is hero.
    hero_ratio : float
        Fraction of canvas for hero panel (0.4–0.7).
    hero_side : str
        'top' or 'left' for hero layout.
    journal : str
        Target journal name.
    dark_mode : str or bool
        'auto' — detect from image brightness.
        True — force dark.
        False — force light (default).
    vector_output : bool
        Whether to also generate SVG/PDF via matplotlib.
    smart_layout : bool
        If True, analyze panel proportions and auto-adjust layout to protect
        text readability. Wide panels get colspan>1; tall panels get rowspan>1.
        Only applies when layout='grid'.
    label_avoidance : str
        'off' — fixed offset (default).
        'auto' — scan panel top row for content; shift label right if overlap
                 detected; fallback to top-right if top row is busy.
        'strict' — more aggressive avoidance with tighter scan range.
    """
    n = len(panels)
    if labels is None:
        labels = [chr(97 + i) for i in range(n)]

    spec = JOURNAL_DEFAULTS.get(journal, JOURNAL_DEFAULTS['nature'])

    if width_mm is None:
        width_mm = spec['full_width_mm']
    if height_mm is None:
        # Default: estimate from layout
        if layout == 'grid' and grid:
            panel_w_mm = (width_mm - 2 * MARGIN_MM - (grid[1] - 1) * GAP_MM) / grid[1]
            panel_h_mm = panel_w_mm * 0.75  # assume 4:3 aspect
            height_mm = 2 * MARGIN_MM + grid[0] * panel_h_mm + (grid[0] - 1) * GAP_MM
        else:
            height_mm = width_mm * 0.65  # default ~2:3
        height_mm = max(height_mm, 80)

    # Enforce A4 canvas constraint before pixel computation
    width_mm, height_mm, a4_warnings = enforce_a4_limits(width_mm, height_mm, journal)
    for w in a4_warnings:
        print(f"⚠️  {w}")

    W = int(width_mm / 25.4 * dpi)
    H = int(height_mm / 25.4 * dpi)
    MARGIN = int(MARGIN_MM / 25.4 * dpi)
    GAP = int(GAP_MM / 25.4 * dpi)

    # Supplementary figures: tighter spacing, smaller labels
    if figure_type == 'supplementary':
        GAP = int(GAP_MM / 25.4 * dpi * 0.6)  # 40% tighter
        print("  Supplementary mode: tighter spacing, smaller labels")

    # ── Smart layout: auto-adjust based on panel proportions ──
    if smart_layout and layout == 'grid':
        print("\nAnalyzing panel proportions for content-aware sizing...")
        # Estimate grid cols for analysis
        est_cols = grid[1] if grid else max(2, int(len(panels) ** 0.5))
        panel_analysis = analyze_panel_proportions(panels, journal, est_cols, dpi)
        print_proportion_report(panel_analysis)

        # Generate layout specs from analysis
        auto_specs, auto_cols, auto_rows, sug_height = compute_smart_layout_specs(
            panel_analysis, max_cols=max(3, est_cols)
        )

        # Check if any panel needs regeneration
        regen = [pa for pa in panel_analysis
                 if pa.get('strategy') == 'REGENERATE']
        if regen:
            print(f"\n⚠️  {len(regen)} panel(s) will have unreadable text even with")
            print("   smart layout. Recommended action: regenerate from source data")
            print("   using larger font sizes (≥ 8 pt at intended print width).")

        # Switch to custom layout with auto-generated specs
        layout = 'custom'
        layout_specs = auto_specs
        grid = (auto_rows, auto_cols)
        if height_mm is None or height_mm < sug_height:
            height_mm = sug_height
            H = int(height_mm / 25.4 * dpi)
            print(f"   Adjusted figure height to {height_mm} mm for readability.")

        print(f"   Auto layout: {auto_rows} rows × {auto_cols} cols")
        for i, spec in enumerate(auto_specs):
            if spec['colspan'] > 1 or spec['rowspan'] > 1:
                print(f"   Panel {chr(97+i)}: spans {spec['rowspan']}×{spec['colspan']} cells")

    # Compute positions
    if layout == 'grid':
        if grid is None:
            # Auto-determine grid based on trimmed content dimensions
            auto_rows, auto_cols = auto_detect_grid(
                panels, target_width_mm=width_mm,
                gap_mm=GAP_MM, dpi=dpi, max_cols=4
            )
            grid = (auto_rows, auto_cols)
            print(f"  Auto-detected grid: {auto_rows} rows × {auto_cols} cols "
                  f"(based on trimmed content sizing)")
        positions = compute_grid_positions(n, grid[0], grid[1], W, H, MARGIN, GAP)

    elif layout == 'custom':
        if layout_specs is None:
            raise ValueError("layout='custom' requires layout_specs")
        positions = compute_custom_positions(layout_specs, W, H, MARGIN, GAP)

    elif layout.startswith('hero'):
        if hero_index is None:
            hero_index = 0
        positions = compute_hero_support_positions(
            n, hero_index, hero_ratio, W, H, MARGIN, GAP,
            hero_side=hero_side
        )

    else:
        raise ValueError(f"Unknown layout: {layout}")

    # Auto-detect dark mode
    if dark_mode == 'auto':
        dark_count = 0
        for p in panels:
            if os.path.exists(p):
                try:
                    img = load_image_any_format(p)
                    if estimate_image_brightness(img) < 60:
                        dark_count += 1
                except Exception:
                    pass
        dark_mode = dark_count >= max(1, n // 2)
        if dark_mode:
            print(f"  Auto-detected dark mode ({dark_count}/{n} panels dark)")
    else:
        dark_mode = bool(dark_mode)

    # Compose raster
    print("\nComposing raster output (PIL)...")
    compose_raster(
        panels, labels, positions,
        journal=journal, width_mm=width_mm, height_mm=height_mm, dpi=dpi,
        output=output,
        standardize_bg=standardize_bg, dark_mode=dark_mode,
        fit_mode=fit_mode, label_position=label_position,
        bg_color=bg_color, font_path=font_path,
        label_avoidance=label_avoidance,
        align=align,
        strip_top_pct=strip_top_pct,
    )

    # Compose vector (SVG via matplotlib)
    if vector_output:
        print("\nComposing vector output (matplotlib SVG)...")
        try:
            compose_vector(
                panels, labels, positions,
                journal=journal, width_mm=width_mm, height_mm=height_mm, dpi=dpi,
                output=output,
                fit_mode=fit_mode, label_position=label_position,
                dark_mode=dark_mode, font_path=font_path,
                label_avoidance=label_avoidance,
                align=align,
            )
        except Exception as e:
            print(f"  Vector output skipped: {e}")

    # Compose native editable PDF (pymupdf — panels stay vector)
    print("\nComposing native vector PDF (pymupdf)...")
    try:
        compose_pdf_native(
            panels, labels, positions,
            journal=journal, width_mm=width_mm, height_mm=height_mm, dpi=dpi,
            output=output,
            dark_mode=dark_mode, label_position=label_position,
            label_avoidance=label_avoidance,
            align=align,
            strip_top_pct=strip_top_pct,
        )
    except Exception as e:
        print(f"  Native PDF output skipped: {e}")

    return positions


# ═══════════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description='Assemble individual plots into a publication-ready multi-panel figure'
    )
    parser.add_argument('--config', type=str, help='JSON config file')
    parser.add_argument('--panels', nargs='+', help='Panel image files')
    parser.add_argument('--labels', nargs='+', help='Panel labels (a, b, c, ...)')
    parser.add_argument('--grid', nargs=2, type=int, help='Grid rows cols (e.g., 2 2)')
    parser.add_argument('--layout', default='grid',
                        choices=['grid', 'custom', 'hero-top', 'hero-left'],
                        help='Layout archetype')
    parser.add_argument('--hero-index', type=int, help='Which panel is hero (0-based)')
    parser.add_argument('--hero-ratio', type=float, default=0.55,
                        help='Hero panel size ratio (0.4-0.7)')
    parser.add_argument('--journal', default='nature',
                        choices=list(JOURNAL_DEFAULTS.keys()) + ['other'],
                        help='Target journal')
    parser.add_argument('--width-mm', type=int, help='Output width in mm')
    parser.add_argument('--height-mm', type=int, help='Output height in mm')
    parser.add_argument('--dpi', type=int, default=DPI_DEFAULT)
    parser.add_argument('--output', default='./figures/composite')
    parser.add_argument('--fit-mode', default='fit',
                        choices=['fit', 'fill', 'original', 'stretch'],
                        help='How to fit images into panel slots')
    parser.add_argument('--label-position', default='top-left',
                        choices=['top-left', 'top-right', 'outside-top-left'],
                        help='Where to place panel labels')
    parser.add_argument('--dark-mode', default='auto',
                        choices=['auto', 'true', 'false'],
                        help='Dark background mode')
    parser.add_argument('--font-path', type=str,
                        help='Path to a TTF font file for labels')
    parser.add_argument('--no-std-bg', action='store_true',
                        help='Skip background standardization')
    parser.add_argument('--no-vector', action='store_true',
                        help='Skip SVG/PDF vector output')
    parser.add_argument('--smart-layout', action='store_true',
                        help='Auto-adjust panel sizes based on original proportions '
                             'to protect text readability. Wide panels get colspan>1; '
                             'tall panels get rowspan>1. Only for layout=grid.')
    parser.add_argument('--label-avoidance', default='off',
                        choices=['off', 'auto', 'strict'],
                        help='Smart label placement: scan panel top row for content and '
                             'shift label to avoid overlap. "auto"=moderate; "strict"=aggressive.')
    parser.add_argument('--align', default='loose',
                        choices=['loose', 'strict'],
                        help='Panel alignment within grid slots. "loose"=center (default); '
                             '"strict"=top-left align to reduce visual misalignment.')
    parser.add_argument('--strip-top-pct', type=float, default=0,
                        help='Strip N%% from the top of each panel (0-20). Useful for removing '
                             'embedded figure titles before assembly. Cell Press prohibits '
                             'titles embedded in figure images.')
    parser.add_argument('--figure-type', default='main',
                        choices=['main', 'supplementary'],
                        help='Figure category. "supplementary" uses tighter spacing and smaller labels.')
    parser.add_argument('--audit-only', action='store_true',
                        help='Only run consistency audit, do not compose')

    args = parser.parse_args()

    # Load from config or CLI
    if args.config:
        with open(args.config) as f:
            config = json.load(f)
        panels = config.get('panels', [])
        labels = config.get('labels', None)
        layout = config.get('layout', 'grid')
        layout_specs = config.get('layout_specs', None)
        grid = config.get('grid', None)
        hero_index = config.get('hero_index', None)
        hero_ratio = config.get('hero_ratio', 0.55)
        journal = config.get('journal', 'nature')
        width_mm = config.get('width_mm')
        height_mm = config.get('height_mm')
        output = config.get('output', './figures/composite')
        dpi = config.get('dpi', DPI_DEFAULT)
        fit_mode = config.get('fit_mode', 'fit')
        label_position = config.get('label_position', 'top-left')
        dark_mode = config.get('dark_mode', 'auto')
        font_path = config.get('font_path', None)
        standardize_bg = config.get('standardize_bg', True)
        vector_output = config.get('vector_output', True)
        smart_layout = config.get('smart_layout', False)
        label_avoidance = config.get('label_avoidance', 'off')
        align = config.get('align', 'loose')
        strip_top_pct = config.get('strip_top_pct', 0)
        figure_type = config.get('figure_type', 'main')
    else:
        panels = args.panels or []
        labels = args.labels
        layout = args.layout
        layout_specs = None
        grid = args.grid
        hero_index = args.hero_index
        hero_ratio = args.hero_ratio
        journal = args.journal
        width_mm = args.width_mm
        height_mm = args.height_mm
        output = args.output
        dpi = args.dpi
        fit_mode = args.fit_mode
        label_position = args.label_position
        dark_mode = args.dark_mode
        font_path = args.font_path
        standardize_bg = not args.no_std_bg
        vector_output = not args.no_vector
        smart_layout = args.smart_layout
        label_avoidance = args.label_avoidance
        align = args.align
        strip_top_pct = args.strip_top_pct
        figure_type = args.figure_type

    if not panels:
        print("ERROR: No panel files specified.")
        parser.print_help()
        sys.exit(1)

    if labels is None:
        labels = [chr(97 + i) for i in range(len(panels))]

    if len(labels) != len(panels):
        print(f"WARNING: {len(labels)} labels for {len(panels)} panels. Adjusting.")
        labels = labels[:len(panels)] + [chr(97 + i) for i in range(len(labels), len(panels))]

    # Audit
    print("=" * 60)
    print(" Running consistency audit...")
    print("=" * 60)
    audit_results = audit_panels(panels)
    print_audit_report(audit_results, journal=journal)

    if args.audit_only:
        return

    # Check for critical issues
    critical_issues = [
        r for r in audit_results
        if any(i[0] == 'CRITICAL' for i in r.get('issues', []))
    ]
    if critical_issues:
        print("⚠️  Critical issues found. Proceed anyway? (y/n): ", end='')
        try:
            resp = input().strip().lower()
            if resp not in ('y', 'yes'):
                print("Aborted.")
                sys.exit(1)
        except EOFError:
            print("(non-interactive, proceeding with warnings)")

    # Compose
    print("=" * 60)
    print(" Composing figure...")
    print("=" * 60)

    compose(
        panels=panels,
        labels=labels,
        layout=layout,
        layout_specs=layout_specs,
        grid=grid,
        hero_index=hero_index,
        hero_ratio=hero_ratio,
        journal=journal,
        width_mm=width_mm,
        height_mm=height_mm,
        dpi=dpi,
        output=output,
        standardize_bg=standardize_bg,
        dark_mode=dark_mode,
        fit_mode=fit_mode,
        label_position=label_position,
        font_path=font_path,
        vector_output=vector_output,
        smart_layout=smart_layout,
        label_avoidance=label_avoidance,
        align=align,
        strip_top_pct=strip_top_pct,
        figure_type=figure_type,
    )

    print("\n" + "=" * 60)
    print(" Done!")
    print(f" Output: {output}.*")
    print("=" * 60)


if __name__ == '__main__':
    main()
