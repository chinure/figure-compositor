# Layout Patterns for Multi-Panel Figure Assembly

Reusable layout archetypes and grid calculation formulas for assembling
panels into publication-ready figures.

Read this file when planning Stage 2 (layout selection) of the figure-compositor workflow.

---

## Archetype 1: Regular Grid

### When to use
- 4, 6, 8, or 9 panels of similar type and importance.
- All panels are roughly the same aspect ratio.
- No single panel dominates the narrative.

### Layout formulas

| Panel count | Rows | Columns | Common use |
|-------------|------|---------|-----------|
| 2 | 1 | 2 | Side-by-side comparison |
| 3 | 1 | 3 | Equal comparison trio |
| 4 | 2 | 2 | Standard 2×2 grid |
| 5 | 2 | 3 | (with one empty cell) |
| 6 | 2 | 3 | 2×3 grid |
| 8 | 2 | 4 | Wide comparison |
| 9 | 3 | 3 | Dense grid |

### Grid calculation (Python PIL)

```python
def compute_grid_layout(n_panels, canvas_w, canvas_h, margin, gap):
    """
    Compute panel positions for a regular grid.
    Returns list of (x, y, w, h) tuples.
    """
    cols = int(np.ceil(np.sqrt(n_panels)))
    rows = int(np.ceil(n_panels / cols))

    # Adjust for common patterns
    if n_panels == 3:
        cols, rows = 3, 1
    elif n_panels == 5:
        cols, rows = 3, 2
    elif n_panels == 6:
        cols, rows = 3, 2
    elif n_panels == 8:
        cols, rows = 4, 2

    usable_w = canvas_w - 2 * margin - (cols - 1) * gap
    usable_h = canvas_h - 2 * margin - (rows - 1) * gap
    panel_w = usable_w // cols
    panel_h = usable_h // rows

    positions = []
    for i in range(n_panels):
        row = i // cols
        col = i % cols
        x = margin + col * (panel_w + gap)
        y = margin + row * (panel_h + gap)
        positions.append((x, y, panel_w, panel_h))

    return positions
```

### Example: 2×3 grid for 6 bar charts

```
┌──────────┬──────────┬──────────┐
│    a     │    b     │    c     │
│  bar_1   │  bar_2   │  bar_3   │
├──────────┼──────────┼──────────┤
│    d     │    e     │    f     │
│  bar_4   │  bar_5   │  bar_6   │
└──────────┴──────────┴──────────┘
```

---

## Archetype 2: Hero + Support

### When to use
- One panel carries the primary evidence (heatmap, main comparison, key image).
- 2–6 smaller panels provide validation, detail, or related metrics.
- Common in Nature-style figures.

### Layout variants

**Variant A: Hero top, support row below**
```
┌──────────────────────────────┐
│                              │
│           a (hero)           │
│        100% × 55%            │
├────────────┬─────────────────┤
│     b      │        c        │
│   45%      │       50%       │
└────────────┴─────────────────┘
```
- Hero: 55–60% of total height
- Support: equal-width panels in remaining space

**Variant B: Hero left, support stack right**
```
┌──────────────────┬───────────┐
│                  │     b     │
│                  ├───────────┤
│      a (hero)    │     c     │
│       60%        ├───────────┤
│                  │     d     │
│                  ├───────────┤
│                  │     e     │
└──────────────────┴───────────┘
```
- Hero: 55–65% of total width
- Support: stacked vertically on the right

**Variant C: Hero center, support surrounding**
```
┌──────────┬──────────┬──────────┐
│    a     │          │    b     │
├──────────┤    c     ├──────────┤
│    d     │  (hero)  │    e     │
├──────────┤          ├──────────┤
│    f     │          │    g     │
└──────────┴──────────┴──────────┘
```
- Hero: center panel, spans multiple grid cells
- Support: surrounding panels

### Hero sizing rules
- Hero should occupy **45–60%** of total area.
- Never make hero less than 40% — it should clearly dominate.
- Never make hero more than 70% — support panels need enough space to be legible.
- Hero-to-support gap: 3–5 mm (slightly larger than inter-support gap).

---

## Archetype 3: Row Narrative

### When to use
- Sequential story told left-to-right.
- Each row represents a stage, condition, or timepoint.
- Common for method comparisons, time series, or dose-response.

### Layout

```
┌─────────┬─────────┬─────────┬─────────┐
│    a    │    b    │    c    │    d    │
│ stage 1 │ stage 2 │ stage 3 │ stage 4 │
├─────────┼─────────┼─────────┼─────────┤
│    e    │    f    │    g    │    h    │
│ metric1 │ metric2 │ metric3 │ metric4 │
└─────────┴─────────┴─────────┴─────────┘
```

### Rules
- All panels in a row share the same height.
- Columns are semantically parallel (same measurement across conditions).
- Consider adding a shared x-axis label strip below each row.
- Add a shared legend strip above the top row if legends repeat.

---

## Archetype 4: Column Groups

### When to use
- Related measurements grouped by condition/outcome.
- Each column is a different condition; each row is a different readout.
- Common for clinical figures, multi-omics, or multi-condition experiments.

### Layout

```
┌───────────────┬───────────────┬───────────────┐
│       a       │       b       │       c       │
│  condition 1  │  condition 2  │  condition 3  │
├───────────────┼───────────────┼───────────────┤
│       d       │       e       │       f       │
│  readout 1    │  readout 1    │  readout 1    │
├───────────────┼───────────────┼───────────────┤
│       g       │       h       │       i       │
│  readout 2    │  readout 2    │  readout 2    │
└───────────────┴───────────────┴───────────────┘
```

### Rules
- Columns should have equal width unless conditions have unequal importance.
- Row heights can vary based on readout complexity.
- Add column headers (small text above each column) if the top row does not clearly identify conditions.
- Keep consistent y-axis scales within each row.

---

## Archetype 5: Mixed-Modality Composite

### When to use
- Combines plots, microscopy images, schematics, and/or photographs.
- Different modalities need different handling (dark vs light backgrounds).
- Common for materials science, neuroscience, and systems biology figures.

### Layout strategy

```
┌─────────────────────────────────────┐
│                                     │
│         a (schematic, hero)         │
│                                     │
├───────────────┬─────────────────────┤
│      b        │                     │
│  (dark image  │    c (plot)         │
│   plate)      │                     │
├───────────────┼─────────────────────┤
│      d        │    e (plot)         │
│  (dark image  │                     │
│   plate)      │    f (plot)         │
├───────────────┴─────────────────────┤
│         g (quantification bar)      │
└─────────────────────────────────────┘
```

### Rules
- Group dark panels together; group light panels together.
- Increase gutter width (4–6 mm) where dark and light panels touch.
- Do not place dark image panels on the same row as light plots unless separated by adequate space.
- Keep schematics at the top (they establish visual vocabulary).
- Quantification panels go at the bottom.

---

## Panel count recommendations

All figures must fit on an A4 page (max height 267 mm). The figure legend
usually sits below the figure, so aim for ≤ 200 mm height in practice.

| Panels | Recommended archetype | Notes |
|--------|----------------------|-------|
| 2 | Grid (1×2) or Hero+Support | Side-by-side is simplest |
| 3 | Grid (1×3) or Hero+Support (variant B) | Hero + 2 support is very common |
| 4 | Grid (2×2) | Most common layout |
| 5 | Hero+Support or Grid (2×3 with gap) | Avoid awkward gaps |
| 6 | Grid (2×3) or Hero+Support (hero + 5) | 2×3 is standard |
| 7–8 | Hero+Support or Column Groups | Consider splitting into two figures |
| 9+ | Consider splitting | Unless all panels are tiny and equal |

**A4 height reminder:** A 3-row grid at ~70 mm per row = 210 mm total.
Adding margins + legend = ~250 mm. This is the practical limit.
If your layout exceeds this, split into two figures or use the
content-aware sizing (`--smart-layout`) to compress row heights.

---

## Aspect ratio preservation

When placing images into panel slots, decide on a fitting strategy:

| Strategy | Use when | Visual result |
|----------|----------|--------------|
| **Fit** (preserve AR, letterbox) | Aspect ratios vary significantly | Image centered, background visible |
| **Fill** (preserve AR, crop) | Aspect ratios vary, content is safe to crop | Image fills panel, edges may be clipped |
| **Stretch** (distort AR) | Never recommended for publication | Distorted axes, circles become ellipses |
| **Manual resize** | User wants specific dimensions | Full control, user responsibility |

**Default recommendation: Fit with white background.**
This is the safest choice for publication figures.

```python
def fit_image(img, target_w, target_h, bg_color=(255, 255, 255)):
    """Resize image to fit within target while preserving aspect ratio."""
    img_ratio = img.width / img.height
    target_ratio = target_w / target_h

    if img_ratio > target_ratio:
        new_w = target_w
        new_h = int(target_w / img_ratio)
    else:
        new_h = target_h
        new_w = int(target_h * img_ratio)

    resized = img.resize((new_w, new_h), Image.LANCZOS)

    # Create background canvas
    canvas = Image.new('RGB', (target_w, target_h), bg_color)
    paste_x = (target_w - new_w) // 2
    paste_y = (target_h - new_h) // 2
    canvas.paste(resized, (paste_x, paste_y))

    return canvas
```

---

## Handling extreme aspect ratios (content-aware sizing)

**The core problem:** A raster image (PNG/JPG) contains text that is baked
into pixels. When the image is resized to fit a panel, **the text shrinks by
the exact same factor** as the entire image. This is mathematically unavoidable.

### Example

| Scenario | Original | Target panel | Scale factor | Text after fit |
|----------|----------|-------------|-------------|----------------|
| Normal bar chart | 1200×900, text 24 px | 1000×750 | 0.83× | 20 px ✅ |
| Wide timeline | 3000×400, text 20 px | 1000×750 | 0.33× | 6.7 px ❌ |
| Tall gel image | 600×2400, text 16 px | 1000×750 | 0.31× | 5.0 px ❌ |

At 300 DPI, 6.7 px text ≈ 2.5 pt — far below the 5–7 pt minimum for journal
figures. The figure will be rejected by production editors.

### Why this happens

```
Original panel:                    After fit into uniform grid cell:
┌─────────────────────────────┐    ┌──────────────┐
│  A very wide bar chart with │    │  tiny chart  │
│  readable axis labels and   │ →  │  w/ unread-  │
│  tick marks at 20 px height │    │  able text   │
│  (3000 × 400 pixels)        │    │ (1000 × 133) │
└─────────────────────────────┘    └──────────────┘
```

### Solutions (in order of preference)

#### 1. Content-aware layout allocation (recommended first step)

Give the wide/tall panel more grid space so the scaling factor is larger:

```
Standard grid (problem):           Smart layout (fixed):
┌──────────┬──────────┐           ┌──────────────────────┬──────┐
│          │          │           │                      │      │
│  tiny A  │    B     │     →     │        A (wide)      │  B   │
│  unread- │  (OK)    │           │      readable text   │(OK)  │
│  able    │          │           │                      │      │
├──────────┼──────────┤           ├──────────────────────┼──────┤
│    C     │    D     │           │    C      │     D    │  E   │
│  (OK)    │  (OK)    │           │  (OK)     │   (OK)   │(OK)  │
└──────────┴──────────┘           └──────────────────────┴──────┘
```

Use `--smart-layout` in the script:
```bash
python compose_figure.py --panels wide.png bars.png scatter.png --smart-layout
```

The script will:
- Detect panel A is 3000×400 (AR = 7.5)
- Compute that fitting into 1×1 cell scales text to 6.7 px
- Automatically assign `colspan=3` to panel A
- Reorganize remaining panels into the remaining grid cells

#### 2. Regenerate from source data (best quality)

If smart layout still produces unreadable text (flagged as ❌ REGENERATE),
the only fix is to regenerate the panel at the correct size.

**Wrong approach (produces the problem):**
```python
# Saved as 3000×400 to "fit more data"
plt.figure(figsize=(30, 4))
plt.bar(...)
plt.savefig('panel_a.png', dpi=100)  # 3000×400 px
```

**Correct approach:**
```python
# Match the final panel size: ~180 mm wide at 300 DPI ≈ 2126 px
# For a 2-column figure, each panel ~1000 px wide
# So export at the correct size with readable fonts
plt.figure(figsize=(6.7, 2.5))  # inches
plt.rcParams['font.size'] = 10  # pt
plt.bar(...)
plt.savefig('panel_a.png', dpi=300)  # 2000×750 px
```

Or use the `nature-figure` skill to regenerate with correct dimensions.

#### 3. Crop to essential region

If the wide panel has large empty margins or redundant content:

```python
from PIL import Image
img = Image.open('wide_panel.png')
# Crop to remove 30% empty space on each side
w, h = img.size
left = int(w * 0.15)
right = int(w * 0.85)
cropped = img.crop((left, 0, right, h))
cropped.save('panel_a_cropped.png')
```

Then assemble with the cropped version. **Document all crops** in the
figure legend or methods.

#### 4. Split into multiple panels

A very wide timeline or sequence can be split:

```
Before (one unreadable panel):     After (two readable panels):
┌────────────────────────────────┐  ┌───────────────┬───────────────┐
│ Full timeline, tiny text       │  │ a (days 0–7)  │ b (days 8–14) │
│                                │  │ readable      │ readable      │
│                                │  └───────────────┴───────────────┘
└────────────────────────────────┘
```

Use a break symbol or gradient fade between panels a and b to indicate
continuity.

### Decision flowchart

```
Panel has extreme aspect ratio?
    │
    ├── Yes → Enable --smart-layout?
    │         │
    │         ├── Yes → Script auto-assigns colspan/rowspan
    │         │         │
    │         │         ├── Text still unreadable? (❌ REGENERATE)
    │         │         │   └── Must regenerate from source data
    │         │         │       with correct figsize + font size
    │         │         │
    │         │         └── Text readable (✅ OK or 🔧 ALLOCATE)
    │         │             └── Proceed with adjusted layout
    │         │
    │         └── No → Proceed with fixed grid (risk unreadable text)
    │
    └── No → Standard grid is fine
```

### Auto-detection thresholds

The bundled script uses these heuristics:

| Aspect ratio | Action | Rationale |
|-------------|--------|-----------|
| 0.5 – 2.0 | Normal 1×1 cell | Standard proportions |
| 2.0 – 4.0 | colspan = 2 | Wide panel needs double width |
| > 4.0 | colspan = 3 (max) | Very wide; consider splitting |
| < 0.5 | rowspan = 2 | Tall panel needs double height |

Minimum readable text threshold: **18 px** at final panel size
(≈ 5 pt at 300 DPI, conservative for journal standards).

Read `references/content-aware-sizing.md` for the full algorithm.
