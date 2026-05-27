from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from paper_style import COLORS, apply_paper_style, color_for_completeness, save_figure


ROOT = Path(__file__).resolve().parents[1]


def find_raw_dataset() -> Path:
    candidates = [
        ROOT.parent / "02_Datasets" / "raw" / "FullDataset_CombinedSimple.csv",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    raise FileNotFoundError(
        "Raw dataset not found. Checked: "
        + ", ".join(str(candidate) for candidate in candidates)
    )


RAW_DATA = find_raw_dataset()
MODEL_READY_DATASET_DIR = ROOT.parent / "02_Datasets" / "model_ready"
THERMAL_DATA = MODEL_READY_DATASET_DIR / "thermal_comfort_model_dataset.xlsx"
IEQ_DATA = MODEL_READY_DATASET_DIR / "ieq_model_dataset.xlsx"
FIGURE_DIR = ROOT.parent / "04_Figures"

NA_VALUES = ["", " ", "NA", "N/A", "na", "n/a", "NaN", "nan", "None", "none", "NULL", "null"]


@dataclass(frozen=True)
class FeatureSpec:
    label: str
    columns: tuple[str, ...]


@dataclass(frozen=True)
class FeatureSet:
    title: str
    data_path: Path
    sheet_name: str
    target: FeatureSpec
    inputs: tuple[FeatureSpec, ...]
    output_name: str
    latex_subdir: str


def feature(label: str, *columns: str) -> FeatureSpec:
    return FeatureSpec(label=label, columns=columns or (label,))


FEATURE_SETS = [
    FeatureSet(
        title="Thermal Comfort Dataset",
        data_path=THERMAL_DATA,
        sheet_name="data_before_imputation",
        target=feature("Thermal satisfaction 3-class"),
        inputs=(
            feature("Temperature"),
            feature("RH"),
            feature("CLO"),
            feature("Age"),
            feature("Gender"),
            feature("Student"),
            feature("EA"),
            feature(
                "Position in class",
                "LocationBack",
                "LocationFront",
                "LocationLeft",
                "LocationRight",
                "LocationMiddle",
            ),
            feature("Ttrend"),
            feature("Vote hour"),
            feature("Vote weekday"),
            feature("Moment"),
            feature("AC on/off"),
        ),
        output_name="fig_02_thermal_feature_completeness",
        latex_subdir="thermal_comfort_paper",
    ),
    FeatureSet(
        title="IEQ Dataset",
        data_path=IEQ_DATA,
        sheet_name="data_before_imputation",
        target=feature("IEQ satisfaction 3-class"),
        inputs=(
            feature("Temperature"),
            feature("RH"),
            feature("CLO"),
            feature("CO2"),
            feature("Lighting"),
            feature("Sound"),
            feature("Age"),
            feature("Gender"),
            feature("Student"),
            feature("EA"),
            feature(
                "Position in class",
                "LocationBack",
                "LocationFront",
                "LocationLeft",
                "LocationRight",
                "LocationMiddle",
            ),
            feature("Ttrend"),
            feature("Vote hour"),
            feature("Vote weekday"),
            feature("Moment"),
            feature("AC on/off"),
        ),
        output_name="fig_03_ieq_feature_completeness",
        latex_subdir="ieq_paper",
    ),
]


SATISFACTION_COLUMNS = [
    ("Overall IEQ", "IEQSatisfaction"),
    ("Thermal", "ThermalSatisfaction"),
    ("IAQ", "IAQSatisfaction"),
    ("Visual", "VisualSatisfaction"),
    ("Acoustic", "AcousticSatisfaction"),
]

ENVIRONMENTAL_FEATURES = [
    ("Troom", "Temperature (deg C)"),
    ("RH", "Relative Humidity (%)"),
    ("CO2", "CO2 (ppm)"),
    ("Lighting", "Lighting (lx)"),
    ("Sound", "Sound (dB)"),
]

VOTE_COLORS = {
    1: COLORS["tu_red"],
    2: COLORS["low"],
    3: COLORS["purple"],
    4: COLORS["target"],
    5: COLORS["best"],
}

UNIFIED_SATISFACTION_CATEGORIES = [
    ("1-2", "Dissatisfied", (1, 2), COLORS["low"]),
    ("3", "Neutral", (3,), COLORS["neutral"]),
    ("4-5", "Satisfied", (4, 5), COLORS["best"]),
]


def read_raw_data() -> pd.DataFrame:
    data = pd.read_csv(RAW_DATA, na_values=NA_VALUES, keep_default_na=True)
    for column in data.columns:
        if not (pd.api.types.is_object_dtype(data[column]) or pd.api.types.is_string_dtype(data[column])):
            continue
        stripped = data[column].astype("string").str.strip()
        data[column] = stripped.mask(stripped.isin(NA_VALUES))
    return data


def save_article_figure(fig, output_name: str, latex_subdir: str = "both_papers") -> None:
    output_dir = FIGURE_DIR / latex_subdir
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / output_name
    save_figure(fig, output_path)


def percentage_labels(counts: pd.Series) -> pd.Series:
    return counts / counts.sum() * 100 if counts.sum() else counts.astype(float)


def unified_satisfaction_counts(votes: pd.Series) -> pd.Series:
    return pd.Series(
        [int(votes.isin(source_votes).sum()) for _, _, source_votes, _ in UNIFIED_SATISFACTION_CATEGORIES],
        index=[category[0] for category in UNIFIED_SATISFACTION_CATEGORIES],
    )


def draw_distribution_bars(
    ax,
    counts: pd.Series,
    x_positions: np.ndarray,
    colors: list[str],
    x_label: str,
) -> None:
    percentages = percentage_labels(counts)
    bars = ax.bar(x_positions, counts.values, color=colors, edgecolor=COLORS["border"], linewidth=0.55)

    ax.set_xlabel(x_label, fontsize=10.5)
    ax.set_xticks(x_positions)
    ax.set_xticklabels(counts.index)
    ax.grid(axis="y", color=COLORS["grid"], alpha=0.85)
    ax.grid(axis="x", visible=False)
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)
    ax.spines["left"].set_color(COLORS["axis"])
    ax.spines["bottom"].set_color(COLORS["axis"])
    ax.tick_params(axis="both", labelsize=9.5)

    label_offset = max(counts.max() * 0.018, 18)
    for bar, percent in zip(bars, percentages):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + label_offset,
            f"{percent:.1f}%",
            ha="center",
            va="bottom",
            fontsize=8.8,
            color=COLORS["text"],
        )


def completeness_by_column(data: pd.DataFrame) -> pd.DataFrame:
    total_rows = len(data)
    rows = []
    for column in data.columns:
        complete_rows = int(data[column].notna().sum())
        missing_rows = total_rows - complete_rows
        rows.append(
            {
                "column": column,
                "complete_rows": complete_rows,
                "missing_rows": missing_rows,
                "total_rows": total_rows,
                "complete_percent": complete_rows / total_rows * 100 if total_rows else 0.0,
                "missing_percent": missing_rows / total_rows * 100 if total_rows else 0.0,
            }
        )
    return pd.DataFrame(rows).sort_values(["complete_percent", "column"], ascending=[True, True])


def feature_completeness_table(data: pd.DataFrame, feature_set: FeatureSet) -> pd.DataFrame:
    total_rows = len(data)
    rows = []
    for spec in [feature_set.target, *feature_set.inputs]:
        if len(spec.columns) == 1:
            complete_rows = int(data[spec.columns[0]].notna().sum())
        else:
            complete_rows = int(data[list(spec.columns)].notna().all(axis=1).sum())
        rows.append(
            {
                "feature": spec.label,
                "source_columns": ", ".join(spec.columns),
                "role": "Output" if spec == feature_set.target else "Input",
                "complete_rows": complete_rows,
                "missing_rows": total_rows - complete_rows,
                "total_rows": total_rows,
                "complete_percent": complete_rows / total_rows * 100 if total_rows else 0.0,
            }
        )
    return pd.DataFrame(rows).sort_values(["complete_percent", "feature"], ascending=[True, True])


def split_table(table: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    midpoint = int(np.ceil(len(table) / 2))
    return table.iloc[:midpoint].copy(), table.iloc[midpoint:].copy()


def plot_raw_completeness(data: pd.DataFrame) -> None:
    table = completeness_by_column(data)
    left, right = split_table(table)

    fig, axes = plt.subplots(ncols=2, figsize=(13.6, 8.2), sharex=True)
    fig.suptitle("Belgian Classrooms Dataset: Column Completeness", fontsize=17, fontweight="bold", y=0.985)
    fig.text(
        0.5,
        0.948,
        f"Raw source: FullDataset_CombinedSimple.csv | Rows: {len(data):,} | Missing values counted as empty, whitespace, or NA-like tokens",
        ha="center",
        va="center",
        fontsize=9.5,
        color=COLORS["muted_text"],
    )

    for ax, panel in zip(axes, [left, right]):
        y = np.arange(len(panel))
        complete = panel["complete_percent"].to_numpy()
        missing = panel["missing_percent"].to_numpy()
        ax.barh(y, complete, color=COLORS["best"], edgecolor="white", linewidth=0.4, label="Complete values")
        ax.barh(
            y,
            missing,
            left=complete,
            color=COLORS["low"],
            alpha=0.62,
            edgecolor="white",
            linewidth=0.4,
            label="Missing values",
        )
        ax.set_yticks(y)
        ax.set_yticklabels(panel["column"], fontsize=7.2)
        ax.invert_yaxis()
        ax.set_xlim(0, 112)
        ax.grid(axis="x", color=COLORS["grid"], alpha=0.85)
        ax.grid(axis="y", visible=False)
        for spine in ("top", "right", "left"):
            ax.spines[spine].set_visible(False)
        ax.spines["bottom"].set_color(COLORS["axis"])
        ax.tick_params(axis="y", length=0)
        ax.tick_params(axis="x", labelsize=8.5)

        for row_index, row in enumerate(panel.itertuples()):
            complete_percent = row.complete_percent
            missing_rows = int(row.missing_rows)
            if complete_percent >= 9:
                ax.text(
                    min(complete_percent - 1.0, 98.0),
                    row_index,
                    f"{complete_percent:.1f}%",
                    va="center",
                    ha="right",
                    fontsize=6.5,
                    color=COLORS["text"],
                    fontweight="bold",
                )
            if missing_rows > 0:
                ax.text(
                    104.0,
                    row_index,
                    f"{missing_rows:,}",
                    va="center",
                    ha="left",
                    fontsize=6.4,
                    color=COLORS["low"],
                    fontweight="bold",
                )

    axes[0].legend(loc="upper left", bbox_to_anchor=(0.0, 1.075), ncol=2, frameon=False, fontsize=8.2)
    axes[0].set_xlabel("Percent of rows", fontsize=10.5)
    axes[1].set_xlabel("Percent of rows", fontsize=10.5)
    fig.subplots_adjust(left=0.08, right=0.985, top=0.89, bottom=0.08, wspace=0.2)
    save_article_figure(fig, "fig_01_raw_dataset_column_completeness")
    plt.close(fig)


def plot_feature_completeness(feature_set: FeatureSet) -> None:
    data = pd.read_excel(feature_set.data_path, sheet_name=feature_set.sheet_name)
    table = feature_completeness_table(data, feature_set)

    fig_height = max(5.6, 0.42 * len(table) + 1.7)
    fig, ax = plt.subplots(figsize=(10.8, fig_height))
    colors = [color_for_completeness(row.complete_percent, row.role) for row in table.itertuples()]
    bars = ax.barh(
        table["feature"],
        table["complete_percent"],
        color=colors,
        edgecolor=COLORS["border"],
        linewidth=0.55,
    )

    ax.set_title(f"Feature Completeness: {feature_set.title}", fontsize=17, fontweight="bold", pad=14)
    ax.set_xlabel("Completeness (% of all rows)", fontsize=11.5)
    ax.set_xlim(0, 100)
    ax.grid(axis="x", color=COLORS["grid"], alpha=0.85)
    ax.grid(axis="y", visible=False)
    ax.set_axisbelow(True)
    ax.tick_params(axis="y", length=0, labelsize=10.3)
    ax.tick_params(axis="x", labelsize=10)
    for spine in ("top", "right", "left"):
        ax.spines[spine].set_visible(False)
    ax.spines["bottom"].set_color(COLORS["axis"])

    for bar, row in zip(bars, table.itertuples()):
        percent = row.complete_percent
        label = f"{percent:.1f}%"
        inside = percent >= 88
        x = percent - 1.3 if inside else min(percent + 1.2, 98.5)
        ax.text(
            x,
            bar.get_y() + bar.get_height() / 2,
            label,
            va="center",
            ha="right" if inside else "left",
            fontsize=9.5,
            color=COLORS["text"],
        )

    fig.tight_layout()
    save_article_figure(fig, feature_set.output_name, feature_set.latex_subdir)
    plt.close(fig)


def plot_satisfaction_distribution(data: pd.DataFrame) -> None:
    fig, axes = plt.subplots(ncols=5, figsize=(13.8, 3.9), sharey=True)
    fig.suptitle("Distribution of Overall and Domain Satisfaction Votes", fontsize=17, fontweight="bold", y=1.02)

    for ax, (title, column) in zip(axes, SATISFACTION_COLUMNS):
        votes = pd.to_numeric(data[column], errors="coerce").dropna().astype(int)
        counts = votes.value_counts().reindex([1, 2, 3, 4, 5], fill_value=0)
        percentages = counts / counts.sum() * 100 if counts.sum() else counts.astype(float)
        colors = [VOTE_COLORS[vote] for vote in counts.index]
        bars = ax.bar(counts.index, counts.values, color=colors, edgecolor=COLORS["border"], linewidth=0.55)

        ax.set_title(title, fontsize=12.5, fontweight="bold", pad=7)
        ax.set_xlabel("Vote", fontsize=10)
        ax.set_xticks([1, 2, 3, 4, 5])
        ax.grid(axis="y", color=COLORS["grid"], alpha=0.85)
        ax.grid(axis="x", visible=False)
        for spine in ("top", "right"):
            ax.spines[spine].set_visible(False)
        ax.spines["left"].set_color(COLORS["axis"])
        ax.spines["bottom"].set_color(COLORS["axis"])
        ax.tick_params(axis="both", labelsize=9.3)

        for bar, percent in zip(bars, percentages):
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height() + max(counts.max() * 0.015, 20),
                f"{percent:.1f}%",
                ha="center",
                va="bottom",
                fontsize=8.4,
                color=COLORS["text"],
            )

    axes[0].set_ylabel("Count", fontsize=10.5)
    max_count = max(pd.to_numeric(data[column], errors="coerce").dropna().value_counts().max() for _, column in SATISFACTION_COLUMNS)
    for ax in axes:
        ax.set_ylim(0, max_count * 1.16)

    fig.subplots_adjust(left=0.055, right=0.995, top=0.82, bottom=0.18, wspace=0.08)
    save_article_figure(fig, "fig_04_satisfaction_vote_distribution")
    plt.close(fig)


def plot_unified_satisfaction_distribution(data: pd.DataFrame) -> None:
    fig, axes = plt.subplots(ncols=5, figsize=(13.8, 3.9), sharey=True)
    fig.suptitle("Distribution of Unified Overall and Domain Satisfaction Categories", fontsize=17, fontweight="bold", y=1.02)

    all_counts = []
    x = np.arange(len(UNIFIED_SATISFACTION_CATEGORIES))
    x_labels = [category[0] for category in UNIFIED_SATISFACTION_CATEGORIES]
    colors = [category[3] for category in UNIFIED_SATISFACTION_CATEGORIES]

    for ax, (title, column) in zip(axes, SATISFACTION_COLUMNS):
        votes = pd.to_numeric(data[column], errors="coerce").dropna().astype(int)
        counts = unified_satisfaction_counts(votes)
        all_counts.append(counts)
        percentages = counts / counts.sum() * 100 if counts.sum() else counts.astype(float)
        bars = ax.bar(x, counts.values, color=colors, edgecolor=COLORS["border"], linewidth=0.55)

        ax.set_title(title, fontsize=12.5, fontweight="bold", pad=7)
        ax.set_xlabel("Unified category", fontsize=10)
        ax.set_xticks(x)
        ax.set_xticklabels(x_labels)
        ax.grid(axis="y", color=COLORS["grid"], alpha=0.85)
        ax.grid(axis="x", visible=False)
        for spine in ("top", "right"):
            ax.spines[spine].set_visible(False)
        ax.spines["left"].set_color(COLORS["axis"])
        ax.spines["bottom"].set_color(COLORS["axis"])
        ax.tick_params(axis="both", labelsize=9.3)

        for bar, percent in zip(bars, percentages):
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height() + max(counts.max() * 0.015, 20),
                f"{percent:.1f}%",
                ha="center",
                va="bottom",
                fontsize=8.4,
                color=COLORS["text"],
            )

    axes[0].set_ylabel("Count", fontsize=10.5)
    max_count = max(int(counts.max()) for counts in all_counts)
    for ax in axes:
        ax.set_ylim(0, max_count * 1.16)

    fig.subplots_adjust(left=0.055, right=0.995, top=0.82, bottom=0.18, wspace=0.08)
    save_article_figure(fig, "fig_04b_unified_satisfaction_category_distribution")
    plt.close(fig)


def plot_target_scale_comparison(
    data: pd.DataFrame,
    title: str,
    column: str,
    output_name: str,
    latex_subdir: str,
) -> None:
    votes = pd.to_numeric(data[column], errors="coerce").dropna().astype(int)
    original_counts = votes.value_counts().reindex([1, 2, 3, 4, 5], fill_value=0)
    unified_counts = unified_satisfaction_counts(votes)

    fig, axes = plt.subplots(ncols=2, figsize=(8.4, 3.8), sharey=True)
    fig.suptitle(f"{title} Vote Distribution", fontsize=16.5, fontweight="bold", y=1.02)

    axes[0].set_title("Original five-class scale", fontsize=12.4, fontweight="bold", pad=7)
    draw_distribution_bars(
        axes[0],
        original_counts,
        np.array(original_counts.index),
        [VOTE_COLORS[vote] for vote in original_counts.index],
        "Vote",
    )

    unified_x = np.arange(len(unified_counts))
    axes[1].set_title("Unified three-class scale", fontsize=12.4, fontweight="bold", pad=7)
    draw_distribution_bars(
        axes[1],
        unified_counts,
        unified_x,
        [category[3] for category in UNIFIED_SATISFACTION_CATEGORIES],
        "Unified category",
    )

    axes[0].set_ylabel("Count", fontsize=10.8)
    max_count = max(int(original_counts.max()), int(unified_counts.max()))
    for ax in axes:
        ax.set_ylim(0, max_count * 1.16)

    fig.subplots_adjust(left=0.085, right=0.985, top=0.8, bottom=0.18, wspace=0.15)
    save_article_figure(fig, output_name, latex_subdir)
    plt.close(fig)


def plot_article_target_distributions(data: pd.DataFrame) -> None:
    plot_target_scale_comparison(
        data=data,
        title="Thermal Satisfaction",
        column="ThermalSatisfaction",
        output_name="fig_thermal_satisfaction_vote_distribution_original_unified",
        latex_subdir="thermal_comfort_paper",
    )
    plot_target_scale_comparison(
        data=data,
        title="Overall IEQ Satisfaction",
        column="IEQSatisfaction",
        output_name="fig_overall_ieq_satisfaction_vote_distribution_original_unified",
        latex_subdir="ieq_paper",
    )


def plot_environmental_boxplots(data: pd.DataFrame) -> None:
    plot_data = data.copy()
    plot_data["IEQSatisfaction"] = pd.to_numeric(plot_data["IEQSatisfaction"], errors="coerce")
    for column, _ in ENVIRONMENTAL_FEATURES:
        plot_data[column] = pd.to_numeric(plot_data[column], errors="coerce")

    fig, axes = plt.subplots(nrows=len(ENVIRONMENTAL_FEATURES), ncols=1, figsize=(9.2, 9.6), sharex=True)
    fig.suptitle("Environmental Features by Overall IEQ Satisfaction", fontsize=17, fontweight="bold", y=0.992)

    positions = [1, 2, 3, 4, 5]
    for ax, (column, label) in zip(axes, ENVIRONMENTAL_FEATURES):
        grouped = [
            plot_data.loc[plot_data["IEQSatisfaction"] == vote, column].dropna().to_numpy()
            for vote in positions
        ]
        ax.boxplot(
            grouped,
            positions=positions,
            widths=0.48,
            patch_artist=True,
            showfliers=False,
            medianprops={"color": COLORS["border"], "linewidth": 1.35},
            boxprops={"facecolor": "#BFD8F6", "edgecolor": COLORS["dark_blue"], "linewidth": 1.0},
            whiskerprops={"color": COLORS["dark_blue"], "linewidth": 0.95},
            capprops={"color": COLORS["dark_blue"], "linewidth": 0.95},
        )
        ax.set_title(label, loc="left", fontsize=11.5, fontweight="bold", pad=6)
        ax.set_ylabel(label, fontsize=10.5)
        ax.grid(axis="y", color=COLORS["grid"], alpha=0.85)
        ax.grid(axis="x", visible=False)
        for spine in ("top", "right"):
            ax.spines[spine].set_visible(False)
        ax.spines["left"].set_color(COLORS["axis"])
        ax.spines["bottom"].set_color(COLORS["axis"])
        ax.tick_params(axis="both", labelsize=9.5)

    axes[-1].set_xlabel("Overall IEQ satisfaction vote", fontsize=11)
    axes[-1].set_xticks(positions)
    fig.subplots_adjust(left=0.11, right=0.985, top=0.94, bottom=0.075, hspace=0.58)
    save_article_figure(fig, "fig_05_ieq_environmental_feature_boxplots")
    plt.close(fig)


def main() -> None:
    apply_paper_style()
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)

    raw_data = read_raw_data()
    plot_raw_completeness(raw_data)
    for feature_set in FEATURE_SETS:
        plot_feature_completeness(feature_set)
    plot_satisfaction_distribution(raw_data)
    plot_unified_satisfaction_distribution(raw_data)
    plot_article_target_distributions(raw_data)
    plot_environmental_boxplots(raw_data)

    print(f"Wrote article figures to {FIGURE_DIR}")


if __name__ == "__main__":
    main()
