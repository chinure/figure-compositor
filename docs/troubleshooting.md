# Troubleshooting Guide

Common issues encountered when assembling multi-panel figures and how to resolve them.

Read this file when something goes wrong during Stage 4 (composition) or Stage 5 (QA).

---

## Issue: Output file is extremely large (> 50 MB)

**Symptoms:** PNG/TIFF file exceeds journal limits (Cell: 20 MB, Science: 15 MB).

**Causes:**
1. Input panels are very high-resolution (e.g., 4000×3000 microscopy images).
2. TIFF saved without compression.
3. Canvas dimensions larger than needed.

**Solutions:**
```bash
# Option 1: Reduce DPI (if images are oversized for the panel)
python compose_figure.py --panels *.png --dpi 150

# Option 2: Resize panels before assembly
python -c "
from PIL import Image
for f in ['panel_a.png', 'panel_b.png']:
    img = Image.open(f)
    img = img.resize((int(img.width * 0.5), int(img.height * 0.5)), Image.LANCZOS)
    img.save(f.replace('.png', '_small.png'))
"

# Option 3: Use PNG instead of TIFF (lossless, better compression)
# TIFF with LZW is required by some journals; PNG is acceptable by most.
```

---

## Issue: Panel labels are blurry or pixelated

**Symptoms:** The a, b, c labels look fuzzy or aliased in the output.

**Causes:**
1. Font file not found; script fell back to PIL default bitmap font.
2. Label rendered at too small a size and then scaled up.
3. Output saved at lower DPI than composition DPI.

**Solutions:**
```bash
# Specify a high-quality font explicitly
python compose_figure.py --panels *.png --font-path /usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf

# Check font availability on your system
fc-list : family | grep -i "arial\|helvetica\|dejavu"
```

**Prevention:** Install Arial or Liberation fonts on your system before running.

---

## Issue: Transparent backgrounds turn black

**Symptoms:** A panel with transparent background (e.g., from BioRender or PowerPoint)
shows black where it should be white/transparent.

**Cause:** Older versions of the script used `convert('RGB')` which discards alpha channel
and replaces transparent pixels with black.

**Solution:** This is fixed in the current script. The composer now:
1. Detects RGBA/PA/LA modes.
2. Composites transparent regions onto the target background color before fitting.

If still seeing black:
```python
# Manually pre-process the panel
from PIL import Image
img = Image.open('transparent_panel.png')
# Composite onto white background
bg = Image.new('RGBA', img.size, (255, 255, 255, 255))
img = Image.alpha_composite(bg, img.convert('RGBA'))
img.save('panel_opaque.png')
```

---

## Issue: Dark microscopy panels have white borders

**Symptoms:** Fluorescence images on black backgrounds get a white letterbox border.

**Cause:** Default `fit_mode='fit'` centers the image on the canvas background (white by
default), creating visible borders.

**Solutions:**
```bash
# Use dark mode (auto-detects from image brightness)
python compose_figure.py --panels *.tif --dark-mode auto

# Or force dark mode
python compose_figure.py --panels *.tif --dark-mode true

# Or use fill mode to avoid letterboxing
python compose_figure.py --panels *.tif --fit-mode fill --dark-mode true
```

---

## Issue: PDF text not editable in Adobe Illustrator

**Symptoms:** Opening a panel PDF or composite PDF in Illustrator shows text as
outlines/glyphs. The Fonts panel is empty or shows "Outlined". Cannot select or
edit individual characters.

**Cause 1 — Type 3 fonts:** matplotlib defaults to Type 3 (PostScript graphics)
fonts for PDF output. Each glyph is a vector drawing, not a font character.
Illustrator cannot convert these back to editable text.

**Fix:** Set `pdf.fonttype = 42` to embed TrueType fonts:

```python
plt.rcParams.update({
    'pdf.fonttype': 42,
    'ps.fonttype': 42,
})
```

**Cause 2 — Font not registered:** If Arial (or your target font) is installed in
a non-system directory (e.g. `~/.local/share/fonts/`), matplotlib's font manager
will not find it automatically. It silently falls back to DejaVu Sans, even though
`font.sans-serif` lists Arial first.

**Fix:** Register the font explicitly **before** importing `pyplot`:

```python
import matplotlib.font_manager as fm
fm.fontManager.addfont('/home/user/.local/share/fonts/arial/arial.ttf')
fm.fontManager.addfont('/home/user/.local/share/fonts/arial/arialbd.ttf')

import matplotlib.pyplot as plt  # import AFTER registration
plt.rcParams.update({
    'font.family': 'sans-serif',
    'font.sans-serif': ['Arial', 'DejaVu Sans'],
    'pdf.fonttype': 42,
    'ps.fonttype': 42,
})
```

**Verification:**

```python
import fitz  # pymupdf
doc = fitz.open('panel.pdf')
for f in doc[0].get_fonts(full=True):
    print(f"  {f[3]}: {f[2]}")
# Should show: ArialMT Type0, Arial-BoldMT Type0
# NOT: DejaVuSans Type3
```

---

## Issue: Composite PDF panels are not editable (rasterized)

**Symptoms:** Individual panel PDFs are editable in Illustrator, but after
combining them into a composite Figure, the panels appear as images inside the
PDF. Text cannot be selected.

**Cause:** The vector composition path (`compose_vector()`) uses matplotlib's
`ax.imshow()`, which converts PDF inputs to raster numpy arrays before embedding.
The output PDF contains raster images, not vector panel pages.

**Solution:** The script auto-detects when all inputs are PDF and uses the native
vector path (`compose_pdf_native()`) instead. This path uses pymupdf's
`show_pdf_page()` to embed each panel as a native PDF Form XObject — all text,
lines, and curves remain vector and editable.

**Requirements:**
1. All panels must be PDF (not PNG/JPG).
2. Panels must use Type 42 (TrueType) fonts (see "PDF text not editable" above).
3. The script must have pymupdf installed: `pip install pymupdf`.

**To force/check the native path:**

```bash
# The script auto-selects based on input extensions
python compose_figure.py --config config.json  # panels must be *.pdf
```

If the native path is not available, the script falls back to the vector-hybrid
path (raster panels + vector frame).

---

## Issue: Vector output (SVG/PDF) has blurry/raster images

**Symptoms:** The SVG/PDF frame is vector, but the embedded panel images look pixelated.

**Cause:** The default `compose_vector()` path uses matplotlib's `ax.imshow()`, which
rasterizes any input (even PDF/SVG) into a pixel array before embedding. Only the
frame, labels, and annotations added by the compositor remain vector.

**Three composition paths and their outputs:**

| Path | Function | Input | Panel in output | Best for |
|------|----------|-------|-----------------|----------|
| Raster | `compose_raster()` | Any | Raster (PNG/TIFF) | Preview, pixel-perfect |
| Vector-hybrid | `compose_vector()` | Any | **Raster** (imshow) | Raster inputs needing vector frame |
| Native vector | `compose_pdf_native()` | **PDF only** | **Vector** (PDF XObject) | PDF inputs, Illustrator editing |

**Solution for fully editable vector (PDF inputs):**

If panels are PDF/SVG and you need the composite to be editable in Illustrator:

1. Generate panels as PDF with Type 42 fonts (see "PDF fonts not editable" below).
2. The script auto-detects PDF inputs and uses `compose_pdf_native()` (pymupdf),
   which embeds each panel page as a native PDF Form XObject.
3. All text, lines, and curves remain vector and editable.

```bash
# Config example for vector workflow
{
  "panels": ["a.pdf", "b.pdf", "c.pdf"],
  "vector_output": true,
  "journal": "nature"
}
```

**If panels are raster (PNG/JPG):** Use the vector-hybrid path. The panels will
be raster, but the frame and labels are vector. Ensure panel DPI ≥ 300.

**If you need manual control:** Import individual SVG/PDF panels into Adobe
Illustrator or Inkscape, arrange using the layout sketch from Stage 2, add
labels manually, and export as PDF.

---

## Issue: Panels are misaligned or unevenly spaced

**Symptoms:** Some panels appear larger than others, or gaps are inconsistent.

**Causes:**
1. Input images have different aspect ratios and `fit_mode='fit'` creates letterboxing.
2. Custom layout specs have overlapping or incorrect grid coordinates.
3. Canvas height was auto-estimated incorrectly.

**Solutions:**
```bash
# Use fill mode to make all panels exactly fill their slots
python compose_figure.py --panels *.png --fit-mode fill

# Specify exact canvas dimensions
python compose_figure.py --panels *.png --width-mm 183 --height-mm 120

# For custom layout, double-check layout_specs
# Ensure row/col indices don't overlap and span values are correct
```

---

## Issue: Script crashes with "No module named 'pdf2image'"

**Symptoms:** Error when trying to load PDF inputs.

**Solution:**
```bash
pip install pdf2image
# Also need poppler (system dependency)
# Ubuntu/Debian:
sudo apt-get install poppler-utils
# macOS:
brew install poppler
```

For SVG inputs:
```bash
pip install cairosvg
# Also need cairo (system dependency)
# Ubuntu/Debian:
sudo apt-get install libcairo2-dev
# macOS:
brew install cairo
```

If you cannot install these, convert PDF/SVG to PNG first:
```bash
# Using ImageMagick (if available)
convert panel_a.pdf panel_a.png

# Or use the script with PNG versions only
python compose_figure.py --panels panel_a.png panel_b.png
```

---

## Issue: Fonts look different across panels

**Symptoms:** Some panels have serif fonts, others sans-serif; sizes look inconsistent.

**Cause:** Panels were generated by different tools (e.g., R ggplot2, Python matplotlib,
GraphPad Prism) with different default fonts.

**Solutions:**
1. **Regenerate panels with consistent font settings.** This is the only perfect fix.
2. **Standardize in post-processing** (limited): The composer only adds labels;
   it cannot change fonts inside the raster images.

For panels generated by the `nature-figure` skill, they already use consistent fonts.

---

## Issue: Background standardization creates artifacts

**Symptoms:** After `--standardize-bg`, some non-background white areas are also changed,
creating colored splotches.

**Cause:** The tolerance (default 20) is too high, catching light-colored data regions.

**Solution:**
```bash
# Disable background standardization
python compose_figure.py --panels *.png --no-std-bg

# Or preprocess panels to have identical backgrounds before assembly
```

---

## Issue: "Text may be too small at print size" warning

**Symptoms:** Audit reports text readability warning.

**Cause:** The original panel was exported at high resolution but with very small font sizes,
or the panel will be shrunk significantly during assembly.

**Solution:**
```bash
# Check actual text size
python -c "
from PIL import Image
img = Image.open('panel.png')
print(f'Panel: {img.size[0]}x{img.size[1]} px')
print(f'At 300 DPI, final width = {img.size[0]/300:.1f} in')
print(f'Min readable text ≈ 8 pt = {8/72*300:.0f} px at 300 DPI')
"

# If text is too small, regenerate panel with larger fonts
# For matplotlib: plt.rcParams['font.size'] = 12
# For R ggplot2: theme(text = element_text(size = 12))
```

---

## Issue: Color inconsistency across panels

**Symptoms:** The same condition appears as different colors in different panels.

**Cause:** Panels were generated independently with different color palettes.

**Solution:**
1. Define a shared color mapping before generating any panels.
2. Use the `nature-figure` skill's PALETTE for all panels.

```python
# Shared palette (use across all panel generation scripts)
COLORS = {
    'WT': '#0F4D92',
    'KO': '#B64342',
    'Rescue': '#8BCF8B',
}
```

---

## Issue: Audit flags "Scale bar likely missing"

**Symptoms:** Dark microscopy images trigger a scale bar detection warning.

**Cause:** Cell Press and most journals require scale bars with labeled dimensions on all microscopy images. The heuristic did not find a high-contrast line segment in the bottom region.

**Solutions:**
```bash
# If the image genuinely lacks a scale bar, add one before assembly:
# Use ImageJ/FIJI or your acquisition software to burn in a scale bar
# with explicit dimensions (e.g., "50 μm").

# If the scale bar exists but was not detected (rare):
# Proceed with a manual note to verify visually.
```

**Prevention:** Always include a scale bar during image acquisition or processing.

---

## Issue: Audit flags "Low contrast ratio (< 4.5:1)"

**Symptoms:** Contrast check warns that text may fail WCAG AA accessibility standards.

**Cause:** Text or data colors are too close to the background (mid-tone grays, low-saturation pastels on white, or light grays on black).

**Solutions:**
```python
# For light backgrounds: use dark text (#000000 or #333333)
# For dark backgrounds: use white text (#FFFFFF)
# Avoid mid-tone grays (#888888, #AAAAAA) for text or critical data series
```

**Prevention:** Check contrast during panel generation, not after assembly.

---

## Issue: Audit flags "Colors indistinguishable in grayscale"

**Symptoms:** Grayscale print compatibility check warns that distinct colors may look identical when printed in black and white.

**Cause:** Colors have similar luminance (e.g., red #E15759 and green #59A14F both convert to ~gray #999999).

**Solutions:**
1. Add patterns, hatching, or different marker shapes in addition to color.
2. Add numeric labels or direct annotations.
3. Choose colors with larger luminance gaps.

```python
# Good: dark blue vs light yellow (large luminance separation)
# Bad: red vs green (similar luminance, problematic for colorblind + grayscale)
```

---

## Issue: Journal rejects figure for "text not editable"

**Symptoms:** Journal production team requests editable text in figure.

**Cause:** The output is a raster image (PNG/TIFF) where text is baked into pixels.

**Solution:**
```bash
# Always generate SVG/PDF alongside raster outputs
python compose_figure.py --panels *.png --vector-output

# The SVG contains the panel labels as actual <text> elements
# (panel images inside are still raster, but labels are editable)

# For fully editable figures, assemble in Illustrator using SVG frame + individual SVG panels
```

---

## Quick diagnostic flowchart

```
Problem
  |
  ├── File too large
  │   └── Reduce DPI or resize inputs, use PNG over TIFF
  |
  ├── Labels blurry
  │   └── Specify --font-path, install system fonts
  |
  ├── Transparent → black
  │   └── Fixed in current script; if persists, pre-composite onto white
  |
  ├── Dark panels with white borders
  │   └── Use --dark-mode auto or --fit-mode fill
  |
  ├── Vector output blurry images
  │   └── Expected (raster-in-vector); use Illustrator for pure vector
  |
  ├── Missing dependencies (pdf2image, cairosvg)
  │   └── Install with pip + system packages, or pre-convert to PNG
  |
  ├── Fonts inconsistent across panels
  │   └── Regenerate panels with unified font settings
  |
  ├── Text too small
  │   └── Regenerate panels with larger font sizes (≥ 8 pt at intended size)
  │
  ├── Scale bar missing
  │   └── Add labeled scale bar before assembly (Cell Press requirement)
  │
  ├── Low contrast
  │   └── Use darker text on light backgrounds; avoid mid-tone grays
  │
  └── Colors indistinguishable in grayscale
      └── Add patterns, hatching, or numeric labels alongside color
```
