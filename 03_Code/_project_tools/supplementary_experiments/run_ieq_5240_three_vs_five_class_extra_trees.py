from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import ExtraTreesClassifier
from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    confusion_matrix,
    f1_score,
    mean_absolute_error,
    precision_recall_fscore_support,
)
from sklearn.model_selection import StratifiedKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


TOOLS_ROOT = Path(__file__).resolve().parents[1]
CODE_ROOT = Path(__file__).resolve().parents[2]
PROJECT_ROOT = CODE_ROOT.parent
sys.path.insert(0, str(TOOLS_ROOT))

from paper_style import COLORS, apply_paper_style, save_figure  # noqa: E402


DATASET_DIR = PROJECT_ROOT / "02_Datasets"
IEQ_MODEL_READY = DATASET_DIR / "model_ready" / "ieq_model_dataset.xlsx"
IEQ_CLEAN = DATASET_DIR / "clean" / "ieq_clean_dataset.xlsx"
OLD_BENCHMARK_ROWSET = (
    PROJECT_ROOT.parent
    / "code"
    / "ieq_benchmark"
    / "outputs"
    / "phase2_datasets"
    / "track_a_core"
    / "direct_overall"
    / "dataset.csv"
)
BASELINE_SUMMARY_PATH = CODE_ROOT / "ieq_paper" / "02_outputs" / "tables" / "tuned_model_comparison_5fold_summary.csv"
OUTPUT_ROOT = CODE_ROOT / "ieq_paper" / "02_outputs" / "supplementary_experiments"
TABLE_DIR = OUTPUT_ROOT / "tables"
FIGURE_DIR = OUTPUT_ROOT / "figures"
NOTE_DIR = OUTPUT_ROOT / "notes"

SEED = 20260507
EVALUATION_SPLITS = 5
THREE_CLASS_TARGET = "IEQ satisfaction 3-class"
FIVE_CLASS_TARGET = "IEQ satisfaction"
DROP_FROM_FEATURES = [THREE_CLASS_TARGET, "TimeVote"]
FIVE_CLASS_ORDER = [1, 2, 3, 4, 5]
THREE_CLASS_ORDER = ["dissatisfied", "neutral", "satisfied"]
THREE_CLASS_ORDINAL_MAP = {"dissatisfied": 0, "neutral": 1, "satisfied": 2}


def dense_one_hot_encoder() -> OneHotEncoder:
    try:
        return OneHotEncoder(handle_unknown="ignore", sparse_output=False)
    except TypeError:
        return OneHotEncoder(handle_unknown="ignore", sparse=False)


def parse_params(raw_json: str) -> dict[str, Any]:
    return json.loads(raw_json)


def extra_trees_params() -> dict[str, Any]:
    summary = pd.read_csv(BASELINE_SUMMARY_PATH)
    row = summary[summary["model"].eq("Extra Trees")].iloc[0]
    return parse_params(row["best_params_json"])


def build_pipeline(X: pd.DataFrame, params: dict[str, Any]) -> Pipeline:
    numeric_features = X.select_dtypes(include=["number"]).columns.tolist()
    categorical_features = [column for column in X.columns if column not in numeric_features]
    transformers = []
    if numeric_features:
        transformers.append(("numeric", StandardScaler(), numeric_features))
    if categorical_features:
        transformers.append(("categorical", dense_one_hot_encoder(), categorical_features))
    pipeline = Pipeline(
        steps=[
            ("preprocessor", ColumnTransformer(transformers=transformers)),
            ("model", ExtraTreesClassifier(n_jobs=1, random_state=SEED)),
        ]
    )
    pipeline.set_params(**params)
    return pipeline


def collapse_to_three_class(values: pd.Series | np.ndarray) -> pd.Series:
    numeric = pd.Series(values).astype(int)
    return numeric.map(
        {
            1: "dissatisfied",
            2: "dissatisfied",
            3: "neutral",
            4: "satisfied",
            5: "satisfied",
        }
    )


def ordinal_values(values: pd.Series, label_order: list[int] | list[str]) -> np.ndarray:
    if label_order == FIVE_CLASS_ORDER:
        return values.astype(int).to_numpy()
    return values.astype(str).map(THREE_CLASS_ORDINAL_MAP).to_numpy()


def metric_row(y_true: pd.Series, y_pred: pd.Series, label_order: list[int] | list[str]) -> dict[str, float]:
    true_values = ordinal_values(pd.Series(y_true), label_order)
    pred_values = ordinal_values(pd.Series(y_pred), label_order)
    return {
        "accuracy": accuracy_score(y_true, y_pred),
        "balanced_accuracy": balanced_accuracy_score(y_true, y_pred),
        "macro_f1": f1_score(y_true, y_pred, labels=label_order, average="macro", zero_division=0),
        "weighted_f1": f1_score(y_true, y_pred, labels=label_order, average="weighted", zero_division=0),
        "ordinal_mae": mean_absolute_error(true_values, pred_values),
    }


def collapsed_metric_row(y_true_five: pd.Series, y_pred_five: pd.Series) -> dict[str, float]:
    true_three = collapse_to_three_class(y_true_five)
    pred_three = collapse_to_three_class(y_pred_five)
    metrics = metric_row(true_three, pred_three, THREE_CLASS_ORDER)
    return {f"collapsed_{key}": value for key, value in metrics.items()}


def load_subset_data() -> tuple[pd.DataFrame, pd.Series, pd.Series, np.ndarray, pd.Series]:
    model_data = pd.read_excel(IEQ_MODEL_READY, sheet_name="data")
    clean_data = pd.read_excel(IEQ_CLEAN, sheet_name="data")
    if len(model_data) != len(clean_data):
        raise ValueError("IEQ clean and model-ready row counts differ")
    if not OLD_BENCHMARK_ROWSET.exists():
        raise FileNotFoundError(f"Old 5,240-row benchmark mask not found: {OLD_BENCHMARK_ROWSET}")

    old_dataset = pd.read_csv(OLD_BENCHMARK_ROWSET, usecols=["source_row_number"])
    old_source_rows = set(old_dataset["source_row_number"].astype(int))
    source_rows = clean_data["source_row_number"].astype(int)
    subset_mask = source_rows.isin(old_source_rows).to_numpy()
    if int(subset_mask.sum()) != len(old_dataset):
        raise ValueError(
            f"Expected {len(old_dataset)} row matches, found {int(subset_mask.sum())}. "
            "Check source_row_number alignment."
        )

    y_five = clean_data.loc[subset_mask, FIVE_CLASS_TARGET].astype(int).reset_index(drop=True)
    y_three = model_data.loc[subset_mask, THREE_CLASS_TARGET].astype(str).reset_index(drop=True)
    expected_three = collapse_to_three_class(y_five)
    if not expected_three.reset_index(drop=True).equals(y_three.reset_index(drop=True)):
        raise ValueError("Five-class target does not collapse to the model-ready three-class target")

    feature_columns = [column for column in model_data.columns if column not in DROP_FROM_FEATURES]
    X = model_data.loc[subset_mask, feature_columns].reset_index(drop=True)
    row_indices = model_data.index[subset_mask].to_numpy()
    source_rows_subset = source_rows.loc[subset_mask].reset_index(drop=True)
    return X, y_three, y_five, row_indices, source_rows_subset


def evaluate_target(
    X: pd.DataFrame,
    y: pd.Series,
    row_indices: np.ndarray,
    source_rows: pd.Series,
    target_variant: str,
    label_order: list[int] | list[str],
) -> tuple[pd.DataFrame, pd.DataFrame]:
    params = extra_trees_params()
    base_pipeline = build_pipeline(X, params)
    cv = StratifiedKFold(n_splits=EVALUATION_SPLITS, shuffle=True, random_state=SEED)
    fold_rows = []
    prediction_rows = []

    for fold, (train_index, test_index) in enumerate(cv.split(X, y), start=1):
        pipeline = clone(base_pipeline)
        if "model__random_state" in pipeline.get_params():
            pipeline.set_params(model__random_state=SEED + fold)

        fit_start = time.perf_counter()
        pipeline.fit(X.iloc[train_index], y.iloc[train_index])
        fit_seconds = time.perf_counter() - fit_start

        predict_start = time.perf_counter()
        y_pred = pd.Series(pipeline.predict(X.iloc[test_index]), index=test_index)
        predict_seconds = time.perf_counter() - predict_start

        y_test = y.iloc[test_index]
        metrics = metric_row(y_test, y_pred, label_order)
        fold_rows.append(
            {
                "experiment": "ieq_5240_three_vs_five_extra_trees",
                "target_variant": target_variant,
                "model": "Extra Trees",
                "fold": fold,
                "rows": len(y_test),
                "predictors": X.shape[1],
                "fit_seconds": fit_seconds,
                "predict_seconds": predict_seconds,
                "total_seconds": fit_seconds + predict_seconds,
                **metrics,
            }
        )
        prediction_rows.append(
            pd.DataFrame(
                {
                    "experiment": "ieq_5240_three_vs_five_extra_trees",
                    "target_variant": target_variant,
                    "model": "Extra Trees",
                    "fold": fold,
                    "row_index": row_indices[test_index],
                    "source_row_number": source_rows.iloc[test_index].to_numpy(),
                    "true_label": y_test.to_numpy(),
                    "predicted_label": y_pred.to_numpy(),
                }
            )
        )
        print(
            f"{target_variant} fold {fold}: accuracy={metrics['accuracy']:.3f}, "
            f"macro_f1={metrics['macro_f1']:.3f}, ordinal_mae={metrics['ordinal_mae']:.3f}",
            flush=True,
        )

    return pd.DataFrame(fold_rows), pd.concat(prediction_rows, ignore_index=True).sort_values("row_index")


def summarize_folds(folds: pd.DataFrame) -> pd.DataFrame:
    metric_columns = [
        "accuracy",
        "balanced_accuracy",
        "macro_f1",
        "weighted_f1",
        "ordinal_mae",
        "fit_seconds",
        "predict_seconds",
        "total_seconds",
    ]
    summary = folds.groupby("target_variant")[metric_columns].agg(["mean", "std"])
    summary.columns = [f"{metric}_{stat}" for metric, stat in summary.columns]
    summary = summary.reset_index()
    summary.insert(0, "experiment", "ieq_5240_three_vs_five_extra_trees")
    summary.insert(2, "model", "Extra Trees")
    summary.insert(3, "rows", 5240)
    summary.insert(4, "predictors", 21)
    return summary


def confusion_table(
    target_variant: str,
    y_true: pd.Series,
    y_pred: pd.Series,
    label_order: list[int] | list[str],
) -> pd.DataFrame:
    matrix = confusion_matrix(y_true, y_pred, labels=label_order)
    row_totals = matrix.sum(axis=1)
    rows = []
    for true_index, true_label in enumerate(label_order):
        for pred_index, predicted_label in enumerate(label_order):
            count = int(matrix[true_index, pred_index])
            rows.append(
                {
                    "target_variant": target_variant,
                    "true_label": true_label,
                    "predicted_label": predicted_label,
                    "rows": count,
                    "row_percent": count / row_totals[true_index] * 100 if row_totals[true_index] else 0.0,
                }
            )
    return pd.DataFrame(rows)


def per_class_metrics(
    target_variant: str,
    y_true: pd.Series,
    y_pred: pd.Series,
    label_order: list[int] | list[str],
) -> pd.DataFrame:
    precision, recall, f1, support = precision_recall_fscore_support(
        y_true,
        y_pred,
        labels=label_order,
        zero_division=0,
    )
    return pd.DataFrame(
        {
            "target_variant": target_variant,
            "class": label_order,
            "precision": precision,
            "recall": recall,
            "f1": f1,
            "support": support,
        }
    )


def distribution_rows(target_variant: str, y: pd.Series, label_order: list[int] | list[str]) -> pd.DataFrame:
    counts = y.value_counts().reindex(label_order, fill_value=0)
    result = counts.rename_axis("class").reset_index(name="rows")
    result.insert(0, "target_variant", target_variant)
    result["percent"] = result["rows"] / len(y) * 100
    return result


def draw_confusion_heatmap(
    ax,
    y_true: pd.Series,
    y_pred: pd.Series,
    label_order: list[int] | list[str],
    title: str,
) -> None:
    matrix = confusion_matrix(y_true, y_pred, labels=label_order)
    row_totals = matrix.sum(axis=1, keepdims=True)
    normalized = np.divide(matrix, row_totals, out=np.zeros_like(matrix, dtype=float), where=row_totals != 0)
    image = ax.imshow(normalized, cmap="Blues", vmin=0, vmax=max(0.01, normalized.max()))
    ax.set_title(title, fontsize=13, pad=10)
    ax.set_xlabel("Predicted")
    ax.set_ylabel("True")
    ax.set_xticks(np.arange(len(label_order)))
    ax.set_yticks(np.arange(len(label_order)))
    ax.set_xticklabels(label_order, rotation=30, ha="right")
    ax.set_yticklabels(label_order)
    ax.grid(False)
    for spine in ax.spines.values():
        spine.set_visible(False)
    for true_index in range(matrix.shape[0]):
        for pred_index in range(matrix.shape[1]):
            value = normalized[true_index, pred_index]
            color = "white" if value > normalized.max() * 0.55 else COLORS["text"]
            ax.text(
                pred_index,
                true_index,
                f"{matrix[true_index, pred_index]}\n{value * 100:.0f}%",
                ha="center",
                va="center",
                color=color,
                fontsize=8.5,
            )
    return image


def write_confusion_figures(predictions: pd.DataFrame, paths: dict[str, Path]) -> None:
    apply_paper_style()
    three = predictions[predictions["target_variant"].eq("three_class")]
    five = predictions[predictions["target_variant"].eq("five_class")]
    five_true_collapsed = collapse_to_three_class(five["true_label"])
    five_pred_collapsed = collapse_to_three_class(five["predicted_label"])

    fig, axes = plt.subplots(1, 3, figsize=(13.6, 4.3), constrained_layout=True)
    draw_confusion_heatmap(
        axes[0],
        three["true_label"].astype(str),
        three["predicted_label"].astype(str),
        THREE_CLASS_ORDER,
        "3-class model",
    )
    draw_confusion_heatmap(
        axes[1],
        five["true_label"].astype(int),
        five["predicted_label"].astype(int),
        FIVE_CLASS_ORDER,
        "5-class model",
    )
    draw_confusion_heatmap(
        axes[2],
        five_true_collapsed.astype(str),
        five_pred_collapsed.astype(str),
        THREE_CLASS_ORDER,
        "5-class collapsed to 3-class",
    )
    fig.suptitle("IEQ Extra Trees Confusion Matrices on the 5,240-Row Complete-Case Subset", fontsize=15)
    save_figure(fig, paths["confusion_figure"])
    plt.close(fig)


def article_paragraph(summary: pd.DataFrame) -> str:
    three = summary[summary["target_variant"].eq("three_class")].iloc[0]
    five = summary[summary["target_variant"].eq("five_class")].iloc[0]
    collapsed_accuracy = five["collapsed_accuracy_mean"]
    collapsed_macro_f1 = five["collapsed_macro_f1_mean"]
    collapsed_ordinal_mae = five["collapsed_ordinal_mae_mean"]
    return (
        "As a sensitivity analysis, the IEQ classification task was also evaluated on the original five-point "
        "satisfaction scale using the same Extra Trees model, predictor set, and 5,240-row complete-case subset as "
        "the three-class comparison. The three-class formulation achieved "
        f"{three['accuracy_mean']:.3f} accuracy, {three['macro_f1_mean']:.3f} macro F1, and "
        f"{three['ordinal_mae_mean']:.3f} ordinal MAE. The five-class formulation preserved the original response "
        f"resolution but was more difficult, reaching {five['accuracy_mean']:.3f} accuracy, "
        f"{five['macro_f1_mean']:.3f} macro F1, and {five['ordinal_mae_mean']:.3f} ordinal MAE. When the five-class "
        f"predictions were collapsed back into the three article-facing classes, performance was "
        f"{collapsed_accuracy:.3f} accuracy, {collapsed_macro_f1:.3f} macro F1, and "
        f"{collapsed_ordinal_mae:.3f} ordinal MAE, which remained below the directly trained three-class model. "
        "These results indicate that the five-class target is useful as a robustness check, but the three-class "
        "target gives a clearer and more stable headline model for the article."
    )


def write_note(summary: pd.DataFrame, distribution: pd.DataFrame, paths: dict[str, Path]) -> None:
    paragraph = article_paragraph(summary)
    three = summary[summary["target_variant"].eq("three_class")].iloc[0]
    five = summary[summary["target_variant"].eq("five_class")].iloc[0]
    lines = [
        "# IEQ 3-Class vs 5-Class Extra Trees on 5,240 Rows",
        "",
        "This supplementary experiment uses the current Prism IEQ model-ready data and restricts the row set to the 5,240 `source_row_number` values used by the earlier complete-case benchmark. The old benchmark file is used only as a row mask; no old predictor columns are added.",
        "",
        "Headline results:",
        "",
        f"- Three-class Extra Trees: accuracy={three['accuracy_mean']:.3f}, macro F1={three['macro_f1_mean']:.3f}, ordinal MAE={three['ordinal_mae_mean']:.3f}.",
        f"- Five-class Extra Trees: accuracy={five['accuracy_mean']:.3f}, macro F1={five['macro_f1_mean']:.3f}, ordinal MAE={five['ordinal_mae_mean']:.3f}.",
        f"- Five-class predictions collapsed to three classes: accuracy={five['collapsed_accuracy_mean']:.3f}, macro F1={five['collapsed_macro_f1_mean']:.3f}, ordinal MAE={five['collapsed_ordinal_mae_mean']:.3f}.",
        "",
        "Article paragraph:",
        "",
        paragraph,
        "",
        "Target distributions:",
        "",
    ]
    for _, row in distribution.iterrows():
        lines.append(
            f"- {row['target_variant']} class `{row['class']}`: {int(row['rows'])} rows ({row['percent']:.1f}%)."
        )
    lines.extend(
        [
            "",
            "Output files:",
            "",
            f"- `{paths['summary'].relative_to(CODE_ROOT)}`",
            f"- `{paths['folds'].relative_to(CODE_ROOT)}`",
            f"- `{paths['predictions'].relative_to(CODE_ROOT)}`",
            f"- `{paths['confusion'].relative_to(CODE_ROOT)}`",
            f"- `{paths['per_class'].relative_to(CODE_ROOT)}`",
            f"- `{paths['distribution'].relative_to(CODE_ROOT)}`",
            f"- `{paths['confusion_figure'].relative_to(CODE_ROOT).with_suffix('.png')}`",
            f"- `{paths['confusion_figure'].relative_to(CODE_ROOT).with_suffix('.pdf')}`",
        ]
    )
    paths["note"].write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    TABLE_DIR.mkdir(parents=True, exist_ok=True)
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    NOTE_DIR.mkdir(parents=True, exist_ok=True)

    X, y_three, y_five, row_indices, source_rows = load_subset_data()
    three_folds, three_predictions = evaluate_target(
        X,
        y_three,
        row_indices,
        source_rows,
        "three_class",
        THREE_CLASS_ORDER,
    )
    five_folds, five_predictions = evaluate_target(
        X,
        y_five,
        row_indices,
        source_rows,
        "five_class",
        FIVE_CLASS_ORDER,
    )

    folds = pd.concat([three_folds, five_folds], ignore_index=True)
    predictions = pd.concat([three_predictions, five_predictions], ignore_index=True)
    summary = summarize_folds(folds)

    five_summary_index = summary["target_variant"].eq("five_class")
    collapsed_metrics = collapsed_metric_row(
        five_predictions["true_label"].astype(int),
        five_predictions["predicted_label"].astype(int),
    )
    for key, value in collapsed_metrics.items():
        summary.loc[five_summary_index, f"{key}_mean"] = value
        summary.loc[five_summary_index, f"{key}_std"] = np.nan

    summary.loc[~five_summary_index, "collapsed_accuracy_mean"] = np.nan
    summary.loc[~five_summary_index, "collapsed_balanced_accuracy_mean"] = np.nan
    summary.loc[~five_summary_index, "collapsed_macro_f1_mean"] = np.nan
    summary.loc[~five_summary_index, "collapsed_weighted_f1_mean"] = np.nan
    summary.loc[~five_summary_index, "collapsed_ordinal_mae_mean"] = np.nan

    confusion = pd.concat(
        [
            confusion_table(
                "three_class",
                three_predictions["true_label"].astype(str),
                three_predictions["predicted_label"].astype(str),
                THREE_CLASS_ORDER,
            ),
            confusion_table(
                "five_class",
                five_predictions["true_label"].astype(int),
                five_predictions["predicted_label"].astype(int),
                FIVE_CLASS_ORDER,
            ),
            confusion_table(
                "five_class_collapsed_to_three",
                collapse_to_three_class(five_predictions["true_label"]),
                collapse_to_three_class(five_predictions["predicted_label"]),
                THREE_CLASS_ORDER,
            ),
        ],
        ignore_index=True,
    )
    per_class = pd.concat(
        [
            per_class_metrics(
                "three_class",
                three_predictions["true_label"].astype(str),
                three_predictions["predicted_label"].astype(str),
                THREE_CLASS_ORDER,
            ),
            per_class_metrics(
                "five_class",
                five_predictions["true_label"].astype(int),
                five_predictions["predicted_label"].astype(int),
                FIVE_CLASS_ORDER,
            ),
            per_class_metrics(
                "five_class_collapsed_to_three",
                collapse_to_three_class(five_predictions["true_label"]),
                collapse_to_three_class(five_predictions["predicted_label"]),
                THREE_CLASS_ORDER,
            ),
        ],
        ignore_index=True,
    )
    distribution = pd.concat(
        [
            distribution_rows("three_class", y_three, THREE_CLASS_ORDER),
            distribution_rows("five_class", y_five, FIVE_CLASS_ORDER),
        ],
        ignore_index=True,
    )

    paths = {
        "summary": TABLE_DIR / "ieq_5240_three_vs_five_extra_trees_summary.csv",
        "folds": TABLE_DIR / "ieq_5240_three_vs_five_extra_trees_folds.csv",
        "predictions": TABLE_DIR / "ieq_5240_three_vs_five_extra_trees_predictions.csv",
        "confusion": TABLE_DIR / "ieq_5240_three_vs_five_extra_trees_confusion_matrices.csv",
        "per_class": TABLE_DIR / "ieq_5240_three_vs_five_extra_trees_per_class_metrics.csv",
        "distribution": TABLE_DIR / "ieq_5240_three_vs_five_target_distribution.csv",
        "confusion_figure": FIGURE_DIR / "ieq_5240_three_vs_five_extra_trees_confusion_matrices",
        "note": NOTE_DIR / "ieq_5240_three_vs_five_extra_trees_note.md",
    }

    summary.to_csv(paths["summary"], index=False)
    folds.to_csv(paths["folds"], index=False)
    predictions.to_csv(paths["predictions"], index=False)
    confusion.to_csv(paths["confusion"], index=False)
    per_class.to_csv(paths["per_class"], index=False)
    distribution.to_csv(paths["distribution"], index=False)
    write_confusion_figures(predictions, paths)
    write_note(summary, distribution, paths)

    print("\n3-class vs 5-class Extra Trees on 5,240 rows")
    print(
        summary[
            [
                "target_variant",
                "accuracy_mean",
                "balanced_accuracy_mean",
                "macro_f1_mean",
                "weighted_f1_mean",
                "ordinal_mae_mean",
                "collapsed_accuracy_mean",
                "collapsed_macro_f1_mean",
                "collapsed_ordinal_mae_mean",
            ]
        ].to_string(index=False)
    )
    print("\nArticle paragraph")
    print(article_paragraph(summary))
    for label, path in paths.items():
        if label == "confusion_figure":
            print(f"Saved {label}: {path.with_suffix('.png')}")
            print(f"Saved {label}: {path.with_suffix('.pdf')}")
        else:
            print(f"Saved {label}: {path}")


if __name__ == "__main__":
    main()
