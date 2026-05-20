# Figure Compositor

> Assemble individual plots and images into publication-ready multi-panel figures for top-tier journals.

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## Overview

Figure Compositor is a Python tool and Claude Code skill for assembling existing charts, plots, microscopy images, and diagrams into single composite figures suitable for submission to **Nature, Cell, Science, PNAS, EMBO, eLife, IEEE**, and other high-impact journals.

It handles the entire pipeline from scattered individual files to a journal-compliant composite figure:

```
Raw data ──► nature-figure ──► individual panels (a.svg, b.svg, c.svg)
                                   │
                                   ▼
                          figure-compositor ──► composite figure (Fig.2.svg)
                                   │
                                   ▼
                          QA + export ──► PNG/TIFF/SVG/PDF
```

**Complements but does not replace** data-to-plot tools. Use `nature-figure` (or matplotlib, ggplot2, etc.) to **create** individual panels, then use Figure Compositor to **assemble** them.

## Features

- **7 journal presets**: Nature, Cell, Science, PNAS, EMBO, eLife, IEEE — with correct fonts, label styles, and dimensions
- **5 layout archetypes**: Regular grid, Hero + Support, Row Narrative, Column Groups, Mixed-Modality
- **Content-aware sizing**: Automatically detects extreme aspect ratios and allocates extra grid space to protect text readability
- **A4 canvas constraint**: Enforces printable page limits (180 mm × 267 mm safe area)
- **Consistency audit**: 11 automated checks including DPI, background color, text readability, contrast ratio, grayscale compatibility, scale bar detection, and image metadata
- **Dark mode support**: Auto-detects microscopy/fluorescence images and switches to black background with white labels
- **Vector output**: Exports SVG/PDF with editable vector labels (panel letters, frame) over raster panel images
- **2024–2025 policy compliance**: AI disclosure guidance, image integrity checklist, accessibility checks

## Quick Start

### Installation

```bash
pip install figure-compositor
```

Or from source:

```bash
git clone https://github.com/chinure/figure-compositor.git
cd figure-compositor
pip install -e .
```

### Basic Usage

```bash
# 2×2 grid for Nature
compose-figure --panels heatmap.png bars.png scatter.png trend.png \
    --grid 2 2 --journal nature --output figure_2

# Hero + support layout
compose-figure --panels heatmap.png bars.png scatter.png trend.png quant.png \
    --layout hero-top --hero-index 0 --journal nature

# Dark microscopy images
compose-figure --panels ch1.tif ch2.tif merged.tif bars.png \
    --grid 2 2 --dark-mode auto --fit-mode fill

# Audit panels without composing
compose-figure --panels *.png --audit-only --journal nature

# Smart layout with content-aware sizing
compose-figure --panels wide.png bars.png scatter.png --smart-layout --journal nature
```

### JSON Config

For complex layouts, use a JSON config file:

```bash
compose-figure --config figure_2_config.json
```

See [`examples/`](examples/) for config templates:
- `config_example_grid.json` — Regular grid layout
- `config_example_hero.json` — Hero + support layout
- `config_example_custom.json` — Custom panel positions
- `config_example_dark.json` — Dark-mode microscopy layout

## Output Formats

| Format | Purpose | Command |
|--------|---------|---------|
| **SVG** | Primary editable vector | default (disable with `--no-vector`) |
| **PDF** | Vector for print / submission | default (disable with `--no-vector`) |
| **PNG** | Preview / quick sharing | default |
| **TIFF** | Journal submission (LZW compressed) | `--output` base name |

## Documentation

- [`docs/journal-specs.md`](docs/journal-specs.md) — Dimensions, fonts, resolutions for each journal
- [`docs/layout-patterns.md`](docs/layout-patterns.md) — Layout archetypes and grid formulas
- [`docs/consistency-audit.md`](docs/consistency-audit.md) — Pre-assembly audit checklist (11 checks)
- [`docs/content-aware-sizing.md`](docs/content-aware-sizing.md) — Why raster text shrinks and how to fix it
- [`docs/troubleshooting.md`](docs/troubleshooting.md) — Common issues and solutions
- [`docs/assembly-guide.md`](docs/assembly-guide.md) — Custom Python composition templates

## Workflow

The assembly pipeline has 5 stages. Do not skip stages.

```
Stage 1: Collect inputs   → file paths, panel roles, target journal
Stage 2: Plan layout      → choose archetype, arrange panels, assign sizes
Stage 3: Audit consistency → check fonts, colors, backgrounds, DPI, text readability
Stage 4: Compose          → assemble, label, and export
Stage 5: QA & deliver     → final checklist, export formats, notes
```

## Requirements

- Python 3.8+
- Pillow (PIL)
- NumPy
- Optional: `pdf2image` + poppler (for PDF inputs), `cairosvg` + cairo (for SVG inputs)

## License

MIT License — see [LICENSE](LICENSE).
