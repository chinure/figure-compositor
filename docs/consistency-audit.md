# Consistency Audit Checklist

Run this audit before assembling panels. Flag any issues and decide with the user
whether to fix, proceed with warnings, or exclude the panel.

Read this file during Stage 3 of the figure-compositor workflow.

---

## Automated checks (via compose_figure.py --audit-only)

The bundled script runs these checks automatically. Use `--audit-only` to inspect
panels without composing.

### Check 1: File existence & readability

Verifies each panel file exists and can be opened by PIL.

**Status:**
- ❌ CRITICAL if file missing or unreadable

### Check 2: DPI / resolution

Extracts embedded DPI from image metadata. Falls back to estimating DPI based on
pixel width assuming single-column width (89 mm ≈ 3.5 in).

| Status | DPI range | Action |
|--------|-----------|--------|
| ✅ OK | ≥ 300 (photos) or ≥ 600 (line art) | Proceed |
| ⚠️ WARNING | 150–299 | Flag for user attention |
| ❌ CRITICAL | < 150 | Stop; ask user to regenerate |

**Why this matters:** A 600×400 image at 300 DPI covers only 2 × 1.3 inches. At
Nature's full width of 7.2 inches, it would stretch to ~120 DPI and look pixelated.

### Check 3: Background color consistency

Samples the top-left 20×20 pixel corner of each panel and computes average RGB.

**Threshold:** If any two panels differ by > 15 per RGB channel, flag mismatch.

**Common issue:** #FFFFFF vs #F5F5F5 vs #FAFAFA creates visible seams.

**Fix:** The composer can standardize backgrounds automatically (enabled by default
for light mode; disabled for dark mode).

### Check 4: Aspect ratio

Computes width/height ratio and flags extremes.

| Status | Ratio range |
|--------|-------------|
| ✅ OK | 0.28 – 3.5 |
| ⚠️ WARNING | < 0.28 or > 3.5 |

Extreme ratios may indicate accidental cropping or need layout adjustment.

### Check 5: Image brightness / dark mode detection

Estimates average grayscale brightness (0–255). Used to auto-suggest dark mode.

| Brightness | Interpretation |
|------------|----------------|
| > 180 | Light background (typical plots) |
| 80–180 | Mixed / moderate |
| < 80 | Dark background (typical microscopy) |

If ≥ 50% of panels are dark (< 80), the script suggests enabling dark mode.

### Check 6: Text readability

Roughly estimates whether text in the image will be readable at final print size.

**Method:** Resize image to 400 px width, compute vertical edge density. Infer
minimum text stroke height. If estimated height < 3 px at the original scale
(equivalent to < 5 pt at 300 DPI), flag as potentially unreadable.

**Status:** ⚠️ WARNING if text may be too small.

**Fix:** Regenerate the panel with larger font sizes (≥ 16 px for axis labels).

### Check 7: JPG compression artifacts

For JPEG inputs, detects heavy block compression by analyzing 8×8 DCT block variance.

**Status:** ⚠️ WARNING if block variance is very low (indicates aggressive compression).

**Fix:** Re-export from source as PNG or TIFF with lossless compression.

### Check 8: Scale bar detection (NEW — Cell Press requirement)

Cell Press mandates: **"You must include a scale bar on all microscopy images."**

**Method:** The script analyzes the bottom region of dark/brightness < 100 images
for high-contrast horizontal or vertical line segments that match the typical
appearance of a scale bar (30–200 px long, strong edges).

| Status | Condition |
|--------|-----------|
| ✅ Detected | High-contrast line found in bottom region |
| ⚠️ Likely missing | Dark image, no scale-like edges detected |
| ℹ️ Not checked | Bright image (not microscopy-like) |

**Fix:** Add a scale bar with labeled dimensions (e.g., "50 μm") directly on
the image. White bars on dark backgrounds; black bars on light backgrounds.

### Check 9: Contrast ratio (NEW — accessibility)

All major journals now require colorblind-accessible figures with sufficient contrast.

**Method:** Computes the contrast ratio between the darkest and lightest regions.
WCAG AA standard requires ≥ 4.5:1 for text.

| Status | Ratio | Action |
|--------|-------|--------|
| ✅ OK | ≥ 4.5 | Proceed |
| ⚠️ WARNING | < 4.5 | Increase text/background contrast |

**Fix:** Use darker text on light backgrounds or lighter text on dark backgrounds.
Avoid mid-tone grays for text.

### Check 10: Grayscale distinguishability (NEW — print compatibility)

Figures must remain interpretable when printed in black and white.

**Method:** Extracts dominant colors via k-means, converts to grayscale luminance,
and checks if the minimum separation between any two colors is > 25 (out of 255).

| Status | Min separation | Action |
|--------|----------------|--------|
| ✅ OK | > 25 | Proceed |
| ⚠️ WARNING | ≤ 25 | Add patterns, labels, or hatching to distinguish series |

**Fix:** For heatmaps with red-green encoding, add hatch patterns or numeric labels.
For multi-series plots, use different marker shapes (circles, squares, triangles)
in addition to colors.

### Check 11: Image metadata (NEW — QUAREP-LiMi compliance)

Microscopy images should contain EXIF/IPTC metadata documenting acquisition parameters.

**Method:** Reads image metadata. If no metadata found on dark images
(brightness < 100), flags as INFO.

**Recommended metadata (Methods section):**
- Microscope make/model
- Objective lens (e.g., "63×/1.4 NA oil immersion")
- Excitation/emission wavelengths
- Camera/detector
- Acquisition software
- Image processing software and adjustments

---

## Manual checks (visual inspection)

These require human judgment. The script presents prompts to guide the user.

### Font consistency

Verify:
- [ ] All panels use the same font family.
- [ ] Axis label sizes are consistent across panels.
- [ ] Tick label sizes are consistent.
- [ ] Panel text is readable at expected print size.

**Quick rule:** Text should be ≥ 20 pixels tall in the source image at its
intended display width. At 300 DPI, 89 mm width ≈ 1050 pixels. If your panel is
exported at 800 px wide, text should be ≥ 15 px tall.

### Color palette consistency

Check across panels:
- [ ] The same experimental condition uses the same color in all panels.
- [ ] Colorblind-unsafe combinations (red-green) are not the sole encoding.
- [ ] Overall palette feels cohesive (not a random rainbow).

### Axis and spine style

Verify:
- [ ] All panels use the same spine style (top/right on or off).
- [ ] Axis line weights are consistent.
- [ ] Grid lines are either present everywhere or absent everywhere.
- [ ] Tick mark directions and lengths match.

### Legend strategy

Decide before assembly:
- [ ] Does each panel have its own legend? → Risk: legends may conflict or overlap.
- [ ] Should legends be consolidated into one shared legend panel?
- [ ] Can legends be replaced with direct labels?

**Recommendation:** For multi-panel figures, prefer one shared legend strip or
direct labels over per-panel legends.

---

## AI Disclosure Check (NEW — 2024-2025 policy)

Both Nature and Cell Press now require disclosure of AI tool usage in figures.

### Nature policy
- **Mandatory disclosure** in Methods section if AI tools used for any figure
- AI **authorship prohibited**
- **Experimental images** (microscopy, gels, histology): AI generation prohibited
- **Illustrative figures** (pathways, schematics): Permitted with disclosure

### Cell Press policy (stricter)
- **Mandatory disclosure** in dedicated AI declaration section (before References)
- AI-generated images in **data figures: PROHIBITED**
- **Illustrative/schematic figures**: Permitted with prior editorial approval + disclosure
- **Graphical abstracts**: Must use traditional tools (BioRender, Illustrator, PowerPoint)

### Disclosure checklist

Before submission, verify:
- [ ] **No AI tools** used for experimental data panels (microscopy, gels, blots, etc.).
- [ ] If AI used for **schematics/illustrations**: Disclosed in Methods.
- [ ] For Cell Press: Editor pre-approval obtained for AI-generated content.
- [ ] **AI authorship:** Not listed as author or co-author.
- [ ] Tool name, version, and purpose documented.

---

## Image Integrity Checklist (NEW — before assembly)

Document these in your Methods section or figure legend:

- [ ] All image adjustments are **linear** and applied to the **entire image equally**.
- [ ] No selective enhancement of specific regions.
- [ ] Cropping does not change image meaning or omit important context.
- [ ] Insets/magnifications maintain original pixel resolution (no interpolation).
- [ ] All image processing software documented (name, version).
- [ ] For microscopy: microscope model, objective, acquisition parameters stated.
- [ ] For gels/blots: molecular weight markers indicated; uncropped images available.

---

## Audit report format

The script produces a compact table:

```
===========================================================================
 Figure Consistency Audit Report
===========================================================================
  Target: NATURE
  Min DPI: 300 (photos)
---------------------------------------------------------------------------
 File                   Size         DPI     BG       Status
---------------------------------------------------------------------------
 heatmap.png            1200x900     300     #FFFFFF  OK
 bars.png               600x400      150     #FFFFFF  ⚠ Low DPI 150
 scatter.png            800x600      300     #F5F5F5  ⚠ BG mismatch
 trend.png              900x500      300     #FFFFFF  OK
 image.jpg              2400x1800    300     #FAFAFA  ⚠ BG mismatch
---------------------------------------------------------------------------

 ⚠  Background colors vary by 10 across panels. Standardize recommended.
 ℹ  1 panel appears dark (brightness < 80). Consider dark_mode='true'.
 ⚠  1 panel(s) lack detected scale bars. Cell Press requires scale bars on all microscopy images.
 ⚠  1 panel(s) have low contrast ratio (< 4.5:1). May fail accessibility standards.
 ⚠  1 panel(s) have colors that may be indistinguishable in grayscale print.
===========================================================================
```

---

## Decision tree for flagged issues

```
Issue found
    │
    ├── CRITICAL (file missing, unreadable, DPI < 150)
    │   └── STOP: prompt user to regenerate or exclude
    │       Interactive: ask y/n to proceed
    │       Non-interactive: print warning, continue with note
    │
    ├── WARNING (DPI 150–299, BG mismatch, text too small, no scale bar,
    │            low contrast, grayscale issue)
    │   └── Proceed with warning in output report
    │       Note risk in delivery notes to user
    │
    └── INFO (dark mode suggestion, color palette note, missing metadata)
        └── Note in report; user decides
```

---

## Command-line audit

```bash
# Audit all PNG files in results directory
python scripts/compose_figure.py --panels results/*.png --audit-only

# Audit with specific journal thresholds
python scripts/compose_figure.py --panels a.png b.png --journal science --audit-only

# Audit with smart layout analysis
python scripts/compose_figure.py --panels *.png --smart-layout --audit-only
```
