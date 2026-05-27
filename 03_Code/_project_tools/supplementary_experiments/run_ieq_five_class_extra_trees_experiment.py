from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

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


CODE_ROOT = Path(__file__).resolve().parents[2]
PROJECT_ROOT = CODE_ROOT.parent
DATASET_DIR = PROJECT_ROOT / "02_Datasets"
IEQ_MODEL_READY = DATASET_DIR / "model_ready" / "ieq_model_dataset.xlsx"
IEQ_CLEAN = DATASET_DIR / "clean" / "ieq_clean_dataset.xlsx"
BASELINE_SUMMARY_PATH = CODE_ROOT / "ieq_paper" / "02_outputs" / "tables" / "tuned_model_comparison_5fold_summary.csv"
OUTPUT_ROOT = CODE_ROOT / "ieq_paper" / "02_outputs" / "supplementary_experiments"
TABLE_DIR = OUTPUT_ROOT / "tables"
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


def collapse_to_three_class(values: pd.Series) -> pd.Series:
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


def five_class_metric_row(y_true: pd.Series, y_pred: pd.Series) -> dict[str, float]:
    return {
        "accuracy": accuracy_score(y_true, y_pred),
        "balanced_accuracy": balanced_accuracy_score(y_true, y_pred),
        "macro_f1": f1_score(y_true, y_pred, average="macro", labels=FIVE_CLASS_ORDER),
        "weighted_f1": f1_score(y_true, y_pred, average="weighted", labels=FIVE_CLASS_ORDER),
        "ordinal_mae": mean_absolute_error(y_true.astype(int), pd.Series(y_pred).astype(int)),
    }


def three_class_metric_row(y_true: pd.Series, y_pred: pd.Series) -> dict[str, float]:
    true_three = collapse_to_three_class(y_true)
    pred_three = collapse_to_three_class(y_pred)
    true_ordinal = true_three.map(THREE_CLASS_ORDINAL_MAP).to_numpy()
    pred_ordinal = pred_three.map(THREE_CLASS_ORDINAL_MAP).to_numpy()
    return {
        "collapsed_accuracy": accuracy_score(true_three, pred_three),
        "collapsed_balanced_accuracy": balanced_accuracy_score(true_three, pred_three),
        "collapsed_macro_f1": f1_score(
            true_three,
            pred_three,
            average="macro",
            labels=THREE_CLASS_ORDER,
        ),
        "collapsed_weighted_f1": f1_score(
            true_three,
            pred_three,
            average="weighted",
            labels=THREE_CLASS_ORDER,
        ),
        "collapsed_ordinal_mae": mean_absolute_error(true_ordinal, pred_ordinal),
    }


def summarize_folds(folds: pd.DataFrame) -> pd.DataFrame:
    metric_columns = [
        "accuracy",
        "balanced_accuracy",
        "macro_f1",
        "weighted_f1",
        "ordinal_mae",
        "collapsed_accuracy",
        "collapsed_balanced_accuracy",
        "collapsed_macro_f1",
        "collapsed_weighted_f1",
        "collapsed_ordinal_mae",
        "fit_seconds",
        "predict_seconds",
        "total_seconds",
    ]
    summary = folds[metric_columns].agg(["mean", "std"]).T
    summary.columns = ["mean", "std"]
    row = {"experiment": "ieq_five_class_extra_trees", "model": "Extra Trees"}
    for metric, values in summary.iterrows():
        row[f"{metric}_mean"] = values["mean"]
        row[f"{metric}_std"] = values["std"]
    return pd.DataFrame([row])


def target_distribution(y: pd.Series) -> pd.DataFrame:
    counts = y.value_counts().reindex(FIVE_CLASS_ORDER, fill_value=0)
    distribution = counts.rename_axis("class").reset_index(name="rows")
    distribution["percent"] = distribution["rows"] / len(y) * 100
    distribution["three_class_mapping"] = collapse_to_three_class(distribution["class"])
    return distribution


def per_class_metrics(y_true: pd.Series, y_pred: pd.Series) -> pd.DataFrame:
    precision, recall, f1, support = precision_recall_fscore_support(
        y_true,
        y_pred,
        labels=FIVE_CLASS_ORDER,
        zero_division=0,
    )
    return pd.DataFrame(
        {
            "class": FIVE_CLASS_ORDER,
            "precision": precision,
            "recall": recall,
            "f1": f1,
            "support": support,
            "three_class_mapping": collapse_to_three_class(pd.Series(FIVE_CLASS_ORDER)),
        }
    )


def confusion_matrix_table(y_true: pd.Series, y_pred: pd.Series) -> pd.DataFrame:
    matrix = confusion_matrix(y_true, y_pred, labels=FIVE_CLASS_ORDER)
    rows = []
    for true_index, true_label in enumerate(FIVE_CLASS_ORDER):
        for pred_index, predicted_label in enumerate(FIVE_CLASS_ORDER):
            rows.append(
                {
                    "true_label": true_label,
                    "predicted_label": predicted_label,
                    "rows": int(matrix[true_index, pred_index]),
                }
            )
    return pd.DataFrame(rows)


def load_data() -> tuple[pd.DataFrame, pd.Series, pd.Series]:
    model_data = pd.read_excel(IEQ_MODEL_READY, sheet_name="data")
    clean_data = pd.read_excel(IEQ_CLEAN, sheet_name="data")
    if len(model_data) != len(clean_data):
        raise ValueError("IEQ clean and model-ready row counts differ")

    y_five = clean_data[FIVE_CLASS_TARGET].astype(int)
    expected_three = collapse_to_three_class(y_five)
    actual_three = model_data[THREE_CLASS_TARGET].astype(str)
    if not expected_three.reset_index(drop=True).equals(actual_three.reset_index(drop=True)):
        raise ValueError("Five-class target does not collapse to the model-ready three-class target")

    feature_columns = [column for column in model_data.columns if column not in DROP_FROM_FEATURES]
    return model_data[feature_columns], y_five, actual_three


def evaluate() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    X, y, y_three = load_data()
    params = extra_trees_params()
    base_pipeline = build_pipeline(X, params)
    cv = StratifiedKFold(n_splits=EVALUATION_SPLITS, shuffle=True, random_state=SEED)

    fold_rows = []
    prediction_rows = []

    for fold, (train_index, test_index) in enumerate(cv.split(X, y), start=1):
        pipeline = clone(base_pipeline)
        if "model__random_state" in pipeline.get_params():
            pipeline.set_params(model__random_state=SEED + fold)

        X_train, X_test = X.iloc[train_index], X.iloc[test_index]
        y_train, y_test = y.iloc[train_index], y.iloc[test_index]

        fit_start = time.perf_counter()
        pipeline.fit(X_train, y_train)
        fit_seconds = time.perf_counter() - fit_start

        predict_start = time.perf_counter()
        y_pred = pd.Series(pipeline.predict(X_test), index=y_test.index).astype(int)
        predict_seconds = time.perf_counter() - predict_start

        metrics = {
            **five_class_metric_row(y_test, y_pred),
            **three_class_metric_row(y_test, y_pred),
        }
        fold_row = {
            "experiment": "ieq_five_class_extra_trees",
            "model": "Extra Trees",
            "fold": fold,
            "rows": len(y_test),
            "predictors": X.shape[1],
            "fit_seconds": fit_seconds,
            "predict_seconds": predict_seconds,
            "total_seconds": fit_seconds + predict_seconds,
            **metrics,
        }
        fold_rows.append(fold_row)
        prediction_rows.append(
            pd.DataFrame(
                {
                    "experiment": "ieq_five_class_extra_trees",
                    "model": "Extra Trees",
                    "fold": fold,
                    "row_index": test_index,
                    "true_label": y_test.to_numpy(),
                    "predicted_label": y_pred.to_numpy(),
                    "true_label_3class": y_three.iloc[test_index].to_numpy(),
                    "predicted_label_3class": collapse_to_three_class(y_pred).to_numpy(),
                }
            )
        )
        print(
            f"fold {fold}: 5-class macro_f1={fold_row['macro_f1']:.3f}, "
            f"accuracy={fold_row['accuracy']:.3f}, ordinal_mae={fold_row['ordinal_mae']:.3f}; "
            f"collapsed macro_f1={fold_row['collapsed_macro_f1']:.3f}",
            flush=True,
        )

    folds = pd.DataFrame(fold_rows)
    predictions = pd.concat(prediction_rows, ignore_index=True).sort_values("row_index")
    summary = summarize_folds(folds)
    summary.insert(2, "rows", len(y))
    summary.insert(3, "predictors", X.shape[1])
    distribution = target_distribution(y)
    class_metrics = per_class_metrics(predictions["true_label"], predictions["predicted_label"])
    confusion = confusion_matrix_table(predictions["true_label"], predictions["predicted_label"])
    return summary, folds, predictions, distribution, class_metrics, confusion


def write_note(summary: pd.DataFrame, distribution: pd.DataFrame, paths: dict[str, Path]) -> None:
    row = summary.iloc[0]
    lines = [
        "# IEQ Five-Class Extra Trees Check",
        "",
        "This supplementary experiment reruns the current best IEQ Extra Trees model with the original five-point `IEQ satisfaction` target instead of the paper-facing three-class target.",
        "",
        "Design:",
        "",
        "- Same model-ready predictor table as the three-class IEQ model.",
        "- Same tuned Extra Trees hyperparameters as the current best three-class model.",
        "- Five-fold stratified cross-validation on the five-class target.",
        "- No five-class-specific hyperparameter retuning.",
        "",
        "Target distribution:",
        "",
    ]
    for _, dist_row in distribution.iterrows():
        lines.append(
            f"- Class {int(dist_row['class'])}: {int(dist_row['rows'])} rows ({dist_row['percent']:.1f}%), maps to `{dist_row['three_class_mapping']}`."
        )
    lines.extend(
        [
            "",
            "Headline result:",
            "",
            f"- Five-class Extra Trees: accuracy={row['accuracy_mean']:.3f}, macro F1={row['macro_f1_mean']:.3f}, weighted F1={row['weighted_f1_mean']:.3f}, ordinal MAE={row['ordinal_mae_mean']:.3f}.",
            f"- The same five-class predictions collapsed back to three classes: accuracy={row['collapsed_accuracy_mean']:.3f}, macro F1={row['collapsed_macro_f1_mean']:.3f}, ordinal MAE={row['collapsed_ordinal_mae_mean']:.3f}.",
            "",
            "Output files:",
            "",
            f"- `{paths['summary'].relative_to(CODE_ROOT)}`",
            f"- `{paths['folds'].relative_to(CODE_ROOT)}`",
            f"- `{paths['predictions'].relative_to(CODE_ROOT)}`",
            f"- `{paths['distribution'].relative_to(CODE_ROOT)}`",
            f"- `{paths['per_class'].relative_to(CODE_ROOT)}`",
            f"- `{paths['confusion'].relative_to(CODE_ROOT)}`",
        ]
    )
    paths["note"].write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    TABLE_DIR.mkdir(parents=True, exist_ok=True)
    NOTE_DIR.mkdir(parents=True, exist_ok=True)

    summary, folds, predictions, distribution, class_metrics, confusion = evaluate()

    paths = {
        "summary": TABLE_DIR / "ieq_five_class_extra_trees_summary.csv",
        "folds": TABLE_DIR / "ieq_five_class_extra_trees_folds.csv",
        "predictions": TABLE_DIR / "ieq_five_class_extra_trees_predictions.csv",
        "distribution": TABLE_DIR / "ieq_five_class_target_distribution.csv",
        "per_class": TABLE_DIR / "ieq_five_class_extra_trees_per_class_metrics.csv",
        "confusion": TABLE_DIR / "ieq_five_class_extra_trees_confusion_matrix.csv",
        "note": NOTE_DIR / "ieq_five_class_extra_trees_note.md",
    }

    summary.to_csv(paths["summary"], index=False)
    folds.to_csv(paths["folds"], index=False)
    predictions.to_csv(paths["predictions"], index=False)
    distribution.to_csv(paths["distribution"], index=False)
    class_metrics.to_csv(paths["per_class"], index=False)
    confusion.to_csv(paths["confusion"], index=False)
    write_note(summary, distribution, paths)

    display_columns = [
        "accuracy_mean",
        "balanced_accuracy_mean",
        "macro_f1_mean",
        "weighted_f1_mean",
        "ordinal_mae_mean",
        "collapsed_accuracy_mean",
        "collapsed_macro_f1_mean",
        "collapsed_ordinal_mae_mean",
    ]
    print("\nFive-class Extra Trees summary")
    print(summary[display_columns].to_string(index=False))
    print("\nPer-class metrics")
    print(class_metrics.to_string(index=False))
    for label, path in paths.items():
        print(f"Saved {label}: {path}")


if __name__ == "__main__":
    main()
