---
name: figure-compositor
description: >-
  Assemble individual plots and images into publication-ready multi-panel figures for top-tier journals.
  Use whenever the user has multiple existing charts, plots, microscopy images, or diagrams that need
  to be combined into a single composite figure (e.g., "combine these plots into Fig. 2", "assemble
  my panels for Nature", "put these images together for a paper figure", multi-panel figure layout,
  figure assembly, or journal figure composition). Handles layout planning, journal-specific formatting
  (Nature, Cell, Science, PNAS, EMBO, eLife, IEEE, and others), consistency auditing, panel labeling,
  dark image plate support, and final export in raster and vector formats. Complements but does not
  replace the nature-figure skill — use nature-figure to CREATE individual plots from data, and
  figure-compositor to ASSEMBLE existing plots into multi-panel figures.
---

# Figure Compositor

A workflow for assembling existing plots, images, and diagrams into publication-ready
multi-panel figures. This skill handles the entire pipeline from scattered individual
files to a journal-compliant composite figure.

## When to use this skill

- The user has **existing image files** (PNG, PDF, SVG, TIFF, JPG) they want to combine into one figure.
- The user asks to "assemble", "combine", "merge", "layout", or "compose" multiple panels.
- The user is preparing figures for **Nature, Cell, Science, or similar high-impact journals**.
- The user wants to add **panel labels (a, b, c)** to existing plots.
- The user needs **consistent spacing, alignment, or sizing** across multiple imported plots.
- The user has **microscopy/fluorescence images** that need dark-mode figure plates.
- Post-data-analysis figure assembly: the analysis scripts have already generated individual plots.

## When NOT to use this skill

- The user wants to **create plots from raw data** — use the `nature-figure` skill instead.
- The user only has one panel and wants to style/export it — use `nature-figure` instead.
- The primary workflow is vector illustration (Illustrator, Inkscape, Figma) — this skill uses Python code.
- The user wants interactive/web-based figures.

## Workflow overview

The assembly pipeline has 6 stages. Do not skip stages. **Stage 6 is critical for production quality.**

```
Stage 1: Collect inputs    → file paths, panel roles, target journal
Stage 2: Plan layout       → choose archetype, arrange panels, assign sizes
Stage 3: Audit consistency → check fonts, colors, backgrounds, DPI, text readability
Stage 4: Compose           → Python code to assemble, label, and export
Stage 5: QA & deliver      → final checklist, export formats, notes
Stage 6: Iterative review  → evaluate all outputs, identify issues, refine, repeat
```

**Why Stage 6 matters:** Raster outputs (PNG/TIFF via PIL) and vector outputs (SVG/PDF via matplotlib)
use different rendering engines with different font handling. Labels that look perfect in SVG may be
unreadable in PNG. Layouts that work at design time may break at final resolution. A single pass is
never sufficient for publication-quality figures. Expect 2–5 review cycles.

---

## Synergy with nature-figure

These two skills are designed to work together in a research pipeline:

```
Raw data ──► nature-figure ──► individual panels (a.svg, b.svg, c.svg)
                                   │
                                   ▼
                          figure-compositor ──► composite figure (Fig.2.svg)
                                   │
                                   ▼
                          QA + export ──► PNG/TIFF/SVG/PDF
```

- **`nature-figure`** handles data → plot creation (bars, trends, heatmaps, scatters).
- **`figure-compositor`** handles plot collection → publication figure assembly.

When a user needs both, run `nature-figure` first for any panels that don't exist yet,
then `figure-compositor` to assemble everything.

---

## Stage 1: Collect inputs

### Required information (ask if missing)

1. **File paths**: List of image files to combine. Accept any common format: PNG, JPG, TIFF, PDF, SVG.
2. **Panel content**: Brief description of what each panel shows. This determines layout priority.
3. **Target journal**: Nature, Cell, Science, PNAS, EMBO, eLife, IEEE, or "other".
4. **Figure purpose**: One-sentence claim this figure supports. E.g., "Fig. 2 demonstrates that
   treatment X reduces Y by restoring Z."
5. **Hero panel** (if any): Which panel carries the primary evidence? If none, all panels are equal.

### Optional information

- Preferred output dimensions (if known; otherwise use journal defaults).
- Any panels that should share axes, legends, or color scales.
- Whether the figure contains mixed modalities (plots + microscopy + schematics).
- Whether dark-mode image plates are present (auto-detected if not specified).

### Probing questions

If the user says "combine these plots" without context, ask:
- "What journal are you targeting?"
- "Which panel carries the main finding?"
- "Are these all the same type (e.g., all bar charts), or mixed?"
- "Any microscopy or fluorescence images?" (this affects dark mode)
- "Were any AI tools used to generate or modify any panels?" (Nature/Cell Press now require disclosure; AI use on experimental images is prohibited by Cell Press)

Do not proceed to Stage 2 until you have file paths, target journal, and panel descriptions.

---

## Stage 2: Plan layout

### Select journal spec

Read `references/journal-specs.md` for the exact specifications of the target journal.

Key parameters to extract:

| Parameter | Nature | Cell | Science | PNAS | EMBO | eLife | IEEE |
|-----------|--------|------|---------|------|------|-------|------|
| Panel labels | a, b, c | a, b, c | **A, B, C** | a, b, c | a, b, c | a, b, c | **(a), (b)** |
| Label size | 8 pt bold | 8 pt bold | 10 pt bold | 8 pt bold | 10 pt bold | 8 pt bold | 8 pt bold |
| Full width | 183 mm | 174 mm | 174 mm | 178 mm | 180 mm | 180 mm | 252 mm |
| Font | Arial | Arial | Helvetica | Arial | Arial | sans-serif | **Times** |
| Min DPI photo | 300 | 300 | 300 | 300 | 300 | 300 | 300 |

### Select layout archetype

Based on panel count, types, and the hero panel, choose an archetype:

| Archetype | Use when | Layout pattern |
|-----------|----------|----------------|
| **Grid** | 4–9 panels of similar type | Regular rows × columns |
| **Hero + support** | 1 dominant panel + 2–6 smaller ones | Hero spans 45–60% area, support fills remainder |
| **Row narrative** | Sequential story, left→right | 1 row per story stage; equal height, variable width |
| **Column groups** | Related measurements side by side | Columns share x-axis logic; rows share y-axis logic |
| **Mixed-modality** | Plots + images + schematics | Group by modality; separate dark/light regions |

Read `references/layout-patterns.md` for detailed rules, sizing formulas, and examples
for each archetype.

### A4 canvas constraint

All composite figures are assembled on an **A4 canvas (210 × 297 mm)**.
This is the physical page size used by virtually all journals.

| Limit | Value | Notes |
|-------|-------|-------|
| Max figure width | 180 mm | A4 width (210 mm) minus 15 mm margins each side |
| Max figure height | 267 mm | A4 height (297 mm) minus 15 mm margins each side |
| Practical height | ≤ 200 mm | Reserve space for figure legend below |

The compositor script automatically enforces these limits. If a journal spec
(e.g., IEEE at 252 mm) exceeds A4 width, the script clamps to 180 mm and warns.

### Compute panel dimensions

1. Start from the journal's full-width dimension (clamped to A4 max 180 mm).
2. Subtract gutters (inter-panel spacing = 2–4 mm).
3. Allocate hero panel first if applicable.

### Automatic grid detection (NEW)

When using `layout='grid'` without manually specifying `--grid`, the script now
**automatically infers the optimal row × column count** based on the actual
content dimensions of each panel:

1. **Trim whitespace** from each panel to isolate the true content region
   (removes empty borders, figure titles, or excess padding).
2. **Measure trimmed aspect ratios** — e.g. a wide bar chart (AR ≈ 3.0) needs
   more width per panel than a tall heatmap (AR ≈ 0.5).
3. **Score every plausible column count** (1 to 4) and pick the one that
   minimises the total "wasted" letterbox area after fitting.

This means you no longer need to guess whether 6 panels should be 2×3 or 3×2.
The script makes the decision for you based on the actual shapes of your images.

```bash
# No --grid needed — auto-detected from trimmed content proportions
compose-figure --panels panel_a.png panel_b.png panel_c.png panel_d.png \
    --journal nature

# Override with explicit grid if you prefer
compose-figure --panels *.png --grid 2 3 --journal nature
```

The auto-detection also integrates with `--smart-layout`: if some panels are
extremely wide or tall, the script assigns them `colspan > 1` or `rowspan > 1`
and recalculates the grid accordingly.
4. Distribute remaining space among support panels.
5. Ensure no panel is smaller than 30 mm in any dimension.
6. Ensure total figure height does not exceed A4 safe height (267 mm).

### Content-aware sizing (CRITICAL for readability)

**The problem:** When a panel with an extreme aspect ratio (e.g., very wide
but short) is forced into a uniform grid cell, it must be shrunk to fit. Because
the panel is a raster image (PNG/JPG), the text inside shrinks **by the same
factor**. A panel that started at 3000×500 px with 20 px tall text, when fitted
into a 1000×750 px grid cell, scales to 1000×167 px — the text becomes only
6.7 px tall (≈ 2.5 pt at 300 DPI), unreadable.

**This is physically unavoidable for raster images.** Resize uniformly scales
all content. The only way to keep text large is to give the panel more space
so the scaling factor is smaller.

**The solution — Content-Aware Panel Sizing:**

Before locking the layout, analyze each panel's original dimensions and
automatically adjust the grid to protect text readability:

| Panel type | Aspect ratio | Auto-adjustment |
|-----------|-------------|-----------------|
| Normal | 0.5 – 2.0 | Standard 1×1 grid cell |
| Wide | 2.0 – 4.0 | colspan=2 (double width) |
| Very wide | > 4.0 | colspan=3 (triple width) |
| Tall | < 0.5 | rowspan=2 (double height) |

**How to use:**

```bash
# Enable smart layout — script analyzes proportions and auto-adjusts
python compose_figure.py --panels *.png --smart-layout --journal nature

# Or in JSON config
{
  "panels": ["a.png", "b.png", "c.png"],
  "layout": "grid",
  "smart_layout": true,
  "journal": "nature"
}
```

**What the script does:**
1. Reads each panel's original pixel dimensions.
2. Estimates text height using edge-density analysis.
3. Computes the scaling factor if placed in a uniform grid.
4. If scaled text would be < 18 px (≈ 5 pt at 300 DPI), flags the panel.
5. Automatically assigns colspan > 1 or rowspan > 1 to give more space.
6. Recalculates figure height to accommodate taller rows.
7. Prints a report showing each panel's status:
   - ✅ OK — text remains readable
   - 🔧 ALLOCATE — extra space assigned
   - ⚠️ MARGINAL — may be acceptable; verify visually
   - ❌ REGENERATE — text will be unreadable even with extra space

**When REGENERATE is flagged:**
The panel's original resolution or font size is too low. No amount of layout
trickery can fix this. The only solution is to return to the plotting code
and regenerate the panel with:
- Larger figure size (e.g., `figsize=(10, 3)` instead of `(20, 2)` for wide plots)
- Larger font size (e.g., `plt.rcParams['font.size'] = 12`)
- Or use the `nature-figure` skill to re-export at the correct dimensions

Read `references/content-aware-sizing.md` for the full algorithm and examples.

### Layout planning output

Present the user with a text-based layout sketch before writing code. Example:

```
┌──────────────────────────────┬──────────────┐
│                              │              │
│           a                  │      b       │
│    (heatmap, hero)           │   (bar)      │
│         55% width            │   40% width  │
│         60% height           │              │
├──────────────┬───────────────┼──────────────┤
│      c       │       d       │      e       │
│   (scatter)  │   (scatter)   │   (trend)    │
│   30% width  │   30% width   │   35% width  │
│   35% height │   35% height  │   35% height │
└──────────────┴───────────────┴──────────────┘
```

Wait for user confirmation of the layout before proceeding to Stage 3.

---

## Stage 3: Consistency audit

Before combining panels, audit each input file for consistency.

Run the bundled audit via the script:
```bash
python scripts/compose_figure.py --panels *.png --audit-only
```

Read `references/consistency-audit.md` for the detailed checklist.

### Critical checks (must pass)

| Check | Method | Action if fail |
|-------|--------|----------------|
| **Resolution** | PIL `Image.info` or pixel-width estimate | Flag low-DPI files; warn user |
| **Background color** | Sample corner pixels | Flag panels with different backgrounds |
| **Aspect ratio** | width / height | Flag extreme ratios; may need cropping |
| **File readability** | PIL open attempt | Stop if corrupted or missing |

### Important checks (should pass)

| Check | Method | Action if fail |
|-------|--------|----------------|
| **Text readability** | Edge-density heuristic | Warn if text may be too small at print size |
| **JPG compression** | 8×8 block variance | Warn if heavy artifacts detected |
| **Brightness / dark mode** | Average grayscale | Suggest dark mode for dark panels |
| **Color palette** | Extract dominant colors | Warn if palettes differ wildly |
| **Axis style** | Visual inspection (manual) | Note in report; user decides |
| **Legend presence** | Visual inspection | Suggest shared legend strategy |

If critical issues exist, pause and ask the user whether to:
- Regenerate the problematic panel at higher quality.
- Proceed anyway (note risks in output).
- Exclude the panel.

---

## Stage 4: Compose

### Composition method selection

Choose the right tool for the job:

```
All inputs are raster (PNG/JPG/TIFF)?
    └── Yes → Use the bundled script (PIL method)
              Produces PNG + TIFF output
              Simplest and most reliable

All inputs are PDF/SVG (vector plots from matplotlib/R)?
    └── Yes → Use the bundled script with --vector-output
              Produces native vector PDF (panels embedded as vector objects)
              Panel text/lines remain fully editable in Illustrator
              See "Native vector PDF workflow" below

Need vector output (SVG/PDF) but inputs are raster?
    └── Yes → Use the bundled script with --vector-output
              Produces SVG + PDF (raster images + vector frame)
              Frame and labels are vector; panel images remain raster

Need shared axes, unified legends, or matplotlib-native annotations?
    └── Yes → Use matplotlib gridspec directly
              See references/assembly-guide.md Method B

Mixed dark/light panels (microscopy + plots)?
    └── Yes → Use bundled script with --dark-mode auto
              Auto-detects and handles each panel appropriately
```

### Using the bundled script

The script `scripts/compose_figure.py` is the recommended production tool.

**Command-line examples:**

```bash
# Basic 2×2 grid for Nature
python compose_figure.py \
    --panels heatmap.png bars.png scatter.png trend.png \
    --grid 2 2 \
    --journal nature \
    --output ./figures/figure_2

# Hero + support layout
python compose_figure.py \
    --panels heatmap.png bars.png scatter.png trend.png quant.png \
    --layout hero-top \
    --hero-index 0 \
    --hero-ratio 0.55 \
    --journal nature

# Custom layout via JSON config
python compose_figure.py --config figure_2_config.json

# Dark microscopy images
python compose_figure.py \
    --panels ch1.tif ch2.tif merged.tif bars.png \
    --grid 2 2 \
    --dark-mode auto \
    --fit-mode fill

# No vector output (faster)
python compose_figure.py --panels *.png --no-vector

# Smart label avoidance (auto-detects overlap with heatmap titles, colorbars)
python compose_figure.py --panels *.png --grid 2 2 --journal nature --label-avoidance auto

# Strict avoidance for very dense figures
python compose_figure.py --panels heatmap.png bars.png --label-avoidance strict
```

**JSON config format:**
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

See `scripts/config_example_*.json` for complete examples covering grid, hero,
custom layout, and dark-mode scenarios.

### Panel label placement rules

- Font: Arial (or Helvetica for Science, Times for IEEE), bold.
- Size: 8 pt for Nature/Cell/eLife, 10 pt for Science/EMBO.
- Position: Upper-left corner, **inside** the panel area (not outside).
- Offset: 2–3 mm from top edge, 2–3 mm from left edge.
- Color: black for light backgrounds, **white** for dark backgrounds.
- For Science: **UPPERCASE** labels (A, B, C, D).
- For IEEE: **parenthesized lowercase** ((a), (b), (c)).
- **Smart avoidance** (`--label-avoidance auto`): scans the panel's top-left region for
  dense content (heatmap titles, colorbar labels, plot annotations). If overlap is
  detected, the label shifts right or moves to top-right. Prevents labels from
  obscuring critical content. Recommended for heatmaps, tables, and dense multi-panel
  figures.

### Spacing rules

- **Inter-panel gap**: 2–4 mm (tighter for dense figures, wider for mixed modalities).
- **Outer margin**: 3–5 mm from canvas edge.
- **Hero-to-support gap**: 3–5 mm (slightly larger to create visual hierarchy).
- **Dark-to-light boundary**: 4–6 mm (wider when dark image plates touch light plots).

### Fit mode selection

When placing images into panel slots, choose a fitting strategy:

| Mode | Use when | Visual result |
|------|----------|--------------|
| **fit** (default) | Aspect ratios vary | Image centered, background visible (letterbox) |
| **fill** | Need to avoid letterboxing | Image fills panel, edges may be cropped |
| **original** | User already sized correctly | No resize, original dimensions centered |
| **stretch** | — | **Never use for publication** |

Default recommendation: **fit** for plots and mixed content; **fill** for
microscopy images where the full frame should be used.

### Native vector PDF workflow (PDF input → editable PDF output)

When all panels are **PDF or SVG** (vector plots generated by matplotlib, R ggplot2,
etc.), the script can produce a **fully editable vector composite PDF** where every
panel retains its original vector content (text, lines, curves).

**How it works:**
1. Panel generation scripts save each plot as PDF with Type 42 (TrueType) fonts.
2. The compositor reads the PDF inputs directly via pymupdf.
3. Each panel page is embedded into the composite page as a native PDF object
   (`show_pdf_page`), not rasterized.
4. Panel labels (a, b, c...) are added as vector text with the same Arial font.

**Critical requirement — font registration in matplotlib:**

If Arial is installed in a non-system directory (e.g. `~/.local/share/fonts/`),
matplotlib's font manager will **not** find it automatically. You must register
it explicitly **before** importing `pyplot`:

```python
import matplotlib.font_manager as fm
fm.fontManager.addfont('/home/user/.local/share/fonts/arial/arial.ttf')
fm.fontManager.addfont('/home/user/.local/share/fonts/arial/arialbd.ttf')

import matplotlib.pyplot as plt  # import AFTER registration
plt.rcParams.update({
    'font.family': 'sans-serif',
    'font.sans-serif': ['Arial', 'DejaVu Sans'],
    'pdf.fonttype': 42,   # TrueType embedding (editable in Illustrator)
    'ps.fonttype': 42,
})
```

**Why `pdf.fonttype=42` alone is not enough:**
Setting `pdf.fonttype=42` tells matplotlib to embed TrueType fonts, but if the
font manager doesn't know Arial exists, it silently falls back to DejaVu Sans.
The resulting PDF uses Type 0 DejaVu fonts — still editable, but not Arial.
Register the font first, then set the font preference.

**Verifying the output:**

```bash
# Check that composite PDF contains Arial fonts
python -c "
import fitz
doc = fitz.open('Figure_1.pdf')
fonts = doc[0].get_fonts(full=True)
for f in fonts:
    if 'Arial' in f[3]:
        print(f[3], f[2])  # name, embedding type
"
# Expected: ArialMT / Arial-BoldMT with Type0
```

**If panels are raster (PNG/JPG):** The script falls back to matplotlib
`imshow()`, producing a hybrid PDF with raster panels + vector frame. The
panels themselves cannot be edited as vectors.

### Colorblind safety

If panels contain color-coded data, verify:
- No red-green encoding without additional pattern/label.
- The `nature-figure` skill's PALETTE was used consistently across all panels.
- Consider adding a colorblind-safe check note in the output.

---

## Stage 5: QA & deliver

### Final checklist

Before declaring the figure complete, verify:

- [ ] All panels are present and in correct order (a, b, c, ...).
- [ ] Panel labels match journal convention (lowercase vs uppercase vs parenthesized).
- [ ] Labels are inside panel bounds, not floating outside.
- [ ] Labels are visible (white on dark, black on light).
- [ ] Inter-panel spacing is equal in horizontal and vertical directions.
- [ ] All text is readable at final print size (no pixelation).
- [ ] Background colors are consistent across panels (or intentionally different).
- [ ] Figure width ≤ 180 mm (A4-safe limit).
- [ ] Figure height ≤ 267 mm (A4-safe limit); ≤ 200 mm preferred to leave room for legend.
- [ ] Output files saved in requested formats (PNG/TIFF + SVG/PDF).
- [ ] **All 4 formats viewed** — PNG is the strictest test (raster scaling reveals all flaws).
- [ ] File size is reasonable (< 20 MB per file for most journals).
- [ ] Colorblind safety check passed.
- [ ] **AI disclosure** documented if applicable (Nature: Methods section; Cell Press: dedicated AI declaration + editor pre-approval for schematics).
- [ ] **Source data** referenced in figure legend for all quantitative panels.
- [ ] **Image integrity** documented: linear adjustments only, no selective enhancement, cropping declared, software versions noted.
- [ ] Scale bars present on all microscopy images (Cell Press requirement).
- [ ] Contrast ratio ≥ 4.5:1 for text; colors distinguishable in grayscale print.

### Export formats

| Format | Purpose | DPI |
|--------|---------|-----|
| **SVG** | Primary editable vector (frame + labels) | N/A |
| **PDF** | Vector for print / submission | N/A |
| **PNG** | Preview / quick sharing / lossless raster | 300 |
| **TIFF** | Journal submission (raster, LZW compressed) | 300–600 |

**Important:** The SVG/PDF output from the script has a **vector frame with
raster-embedded images**. The panel labels, frame boundaries, and annotations
are editable vector text; the actual plot/image content remains raster.
This is standard and accepted by most journals.

For **fully editable vector** figures (where even the plot lines are vector
curves), assemble in Adobe Illustrator or Inkscape using individual SVG panels.

### Delivery notes

Provide the user with:
1. The exported file paths for all formats.
2. A brief consistency audit summary (from Stage 3).
3. Any warnings or issues that need attention.
4. A note about what was standardized (fonts, labels, spacing, backgrounds).
5. A reminder to verify vector text editability in the SVG/PDF.

---

## Stage 6: Iterative Review & Refinement (CRITICAL)

**Do not stop after Stage 5.** The first composition is a draft. Systematic visual inspection
across all output formats always reveals issues that automated checks miss.

### The review loop

```
View all formats (PNG/SVG/PDF/TIFF) → Identify issues → Fix at source → Recompose → Repeat
```

Expect **2–5 cycles** for production figures. Keep going until no new issues are found.

### Automated pre-check

Run the review assistant before visual inspection to catch obvious problems:

```bash
# Validate config and check all outputs
python scripts/review_assistant.py --config fig1_config.json --check-all ./figures/ --journal nature

# Generate a review checklist
python scripts/review_assistant.py --generate-checklist --figures 6 --panels 9 --output-checklist review.md
```

### Why multiple formats must be checked

| Format Family | Engine | Font handling | Risk |
|--------------|--------|---------------|------|
| **PNG, TIFF** | PIL (raster) | `ImageFont.truetype()` uses **pixels** | Labels appear tiny if pt→px conversion is missing |
| **SVG, PDF** | matplotlib (vector) | Uses **points** (pt) | Labels render correctly |

**Rule:** Always view the **PNG** output first. It is the most strict.

### Visual inspection checklist

| # | Check item | What to look for | How to fix |
|---|-----------|------------------|-----------|
| 1 | **Panel labels (a–i)** | Size: clearly legible. Color: black on light, white on dark. | Adjust `label_size_pt`; ensure PIL gets px=pt×dpi/72 |
| 2 | **Label overlap** | Labels overlapping content, titles, or colorbars. | Use `--label-avoidance auto` or manual offsets |
| 3 | **Text truncation** | Axis labels or annotations cut off at edges. | Shorten text, rotate, or increase panel width |
| 4 | **Axis label compression** | Multi-word labels merged into one string. | Rotate labels or add line breaks |
| 5 | **Content density** | Panels too small (e.g., dual plots in one grid cell). | Use vertical stacking or `rowspan`/`colspan` |
| 6 | **Spacing & margins** | Unequal gaps, labels too close to edges. | Adjust `hspace`/`wspace`, trim source whitespace |
| 7 | **Color consistency** | Different palettes or backgrounds across panels. | Regenerate with unified `plt.rcParams` |
| 8 | **Content accuracy** | Wrong data, missing annotations, stale titles. | Regenerate from latest data |
| 9 | **Format-specific issues** | PNG pixelation, SVG missing fonts, PDF artifacts. | Increase DPI, embed fonts, flatten transparency |
| 10 | **Cross-panel consistency** | Different font sizes, line widths, or schemes. | Unified `plt.rcParams` across all scripts |

### Issue severity

| Severity | Examples | Action |
|----------|----------|--------|
| **🔴 Critical** | Labels unreadable, text truncated, wrong data, broken layout | Must fix before submission |
| **🟡 Medium** | Labels slightly small, minor spacing, color inconsistency | Fix if time allows |
| **🟢 Low** | Suboptimal color, legend could be tighter, extra whitespace | Nice-to-have |

### Where to fix issues

| Issue location | Fix location | Example |
|---------------|--------------|---------|
| **Panel content** | Source plotting script (`generate_fig*.py`) | Annotation overlap → adjust `adjustText` params |
| **Panel label size** | `compose_figure.py` or PIL font code | Labels too small → fix pt→px conversion |
| **Panel spacing/layout** | JSON config `layout_specs` or `gridspec_kw` | Dual plot compressed → switch to 2×1 vertical |
| **Inter-panel gaps** | Config `gap_mm` or script `GAP_MM` constant | Gaps too wide → reduce from 2.5 mm to 2 mm |

### Review discipline

1. **View all Figures every cycle.** Do not spot-check.
2. **Zoom to 100% actual size.** Thumbnails hide truncation.
3. **Check the worst-case panel.** The smallest panel sets the quality floor.
4. **Fix one issue class at a time.** Don't mix label, spacing, and color fixes.
5. **Recompose after every fix.** Source script changes require full re-run.
6. **Keep a running issue log.** Track fixes to prevent regression.

### When to stop

Stop when: no critical issues remain, ≤2 medium issues remain, user approves,
or two consecutive cycles find zero new issues.

**Full details, real-world case studies, and issue log template:** See [`references/iterative-review.md`](references/iterative-review.md).

---

## Troubleshooting

When things go wrong during composition, read `references/troubleshooting.md`
for solutions to:
- Output files too large
- Labels blurry or pixelated
- **Panel labels (a–i) too small in PNG/TIFF but correct in SVG/PDF**
- Transparent backgrounds turning black
- Dark microscopy panels with white borders
- Vector output with blurry/raster embedded images
- **PDF text not editable in Adobe Illustrator (Type 3 fonts)**
- **Composite PDF panels rasterized instead of vector**
- Missing dependencies (pdf2image, cairosvg, pymupdf)
- Fonts inconsistent across panels
- Text too small at print size
- Color inconsistency across panels
- Journal rejecting for "text not editable"

---

## Related files

| File | Open when |
|------|-----------|
| [references/journal-specs.md](references/journal-specs.md) | Need exact dimensions, fonts, labels, or format requirements for a specific journal |
| [references/layout-patterns.md](references/layout-patterns.md) | Need layout archetype examples or grid calculations for specific panel counts |
| [references/consistency-audit.md](references/consistency-audit.md) | Running Stage 3 audit; need the full checklist |
| [references/assembly-guide.md](references/assembly-guide.md) | Writing custom Python composition code; need PIL/matplotlib templates |
| [references/troubleshooting.md](references/troubleshooting.md) | Something went wrong during composition or export |
| [references/content-aware-sizing.md](references/content-aware-sizing.md) | Panel text too small after scaling; need smart layout |
| [references/iterative-review.md](references/iterative-review.md) | Running Stage 6; need review checklist, case studies, issue log template |
| [scripts/compose_figure.py](scripts/compose_figure.py) | Need a reusable composition script |
| [scripts/review_assistant.py](scripts/review_assistant.py) | Automated pre-checks before visual review; generate checklist |
| [scripts/config_example_grid.json](scripts/config_example_grid.json) | Need a grid layout JSON config example |
| [scripts/config_example_hero.json](scripts/config_example_hero.json) | Need a hero+support layout JSON config example |
| [scripts/config_example_custom.json](scripts/config_example_custom.json) | Need a custom layout JSON config example |
| [scripts/config_example_dark.json](scripts/config_example_dark.json) | Need a dark-mode microscopy JSON config example |
