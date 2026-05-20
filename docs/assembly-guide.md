# Detailed Assembly Guide

Complete Python code templates for composing multi-panel figures.
Read this file when executing Stage 4 of the figure-compositor workflow.

**Preferred approach:** Use the bundled `scripts/compose_figure.py` script for most
assembly tasks. It handles regular grids, hero+support layouts, custom layouts,
dark mode, vector output, and consistency auditing. This guide is for reference
and advanced customization.

---

## Quick start with the script

```bash
# Regular grid
python compose_figure.py --panels a.png b.png c.png d.png --grid 2 2 --journal nature

# Hero + support (hero panel dominates top)
python compose_figure.py --panels heatmap.png bars.png scatter.png \
    --layout hero-top --hero-index 0 --journal nature

# Custom layout via JSON config
python compose_figure.py --config figure_2_config.json

# Dark microscopy images
python compose_figure.py --panels ch1.tif ch2.tif merged.tif quant.png \
    --grid 2 2 --dark-mode auto --fit-mode fill

# Audit only (check before composing)
python compose_figure.py --panels *.png --audit-only
```

See `scripts/config_example_*.json` for complete JSON config examples.

---

## Method A: PIL Canvas Composition (default)

Best for pure assembly of raster images (PNG, JPG, TIFF). The script uses this
method for PNG/TIFF output. Most reliable and produces clean output.

### Core concepts

```python
from PIL import Image, ImageDraw, ImageFont
import numpy as np

# 1. Create canvas at target dimensions
canvas = Image.new('RGBA', (width_px, height_px), (255, 255, 255, 255))

# 2. Load and fit each panel image
img = Image.open('panel.png')
# Handle alpha channel properly
if img.mode in ('RGBA', 'LA', 'P'):
    bg = Image.new('RGBA', img.size, bg_color + (255,))
    img = Image.alpha_composite(bg, img.convert('RGBA'))

# 3. Resize preserving aspect ratio (fit mode)
resized = img.resize((new_w, new_h), Image.LANCZOS)
canvas.paste(resized, (paste_x, paste_y))

# 4. Add label
draw = ImageDraw.Draw(canvas)
draw.text((x + offset, y + offset), 'a', font=font, fill=(0, 0, 0))

# 5. Convert to RGB and save
canvas.convert('RGB').save('output.png', dpi=(300, 300))
```

### Fit modes

| Mode | Behavior | Use when |
|------|----------|----------|
| **fit** | Preserve AR, letterbox on bg_color | Aspect ratios vary (default) |
| **fill** | Preserve AR, center-crop to fill | Need to avoid letterboxing |
| **original** | No resize, center at original size | User already sized correctly |
| **stretch** | Distort to fill | **Never for publication** |

### Background standardization (numpy-fast)

```python
import numpy as np

def standardize_background_fast(img, target_bg=(255, 255, 255), tolerance=20):
    arr = np.array(img.convert('RGB'))
    white_mask = (
        (arr[:, :, 0] > 255 - tolerance) &
        (arr[:, :, 1] > 255 - tolerance) &
        (arr[:, :, 2] > 255 - tolerance)
    )
    arr[white_mask] = target_bg
    return Image.fromarray(arr, 'RGB')
```

---

## Method B: Matplotlib Gridspec (for vector output)

Best when you need SVG/PDF vector output with editable frame and labels.
Panel images are embedded as raster, but the frame, labels, and annotations
remain vector.

```python
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from PIL import Image
import numpy as np

# Mandatory for editable text
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = ['Arial', 'Helvetica', 'DejaVu Sans']
plt.rcParams['svg.fonttype'] = 'none'
plt.rcParams['pdf.fonttype'] = 42

fig = plt.figure(figsize=(7.2, 5.5), dpi=300)

# Define layout via gridspec
import matplotlib.gridspec as gridspec
gs = gridspec.GridSpec(2, 3, figure=fig, wspace=0.15, hspace=0.15)

# Place images
for i, (gs_slice, img_path, label) in enumerate([
    (gs[0, :2], 'hero.png', 'a'),
    (gs[0, 2], 'sup1.png', 'b'),
    (gs[1, 0], 'sup2.png', 'c'),
    (gs[1, 1], 'sup3.png', 'd'),
    (gs[1, 2], 'sup4.png', 'e'),
]):
    ax = fig.add_subplot(gs_slice)
    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_visible(False)

    img = Image.open(img_path)
    arr = np.array(img.convert('RGB'))
    ax.imshow(arr, aspect='auto', interpolation='nearest')

    ax.text(0.02, 0.98, label, transform=ax.transAxes,
            fontsize=8, fontweight='bold', va='top', ha='left')

fig.savefig('output.svg', bbox_inches='tight')
fig.savefig('output.pdf', bbox_inches='tight')
plt.close(fig)
```

### Method A vs B: decision flow

```
Need vector output (SVG/PDF)?
    ├── Yes → Method B (matplotlib) for frame + labels
    │         Embedded images still raster (expected)
    │         For fully editable vector, use Illustrator
    │
    └── No  → Method A (PIL)
              Simpler, faster, more reliable
              All outputs raster (PNG/TIFF)
```

---

## Handling PDF/SVG inputs

When panels are vector files, rasterize them before PIL composition.

```python
def load_vector_as_raster(path, dpi=300):
    ext = path.lower().split('.')[-1]
    if ext == 'pdf':
        from pdf2image import convert_from_path
        return convert_from_path(path, dpi=dpi)[0]
    elif ext == 'svg':
        import cairosvg, io
        png_data = cairosvg.svg2png(url=path, dpi=dpi)
        return Image.open(io.BytesIO(png_data))
    else:
        return Image.open(path)
```

**Dependencies:**
- PDF: `pip install pdf2image` + system `poppler-utils`
- SVG: `pip install cairosvg` + system `libcairo2-dev`

If unavailable, pre-convert to PNG before assembly.

---

## Dark image plates

For microscopy, fluorescence, or volume-rendering panels on black backgrounds:

```python
# Auto-detect brightness and switch to dark mode
brightness = estimate_image_brightness(img)  # 0-255
is_dark = brightness < 60

bg_color = (0, 0, 0) if is_dark else (255, 255, 255)
label_color = (255, 255, 255) if is_dark else (0, 0, 0)

canvas = Image.new('RGBA', (W, H), bg_color + (255,))
# ... paste images ...
draw.text((x, y), 'a', fill=label_color)
```

The bundled script auto-detects this with `--dark-mode auto`.

---

## Shared legend panel

When panels share the same legend, add a dedicated legend panel or strip.

### With matplotlib (Method B)

```python
# Collect handles from first panel
handles, labels = axes[0].get_legend_handles_labels()

# Create shared legend axis
fig.legend(handles, labels, loc='upper center',
           bbox_to_anchor=(0.5, 0.98), ncol=4,
           frameon=False, fontsize=7)
```

### With PIL (Method A)

```python
def draw_text_legend(draw, items, x, y, font, line_height=20):
    """Draw color swatch + text legend."""
    for i, (color, text) in enumerate(items):
        iy = y + i * line_height
        draw.rectangle([x, iy, x + 15, iy + 12], fill=color)
        draw.text((x + 20, iy), text, font=font, fill=(0, 0, 0))
```

---

## Complete script API reference

The bundled `compose_figure.py` script provides a Python API:

```python
from scripts.compose_figure import compose, audit_panels

# Audit only
results = audit_panels(['a.png', 'b.png', 'c.png'])

# Full composition with custom layout
compose(
    panels=['hero.png', 'sup1.png', 'sup2.png'],
    labels=['a', 'b', 'c'],
    layout='hero-top',
    hero_index=0,
    hero_ratio=0.55,
    journal='nature',
    width_mm=183,
    dpi=300,
    output='./figures/figure_2',
    dark_mode='auto',
    fit_mode='fit',
    vector_output=True,
)
```

See `scripts/compose_figure.py` for full docstrings.
