# Paper Figure Style Guide

This guide defines the shared figure style for the thermal comfort and IEQ papers.
The aim is a clean scientific style inspired by TU Berlin / HRI presentation rules,
while keeping the figures journal-ready and readable in print.

Authoritative project files:

- Human-readable guide: `PAPER_FIGURE_STYLE_GUIDE.md`
- Matplotlib helper to edit: `ieq_paper/01_notebook/paper_style.py`
- Compatibility import wrapper: `_project_tools/paper_style.py`
- Matplotlib style file: `_project_tools/tu_hri_paper.mplstyle`
- Paper-facing export folder: `../04_Figures`

## Core Principles

- Use English for all figure titles, axis labels, legends, and annotations.
- Use a white background.
- Keep graphs restrained and scientific: no decorative gradients, logos, shadows, or heavy frames.
- Use TU red only as a rare accent, not as the dominant color in data plots.
- Prefer colorblind-aware colors and make the meaning of colors consistent across papers.
- Export every paper-facing figure as both `PNG` and `PDF`.
- Store manuscript-ready figure exports in `../04_Figures/<paper-folder>`.
- LaTeX files should reference figures from `../04_Figures`, not from notebook or code output folders.
- Keep full source tables next to figures in the paper-specific outputs folder whenever possible.

## Typography

- Preferred font: `Arial`.
- TU Berlin house font `Muli` can be used when available, but `Arial` is the stable default for reproducibility.
- Titles: bold, approximately 15-18 pt.
- Axis labels: approximately 11-12 pt.
- Tick labels: approximately 9.5-10.5 pt.
- Avoid italic text except when required by scientific notation.
- Avoid font sizes below 7 pt.

## Layout

- Single-panel figures: use roughly `7.0 x 4.6 in`.
- Wide comparison figures: use roughly `10.5 x 5.5 in`.
- Multi-panel figures: keep consistent panel spacing and align axes.
- Remove top and right spines.
- Avoid full box frames unless the plot type needs them.
- Use light horizontal or vertical gridlines only where they help reading values.
- Place values at the end of bars when this improves readability.

## Shared Color Palette

- Text: `#111827`
- Muted text: `#4B5563`
- Border / axis: `#AAB2B8`
- Grid: `#D9DEE3`
- Target / reference blue: `#2563EB`
- Main / best / high completeness teal: `#2A9D8F`
- Medium / caution amber: `#E9C46A`
- Low / weak / warning coral: `#E76F51`
- Neutral gray: `#6B7280`
- Dark blue: `#457B9D`
- Secondary green: `#5A9E6F`
- Purple accent: `#7C6EE6`
- TU red accent: `#C50E1F`

## Semantic Color Rules

Completeness plots:

- Output/target variable: blue.
- Feature completeness `>= 95%`: teal.
- Feature completeness `80-95%`: amber.
- Feature completeness `< 80%`: coral.

Model performance plots:

- Best model: teal.
- Middle/comparison models: amber, blue, or neutral gray.
- Weakest model: coral only when the contrast is meaningful.
- Do not color a best-performing model red.

Feature importance plots:

- Use one main color for a single selected model, usually dark blue or teal.
- Use different colors only when comparing model families or feature groups.
- Keep encoded indicators separate when interpretation requires it.
- Group indicators only when the figure is explicitly source-feature level.

Missingness and cleaning plots:

- Missing or incomplete data should use amber/coral depending on severity.
- Avoid using green for missingness.

## Code Usage

In project scripts inside `_project_tools`, import the shared helper directly.
The import is kept stable by `_project_tools/paper_style.py`, while the editable
implementation lives next to the IEQ notebooks:

```python
from paper_style import COLORS, apply_paper_style, color_for_completeness, save_figure

apply_paper_style()
```

In IEQ notebooks, `paper_style.py` is in the same folder as the notebooks. In
other notebooks, add `_project_tools` to `sys.path` before importing:

```python
from pathlib import Path
import sys

ROOT = Path.cwd()
while not (ROOT / "_project_tools").exists() and ROOT.parent != ROOT:
    ROOT = ROOT.parent

sys.path.append(str(ROOT / "_project_tools"))
from paper_style import COLORS, apply_paper_style, save_figure

apply_paper_style()
```

Save figures through the helper:

```python
save_figure(fig, output_path_without_suffix)
```

This writes both `.png` and `.pdf`.

## Current Decision

All new figures for both papers should follow this guide unless a target journal
requires a different style. If a journal template conflicts with this guide, the
journal template takes priority.
