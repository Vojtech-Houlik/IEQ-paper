from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LinearSegmentedColormap, Normalize, PowerNorm


COLORS = {
    "text": "#111827",
    "muted_text": "#4B5563",
    "border": "#1F2933",
    "axis": "#AAB2B8",
    "grid": "#D9DEE3",
    "target": "#2563EB",
    "best": "#2A9D8F",
    "high": "#2A9D8F",
    "medium": "#E9C46A",
    "low": "#E76F51",
    "neutral": "#6B7280",
    "dark_blue": "#457B9D",
    "secondary_green": "#5A9E6F",
    "purple": "#7C6EE6",
    "tu_red": "#C50E1F",
}

MODEL_PALETTE = [
    COLORS["best"],
    COLORS["medium"],
    COLORS["dark_blue"],
    COLORS["neutral"],
    COLORS["purple"],
    COLORS["secondary_green"],
]

CONFUSION_CMAP = LinearSegmentedColormap.from_list(
    "paper_confusion",
    ["#F8FAFC", "#A9C1D3", "#376F96", "#123A5A"],
)
CONFUSION_NORM = PowerNorm(gamma=0.68, vmin=0, vmax=100)


def apply_paper_style() -> None:
    """Apply the shared Building and Environment manuscript figure style."""
    plt.rcParams.update(
        {
            "figure.dpi": 300,
            "figure.facecolor": "white",
            "axes.facecolor": "white",
            "savefig.facecolor": "white",
            "savefig.bbox": "tight",
            "savefig.dpi": 300,
            "font.family": "sans-serif",
            "font.sans-serif": ["Arial", "DejaVu Sans", "Liberation Sans"],
            "font.size": 11,
            "axes.titlesize": 11,
            "axes.titleweight": "normal",
            "axes.labelsize": 11,
            "axes.labelcolor": COLORS["text"],
            "axes.edgecolor": COLORS["axis"],
            "axes.linewidth": 0.8,
            "axes.grid": True,
            "axes.axisbelow": True,
            "xtick.labelsize": 9.5,
            "ytick.labelsize": 9.5,
            "xtick.color": COLORS["text"],
            "ytick.color": COLORS["text"],
            "xtick.major.size": 3.0,
            "ytick.major.size": 0.0,
            "grid.color": COLORS["grid"],
            "grid.linewidth": 0.8,
            "grid.alpha": 0.85,
            "legend.frameon": False,
            "legend.fontsize": 9.5,
            "lines.linewidth": 2.0,
            "patch.edgecolor": COLORS["border"],
            "patch.linewidth": 0.55,
        }
    )


def style_axes(ax, grid_axis: str = "x") -> None:
    """Apply final axis cleanup after plotting."""
    ax.grid(axis=grid_axis, color=COLORS["grid"], alpha=0.85, linewidth=0.8)
    ax.set_axisbelow(True)
    for spine in ("top", "right", "left"):
        ax.spines[spine].set_visible(False)
    ax.spines["bottom"].set_color(COLORS["axis"])
    ax.tick_params(axis="y", length=0)


def _relative_luminance(rgb: tuple[float, float, float]) -> float:
    def linearize(channel: float) -> float:
        return channel / 12.92 if channel <= 0.03928 else ((channel + 0.055) / 1.055) ** 2.4

    red, green, blue = (linearize(channel) for channel in rgb)
    return 0.2126 * red + 0.7152 * green + 0.0722 * blue


def text_color_for_background(color) -> str:
    """Choose black or white text by WCAG-style contrast against a matplotlib color."""
    red, green, blue = color[:3]
    background_luminance = _relative_luminance((red, green, blue))
    contrast_with_white = 1.05 / (background_luminance + 0.05)
    contrast_with_black = (background_luminance + 0.05) / 0.05
    return "white" if contrast_with_white >= contrast_with_black else COLORS["text"]


def confusion_text_color(value: float, norm=None, cmap=None) -> str:
    """Return a readable annotation color for a confusion-matrix cell value."""
    norm = CONFUSION_NORM if norm is None else norm
    cmap = CONFUSION_CMAP if cmap is None else cmap
    return text_color_for_background(cmap(norm(float(value))))


def style_confusion_axis(ax) -> None:
    """Remove grid lines and frame styling from a confusion-matrix axis."""
    ax.grid(False)
    ax.minorticks_off()
    ax.tick_params(which="both", length=0)
    for spine in ax.spines.values():
        spine.set_visible(False)


def plot_confusion_matrix(
    ax,
    matrix,
    labels: list[str] | None = None,
    display_labels: list[str] | None = None,
    *,
    title: str | None = None,
    normalize_rows: bool = True,
    cmap=None,
    norm=None,
    vmin: float = 0,
    vmax: float = 100,
    percent_decimals: int = 0,
    count_decimals: int = 0,
    annotation_fontsize: float = 8.5,
    xtick_rotation: float = 45,
):
    """Draw a paper-style confusion matrix with contrast-aware cell labels.

    The input matrix is expected to contain counts. Cell colors are row-normalized
    percentages by default, while annotations show both percentage and count.
    """
    values = np.asarray(matrix, dtype=float)
    counts = np.asarray(matrix, dtype=float)
    if normalize_rows:
        row_totals = values.sum(axis=1, keepdims=True)
        color_values = values / np.where(row_totals == 0, 1, row_totals) * 100
        colorbar_label = "Row-normalized share (%)"
        norm = CONFUSION_NORM if norm is None else norm
    else:
        color_values = values
        colorbar_label = "Count"
        norm = Normalize(vmin=vmin, vmax=max(vmax, float(np.nanmax(color_values)))) if norm is None else norm

    cmap = CONFUSION_CMAP if cmap is None else cmap
    image = ax.imshow(color_values, cmap=cmap, norm=norm, interpolation="nearest")

    if labels is None:
        if hasattr(matrix, "index"):
            labels = [str(label) for label in matrix.index]
        else:
            labels = [str(index) for index in range(values.shape[0])]
    if display_labels is None:
        display_labels = labels

    ax.set_xticks(np.arange(len(display_labels)))
    ax.set_yticks(np.arange(len(display_labels)))
    ax.set_xticklabels(display_labels, rotation=xtick_rotation, ha="right")
    ax.set_yticklabels(display_labels)
    if title:
        ax.set_title(title)
    ax.set_xlabel("Predicted class")
    ax.set_ylabel("True class")
    style_confusion_axis(ax)

    for row_index, (count_row, color_row) in enumerate(zip(counts, color_values)):
        for column_index, (count, color_value) in enumerate(zip(count_row, color_row)):
            count_text = f"{count:.{count_decimals}f}" if count_decimals else f"{int(round(count))}"
            ax.text(
                column_index,
                row_index,
                f"{color_value:.{percent_decimals}f}%\n{count_text}" if normalize_rows else count_text,
                ha="center",
                va="center",
                fontsize=annotation_fontsize,
                color=confusion_text_color(color_value, norm=norm, cmap=cmap),
            )

    return image, colorbar_label


def color_for_completeness(percent: float, role: str | None = None) -> str:
    if role == "Output":
        return COLORS["target"]
    if percent >= 95:
        return COLORS["high"]
    if percent >= 80:
        return COLORS["medium"]
    return COLORS["low"]


def colors_for_ranked_values(values, higher_is_better: bool = True) -> list[str]:
    """Return semantic colors where the best value is teal."""
    values = list(values)
    if not values:
        return []

    best_value = max(values) if higher_is_better else min(values)
    worst_value = min(values) if higher_is_better else max(values)

    colors = []
    for value in values:
        if value == best_value:
            colors.append(COLORS["best"])
        elif value == worst_value and len(set(values)) > 2:
            colors.append(COLORS["low"])
        else:
            colors.append(COLORS["medium"])
    return colors


def save_figure(fig, output_path: Path | str, dpi: int = 300) -> None:
    """Save a figure as PNG and PDF using the shared paper export settings."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path.with_suffix(".png"), dpi=dpi, bbox_inches="tight")
    fig.savefig(path.with_suffix(".pdf"), bbox_inches="tight")
