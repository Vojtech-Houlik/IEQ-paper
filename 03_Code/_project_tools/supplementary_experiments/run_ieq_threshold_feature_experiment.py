from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

import pandas as pd
from sklearn.base import clone
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import ExtraTreesClassifier
from sklearn.metrics import accuracy_score, balanced_accuracy_score, f1_score, mean_absolute_error
from sklearn.model_selection import StratifiedKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


CODE_ROOT = Path(__file__).resolve().parents[2]
PROJECT_ROOT = CODE_ROOT.parent
DATASET_PATH = PROJECT_ROOT / "02_Datasets" / "model_ready" / "ieq_model_dataset.xlsx"
BASELINE_SUMMARY_PATH = CODE_ROOT / "ieq_paper" / "02_outputs" / "tables" / "tuned_model_comparison_5fold_summary.csv"
OUTPUT_ROOT = CODE_ROOT / "ieq_paper" / "02_outputs" / "supplementary_experiments"
TABLE_DIR = OUTPUT_ROOT / "tables"
NOTE_DIR = OUTPUT_ROOT / "notes"

SEED = 20260507
EVALUATION_SPLITS = 5
TARGET = "IEQ satisfaction 3-class"
DROP_FROM_FEATURES = [TARGET, "TimeVote"]
ORDINAL_MAP = {"dissatisfied": 0, "neutral": 1, "satisfied": 2}

CO2_HIGH_THRESHOLD = 1000.0
TEMP_LOW_THRESHOLD = 18.0
TEMP_HIGH_THRESHOLD = 24.0

ENGINEERED_FEATURES = {
    "CO2_gt_1000ppm": {
        "formula": "CO2 > 1000 ppm",
        "unit": "binary",
        "group": "co2",
        "description": "High CO2 indicator.",
    },
    "Temperature_lt_18C": {
        "formula": "Temperature < 18 deg C",
        "unit": "binary",
        "group": "temperature",
        "description": "Low-temperature indicator.",
    },
    "Temperature_gt_24C": {
        "formula": "Temperature > 24 deg C",
        "unit": "binary",
        "group": "temperature",
        "description": "High-temperature indicator.",
    },
}

VARIANT_FEATURES = {
    "baseline": [],
    "threshold_flags_co2_1000_t18_t24": [
        "CO2_gt_1000ppm",
        "Temperature_lt_18C",
        "Temperature_gt_24C",
    ],
}

VARIANT_DESCRIPTIONS = {
    "baseline": "Current model-ready IEQ predictors only.",
    "threshold_flags_co2_1000_t18_t24": "Adds three binary threshold indicators: CO2 > 1000 ppm, Temperature < 18 deg C, and Temperature > 24 deg C.",
}


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


def add_engineered_features(frame: pd.DataFrame) -> pd.DataFrame:
    engineered = frame.copy()
    engineered["CO2_gt_1000ppm"] = engineered["CO2"].gt(CO2_HIGH_THRESHOLD).astype(int)
    engineered["Temperature_lt_18C"] = engineered["Temperature"].lt(TEMP_LOW_THRESHOLD).astype(int)
    engineered["Temperature_gt_24C"] = engineered["Temperature"].gt(TEMP_HIGH_THRESHOLD).astype(int)
    return engineered


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


def ordinal_mae(y_true: pd.Series, y_pred: pd.Series) -> float:
    true_values = y_true.map(ORDINAL_MAP).to_numpy()
    pred_values = pd.Series(y_pred).map(ORDINAL_MAP).to_numpy()
    return mean_absolute_error(true_values, pred_values)


def metric_row(y_true: pd.Series, y_pred: pd.Series) -> dict[str, float]:
    return {
        "accuracy": accuracy_score(y_true, y_pred),
        "balanced_accuracy": balanced_accuracy_score(y_true, y_pred),
        "macro_f1": f1_score(y_true, y_pred, average="macro"),
        "weighted_f1": f1_score(y_true, y_pred, average="weighted"),
        "ordinal_mae": ordinal_mae(y_true, y_pred),
    }


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
    summary = folds.groupby("variant")[metric_columns].agg(["mean", "std"])
    summary.columns = [f"{metric}_{stat}" for metric, stat in summary.columns]
    summary = summary.reset_index()
    return summary


def feature_definitions_table(engineered: pd.DataFrame) -> pd.DataFrame:
    rows = []
    total_rows = len(engineered)
    for feature, metadata in ENGINEERED_FEATURES.items():
        values = engineered[feature]
        nonzero_count = int(values.ne(0).sum())
        rows.append(
            {
                "feature": feature,
                **metadata,
                "nonzero_count": nonzero_count,
                "nonzero_percent": nonzero_count / total_rows * 100,
                "mean": float(values.mean()),
                "max": float(values.max()),
            }
        )
    return pd.DataFrame(rows)


def feature_set_membership_table(base_feature_count: int) -> pd.DataFrame:
    rows = []
    for variant, features in VARIANT_FEATURES.items():
        for feature in features:
            rows.append(
                {
                    "variant": variant,
                    "engineered_feature": feature,
                    "base_feature_count": base_feature_count,
                    "engineered_feature_count": len(features),
                    "total_feature_count": base_feature_count + len(features),
                    "variant_description": VARIANT_DESCRIPTIONS[variant],
                }
            )
        if not features:
            rows.append(
                {
                    "variant": variant,
                    "engineered_feature": "",
                    "base_feature_count": base_feature_count,
                    "engineered_feature_count": 0,
                    "total_feature_count": base_feature_count,
                    "variant_description": VARIANT_DESCRIPTIONS[variant],
                }
            )
    return pd.DataFrame(rows)


def evaluate_variants(data: pd.DataFrame) -> pd.DataFrame:
    engineered_feature_names = set(ENGINEERED_FEATURES)
    base_feature_columns = [
        column
        for column in data.columns
        if column not in DROP_FROM_FEATURES and column not in engineered_feature_names
    ]
    y = data[TARGET].astype(str)
    params = extra_trees_params()
    rows = []
    cv = StratifiedKFold(n_splits=EVALUATION_SPLITS, shuffle=True, random_state=SEED)

    for variant, engineered_features in VARIANT_FEATURES.items():
        feature_columns = base_feature_columns + engineered_features
        X = data[feature_columns]
        base_pipeline = build_pipeline(X, params)
        print(f"{variant}: {len(feature_columns)} predictors", flush=True)

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
            y_pred = pd.Series(pipeline.predict(X_test), index=y_test.index)
            predict_seconds = time.perf_counter() - predict_start
            metrics = metric_row(y_test, y_pred)

            row = {
                "variant": variant,
                "fold": fold,
                "rows": len(y),
                "base_feature_count": len(base_feature_columns),
                "engineered_feature_count": len(engineered_features),
                "predictors": len(feature_columns),
                "fit_seconds": fit_seconds,
                "predict_seconds": predict_seconds,
                "total_seconds": fit_seconds + predict_seconds,
                **metrics,
            }
            rows.append(row)
            print(
                f"  fold {fold}: macro_f1={row['macro_f1']:.3f}, "
                f"accuracy={row['accuracy']:.3f}, ordinal_mae={row['ordinal_mae']:.3f}, "
                f"time={row['total_seconds']:.1f}s",
                flush=True,
            )
    return pd.DataFrame(rows)


def add_summary_context(summary: pd.DataFrame) -> pd.DataFrame:
    summary.insert(0, "experiment", "ieq_threshold_feature_engineering")
    summary.insert(2, "variant_description", summary["variant"].map(VARIANT_DESCRIPTIONS))
    baseline = summary[summary["variant"].eq("baseline")].iloc[0]
    for metric in ["accuracy", "balanced_accuracy", "macro_f1", "weighted_f1", "ordinal_mae"]:
        summary[f"{metric}_delta_vs_baseline"] = summary[f"{metric}_mean"] - baseline[f"{metric}_mean"]
    return summary


def write_note(summary: pd.DataFrame, definitions: pd.DataFrame, paths: dict[str, Path]) -> None:
    best = summary.sort_values("macro_f1_mean", ascending=False).iloc[0]
    baseline = summary[summary["variant"].eq("baseline")].iloc[0]
    lines = [
        "# IEQ Threshold Feature Engineering Note",
        "",
        "This supplementary experiment reruns a compact, article-readable feature-engineering check for the IEQ model.",
        "",
        "Engineered thresholds:",
        "",
        f"- `CO2_gt_1000ppm`: CO2 > {CO2_HIGH_THRESHOLD:.0f} ppm.",
        f"- `Temperature_lt_18C`: Temperature < {TEMP_LOW_THRESHOLD:.0f} deg C.",
        f"- `Temperature_gt_24C`: Temperature > {TEMP_HIGH_THRESHOLD:.0f} deg C.",
        "",
        "Main result:",
        "",
        f"- Baseline Extra Trees macro F1 = {baseline['macro_f1_mean']:.3f}, accuracy = {baseline['accuracy_mean']:.3f}, ordinal MAE = {baseline['ordinal_mae_mean']:.3f}.",
        f"- Three-threshold variant macro F1 = {summary.loc[summary['variant'].eq('threshold_flags_co2_1000_t18_t24'), 'macro_f1_mean'].iloc[0]:.3f}, accuracy = {summary.loc[summary['variant'].eq('threshold_flags_co2_1000_t18_t24'), 'accuracy_mean'].iloc[0]:.3f}, ordinal MAE = {summary.loc[summary['variant'].eq('threshold_flags_co2_1000_t18_t24'), 'ordinal_mae_mean'].iloc[0]:.3f}.",
        f"- Three-threshold macro F1 delta versus baseline = {summary.loc[summary['variant'].eq('threshold_flags_co2_1000_t18_t24'), 'macro_f1_delta_vs_baseline'].iloc[0]:+.3f}.",
        "",
        "Threshold prevalence in the model-ready IEQ dataset:",
        "",
    ]
    for _, row in definitions.iterrows():
        if row["unit"] == "binary":
            lines.append(f"- `{row['feature']}`: {row['nonzero_count']} rows ({row['nonzero_percent']:.1f}%).")
    lines.extend(
        [
            "",
            "Output files:",
            "",
            f"- `{paths['summary'].relative_to(CODE_ROOT)}`",
            f"- `{paths['folds'].relative_to(CODE_ROOT)}`",
            f"- `{paths['definitions'].relative_to(CODE_ROOT)}`",
            f"- `{paths['membership'].relative_to(CODE_ROOT)}`",
        ]
    )
    paths["note"].write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    TABLE_DIR.mkdir(parents=True, exist_ok=True)
    NOTE_DIR.mkdir(parents=True, exist_ok=True)

    raw_data = pd.read_excel(DATASET_PATH, sheet_name="data")
    data = add_engineered_features(raw_data)
    base_feature_count = len([column for column in raw_data.columns if column not in DROP_FROM_FEATURES])

    definitions = feature_definitions_table(data)
    membership = feature_set_membership_table(base_feature_count)
    folds = evaluate_variants(data)
    summary = add_summary_context(summarize_folds(folds))

    paths = {
        "summary": TABLE_DIR / "ieq_threshold_feature_engineering_summary.csv",
        "folds": TABLE_DIR / "ieq_threshold_feature_engineering_folds.csv",
        "definitions": TABLE_DIR / "ieq_threshold_feature_definitions.csv",
        "membership": TABLE_DIR / "ieq_threshold_feature_sets.csv",
        "note": NOTE_DIR / "ieq_threshold_feature_engineering_note.md",
    }

    summary.to_csv(paths["summary"], index=False)
    folds.to_csv(paths["folds"], index=False)
    definitions.to_csv(paths["definitions"], index=False)
    membership.to_csv(paths["membership"], index=False)
    write_note(summary, definitions, paths)

    display_columns = [
        "variant",
        "accuracy_mean",
        "balanced_accuracy_mean",
        "macro_f1_mean",
        "weighted_f1_mean",
        "ordinal_mae_mean",
        "macro_f1_delta_vs_baseline",
        "ordinal_mae_delta_vs_baseline",
    ]
    print("\nSummary")
    print(summary.sort_values("macro_f1_mean", ascending=False)[display_columns].to_string(index=False))
    for label, path in paths.items():
        print(f"Saved {label}: {path}")


if __name__ == "__main__":
    main()
