from __future__ import annotations

import importlib.util
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
STYLE_PATH = PROJECT_ROOT / "03_Code" / "ieq_paper" / "01_notebook" / "paper_style.py"

spec = importlib.util.spec_from_file_location("_ieq_notebook_paper_style", STYLE_PATH)
if spec is None or spec.loader is None:
    raise ImportError(f"Could not load paper style helper from {STYLE_PATH}")

module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

COLORS = module.COLORS
MODEL_PALETTE = module.MODEL_PALETTE
CONFUSION_CMAP = module.CONFUSION_CMAP
CONFUSION_NORM = module.CONFUSION_NORM
apply_paper_style = module.apply_paper_style
style_axes = module.style_axes
style_confusion_axis = module.style_confusion_axis
text_color_for_background = module.text_color_for_background
confusion_text_color = module.confusion_text_color
plot_confusion_matrix = module.plot_confusion_matrix
color_for_completeness = module.color_for_completeness
colors_for_ranked_values = module.colors_for_ranked_values
save_figure = module.save_figure
