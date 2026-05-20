# Figure Compositor Workflow Guide

Complete guide for assembling publication-ready multi-panel figures.

## When to use this tool

- You have **existing image files** (PNG, PDF, SVG, TIFF, JPG) to combine into one figure
- You need to add **panel labels (a, b, c)** to existing plots
- You need **consistent spacing, alignment, or sizing** across imported plots
- You have **microscopy/fluorescence images** that need dark-mode figure plates
- Post-data-analysis figure assembly: analysis scripts already generated individual plots

## When NOT to use this tool

- You want to **create plots from raw data** — use `nature-figure`, matplotlib, ggplot2, etc. instead
- You only have one panel and want to style/export it
- Your primary workflow is vector illustration (Illustrator, Inkscape, Figma)

## Workflow overview

The assembly pipeline has 5 stages. Do not skip stages.

```
Stage 1: Collect inputs    → file paths, panel roles, target journal
Stage 2: Plan layout       → choose archetype, arrange panels, assign sizes
Stage 3: Audit consistency → check fonts, colors, backgrounds, DPI, text readability
Stage 4: Compose           → assemble, label, and export
Stage 5: QA & deliver      → final checklist, export formats, notes
```

---

## Stage 1: Collect inputs

### Required information

1. **File paths**: List of image files to combine
2. **Panel content**: Brief description of what each panel shows
3. **Target journal**: Nature, Cell, Science, PNAS, EMBO, eLife, IEEE, or "other"
4. **Figure purpose**: One-sentence claim this figure supports
5. **Hero panel** (if any): Which panel carries the primary evidence?

### Probing questions (ask yourself)

- What journal are you targeting?
- Which panel carries the main finding?
- Are these all the same type (all bar charts), or mixed?
- Any microscopy or fluorescence images? (affects dark mode)
- Were any AI tools used to generate or modify panels? (Nature/Cell Press disclosure required)

Do not proceed to Stage 2 until you have file paths, target journal, and panel descriptions.

---

## Stage 2: Plan layout

### Select journal spec

Read [`journal-specs.md`](journal-specs.md) for exact specifications.

Key parameters:

| Parameter | Nature | Cell | Science | PNAS | EMBO | eLife | IEEE |
|-----------|--------|------|---------|------|------|-------|------|
| Panel labels | a, b, c | a, b, c | **A, B, C** | a, b, c | a, b, c | a, b, c | **(a), (b)** |
| Label size | 8 pt bold | 8 pt bold | 10 pt bold | 8 pt bold | 10 pt bold | 8 pt bold | 8 pt bold |
| Full width | 183 mm | 174 mm | 174 mm | 178 mm | 180 mm | 180 mm | 252 mm* |
| Font | Arial | Arial, Avenir | Helvetica | Arial | Arial | sans-serif | **Times** |

\* IEEE 252 mm exceeds A4; script clamps to 180 mm with warning.

### Select layout archetype

| Archetype | Use when | Layout pattern |
|-----------|----------|----------------|
| **Grid** | 4–9 panels of similar type | Regular rows × columns |
| **Hero + support** | 1 dominant panel + 2–6 smaller | Hero spans 45–60% area |
| **Row narrative** | Sequential story, left→right | 1 row per story stage |
| **Column groups** | Related measurements side by side | Columns share x-axis logic |
| **Mixed-modality** | Plots + images + schematics | Group by modality; separate dark/light |

Read [`layout-patterns.md`](layout-patterns.md) for detailed rules, sizing formulas, and examples.

### A4 canvas constraint

All figures are assembled on an A4 canvas:
- Max figure width: **180 mm**
- Max figure height: **267 mm**
- Practical height: **≤ 200 mm** (reserve space for legend)

### Content-aware sizing (CRITICAL)

When a panel with extreme aspect ratio is forced into a uniform grid, text shrinks proportionally. A 3000×400 image with 20 px text fitted into a 1000×750 cell becomes 1000×133 — text is only 6.7 px tall (≈ 2.5 pt), unreadable.

**Solution:** Enable `--smart-layout` to auto-assign extra grid space:

```bash
python -m figure_compositor.compose_figure --panels *.png --smart-layout --journal nature
```

The script reads each panel's original dimensions, estimates text height, and auto-adjusts the grid. Panels are classified as: ✅ OK / 🔧 ALLOCATE / ⚠️ MARGINAL / ❌ REGENERATE.

Read [`content-aware-sizing.md`](content-aware-sizing.md) for the full algorithm.

---

## Stage 3: Consistency audit

Run the audit before composing:

```bash
compose-figure --panels *.png --audit-only --journal nature
```

### Critical checks (must pass)

| Check | Method | Action if fail |
|-------|--------|----------------|
| **Resolution** | PIL `Image.info` or pixel-width estimate | Flag low-DPI files |
| **Background color** | Sample corner pixels | Flag mismatched backgrounds |
| **Aspect ratio** | width / height | Flag extremes; may need cropping |
| **File readability** | PIL open attempt | Stop if corrupted |

### Important checks (should pass)

| Check | Method | Action if fail |
|-------|--------|----------------|
| **Text readability** | Edge-density heuristic | Warn if text too small |
| **JPG compression** | 8×8 block variance | Warn if heavy artifacts |
| **Brightness / dark mode** | Average grayscale | Suggest dark mode |
| **Scale bar detection** | Bottom-region edge analysis | Cell Press requires scale bars |
| **Contrast ratio** | Darkest vs lightest regions | WCAG AA ≥ 4.5:1 |
| **Grayscale compatibility** | k-means luminance separation | Add patterns if colors merge |
| **Image metadata** | EXIF/IPTC extraction | Document acquisition params |

Read [`consistency-audit.md`](consistency-audit.md) for the full checklist.

---

## Stage 4: Compose

### Command-line examples

```bash
# Basic 2×2 grid for Nature
compose-figure \
    --panels heatmap.png bars.png scatter.png trend.png \
    --grid 2 2 \
    --journal nature \
    --output ./figures/figure_2

# Hero + support layout
compose-figure \
    --panels heatmap.png bars.png scatter.png trend.png quant.png \
    --layout hero-top \
    --hero-index 0 \
    --hero-ratio 0.55 \
    --journal nature

# Custom layout via JSON config
compose-figure --config figure_2_config.json

# Dark microscopy images
compose-figure \
    --panels ch1.tif ch2.tif merged.tif bars.png \
    --grid 2 2 \
    --dark-mode auto \
    --fit-mode fill

# Smart layout for mixed aspect ratios
compose-figure --panels wide.png bars.png scatter.png --smart-layout --journal nature
```

### JSON config format

```json
{
  "panels": ["a.png", "b.png", "c.png"],
  "labels": ["a", "b", "c"],
  "layout": "grid",
  "grid": [2, 2],
  "journal": "nature",
  "output": "./figures/figure_2",
  "dark_mode": "auto",
  "fit_mode": "fit",
  "vector_output": true
}
```

### Panel label placement rules

- Font: Arial (Helvetica for Science, Times for IEEE), bold
- Size: 8 pt for Nature/Cell/eLife, 10 pt for Science/EMBO
- Position: Upper-left corner, **inside** panel bounds
- Offset: 2–3 mm from top and left edges
- Color: black on light, **white** on dark backgrounds
- Science: **UPPERCASE** (A, B, C); IEEE: **parenthesized lowercase** ((a), (b), (c))

### Fit mode selection

| Mode | Use when | Result |
|------|----------|--------|
| **fit** (default) | Aspect ratios vary | Image centered, background visible |
| **fill** | Avoid letterboxing | Image fills panel, edges may clip |
| **original** | Already sized correctly | No resize, centered |
| **stretch** | — | **Never use** |

Default: **fit** for plots and mixed content; **fill** for microscopy images.

---

## Stage 5: QA & deliver

### Final checklist

- [ ] All panels present and in correct order (a, b, c, ...)
- [ ] Panel labels match journal convention (lowercase / uppercase / parenthesized)
- [ ] Labels inside panel bounds, visible (white on dark, black on light)
- [ ] Inter-panel spacing equal in both directions
- [ ] All text readable at final print size (no pixelation)
- [ ] Background colors consistent across panels (or intentionally different)
- [ ] Figure width ≤ 180 mm, height ≤ 267 mm; ≤ 200 mm preferred
- [ ] Output files in requested formats (PNG/TIFF + SVG/PDF)
- [ ] File size reasonable (< 20 MB per file)
- [ ] Colorblind safety check passed
- [ ] **AI disclosure** documented if applicable
- [ ] **Source data** referenced in figure legend for quantitative panels
- [ ] **Image integrity** documented: linear adjustments only, no selective enhancement
- [ ] Scale bars present on all microscopy images
- [ ] Contrast ratio ≥ 4.5:1; colors distinguishable in grayscale print

### Export formats

| Format | Purpose | DPI |
|--------|---------|-----|
| **SVG** | Primary editable vector | N/A |
| **PDF** | Vector for print / submission | N/A |
| **PNG** | Preview / quick sharing | 300 |
| **TIFF** | Journal submission (LZW compressed) | 300–600 |

**Note:** SVG/PDF output has a **vector frame with raster-embedded images**. Panel labels, frame boundaries, and annotations are editable vector; plot content remains raster. This is standard practice.

For **fully editable vector** figures, assemble in Adobe Illustrator or Inkscape using individual SVG panels.

---

## Troubleshooting

Read [`troubleshooting.md`](troubleshooting.md) for solutions to:
- Output files too large
- Labels blurry or pixelated
- Transparent backgrounds turning black
- Dark microscopy panels with white borders
- Vector output with blurry embedded images
- Missing dependencies (pdf2image, cairosvg)
- Fonts inconsistent across panels
- Text too small at print size
- Color inconsistency across panels
- Scale bar missing on microscopy images
- Low contrast ratio (< 4.5:1)
- Colors indistinguishable in grayscale print
- Journal rejecting for "text not editable"

---

## Related files

| File | Open when |
|------|-----------|
| [`journal-specs.md`](journal-specs.md) | Need exact dimensions, fonts, labels, or format requirements |
| [`layout-patterns.md`](layout-patterns.md) | Need layout archetype examples or grid calculations |
| [`consistency-audit.md`](consistency-audit.md) | Running Stage 3 audit; need the full checklist |
| [`assembly-guide.md`](assembly-guide.md) | Writing custom Python composition code |
| [`troubleshooting.md`](troubleshooting.md) | Something went wrong during composition or export |
| [`content-aware-sizing.md`](content-aware-sizing.md) | Panel text too small after scaling; need smart layout |
