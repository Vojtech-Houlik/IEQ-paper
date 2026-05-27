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
DATASET_DIR = ROOT.parent / "02_Datasets" / "clean"
apply_paper_style()


@dataclass(frozen=True)
class PaperDataset:
    name: str
    title: str
    dataset_path: Path
    figure_dir: Path
    table_dir: Path
    target: str
    inputs: tuple[str, ...]
    slug: str


PAPERS = [
    PaperDataset(
        name="thermal",
        title="Thermal Comfort Dataset",
        dataset_path=DATASET_DIR / "thermal_comfort_clean_dataset.xlsx",
        figure_dir=ROOT / "thermal_comfort_paper" / "04_outputs" / "figures",
        table_dir=ROOT / "thermal_comfort_paper" / "04_outputs" / "tables",
        target="Thermal satisfaction",
        inputs=(
            "Temperature",
            "RH",
            "CLO",
            "Age",
            "Gender",
            "EA",
            "LocationBack",
            "LocationFront",
            "LocationLeft",
            "LocationRight",
            "LocationMiddle",
            "Ttrend",
            "Vote hour",
            "Vote weekday",
            "Moment",
            "AC on/off",
        ),
        slug="thermal_comfort",
    ),
    PaperDataset(
        name="ieq",
        title="IEQ Dataset",
        dataset_path=DATASET_DIR / "ieq_clean_dataset.xlsx",
        figure_dir=ROOT / "ieq_paper" / "02_outputs" / "figures",
        table_dir=ROOT / "ieq_paper" / "02_outputs" / "tables",
        target="IEQ satisfaction",
        inputs=(
            "Temperature",
            "RH",
            "CLO",
            "CO2",
            "Lighting",
            "Sound",
            "Age",
            "Gender",
            "EA",
            "LocationBack",
            "LocationFront",
            "LocationLeft",
            "LocationRight",
            "LocationMiddle",
            "Ttrend",
            "Vote hour",
            "Vote weekday",
            "Moment",
            "AC on/off",
        ),
        slug="ieq",
    ),
]


def completeness_table(data: pd.DataFrame, paper: PaperDataset) -> pd.DataFrame:
    rows = []
    columns = [paper.target, *paper.inputs]
    for column in columns:
        complete_rows = int(data[column].notna().sum())
        total_rows = int(len(data))
        role = "Output" if column == paper.target else "Input"
        rows.append(
            {
                "feature": column,
                "role": role,
                "complete_rows": complete_rows,
                "missing_rows": total_rows - complete_rows,
                "total_rows": total_rows,
                "completeness_percent": complete_rows / total_rows * 100 if total_rows else 0.0,
            }
        )
    return pd.DataFrame(rows)


def complete_case_table(data: pd.DataFrame, paper: PaperDataset) -> pd.DataFrame:
    target_mask = data[paper.target].notna()
    input_mask = data[list(paper.inputs)].notna().all(axis=1)
    target_input_mask = target_mask & input_mask
    total_rows = int(len(data))
    rows = [
        ("Target available", int(target_mask.sum())),
        ("All inputs complete", int(input_mask.sum())),
        ("Target + all inputs complete", int(target_input_mask.sum())),
    ]
    return pd.DataFrame(
        [
            {
                "case_definition": name,
                "complete_rows": count,
                "missing_or_incomplete_rows": total_rows - count,
                "total_rows": total_rows,
                "complete_percent": count / total_rows * 100 if total_rows else 0.0,
            }
            for name, count in rows
        ]
    )


def plot_feature_completeness(table: pd.DataFrame, paper: PaperDataset, output_path: Path) -> None:
    plot_df = table.sort_values("completeness_percent", ascending=True).reset_index(drop=True)
    colors = [color_for_completeness(row.completeness_percent, row.role) for row in plot_df.itertuples()]

    fig_height = max(5.6, 0.42 * len(plot_df) + 1.9)
    fig, ax = plt.subplots(figsize=(10.6, fig_height))
    bars = ax.barh(
        plot_df["feature"],
        plot_df["completeness_percent"],
        color=colors,
        edgecolor=COLORS["border"],
        linewidth=0.55,
    )
    ax.set_title(f"Feature Completeness: {paper.title}", fontsize=18, fontweight="bold", pad=18)
    ax.set_xlabel("Completeness (% of all rows)", fontsize=11.5)
    ax.set_xlim(0, 100)
    ax.grid(axis="x", color=COLORS["grid"], alpha=0.85)
    ax.set_axisbelow(True)
    ax.tick_params(axis="y", length=0, labelsize=10.5)
    ax.tick_params(axis="x", labelsize=10)
    for spine in ("top", "right", "left"):
        ax.spines[spine].set_visible(False)
    ax.spines["bottom"].set_color(COLORS["axis"])

    for bar, row in zip(bars, plot_df.itertuples()):
        percent = row.completeness_percent
        label = f"{percent:.1f}%"
        x = min(percent + 1.2, 98.5)
        ha = "left" if percent < 92 else "right"
        if percent >= 92:
            x = percent - 1.2
        ax.text(
            x,
            bar.get_y() + bar.get_height() / 2,
            label,
            va="center",
            ha=ha,
            fontsize=9.5,
            color=COLORS["text"],
        )

    fig.tight_layout()
    save_figure(fig, output_path)
    plt.close(fig)


def plot_complete_cases(table: pd.DataFrame, paper: PaperDataset, output_path: Path) -> None:
    plot_df = table.iloc[::-1].reset_index(drop=True)
    colors = [color_for_completeness(value) for value in plot_df["complete_percent"]]

    fig, ax = plt.subplots(figsize=(9.4, 4.8))
    bars = ax.barh(
        plot_df["case_definition"],
        plot_df["complete_percent"],
        color=colors,
        edgecolor=COLORS["border"],
        linewidth=0.55,
    )
    ax.set_title(f"Complete-Case Availability\n{paper.title}", fontsize=16, fontweight="bold", pad=16)
    ax.set_xlabel("Complete rows (% of all rows)", fontsize=11.5)
    ax.set_xlim(0, 100)
    ax.grid(axis="x", color=COLORS["grid"], alpha=0.85)
    ax.set_axisbelow(True)
    ax.tick_params(axis="y", length=0, labelsize=10.5)
    for spine in ("top", "right", "left"):
        ax.spines[spine].set_visible(False)
    ax.spines["bottom"].set_color(COLORS["axis"])

    total_rows = int(plot_df["total_rows"].iloc[0])
    for bar, row in zip(bars, plot_df.itertuples()):
        percent = row.complete_percent
        label = f"{row.complete_rows:,} rows ({percent:.1f}%)"
        x = min(percent + 1.2, 98.5)
        ha = "left" if percent < 82 else "right"
        if percent >= 82:
            x = percent - 1.2
        ax.text(
            x,
            bar.get_y() + bar.get_height() / 2,
            label,
            va="center",
            ha=ha,
            fontsize=10,
            color=COLORS["text"],
        )
    fig.text(
        0.52,
        0.045,
        f"Total rows: {total_rows:,}. Missing values are not imputed or removed in this Step 1 dataset.",
        ha="center",
        va="bottom",
        fontsize=9.5,
        color=COLORS["muted_text"],
    )

    fig.subplots_adjust(left=0.29, right=0.98, bottom=0.22, top=0.76)
    save_figure(fig, output_path)
    plt.close(fig)


def process_paper(paper: PaperDataset) -> None:
    paper.figure_dir.mkdir(parents=True, exist_ok=True)
    paper.table_dir.mkdir(parents=True, exist_ok=True)

    data = pd.read_excel(paper.dataset_path, sheet_name="data")
    missing_columns = [column for column in [paper.target, *paper.inputs] if column not in data.columns]
    if missing_columns:
        raise ValueError(f"{paper.name}: missing columns in clean dataset: {missing_columns}")

    feature_table = completeness_table(data, paper)
    complete_cases = complete_case_table(data, paper)

    feature_table.to_csv(paper.table_dir / f"feature_completeness_{paper.slug}.csv", index=False)
    complete_cases.to_csv(paper.table_dir / f"complete_case_availability_{paper.slug}.csv", index=False)

    plot_feature_completeness(
        feature_table,
        paper,
        paper.figure_dir / f"01_feature_completeness_{paper.slug}",
    )
    plot_complete_cases(
        complete_cases,
        paper,
        paper.figure_dir / f"02_complete_case_availability_{paper.slug}",
    )

    print(f"{paper.title}:")
    print(feature_table[["feature", "role", "completeness_percent", "missing_rows"]].to_string(index=False))
    print(complete_cases.to_string(index=False))


def main() -> None:
    for paper in PAPERS:
        process_paper(paper)


if __name__ == "__main__":
    main()
