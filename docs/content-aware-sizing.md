# Content-Aware Panel Sizing

A deep-dive reference on why raster images lose text readability when resized,
and how the figure-compositor script automatically mitigates this.

Read this file when:
- A panel has an extreme aspect ratio (very wide or very tall).
- Text in the assembled figure appears too small.
- The script flags a panel with ❌ REGENERATE or ⚠️ MARGINAL.
- You want to understand the `--smart-layout` algorithm.

---

## The physics of the problem

A raster image (PNG, JPG, TIFF) is a grid of pixels. Text in the image is
just a pattern of colored pixels — it has no semantic meaning to the image
file. When you resize the image, every pixel is resampled uniformly.

**There is no way to resize a raster image while preserving text size.**
This is not a software limitation. It is a mathematical fact.

### Concrete example

```
Panel A: 3000 × 400 pixels, axis text is 20 px tall
Panel B: 1200 × 900 pixels, axis text is 24 px tall
Panel C: 800 × 600 pixels, axis text is 16 px tall

Figure width: Nature full width = 183 mm = 2160 px at 300 DPI
Grid: 2 columns

Each grid cell: ~1000 × 750 pixels (after margins and gaps)

Panel A fit result: scales to 1000 × 133 px
    Text height: 20 px × (1000/3000) = 6.7 px  →  ≈ 2.5 pt  ❌ UNREADABLE

Panel B fit result: scales to 1000 × 750 px
    Text height: 24 px × (1000/1200) = 20 px    →  ≈ 7.5 pt  ✅ OK

Panel C fit result: scales to 800 × 600 px (original mode) or 1000×750 fit
    Text height: 16 px × (1000/800) = 20 px      →  ≈ 7.5 pt  ✅ OK
```

At 300 DPI, the minimum readable text for journal production is **5 pt** ≈ **21 px**.
Panel A fails by a wide margin.

---

## Why this happens in practice

Researchers often generate individual plots at arbitrary sizes:

```python
# Common but problematic pattern
plt.figure(figsize=(20, 3))   # Very wide, short figure
plt.bar(range(50), data)      # 50 bars crammed horizontally
plt.xticks(rotation=45)
plt.savefig('panel_a.png', dpi=150)   # 3000 × 450 px
```

The figure was made wide to "fit all the bars." But when this 3000 px wide
image must fit into a ~1000 px panel, everything shrinks by 3×.

**The fix at generation time:**
```python
# Correct approach: size for the destination
# A 2-column Nature panel is ~90 mm ≈ 3.5 in wide
plt.figure(figsize=(3.5, 2.5))   # Match final panel size
plt.rcParams['font.size'] = 10    # Ensure readable text
plt.bar(range(50), data)
# ... reduce bar count or use grouped display if needed
plt.savefig('panel_a.png', dpi=300)   # 1050 × 750 px
```

---

## The content-aware solution

Since we cannot change the raster image's text size post-hoc, we change the
**layout** to give the problematic panel more space, reducing the scaling factor.

### Algorithm overview

```
1. For each panel:
   a. Read original pixel dimensions (W, H)
   b. Estimate text height via edge-density analysis
   c. Compute expected panel size in uniform grid
   d. Compute scaling factor = panel_size / original_size
   e. Compute scaled_text = original_text × scale_factor

2. Classify each panel:
   scaled_text ≥ 18 px     → ✅ OK
   scaled_text ≥ 10 px,
     aspect_ratio > 2.5    → 🔧 WIDE_ALLOCATE (colspan=2 or 3)
     aspect_ratio < 0.4    → 🔧 TALL_ALLOCATE (rowspan=2)
   scaled_text < 10 px     → ⚠️ MARGINAL
   scaled_text < 5 px      → ❌ REGENERATE

3. Generate layout_specs with adjusted colspan/rowspan

4. Compute minimum figure height to accommodate tall rows

5. Print report; proceed with adjusted layout or warn user
```

### Text height estimation

The script estimates text height without OCR by analyzing edge density:

```python
def estimate_min_text_height(img):
    """
    1. Convert to grayscale, downsample to 400 px width for speed.
    2. Compute vertical gradient (pixel differences along columns).
    3. Text produces strong vertical edges (horizontal strokes).
    4. Measure the density of vertical edges per column.
    5. High-density columns = text columns.
    6. Estimate character height from edge density distribution.
    7. Scale back to original image pixel dimensions.
    """
```

This is a heuristic, not exact OCR. It tends to underestimate slightly
(conservative), which is safe — better to flag a panel as marginal than
miss a readability problem.

### Layout generation

After classifying panels, the script greedily places them left-to-right,
top-to-bottom in a grid, giving wide panels extra columns:

```python
# Example: 4 panels where A is very wide
panels = ['wide.png', 'bars.png', 'scatter.png', 'trend.png']
analysis = [
    {'strategy': 'WIDE_ALLOCATE', 'colspan': 3},  # panel a
    {'strategy': 'OK', 'colspan': 1},              # panel b
    {'strategy': 'OK', 'colspan': 1},              # panel c
    {'strategy': 'OK', 'colspan': 1},              # panel d
]

# Generated layout:
# Row 0: [a (colspan=3)]
# Row 1: [b] [c] [d]
# Grid: 2 rows × 3 columns
```

Result:
```
┌─────────────────────────────────────────────────┐
│                      a                            │
│              (wide panel, readable)               │
├─────────────────┬─────────────────┬─────────────┤
│        b        │        c        │      d      │
│     (bars)      │    (scatter)    │   (trend)   │
└─────────────────┴─────────────────┴─────────────┘
```

---

## Thresholds and their rationale

| Threshold | Value | Why |
|-----------|-------|-----|
| Min readable text | 18 px | 5 pt at 300 DPI; conservative margin below journal 6-8 pt standard |
| Marginal text | 10–18 px | May be acceptable for minor labels; verify visually |
| Wide AR trigger | > 2.0 | Text width exceeds panel width by 2× |
| Very wide AR trigger | > 4.0 | Needs 3× width or split |
| Tall AR trigger | < 0.5 | Text height exceeds panel height by 2× |

---

## When smart layout is not enough

Smart layout can only redistribute space. It cannot create pixels that don't
exist. If a panel's original text is already tiny (e.g., 8 px tall in the
source image), even giving it the entire figure width won't help.

In this case, the script flags ❌ REGENERATE and advises:

```
⚠️  1 panel(s) will have unreadable text even with smart layout.
   Recommended action: regenerate from source data using larger font sizes
   (≥ 8 pt at intended print width).
```

**Regeneration checklist:**
- [ ] Increase `figsize` to match the final panel's physical dimensions
- [ ] Increase `font.size` to ≥ 8 pt (matplotlib) or `base_size` ≥ 10 (ggplot2)
- [ ] Ensure `dpi` is 300 (not the default 100)
- [ ] Re-export as PNG or SVG
- [ ] Re-run the compositor

---

## Command-line usage

```bash
# Enable smart layout for any grid layout
python compose_figure.py \
    --panels wide_timeline.png bars.png scatter.png \
    --layout grid --smart-layout \
    --journal nature --output ./figures/figure_2

# Smart layout + audit to preview before composing
python compose_figure.py \
    --panels *.png --smart-layout --audit-only

# JSON config
{
  "panels": ["wide.png", "bars.png", "scatter.png"],
  "layout": "grid",
  "smart_layout": true,
  "journal": "nature",
  "output": "./figures/figure_2"
}
```

---

## Limitations

1. **Raster only:** Smart layout cannot fix text size in already-exported
   raster images. The best it can do is reduce the scaling factor.

2. **Heuristic text detection:** Edge-density analysis can be fooled by
   images with high natural texture (e.g., microscopy, photos). For plots
   and charts it is reliable.

3. **Does not create space:** If ALL panels are wide, there's not enough
   horizontal space to give everyone colspan > 1. The script will do its
   best but may still flag panels as marginal.

4. **Single-panel limit:** Maximum colspan is 3. Panels wider than 3× the
   normal cell width should be split or regenerated.

---

## Related

- `references/layout-patterns.md` — Layout archetypes including hero+support
- `references/troubleshooting.md` — "Text too small at print size"
- `nature-figure` skill — Regenerating panels with correct dimensions
