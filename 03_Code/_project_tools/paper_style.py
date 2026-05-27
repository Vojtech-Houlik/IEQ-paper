from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt


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


def apply_paper_style() -> None:
    """Apply the shared TU Berlin / HRI inspired scientific figure style."""
    plt.rcParams.update(
        {
            "figure.facecolor": "white",
            "axes.facecolor": "white",
            "savefig.facecolor": "white",
            "savefig.bbox": "tight",
            "savefig.dpi": 300,
            "font.family": "sans-serif",
            "font.sans-serif": ["Arial", "DejaVu Sans", "Liberation Sans"],
            "font.size": 10.5,
            "axes.titlesize": 16,
            "axes.titleweight": "bold",
            "axes.labelsize": 11.5,
            "axes.labelcolor": COLORS["text"],
            "axes.edgecolor": COLORS["axis"],
            "axes.linewidth": 0.8,
            "axes.grid": True,
            "axes.axisbelow": True,
            "xtick.labelsize": 10,
            "ytick.labelsize": 10,
            "xtick.color": COLORS["text"],
            "ytick.color": COLORS["text"],
            "xtick.major.size": 3.0,
            "ytick.major.size": 0.0,
            "grid.color": COLORS["grid"],
            "grid.linewidth": 0.8,
            "grid.alpha": 0.85,
            "legend.frameon": False,
            "legend.fontsize": 10,
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
