from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

import pandas as pd
from sklearn.base import clone
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import ExtraTreesClassifier, GradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, balanced_accuracy_score, confusion_matrix, f1_score, mean_absolute_error
from sklearn.model_selection import StratifiedKFold
from sklearn.neural_network import MLPClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


ROOT = Path(__file__).resolve().parents[1]
DATASET_DIR = ROOT.parent / "02_Datasets"
SEED = 20260507
EVALUATION_SPLITS = 5
PRIMARY_GROUP = "Primary school"
ORDINAL_MAP = {"dissatisfied": 0, "neutral": 1, "satisfied": 2}

PAPERS = [
    {
        "paper": "thermal_comfort",
        "model_ready": DATASET_DIR / "model_ready" / "thermal_comfort_model_dataset.xlsx",
        "clean": DATASET_DIR / "clean" / "thermal_comfort_clean_dataset.xlsx",
        "target": "Thermal satisfaction 3-class",
        "drop": ["Thermal satisfaction", "Thermal satisfaction 3-class", "TimeVote"],
        "summary": ROOT / "thermal_comfort_paper" / "04_outputs" / "tables" / "tuned_model_comparison_5fold_summary.csv",
        "full_predictions": ROOT / "thermal_comfort_paper" / "04_outputs" / "tables" / "tuned_model_comparison_5fold_predictions.csv",
        "output_dir": ROOT / "thermal_comfort_paper" / "04_outputs" / "tables",
    },
    {
        "paper": "ieq",
        "model_ready": DATASET_DIR / "model_ready" / "ieq_model_dataset.xlsx",
        "clean": DATASET_DIR / "clean" / "ieq_clean_dataset.xlsx",
        "target": "IEQ satisfaction 3-class",
        "drop": ["IEQ satisfaction 3-class", "TimeVote"],
        "summary": ROOT / "ieq_paper" / "02_outputs" / "tables" / "tuned_model_comparison_5fold_summary.csv",
        "full_predictions": ROOT / "ieq_paper" / "02_outputs" / "tables" / "tuned_model_comparison_5fold_predictions.csv",
        "output_dir": ROOT / "ieq_paper" / "02_outputs" / "tables",
    },
]


def dense_one_hot_encoder() -> OneHotEncoder:
    try:
        return OneHotEncoder(handle_unknown="ignore", sparse_output=False)
    except TypeError:
        return OneHotEncoder(handle_unknown="ignore", sparse=False)


def model_factories() -> dict[str, Any]:
    return {
        "Logistic regression": LogisticRegression(max_iter=2500, random_state=SEED),
        "Random Forest": RandomForestClassifier(n_jobs=1, random_state=SEED),
        "Extra Trees": ExtraTreesClassifier(n_jobs=1, random_state=SEED),
        "Gradient boosting": GradientBoostingClassifier(random_state=SEED),
        "ANN / MLP": MLPClassifier(max_iter=250, early_stopping=False, random_state=SEED),
    }


def parse_params(raw_json: str) -> dict[str, Any]:
    params = json.loads(raw_json)
    for key, value in list(params.items()):
        if key.endswith("hidden_layer_sizes") and isinstance(value, list):
            params[key] = tuple(value)
    return params


def build_pipeline(model_name: str, X: pd.DataFrame, params: dict[str, Any]) -> Pipeline:
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
            ("model", model_factories()[model_name]),
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
    summary = folds.groupby(["paper", "variant", "model"])[metric_columns].agg(["mean", "std"])
    summary.columns = [f"{metric}_{stat}" for metric, stat in summary.columns]
    return summary.reset_index()


def evaluate_primary_only_cv(
    paper: str,
    X_primary: pd.DataFrame,
    y_primary: pd.Series,
    params_by_model: dict[str, dict[str, Any]],
) -> pd.DataFrame:
    rows = []
    cv = StratifiedKFold(n_splits=EVALUATION_SPLITS, shuffle=True, random_state=SEED)

    for model_name, params in params_by_model.items():
        base_pipeline = build_pipeline(model_name, X_primary, params)
        for fold, (train_index, test_index) in enumerate(cv.split(X_primary, y_primary), start=1):
            pipeline = clone(base_pipeline)
            if "model__random_state" in pipeline.get_params():
                pipeline.set_params(model__random_state=SEED + fold)

            X_train, X_test = X_primary.iloc[train_index], X_primary.iloc[test_index]
            y_train, y_test = y_primary.iloc[train_index], y_primary.iloc[test_index]

            fit_start = time.perf_counter()
            pipeline.fit(X_train, y_train)
            fit_seconds = time.perf_counter() - fit_start

            predict_start = time.perf_counter()
            y_pred = pd.Series(pipeline.predict(X_test), index=y_test.index)
            predict_seconds = time.perf_counter() - predict_start

            rows.append(
                {
                    "paper": paper,
                    "variant": "primary_only_training_and_evaluation",
                    "model": model_name,
                    "fold": fold,
                    "rows": len(y_primary),
                    "fit_seconds": fit_seconds,
                    "predict_seconds": predict_seconds,
                    "total_seconds": fit_seconds + predict_seconds,
                    **metric_row(y_test, y_pred),
                }
            )
    return pd.DataFrame(rows)


def evaluate_full_predictions_on_primary(config: dict[str, Any], primary_indices: pd.Index) -> pd.DataFrame:
    predictions = pd.read_csv(config["full_predictions"])
    primary_predictions = predictions[predictions["row_index"].isin(primary_indices)].copy()
    rows = []
    for model_name, model_predictions in primary_predictions.groupby("model"):
        y_true = model_predictions["true_label"].astype(str)
        y_pred = model_predictions["predicted_label"].astype(str)
        rows.append(
            {
                "paper": config["paper"],
                "variant": "full_dataset_training_primary_rows_only",
                "model": model_name,
                "rows": len(model_predictions),
                **metric_row(y_true, y_pred),
            }
        )
    return pd.DataFrame(rows)


def make_confusion_matrix_table(summary_predictions: pd.DataFrame, paper: str, variant: str, model: str) -> pd.DataFrame:
    labels = ["dissatisfied", "neutral", "satisfied"]
    matrix = confusion_matrix(
        summary_predictions["true_label"],
        summary_predictions["predicted_label"],
        labels=labels,
    )
    rows = []
    for true_index, true_label in enumerate(labels):
        row_total = matrix[true_index].sum()
        for predicted_index, predicted_label in enumerate(labels):
            count = int(matrix[true_index, predicted_index])
            rows.append(
                {
                    "paper": paper,
                    "variant": variant,
                    "model": model,
                    "true_label": true_label,
                    "predicted_label": predicted_label,
                    "count": count,
                    "row_percent": count / row_total * 100 if row_total else 0.0,
                }
            )
    return pd.DataFrame(rows)


def run_paper(config: dict[str, Any]) -> pd.DataFrame:
    model_data = pd.read_excel(config["model_ready"], sheet_name="data")
    clean_data = pd.read_excel(config["clean"], sheet_name="data")
    if len(model_data) != len(clean_data):
        raise ValueError(f"{config['paper']}: clean and model-ready row counts differ")

    primary_mask = clean_data["Group"].eq(PRIMARY_GROUP)
    primary_indices = model_data.index[primary_mask]

    feature_columns = [column for column in model_data.columns if column not in config["drop"]]
    X_primary = model_data.loc[primary_mask, feature_columns].reset_index(drop=True)
    y_primary = model_data.loc[primary_mask, config["target"]].astype(str).reset_index(drop=True)

    baseline = pd.read_csv(config["summary"])
    params_by_model = {
        row["model"]: parse_params(row["best_params_json"])
        for _, row in baseline.iterrows()
        if row["model"] in model_factories()
    }

    target_distribution = y_primary.value_counts().rename_axis("label").reset_index(name="count")
    target_distribution.insert(0, "paper", config["paper"])
    target_distribution.insert(1, "group", PRIMARY_GROUP)
    target_distribution["percent"] = target_distribution["count"] / len(y_primary) * 100

    primary_folds = evaluate_primary_only_cv(config["paper"], X_primary, y_primary, params_by_model)
    primary_summary = summarize_folds(primary_folds)

    full_primary_summary = evaluate_full_predictions_on_primary(config, primary_indices)
    full_primary_summary = full_primary_summary.rename(
        columns={
            "accuracy": "accuracy_mean",
            "balanced_accuracy": "balanced_accuracy_mean",
            "macro_f1": "macro_f1_mean",
            "weighted_f1": "weighted_f1_mean",
            "ordinal_mae": "ordinal_mae_mean",
        }
    )
    full_primary_summary["accuracy_std"] = pd.NA
    full_primary_summary["balanced_accuracy_std"] = pd.NA
    full_primary_summary["macro_f1_std"] = pd.NA
    full_primary_summary["weighted_f1_std"] = pd.NA
    full_primary_summary["ordinal_mae_std"] = pd.NA
    for column in ["fit_seconds_mean", "fit_seconds_std", "predict_seconds_mean", "predict_seconds_std", "total_seconds_mean", "total_seconds_std"]:
        full_primary_summary[column] = pd.NA

    combined = pd.concat([primary_summary, full_primary_summary], ignore_index=True, sort=False)
    combined.insert(3, "group", PRIMARY_GROUP)
    combined["rows"] = len(y_primary)
    combined.insert(5, "predictors", len(feature_columns))

    baseline_columns = [
        "model",
        "accuracy_mean",
        "balanced_accuracy_mean",
        "macro_f1_mean",
        "weighted_f1_mean",
        "ordinal_mae_mean",
    ]
    combined = combined.merge(
        baseline[baseline_columns].rename(
            columns={column: f"full_dataset_overall_{column}" for column in baseline_columns if column != "model"}
        ),
        on="model",
        how="left",
    )

    full_primary_metrics = full_primary_summary[
        ["model", "accuracy_mean", "balanced_accuracy_mean", "macro_f1_mean", "weighted_f1_mean", "ordinal_mae_mean"]
    ].rename(
        columns={
            "accuracy_mean": "full_training_primary_accuracy",
            "balanced_accuracy_mean": "full_training_primary_balanced_accuracy",
            "macro_f1_mean": "full_training_primary_macro_f1",
            "weighted_f1_mean": "full_training_primary_weighted_f1",
            "ordinal_mae_mean": "full_training_primary_ordinal_mae",
        }
    )
    combined = combined.merge(full_primary_metrics, on="model", how="left")

    primary_only_rows = combined["variant"].eq("primary_only_training_and_evaluation")
    combined.loc[primary_only_rows, "primary_only_vs_full_training_primary_macro_f1_delta"] = (
        combined.loc[primary_only_rows, "macro_f1_mean"] - combined.loc[primary_only_rows, "full_training_primary_macro_f1"]
    )
    combined.loc[primary_only_rows, "primary_only_vs_full_training_primary_accuracy_delta"] = (
        combined.loc[primary_only_rows, "accuracy_mean"] - combined.loc[primary_only_rows, "full_training_primary_accuracy"]
    )

    output_dir = config["output_dir"]
    supplementary_dir = output_dir.parent / "supplementary_experiments" / "tables"
    supplementary_dir.mkdir(parents=True, exist_ok=True)
    primary_folds.to_csv(supplementary_dir / "primary_only_model_experiment_folds.csv", index=False)
    combined.to_csv(supplementary_dir / "primary_only_model_experiment_summary.csv", index=False)
    target_distribution.to_csv(supplementary_dir / "primary_only_target_distribution.csv", index=False)
    return combined


def main() -> None:
    summaries = [run_paper(config) for config in PAPERS]
    combined = pd.concat(summaries, ignore_index=True)
    supplementary_dir = ROOT / "_project_tools" / "supplementary_experiments"
    supplementary_dir.mkdir(parents=True, exist_ok=True)
    combined.to_csv(supplementary_dir / "primary_only_model_experiment_summary.csv", index=False)

    display_columns = [
        "paper",
        "variant",
        "model",
        "accuracy_mean",
        "macro_f1_mean",
        "ordinal_mae_mean",
        "primary_only_vs_full_training_primary_macro_f1_delta",
        "primary_only_vs_full_training_primary_accuracy_delta",
    ]
    print(
        combined.sort_values(["paper", "variant", "macro_f1_mean"], ascending=[True, True, False])[display_columns]
        .to_string(index=False)
    )


if __name__ == "__main__":
    main()
