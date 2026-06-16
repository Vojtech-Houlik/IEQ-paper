from __future__ import annotations

from pathlib import Path
import sys

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "03_Code" / "_project_tools"))

from paper_style import COLORS as PAPER_COLORS, apply_paper_style, plot_confusion_matrix, save_figure, style_axes


TABLE_DIR = PROJECT_ROOT / "03_Code" / "ieq_paper" / "02_outputs" / "final_extra_trees_model" / "tables"
FIGURE_DIR = PROJECT_ROOT / "03_Code" / "ieq_paper" / "02_outputs" / "final_extra_trees_model" / "figures"
IEQ_OUTPUT_TABLE_DIR = PROJECT_ROOT / "03_Code" / "ieq_paper" / "02_outputs" / "tables"
IEQ_OUTPUT_FIGURE_DIR = PROJECT_ROOT / "03_Code" / "ieq_paper" / "02_outputs" / "figures"
PAPER_FIGURE_DIR = PROJECT_ROOT / "04_Figures"

CONFUSION_TABLE = TABLE_DIR / "ieq_final_extra_trees_confusion_matrices.csv"
IMPORTANCE_TABLE = TABLE_DIR / "ieq_final_extra_trees_article_feature_importance.csv"
TUNED_CONFUSION_TABLE = IEQ_OUTPUT_TABLE_DIR / "tuned_model_confusion_matrices.csv"

FINAL_VARIANT = "final_imputation_class_weight_threshold_10fold"
CLASS_ORDER = ["dissatisfied", "neutral", "satisfied"]
CLASS_DISPLAY_LABELS = ["Dissatisfied", "Neutral", "Satisfied"]
MODEL_ORDER = [
    "Extra Trees",
    "Random Forest",
    "ANN / MLP",
    "Gradient boosting",
    "Logistic regression",
]
MODEL_LABELS = {
    "Extra Trees": "Extra Trees",
    "Random Forest": "Random Forest",
    "ANN / MLP": "MLP",
    "Gradient boosting": "Gradient Boosting",
    "Logistic regression": "Logistic Regression",
}

def create_tuned_confusion_matrices_figure() -> None:
    confusion = pd.read_csv(TUNED_CONFUSION_TABLE)
    fig, axes = plt.subplots(ncols=len(MODEL_ORDER), figsize=(13.6, 3.6), sharex=True, sharey=True)

    image = None
    for ax, model in zip(axes, MODEL_ORDER):
        model_confusion = confusion[confusion["model"].eq(model)]
        matrix = (
            model_confusion.pivot(index="true_label", columns="predicted_label", values="count")
            .reindex(index=CLASS_ORDER, columns=CLASS_ORDER)
            .fillna(0)
            .astype(int)
        )
        image, colorbar_label = plot_confusion_matrix(
            ax,
            matrix,
            labels=CLASS_ORDER,
            display_labels=CLASS_DISPLAY_LABELS,
            title=MODEL_LABELS[model],
            annotation_fontsize=8.2,
        )

    for ax in axes[1:]:
        ax.set_ylabel("")

    fig.subplots_adjust(wspace=0.22, bottom=0.27, top=0.82, right=0.92)
    colorbar_axis = fig.add_axes([0.935, 0.30, 0.012, 0.43])
    colorbar = fig.colorbar(image, cax=colorbar_axis)
    colorbar.set_label(colorbar_label)

    save_figure(fig, IEQ_OUTPUT_FIGURE_DIR / "tuned_model_comparison_confusion_matrices")
    save_figure(fig, PAPER_FIGURE_DIR / "tuned_model_comparison_confusion_matrices")
    plt.close(fig)


def create_confusion_matrix_figure() -> None:
    confusion = pd.read_csv(CONFUSION_TABLE)
    confusion = confusion[confusion["variant"].eq(FINAL_VARIANT)]
    matrix = (
        confusion.pivot(index="true_label", columns="predicted_label", values="count")
        .reindex(index=CLASS_ORDER, columns=CLASS_ORDER)
        .fillna(0)
        .astype(int)
    )
    fig, ax = plt.subplots(figsize=(5.4, 4.7), constrained_layout=True)
    image, colorbar_label = plot_confusion_matrix(
        ax,
        matrix,
        labels=CLASS_ORDER,
        display_labels=CLASS_DISPLAY_LABELS,
        title=None,
        annotation_fontsize=10,
    )

    colorbar = fig.colorbar(image, ax=ax, fraction=0.046, pad=0.04)
    colorbar.set_label(colorbar_label, fontsize=11)
    colorbar.ax.tick_params(labelsize=10)

    save_figure(fig, FIGURE_DIR / "ieq_final_extra_trees_confusion_matrix")
    save_figure(fig, PAPER_FIGURE_DIR / "final_extra_trees_confusion_matrix")
    plt.close(fig)


def create_importance_figure() -> None:
    importance = pd.read_csv(IMPORTANCE_TABLE)
    plot_data = importance.sort_values("builtin_importance", ascending=True)

    method_panels = [
        (
            "builtin_normalized",
            "builtin_importance_percent",
            "Built-in ET\nimportance",
            lambda value: f"{value:.1f}%",
            PAPER_COLORS["best"],
        ),
        (
            "permutation_normalized",
            "permutation_macro_f1_drop_mean",
            "Permutation\nmacro-F1 drop",
            lambda value: f"{value:.3f}",
            PAPER_COLORS["secondary_green"],
        ),
        (
            "shap_normalized",
            "shap_importance_percent",
            "TreeSHAP\nmean |SHAP|",
            lambda value: f"{value:.1f}%",
            PAPER_COLORS["medium"],
        ),
    ]

    fig, axes = plt.subplots(ncols=3, figsize=(11.2, 8.6), sharey=True)
    for ax, (normalized_column, raw_column, title, formatter, color) in zip(axes, method_panels):
        bars = ax.barh(
            plot_data["feature"],
            plot_data[normalized_column],
            color=color,
            edgecolor=PAPER_COLORS["border"],
            linewidth=0.55,
            alpha=0.92,
        )
        ax.set_title(title, fontsize=11.5, fontweight="bold", pad=9)
        ax.set_xlim(0, 1.22)
        ax.set_xlabel("Normalized importance", fontsize=11, labelpad=6)
        ax.set_xticks([0.0, 0.5, 1.0])
        style_axes(ax, grid_axis="x")
        ax.tick_params(axis="x", labelsize=10)
        ax.tick_params(axis="y", labelsize=10)
        for bar, raw_value in zip(bars, plot_data[raw_column]):
            label = "n/a" if pd.isna(raw_value) else formatter(raw_value)
            ax.text(
                bar.get_width() + 0.025,
                bar.get_y() + bar.get_height() / 2,
                label,
                va="center",
                fontsize=10,
                color=PAPER_COLORS["text"],
            )

    axes[0].set_ylabel("Predictor", fontsize=11, labelpad=8)
    for ax in axes[1:]:
        ax.tick_params(axis="y", labelleft=False)

    fig.tight_layout(w_pad=2.3)

    save_figure(fig, FIGURE_DIR / "ieq_final_extra_trees_importance_method_comparison")
    save_figure(fig, PAPER_FIGURE_DIR / "final_extra_trees_importance_method_comparison")
    plt.close(fig)


def main() -> None:
    apply_paper_style()
    create_tuned_confusion_matrices_figure()
    create_confusion_matrix_figure()
    create_importance_figure()
    print("Saved IEQ paper figures.")


if __name__ == "__main__":
    main()
