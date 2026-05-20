# Journal-Specific Figure Specifications

Technical specifications for assembling multi-panel figures for major journals.
Always verify against the journal's latest author guidelines before submission.

---

## A4 Canvas Constraint

**All composite figures in this skill are assembled on an A4 canvas (210 × 297 mm).**
This reflects the physical reality of journal page layouts — every figure must fit
within the printable area of a standard page.

### A4 dimensions

| Parameter | Value |
|-----------|-------|
| A4 width | 210 mm |
| A4 height | 297 mm |
| Typical print margins | 15 mm each side |
| **Safe figure width** | **≤ 180 mm** |
| **Safe figure height** | **≤ 267 mm** |

### Why A4 matters

Most journals specify figure widths that are designed to fit within a standard
A4 page with margins:

| Journal | Full width | Fits A4? |
|---------|-----------|----------|
| Nature | 183 mm | ✅ Yes (tight but fits) |
| Cell | 174 mm | ✅ Yes |
| Science | 174 mm | ✅ Yes |
| PNAS | 178 mm | ✅ Yes |
| EMBO | 180 mm | ✅ Yes |
| eLife | 180 mm | ✅ Yes |
| **IEEE** | **252 mm** | ❌ **Exceeds A4 width** |

**IEEE exception:** IEEE Transactions specify 252 mm (double column), which exceeds
A4 printable width. For IEEE figures, the compositor clamps to 180 mm (A4-safe)
and prints a warning. If true IEEE width is required, use the journal's native
template or override with `--width-mm 252` at your own risk.

### Enforcement

The compositor script automatically enforces A4 limits:
- Widths > 180 mm are clamped to 180 mm with a warning.
- Heights > 267 mm are clamped to 267 mm with a warning.
- Figure legends must also fit on the page below the figure.

**Recommendation:** Design figures to fit within a single A4 page, including space
for the figure legend (typically 40–80 mm of vertical space).

---

## Nature (and Nature-family journals)

### Source
- [Nature Figure Guide](https://www.nature.com/nature/for-authors/final-submission)
- [Nature Research Figure Guide](https://research-figure-guide.nature.com/)

### Dimensions

| Width type | Size | Use case |
|-----------|------|----------|
| Single column | 89 mm (3.5 in) | Simple plots, 1–2 panels |
| 1.5 column | 120–136 mm (4.7–5.4 in) | Medium complexity |
| Double column (full width) | 183 mm (7.2 in) | Multi-panel composite figures |
| Maximum height | 170–247 mm | Must fit on one page with legend |

### Typography

| Element | Specification |
|---------|--------------|
| Font family | Arial, Helvetica, or equivalent sans-serif |
| General text | 5–7 pt |
| Panel labels (a, b, c) | **8 pt bold**, lowercase |
| Line weight minimum | 0.25 pt |
| Text must be | Editable (do not outline) |

### Panel labels
- Lowercase bold letters: **a, b, c, d, e, f, g, h**
- Position: upper-left corner of each panel
- Reading order: left-to-right, top-to-bottom
- Alphabetical order required

### Resolution & formats

| Content type | Resolution | Preferred format |
|-------------|-----------|-----------------|
| Line art (graphs) | 1000+ DPI | Vector: PDF, EPS, SVG |
| Halftone/photos | 300 DPI min | TIFF with LZW |
| Combination | 600 DPI min | PDF preferred |

### Color
- RGB for online submission
- Colorblind accessibility **required**
- Avoid red-green combinations without additional encoding (pattern, shape, label)

### Figure limits
- **Nature** (main Article): 6 figures + tables combined
- **Nature Communications**: 10 figures + tables combined
- **Extended Data**: up to 10 (online only, peer-reviewed)

### Practical panel limit
- No strict maximum, but editors push back on figures that are unreadable at print size.
- **Recommendation: keep under 8 panels per figure.**

---

## Cell Press (Cell, Molecular Cell, Cell Reports, etc.)

### Source
- [Cell Press Figure Guidelines](https://www.cell.com/information-for-authors/figure-guidelines)

### Dimensions

| Width type | Size |
|-----------|------|
| 1 column | 8.5 cm |
| 1.5 columns | 11.4 cm |
| Full width (2 columns) | 17.4 cm |
| Maximum figure size | Must fit on one page; recommend ≤ 16.5 × 20 cm |
| File size limit | 20 MB per figure file |

### Typography

| Element | Specification |
|---------|--------------|
| Font family | **Arial, Avenir** |
| Text size | **6–8 pt** at final print size |
| Panel labels | **Lowercase a, b, c, d** — NOT uppercase |
| Line weights | 0.5–1.5 pt range |
| Font embedding | Required (or convert to outlines) |

### Panel labels
- Lowercase bold letters
- Position: upper-left corner

### Resolution & formats

| Content type | Min DPI | Preferred format |
|-------------|---------|-----------------|
| Color/grayscale | 300 | TIFF or PDF |
| Black and white | 500 | TIFF or PDF |
| Line art | 1000 | EPS or PDF |

### Critical requirements
- Each figure file must include **ALL panels** — do not send as separate files.
- Figure titles/legends must **NOT** be part of the image.
- Flatten to one layer before saving (except Leading Edge figures in *Cell*).
- Encode color as **RGB**; do not use CMYK, Spot, Pantone, or Hex.
- Gray fills must differ by at least 20%.

---

## Science (AAAS journals)

### Source
- [Science Instructions](https://www.science.org/content/page/instructions-preparing-initial-manuscript)

### Display limits

| Article type | Max figures + tables |
|-------------|---------------------|
| Report | 4 combined |
| Research Article | 5 combined |

### Dimensions

| Width type | Size |
|-----------|------|
| Single column | 8.5 cm |
| Two-column (full width) | 17.5 cm |

### Typography

| Element | Specification |
|---------|--------------|
| Font family | Helvetica, Arial, or Symbol |
| Text size | **6–8 pt** minimum |
| Panel labels | **UPPERCASE A, B, C, D** — bold, 10 pt |
| Line weights | Minimum 0.5 pt |

### Panel labels
- UPPERCASE bold letters: **A, B, C, D**
- Position: upper-left corner when possible
- For image panels, place labels **inside** the perimeter to save space.
- **No subpart labels** if avoidable (avoid A, B, C(a), C(b)).
- If subparts unavoidable: use lowercase (a, b, c), prime symbols, or Roman numerals.
- Use **numbers (1, 2, 3)** ONLY for time sequences of images.

### Resolution & formats

| Content type | Min DPI | Preferred format |
|-------------|---------|-----------------|
| Photos | 300 | EPS, PDF, TIFF |
| Line art | 1200 | EPS, PDF |
| File size limit | 15 MB per figure |

### Image integrity
- Linear adjustments (contrast, brightness, color) must apply to **entire image equally**.
- Nonlinear adjustments must be specified in figure caption.
- Selective enhancement of one part is **NOT acceptable**.
- When combining images, indicate borders with lines or spaces.

---

## PNAS (Proceedings of the National Academy of Sciences)

### Dimensions

| Width type | Size |
|-----------|------|
| Single column | 8.7 cm |
| Full width | 17.8 cm |
| Maximum figures | 6 for Research Articles |

### Typography

| Element | Specification |
|---------|--------------|
| Font family | Arial |
| Panel labels | **Lowercase a, b, c** — bold, 8 pt |
| General text | 6–8 pt |

### Resolution
- Photos: 300 DPI minimum
- Line art: 600 DPI minimum
- Preferred format: TIFF or PDF

### Notes
- Figures should be provided as **separate files** (not embedded in manuscript).
- Color figures incur charges unless essential to the science.
- Use consistent sizing across all figure panels.

---

## EMBO Journal / EMBO Molecular Medicine

### Dimensions

| Width type | Size |
|-----------|------|
| Single column | 8.8 cm |
| Full width | 18.0 cm |
| Maximum height | ~22 cm |

### Typography

| Element | Specification |
|---------|--------------|
| Font family | Arial |
| Panel labels | **Lowercase a, b, c** — bold, 10 pt |
| General text | 6–8 pt |

### Resolution
- Photos: 300 DPI minimum
- Line art: 600 DPI minimum
- Preferred format: TIFF or EPS

### Notes
- Figures can be up to **9 panels** in EMBO Journal.
- All figures uploaded as **separate files**.
- Multipanel figures should have consistent panel sizes and spacing.

---

## eLife

### Dimensions

| Width type | Size |
|-----------|------|
| Full width | 18.0 cm |
| Single column | ~8.8 cm |

### Typography

| Element | Specification |
|---------|--------------|
| Font family | sans-serif (Arial / Helvetica preferred) |
| Panel labels | **Lowercase a, b, c** — bold, 8 pt |
| General text | 6–8 pt |

### Resolution
- Photos: 300 DPI minimum
- Line art: 600 DPI minimum
- Preferred format: TIFF

### Notes
- Open-access journal with permissive figure policies.
- Figures can be color at no extra charge.
- Source data encouraged for all quantitative panels.

---

## IEEE Transactions

### Dimensions

| Width type | Size |
|-----------|------|
| Single column | 8.8 cm |
| Double column (full width) | 25.2 cm |

### Typography

| Element | Specification |
|---------|--------------|
| Font family | **Times** (serif required) |
| Panel labels | **(a), (b), (c)** — bold, 8 pt |
| General text | 8–10 pt |

### Resolution
- Photos: 300 DPI minimum
- Line art: 600 DPI minimum
- Preferred format: EPS or PDF

### Notes
- Engineering/CS field; figures often include block diagrams and algorithms.
- Panel labels use **parenthesized lowercase**: (a), (b), (c).
- Serif fonts (Times) preferred over sans-serif.
- Color is free in IEEE Xplore digital library.

---

## Other journals (general defaults)

If the target journal is not listed above, use these conservative defaults:

| Parameter | Default value |
|-----------|--------------|
| Full width | 180 mm |
| Single column | 90 mm |
| Panel labels | lowercase a, b, c, 8 pt bold |
| Font | Arial |
| Body text | 6–8 pt |
| Min line weight | 0.5 pt |
| Min DPI (photos) | 300 |
| Min DPI (line art) | 600 |
| Preferred format | PDF + TIFF |
| Color mode | RGB |

---

## Quick reference comparison table

| Parameter | Nature | Cell | Science | PNAS | EMBO | eLife | IEEE |
|-----------|--------|------|---------|------|------|-------|------|
| Full width | 183 mm | 174 mm | 174 mm | 178 mm | 180 mm | 180 mm | **252 mm** |
| Single col | 89 mm | 85 mm | 85 mm | 87 mm | 88 mm | 88 mm | 88 mm |
| Panel labels | a, b, c | a, b, c | **A, B, C** | a, b, c | a, b, c | a, b, c | **(a), (b)** |
| Label size | 8 pt bold | 8 pt bold | 10 pt bold | 8 pt bold | 10 pt bold | 8 pt bold | 8 pt bold |
| Font | Arial | **Arial, Avenir** | Helvetica/Arial | Arial | Arial | sans-serif | **Times** |
| Body text | 5–7 pt | 6–8 pt | 6–8 pt | 6–8 pt | 6–8 pt | 6–8 pt | 8–10 pt |
| Min DPI photo | 300 | 300 | 300 | 300 | 300 | 300 | 300 |
| Min DPI line art | 1000 | 1000 | 1200 | 600 | 600 | 600 | 600 |
| **Fits A4?** | **✅** | **✅** | **✅** | **✅** | **✅** | **✅** | **❌ Clamped** |
| Max file size | — | 20 MB | 15 MB | — | — | — | — |
| Color mode | RGB | RGB | RGB | RGB | RGB | RGB | RGB |
| Max figures (Article) | 6 | varies | 5 | 6 | varies | varies | varies |
