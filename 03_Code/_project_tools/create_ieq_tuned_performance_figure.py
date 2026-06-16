from __future__ import annotations

from pathlib import Path
import sys

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "03_Code" / "_project_tools"))

from paper_style import COLORS as PAPER_COLORS, apply_paper_style, save_figure, style_axes


SUMMARY_PATH = PROJECT_ROOT / "03_Code" / "ieq_paper" / "02_outputs" / "tables" / "tuned_model_comparison_5fold_summary.csv"
OUTPUT_DIRS = [
    PROJECT_ROOT / "03_Code" / "ieq_paper" / "02_outputs" / "figures",
    PROJECT_ROOT / "04_Figures",
]

MODEL_ORDER = [
    "Extra Trees",
    "Random Forest",
    "ANN / MLP",
    "Gradient boosting",
    "Logistic regression",
]
MODEL_LABELS = {
    "Extra Trees": "Extra\nTrees",
    "Random Forest": "Random\nForest",
    "ANN / MLP": "MLP",
    "Gradient boosting": "Grad.\nBoosting",
    "Logistic regression": "Logistic\nReg.",
}
MODEL_COLORS = {
    "Extra Trees": PAPER_COLORS["best"],
    "Random Forest": PAPER_COLORS["secondary_green"],
    "ANN / MLP": PAPER_COLORS["purple"],
    "Gradient boosting": PAPER_COLORS["medium"],
    "Logistic regression": PAPER_COLORS["dark_blue"],
}


def model_value_label_color(model: str) -> str:
    return PAPER_COLORS["text"] if model == "Gradient boosting" else "white"


def main() -> None:
    apply_paper_style()
    summary = pd.read_csv(SUMMARY_PATH)
    plot_df = summary.set_index("model").reindex(MODEL_ORDER)

    performance_metrics = [
        ("macro_f1_mean", "macro_f1_std", "Macro F1"),
        ("accuracy_mean", "accuracy_std", "Accuracy"),
        ("balanced_accuracy_mean", "balanced_accuracy_std", "Balanced accuracy"),
        ("ordinal_mae_mean", "ordinal_mae_std", "Ordinal MAE\n(lower is better)"),
    ]

    x = np.arange(len(MODEL_ORDER))
    bar_colors = [MODEL_COLORS[model] for model in MODEL_ORDER]

    fig, axes = plt.subplots(ncols=4, figsize=(13.6, 3.9), sharey=True)
    for ax, (mean_col, std_col, label) in zip(axes, performance_metrics):
        values = plot_df[mean_col].astype(float)
        errors = plot_df[std_col].astype(float)
        bars = ax.bar(
            x,
            values,
            yerr=errors,
            capsize=2.5,
            color=bar_colors,
            edgecolor=PAPER_COLORS["border"],
            linewidth=0.55,
            error_kw={"elinewidth": 0.8, "capthick": 0.8, "ecolor": PAPER_COLORS["axis"]},
        )
        for bar, model, value in zip(bars, MODEL_ORDER, values):
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                value - 0.035,
                f"{value:.2f}",
                ha="center",
                va="top",
                fontsize=8.2,
                fontweight="bold",
                color=model_value_label_color(model),
            )
        ax.set_title(label, fontsize=11.5, fontweight="bold", pad=8)
        ax.set_ylim(0, 1)
        ax.set_xticks(x)
        ax.set_xticklabels([MODEL_LABELS[model] for model in MODEL_ORDER])
        style_axes(ax, grid_axis="y")

    axes[0].set_ylabel("Score")
    for ax in axes[1:]:
        ax.tick_params(axis="y", labelleft=False)

    fig.tight_layout()

    for output_dir in OUTPUT_DIRS:
        save_figure(fig, output_dir / "tuned_model_comparison_performance")

    plt.close(fig)


if __name__ == "__main__":
    main()
