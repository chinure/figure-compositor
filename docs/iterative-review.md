# Iterative Review & Refinement

This document details Stage 6 of the figure-compositor workflow: the systematic,
repeatable process of evaluating composite figures across all output formats,
identifying issues, and refining until publication quality is reached.

**Context:** The first composition is always a draft. Automated checks catch
technical problems but miss visual subtleties — label overlap at actual print size,
micro-compression artifacts, or color inconsistency that only appears when panels
are placed side by side. Manual visual inspection across multiple review cycles
is mandatory.

---

## The Review Loop

```
View all formats (PNG/SVG/PDF/TIFF) → Identify issues → Fix at source → Recompose → Repeat
```

Expect **2–5 cycles** for production figures. Complex multi-panel figures with
mixed modalities may require more. Keep going until no new issues are found.

**Why multiple passes are necessary:** Each cycle fixes a class of issues. The
first cycle usually catches obvious problems (labels too small, text truncated).
The second cycle reveals subtler issues (spacing inconsistency, color mismatch).
The third cycle catches edge cases (format-specific rendering quirks). Stopping
after one cycle guarantees missed problems.

---

## Why Multiple Formats Must Be Checked

The compositor produces two output families via different rendering engines:

| Format Family | Engine | Font handling | Risk |
|--------------|--------|---------------|------|
| **PNG, TIFF** | PIL (raster) | `ImageFont.truetype()` uses **pixels** | Labels appear tiny if pt→px conversion is missing |
| **SVG, PDF** | matplotlib (vector) | Uses **points** (pt) | Labels render correctly |

**Critical bug pattern:** PIL interprets `label_size_pt` as pixels, not points.
At 300 DPI, 15 pt should be ~62 px, but PIL renders it as 15 px — unreadable.
The fix: convert explicitly: `label_px = int(pt * dpi / 72)`.

**Rule:** Always view the **PNG** output first. It is the most strict (raster
scaling reveals all flaws). If PNG looks good, other formats usually do too.

---

## Visual Inspection Checklist

Inspect each figure systematically. Do not spot-check.

| # | Check item | What to look for | How to fix |
|---|-----------|------------------|-----------|
| 1 | **Panel labels (a–i)** | Size: must be clearly legible in the grid. Color: black on light bg, white on dark bg. | Adjust `label_size_pt` in journal defaults; ensure PIL gets px=pt×dpi/72 |
| 2 | **Label overlap** | Labels overlapping each other, panel titles, colorbars, or dense data regions. | Use `--label-avoidance auto` or manual offset adjustments |
| 3 | **Text truncation** | Axis labels, tick labels, or annotations cut off at panel edges. | Shorten text, rotate (`rotation=35, ha='right'`), or increase panel width |
| 4 | **Axis label compression** | Multi-word X/Y labels merged into one word. | Rotate labels or add explicit line breaks (`\n`) |
| 5 | **Content density** | Some panels too small (e.g., dual-panel plots squeezed into 1/9 of figure). | Change to vertical stacking (2×1 instead of 1×2), or use `rowspan`/`colspan` |
| 6 | **Spacing & margins** | Unequal gaps between panels, labels too close to edges, excessive whitespace. | Adjust `hspace`/`wspace` in `gridspec_kw`, trim whitespace from source panels |
| 7 | **Color consistency** | Panels from different scripts use different palettes or background tones. | Regenerate source panels with unified palette; use `--standardize-bg` |
| 8 | **Content accuracy** | Wrong data shown, missing annotations, outdated titles, stale statistics. | Regenerate source panel from latest data |
| 9 | **Format-specific issues** | PNG: pixelation, jagged edges. SVG: fonts not embedded. PDF: transparency artifacts. | Increase DPI for PNG; embed fonts for SVG; flatten transparency for PDF |
| 10 | **Cross-panel consistency** | Similar panels have different font sizes, line widths, or color schemes. | Regenerate all panels with unified `plt.rcParams` |

---

## Real-World Case Studies

The following cases are drawn from actual production work on multi-panel
NMR/CYBB-NOX2→KHK regulatory axis figures (6 Figures × 9 panels each,
Nature journal style). Each illustrates a common failure mode and the fix.

### Case 1: Extreme Value Skews Y-Axis Scale (Data Normalization)

**Symptom:** In a multi-gene expression trajectory panel (Fig 1i), one gene
(CYBB) had expression values ~25,000 while all others were ~10,000. The CYBB
line dominated the plot, compressing all other genes into an unreadable flat
band near the bottom.

**Root cause:** Raw expression values have vastly different dynamic ranges across
genes. Plotting on a shared linear scale is mathematically correct but visually
useless.

**Fix — Z-score normalization per gene:**

```python
# Before: raw values — CYBB dwarfs everything
ax.plot(time_points, expr_matrix[gene])  # CYBB ~25k, others ~10k

# After: z-score normalize each gene independently
from scipy.stats import zscore
expr_zscore = zscore(expr_matrix, axis=1)  # row-wise normalization
ax.plot(time_points, expr_zscore[gene])
ax.set_ylabel('Z-score (normalized)')
```

**When to apply:** Any multi-line or multi-gene trend plot where values span
more than one order of magnitude. Normalization preserves shape while enabling
comparison.

---

### Case 2: Dual-Panel Plot Compressed in Grid Cell (Layout)

**Symptom:** Fig 1g contained two scatter plots side-by-side (1×2 horizontal)
within a single 3×3 grid cell. At final figure width (~60 mm per cell), each
subplot was only ~25 mm wide — too narrow for readable axis labels and point
distributions.

**Root cause:** A 1×2 subplot arrangement inside a single grid cell halves the
already-limited width. Text, points, and margins all shrink proportionally.

**Fix — Switch to vertical stacking with increased figure size:**

```python
# Before: horizontal, too compressed
fig, axes = plt.subplots(1, 2, figsize=(5.0, 4.0), gridspec_kw={'wspace': 0.15})

# After: vertical stack with more height and breathing room
fig, axes = plt.subplots(2, 1, figsize=(5.0, 8.0), gridspec_kw={'hspace': 0.25})
```

**Additional adjustments:**
- Increase `hspace` from 0.15 to 0.25 to prevent annotation overlap
- Increase `bbox_inches` pad from 0.05 to 0.08 for edge labels
- Increase annotation font size from 8 pt to 12 pt

**General principle:** When a panel contains multiple subplots, prefer vertical
stacking (2×1) over horizontal (1×2) in a grid layout. Height is usually less
constrained than width in multi-column figures.

---

### Case 3: Volcano Plot Label Overlap (Annotation Density)

**Symptom:** In volcano plots (Fig 1a-b), gene name annotations for significant
DEGs overlapped heavily, creating an unreadable tangle of text strings.

**Root cause:** Too many genes labeled in a small space with default matplotlib
text placement (no collision avoidance).

**Fix — Use adjustText library with tuned parameters:**

```python
from adjustText import adjust_text

texts = []
for _, row in sig_genes.iterrows():
    texts.append(ax.text(row['log2FoldChange'], row['negLog10P'],
                         row['gene_name'], fontsize=7))

adjust_text(texts,
            arrowprops=dict(arrowstyle='->', color='gray', lw=0.5),
            force_text=(0.8, 1.5),      # Push labels apart horizontally/vertically
            expand_text=(1.2, 1.5),     # Expand label bounding boxes
            expand_points=(1.5, 1.5),   # Expand point bounding boxes
            lim=500)                    # Max iterations
```

**Key parameters explained:**
| Parameter | Effect | Typical range |
|-----------|--------|---------------|
| `force_text` | How strongly labels repel each other | (0.5, 1.0) to (1.5, 2.5) |
| `expand_text` | Padding added to text bounding box | (1.1, 1.3) to (1.5, 2.0) |
| `expand_points` | Padding added to point bounding box | (1.2, 1.5) to (2.0, 2.5) |

**When adjustText is not enough:** If >30 labels compete for space, consider:
1. Reduce the significance threshold (stricter p-value or log2FC cutoff)
2. Label only the top N genes by significance
3. Use a two-tier system: label top 10 directly, use a side table for the rest

---

### Case 4: PIL Font Size Unit Bug (Format-Specific)

**Symptom:** Panel labels (a, b, c...) were correctly sized in SVG/PDF outputs
but appeared microscopic (barely visible) in PNG and TIFF outputs.

**Root cause:** PIL's `ImageFont.truetype()` interprets the `size` parameter as
**pixels**, not **points**. Matplotlib correctly handles points (converting via
DPI), so SVG/PDF were fine. But when the compositor passed `label_size_pt=15`
directly to PIL, it rendered a 15-pixel font instead of a 15-point font.

At 300 DPI: 15 pt = 15/72 × 300 = 62.5 px. PIL rendered 15 px — a 4× error.

**Fix — Explicit pt-to-px conversion in the compositor:**

```python
# BUG: PIL receives points, interprets as pixels
label_font = ImageFont.truetype(font_path, size=15)  # Renders 15 px

# FIX: Convert points to pixels before passing to PIL
label_px = max(8, int(label_size_pt * dpi / 72))    # 15 pt → 62 px at 300 DPI
label_font = ImageFont.truetype(font_path, size=label_px)
```

**Universal check:** After every font-size change, verify PNG output at 100%
zoom. Do not trust SVG/PDF as the sole reference.

---

### Case 5: X-Axis Label Merging (Tick Label Layout)

**Symptom:** In a multi-pathway bar plot (Fig 5i), long pathway names like
"Inflammation", "Metabolism", "Hypoxia" were concatenated into a single
unreadable string: "InflammatiMetabolismHypoxia".

**Root cause:** Default `xticklabels` with `ha='center'` on a dense bar chart
causes adjacent labels to collide and visually merge.

**Fix — Rotate and right-align tick labels:**

```python
# Before: default center alignment — labels merge
ax.set_xticklabels(pathway_names)

# After: rotated right-alignment — labels are readable
ax.set_xticklabels(pathway_names, rotation=30, ha='right', fontsize=9)
```

**Alternative for very long labels:** Use abbreviations with a legend:

```python
abbrev_map = {
    'EXTRACELLULAR_MATRIX_ORGANIZATION': 'ECM_ORGANIZATION',
    'OXIDATIVE_PHOSPHORYLATION': 'OX_PHOSPHORYLATION',
    'FATTY_ACID_METABOLISM': 'FA_METABOLISM',
}
```

---

### Case 6: Long Y-Axis Label Truncation (Panel Boundary)

**Symptom:** In a pathway enrichment dot plot (Fig 4g), long pathway names on
the Y-axis were truncated at the left edge of the panel:
"EXTRACELLULAR_MATRIX_ORGANIZATION" became "...GANIZATION".

**Root cause:** The left margin (`left` parameter in `plt.subplots_adjust`) was
too small to accommodate the longest label at the current font size.

**Fix — Abbreviate labels AND increase margin:**

```python
# Fix 1: Abbreviate long labels
label_map = {
    'EXTRACELLULAR_MATRIX_ORGANIZATION': 'ECM_ORGANIZATION',
    'OXIDATIVE_PHOSPHORYLATION': 'OX_PHOSPHORYLATION',
    'FATTY_ACID_METABOLISM': 'FA_METABOLISM',
}
y_labels = [label_map.get(l, l) for l in raw_labels]

# Fix 2: Increase left margin
plt.subplots_adjust(left=0.28)  # Was 0.20; increase for long labels
```

---

### Case 7: Panel Title Truncation (Multi-Panel Grid)

**Symptom:** In a multi-panel grid of proteome comparisons (Fig 1c-d), panel
titles like "Proteome: Model vs Control" were truncated to "Proteome: M vs C"
at the top edge.

**Root cause:** The `top` margin in `plt.subplots_adjust` was too small, and the
title font size was too large for the allocated space.

**Fix — Shorten titles AND increase top margin:**

```python
# Fix 1: Abbreviate titles
ax.set_title('Prot: M vs C', fontsize=10)  # Was "Proteome: Model vs Control"

# Fix 2: Increase top margin
plt.subplots_adjust(top=0.92)  # Was 0.88
```

---

### Case 8: Inconsistent Color Palette Across Figures (Cross-Figure)

**Symptom:** Different figures used different blue/red shades for up/down
regulation. Fig 1 used a cool blue, Fig 3 used a purple-blue. When figures
appeared in the same manuscript, the inconsistency was jarring.

**Root cause:** Each plotting script defined its own colors independently.

**Fix — Define a unified palette at the project level:**

```python
# palette.py — imported by all figure generation scripts
PALETTE = {
    'up': '#E64B35',        # Warm red
    'down': '#4DBBD5',      # Cool blue
    'ns': '#BCBCBC',        # Not significant gray
    'highlight': '#F39B7F', # Highlight orange
    'accent1': '#00A087',   # Teal
    'accent2': '#3C5488',   # Navy
    'accent3': '#8491B4',   # Light purple
    'dark': '#7E6148',      # Brown
}
```

Apply this palette consistently across ALL figure generation scripts.

---

### Case 9: Correlation Heatmap Missing Key Annotations (Content)

**Symptom:** A gene-to-gene correlation heatmap had no annotations highlighting
the most biologically significant correlations. Viewers could not quickly identify
the key findings.

**Root cause:** The heatmap showed all correlations equally without emphasizing
the biologically relevant ones (e.g., CYBB-KHK, CYBB-NOX2).

**Fix — Add selective annotations with asterisks for significant pairs:**

```python
# Annotate top correlations
for i, g1 in enumerate(genes):
    for j, g2 in enumerate(genes):
        val = corr_matrix[i, j]
        if abs(val) > 0.7 and i != j:  # Strong correlation, not diagonal
            sig = '***' if abs(val) > 0.9 else '**' if abs(val) > 0.8 else '*'
            ax.text(j, i, sig, ha='center', va='center',
                    color='white' if abs(val) > 0.8 else 'black',
                    fontsize=8, fontweight='bold')
```

---

### Case 10: PDF Fonts Not Editable in Illustrator (Type 3 vs Type 42)

**Symptom:** Individual panel PDFs opened in Adobe Illustrator showed text as
outlines/glyphs rather than editable text. The Fonts panel showed no fonts,
only "Outlined" or "Compound Path".

**Root cause:** matplotlib defaults to **Type 3** fonts for PDF output.
Type 3 fonts are actually PostScript graphics (each glyph is a drawing),
which Illustrator cannot edit as text. Type 42 (TrueType) fonts are required
for text editability.

**Two-step fix:**

Step 1 — Register Arial with matplotlib's font manager (critical for custom font paths):

```python
import matplotlib.font_manager as fm
# BEFORE importing pyplot — register fonts in non-system directories
fm.fontManager.addfont('/home/user/.local/share/fonts/arial/arial.ttf')
fm.fontManager.addfont('/home/user/.local/share/fonts/arial/arialbd.ttf')

import matplotlib.pyplot as plt
```

Step 2 — Set font parameters:

```python
plt.rcParams.update({
    'font.family': 'sans-serif',
    'font.sans-serif': ['Arial', 'DejaVu Sans'],
    'pdf.fonttype': 42,   # TrueType embedding
    'ps.fonttype': 42,
})
```

**Why both steps are necessary:**
| Step | What it does | What happens if skipped |
|------|-------------|------------------------|
| `addfont()` | Tells matplotlib "Arial exists at this path" | Falls back to DejaVu Sans (not Arial) |
| `pdf.fonttype=42` | Embeds as TrueType (editable) | Uses Type 3 (outlined, not editable) |

**Verification:**

```python
import fitz  # pymupdf
doc = fitz.open('panel.pdf')
for f in doc[0].get_fonts(full=True):
    print(f[3], f[2])  # should show: ArialMT Type0, not Type3
```

---

### Case 11: PDF Panels Rasterized in Composite (Vector → Raster)

**Symptom:** After combining individual PDF panels into a composite Figure,
the resulting PDF was not editable in Illustrator. Panel text appeared as images,
not selectable text.

**Root cause:** The compositor script's `compose_vector()` function used
matplotlib's `ax.imshow()` to display panels. `imshow()` converts any input
(PDF, SVG, PNG) into a raster numpy array before embedding. Even though the
output is a PDF file, the panel content inside it is a raster image.

**The two rendering paths in the compositor:**

| Path | Method | Panel content | Use when |
|------|--------|--------------|----------|
| **Raster** | `compose_raster()` — PIL | PNG/TIFF | Raster inputs, preview, pixel-perfect placement |
| **Vector-hybrid** | `compose_vector()` — matplotlib | Raster (imshow) | Raster inputs needing vector frame |
| **Native vector** | `compose_pdf_native()` — pymupdf | **Vector PDF** | **PDF inputs, Illustrator editability required** |

**Fix — Use pymupdf native embedding for PDF panels:**

```python
# In the compositor: embed PDF pages as native PDF objects
def compose_pdf_native(panels, ...):
    doc = fitz.open()
    page = doc.new_page(width=W, height=H)
    for panel_path, label, (px, py, pw, ph) in ...:
        src = fitz.open(panel_path)
        target_rect = fitz.Rect(px, py, px+pw, py+ph)
        page.show_pdf_page(target_rect, src, 0)  # ← native embedding
        src.close()
        # Add vector label
        page.insert_text((label_x, label_y), label,
                         fontsize=label_size_pt,
                         fontname="ArialBold",
                         color=(0, 0, 0))
    doc.save('Figure_composite.pdf')
```

**Key difference:** `page.show_pdf_page()` places the source PDF page as a
**Form XObject** inside the destination page. All text, lines, and curves
remain vector and editable. `ax.imshow()` rasterizes everything to pixels.

**When to use which path:**
- Inputs are PNG/JPG/TIFF → `compose_raster()` + `compose_vector()` (hybrid)
- Inputs are PDF/SVG and editability matters → `compose_pdf_native()` (full vector)
- Need both raster preview and vector output → run all three paths

---

## Issue Severity Classification

| Severity | Examples | Action |
|----------|----------|--------|
| **🔴 Critical** | Labels unreadable, text truncated, wrong data, broken layout | Must fix before submission |
| **🟡 Medium** | Labels slightly small, minor spacing issues, color inconsistency | Fix if time allows |
| **🟢 Low** | Suboptimal color choice, legend could be tighter, extra whitespace | Nice-to-have |

---

## Where to Fix Issues

| Issue location | Fix location | Example |
|---------------|--------------|---------|
| **Panel content** (plots, labels, data) | Source plotting script (`generate_fig*.py`) | Gene annotation overlap → adjust `adjustText` params |
| **Panel label size/position** | `compose_figure.py` journal defaults or PIL font code | a–i labels too small → fix pt→px conversion |
| **Panel spacing/layout** | JSON config `layout_specs` or `gridspec_kw` | Dual scatter too compressed → switch to 2×1 vertical |
| **Inter-panel gaps** | Config `gap_mm` or script `GAP_MM` constant | Gaps too wide → reduce from 2.5 mm to 2 mm |

---

## Review Discipline

1. **View all Figures every cycle.** Do not spot-check. Issues cluster in unexpected places.
2. **Zoom to 100% actual size.** Small-screen thumbnails hide truncation and overlap.
3. **Check the worst-case panel.** The smallest or most densely labeled panel sets the quality floor.
4. **Fix one issue class at a time.** Don't try to fix labels, spacing, and colors simultaneously.
5. **Recompose after every fix.** A fix in the source script or config requires a full re-run.
6. **Keep a running issue log.** Track what's been fixed and what remains. Prevents regression.

### Issue Log Template

Use this template to track issues across review cycles:

```markdown
## Review Cycle N — Date

### Critical (🔴)
| Figure | Panel | Issue | Fix applied | Status |
|--------|-------|-------|-------------|--------|
| Fig 2 | b | Labels overlap | Increased adjustText force_text | ✅ Fixed |

### Medium (🟡)
| Figure | Panel | Issue | Fix applied | Status |
|--------|-------|-------|-------------|--------|
| Fig 4 | g | Y-label truncated | Abbreviated pathway names | ⏳ Pending |

### Low (🟢)
| Figure | Panel | Issue | Fix applied | Status |
|--------|-------|-------|-------------|--------|
| Fig 1 | a | Legend could be smaller | — | 📋 Backlog |
```

---

## When to Stop Iterating

Stop when ALL of the following are true:

- No critical (🔴) issues remain
- No more than 2 minor (🟡) issues remain
- The user explicitly says "good enough"
- Two consecutive review cycles find zero new issues

**Warning:** Do not chase perfection indefinitely. A figure that is "good enough"
for submission is better than one that is endlessly refined. Journal reviewers
will request changes anyway — reserve some polish for the revision.
