from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

import numpy as np
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
DATASET_DIR = PROJECT_ROOT / "02_Datasets"
IEQ_MODEL_READY = DATASET_DIR / "model_ready" / "ieq_model_dataset.xlsx"
IEQ_CLEAN = DATASET_DIR / "clean" / "ieq_clean_dataset.xlsx"
BASELINE_SUMMARY_PATH = CODE_ROOT / "ieq_paper" / "02_outputs" / "tables" / "tuned_model_comparison_5fold_summary.csv"
BASELINE_PREDICTIONS_PATH = CODE_ROOT / "ieq_paper" / "02_outputs" / "tables" / "tuned_model_comparison_5fold_predictions.csv"
OUTPUT_ROOT = CODE_ROOT / "ieq_paper" / "02_outputs" / "supplementary_experiments"
TABLE_DIR = OUTPUT_ROOT / "tables"
NOTE_DIR = OUTPUT_ROOT / "notes"

SEED = 20260507
EVALUATION_SPLITS = 5
TARGET = "IEQ satisfaction 3-class"
DROP_FROM_FEATURES = [TARGET, "TimeVote"]
PRIMARY_GROUP = "Primary school"
CLASS_ORDER = ["dissatisfied", "neutral", "satisfied"]
ORDINAL_MAP = {"dissatisfied": 0, "neutral": 1, "satisfied": 2}


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


def probabilities_in_class_order(pipeline: Pipeline, X: pd.DataFrame) -> np.ndarray:
    probabilities = pipeline.predict_proba(X)
    classes = list(pipeline.classes_)
    aligned = np.zeros((len(X), len(CLASS_ORDER)))
    for source_index, label in enumerate(classes):
        aligned[:, CLASS_ORDER.index(label)] = probabilities[:, source_index]
    return aligned


def load_data() -> tuple[pd.DataFrame, pd.Series, pd.Series]:
    model_data = pd.read_excel(IEQ_MODEL_READY, sheet_name="data")
    clean_data = pd.read_excel(IEQ_CLEAN, sheet_name="data")
    if len(model_data) != len(clean_data):
        raise ValueError("IEQ clean and model-ready row counts differ")

    feature_columns = [column for column in model_data.columns if column not in DROP_FROM_FEATURES]
    X = model_data[feature_columns]
    y = model_data[TARGET].astype(str)
    groups = clean_data["Group"].astype(str)
    return X, y, groups


def baseline_group_metrics(y: pd.Series, groups: pd.Series) -> tuple[pd.DataFrame, pd.DataFrame]:
    predictions = pd.read_csv(BASELINE_PREDICTIONS_PATH)
    model_predictions = predictions[predictions["model"].eq("Extra Trees")].copy()
    model_predictions["group"] = groups.iloc[model_predictions["row_index"].to_numpy()].to_numpy()
    model_predictions["evaluation_population"] = model_predictions["group"]

    rows = []
    for population, frame in [
        ("All rows", model_predictions),
        *[(group, group_frame) for group, group_frame in model_predictions.groupby("group")],
    ]:
        metrics = metric_row(frame["true_label"].astype(str), frame["predicted_label"].astype(str))
        rows.append(
            {
                "experiment": "all_school_tuned_extra_trees_oof",
                "training_population": "All schools",
                "evaluation_population": population,
                "rows": len(frame),
                "predictors": len([column for column in pd.read_excel(IEQ_MODEL_READY, sheet_name="data").columns if column not in DROP_FROM_FEATURES]),
                **metrics,
            }
        )
    return pd.DataFrame(rows), model_predictions


def evaluate_primary_trained_transfer(X: pd.DataFrame, y: pd.Series, groups: pd.Series) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    primary_mask = groups.eq(PRIMARY_GROUP)
    nonprimary_mask = ~primary_mask
    primary_indices = np.flatnonzero(primary_mask.to_numpy())
    nonprimary_indices = np.flatnonzero(nonprimary_mask.to_numpy())
    X_primary = X.iloc[primary_indices].reset_index(drop=True)
    y_primary = y.iloc[primary_indices].reset_index(drop=True)

    params = extra_trees_params()
    base_pipeline = build_pipeline(X_primary, params)
    cv = StratifiedKFold(n_splits=EVALUATION_SPLITS, shuffle=True, random_state=SEED)

    oof_primary_predictions = pd.Series(index=primary_indices, dtype=object)
    nonprimary_probability_sum = np.zeros((len(nonprimary_indices), len(CLASS_ORDER)))
    fold_rows = []

    for fold, (train_index, test_index) in enumerate(cv.split(X_primary, y_primary), start=1):
        pipeline = clone(base_pipeline)
        if "model__random_state" in pipeline.get_params():
            pipeline.set_params(model__random_state=SEED + fold)

        fit_start = time.perf_counter()
        pipeline.fit(X_primary.iloc[train_index], y_primary.iloc[train_index])
        fit_seconds = time.perf_counter() - fit_start

        predict_start = time.perf_counter()
        primary_pred = pd.Series(pipeline.predict(X_primary.iloc[test_index]), index=primary_indices[test_index])
        nonprimary_probabilities = probabilities_in_class_order(pipeline, X.iloc[nonprimary_indices])
        nonprimary_pred = pd.Series(
            [CLASS_ORDER[index] for index in np.argmax(nonprimary_probabilities, axis=1)],
            index=nonprimary_indices,
        )
        predict_seconds = time.perf_counter() - predict_start

        oof_primary_predictions.loc[primary_indices[test_index]] = primary_pred
        nonprimary_probability_sum += nonprimary_probabilities

        fold_predictions = pd.DataFrame(
            {
                "row_index": primary_pred.index.to_numpy(),
                "group": groups.iloc[primary_pred.index].to_numpy(),
                "true_label": y.iloc[primary_pred.index].to_numpy(),
                "predicted_label": primary_pred.to_numpy(),
            }
        )
        fold_nonprimary = pd.DataFrame(
            {
                "row_index": nonprimary_pred.index.to_numpy(),
                "group": groups.iloc[nonprimary_pred.index].to_numpy(),
                "true_label": y.iloc[nonprimary_pred.index].to_numpy(),
                "predicted_label": nonprimary_pred.to_numpy(),
            }
        )
        fold_predictions = pd.concat([fold_predictions, fold_nonprimary], ignore_index=True)

        for population, frame in [
            ("All rows", fold_predictions),
            *[(group, group_frame) for group, group_frame in fold_predictions.groupby("group")],
        ]:
            metrics = metric_row(frame["true_label"].astype(str), frame["predicted_label"].astype(str))
            fold_rows.append(
                {
                    "experiment": "primary_trained_fold_models",
                    "training_population": PRIMARY_GROUP,
                    "evaluation_population": population,
                    "fold": fold,
                    "rows": len(frame),
                    "fit_seconds": fit_seconds,
                    "predict_seconds": predict_seconds,
                    "total_seconds": fit_seconds + predict_seconds,
                    **metrics,
                }
            )
        print(
            f"fold {fold}: primary OOF macro_f1={metric_row(y.iloc[primary_pred.index], primary_pred)['macro_f1']:.3f}; "
            f"non-primary macro_f1={metric_row(y.iloc[nonprimary_pred.index], nonprimary_pred)['macro_f1']:.3f}",
            flush=True,
        )

    averaged_nonprimary_probabilities = nonprimary_probability_sum / EVALUATION_SPLITS
    nonprimary_predictions = pd.Series(
        [CLASS_ORDER[index] for index in np.argmax(averaged_nonprimary_probabilities, axis=1)],
        index=nonprimary_indices,
    )

    combined_predictions = pd.concat([oof_primary_predictions, nonprimary_predictions]).sort_index()
    prediction_table = pd.DataFrame(
        {
            "experiment": "primary_trained_oof_primary_ensemble_nonprimary",
            "model": "Extra Trees",
            "row_index": combined_predictions.index,
            "group": groups.iloc[combined_predictions.index].to_numpy(),
            "true_label": y.iloc[combined_predictions.index].to_numpy(),
            "predicted_label": combined_predictions.to_numpy(),
            "prediction_mode": np.where(
                groups.iloc[combined_predictions.index].eq(PRIMARY_GROUP),
                "primary_out_of_fold",
                "nonprimary_average_probability_across_primary_fold_models",
            ),
        }
    )

    summary_rows = []
    for population, frame in [
        ("All rows", prediction_table),
        *[(group, group_frame) for group, group_frame in prediction_table.groupby("group")],
    ]:
        metrics = metric_row(frame["true_label"].astype(str), frame["predicted_label"].astype(str))
        summary_rows.append(
            {
                "experiment": "primary_trained_oof_primary_ensemble_nonprimary",
                "training_population": PRIMARY_GROUP,
                "evaluation_population": population,
                "rows": len(frame),
                "predictors": X.shape[1],
                **metrics,
            }
        )

    return pd.DataFrame(summary_rows), pd.DataFrame(fold_rows), prediction_table


def add_comparison_columns(summary: pd.DataFrame, baseline: pd.DataFrame) -> pd.DataFrame:
    baseline_columns = [
        "evaluation_population",
        "accuracy",
        "balanced_accuracy",
        "macro_f1",
        "weighted_f1",
        "ordinal_mae",
    ]
    merged = summary.merge(
        baseline[baseline_columns].rename(
            columns={
                "accuracy": "all_school_accuracy",
                "balanced_accuracy": "all_school_balanced_accuracy",
                "macro_f1": "all_school_macro_f1",
                "weighted_f1": "all_school_weighted_f1",
                "ordinal_mae": "all_school_ordinal_mae",
            }
        ),
        on="evaluation_population",
        how="left",
    )
    for metric in ["accuracy", "balanced_accuracy", "macro_f1", "weighted_f1", "ordinal_mae"]:
        merged[f"{metric}_delta_vs_all_school"] = merged[metric] - merged[f"all_school_{metric}"]
    return merged


def write_note(summary: pd.DataFrame, baseline: pd.DataFrame, paths: dict[str, Path]) -> None:
    all_rows = summary[summary["evaluation_population"].eq("All rows")].iloc[0]
    all_rows_baseline = baseline[baseline["evaluation_population"].eq("All rows")].iloc[0]
    secondary = summary[summary["evaluation_population"].eq("Secondary school")].iloc[0]
    lecture = summary[summary["evaluation_population"].eq("Test lecture room")].iloc[0]

    lines = [
        "# IEQ Primary-Trained Transfer Check",
        "",
        "This supplementary experiment tests the reverse of the earlier primary-row evaluation: models are trained only on primary-school observations and then applied to the whole IEQ dataset.",
        "",
        "Evaluation design:",
        "",
        "- Model family: tuned Extra Trees configuration from the main IEQ comparison.",
        "- Training population: primary-school rows only.",
        "- Primary-school rows are evaluated with out-of-fold predictions.",
        "- Secondary-school and test-lecture-room rows are predicted by averaging probabilities across the five primary-trained fold models.",
        "",
        "Headline result:",
        "",
        f"- All-school tuned Extra Trees baseline on all rows: accuracy={all_rows_baseline['accuracy']:.3f}, macro F1={all_rows_baseline['macro_f1']:.3f}, ordinal MAE={all_rows_baseline['ordinal_mae']:.3f}.",
        f"- Primary-trained transfer-style model on all rows: accuracy={all_rows['accuracy']:.3f}, macro F1={all_rows['macro_f1']:.3f}, ordinal MAE={all_rows['ordinal_mae']:.3f}.",
        f"- All-row macro F1 delta versus all-school baseline: {all_rows['macro_f1_delta_vs_all_school']:+.3f}.",
        "",
        "Non-primary transfer performance:",
        "",
        f"- Secondary school: accuracy={secondary['accuracy']:.3f}, macro F1={secondary['macro_f1']:.3f}, ordinal MAE={secondary['ordinal_mae']:.3f}.",
        f"- Test lecture room: accuracy={lecture['accuracy']:.3f}, macro F1={lecture['macro_f1']:.3f}, ordinal MAE={lecture['ordinal_mae']:.3f}.",
        "",
        "Output files:",
        "",
        f"- `{paths['summary'].relative_to(CODE_ROOT)}`",
        f"- `{paths['folds'].relative_to(CODE_ROOT)}`",
        f"- `{paths['predictions'].relative_to(CODE_ROOT)}`",
        f"- `{paths['baseline'].relative_to(CODE_ROOT)}`",
    ]
    paths["note"].write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    TABLE_DIR.mkdir(parents=True, exist_ok=True)
    NOTE_DIR.mkdir(parents=True, exist_ok=True)

    X, y, groups = load_data()
    baseline_summary, baseline_predictions = baseline_group_metrics(y, groups)
    transfer_summary, fold_metrics, transfer_predictions = evaluate_primary_trained_transfer(X, y, groups)
    transfer_summary = add_comparison_columns(transfer_summary, baseline_summary)

    paths = {
        "summary": TABLE_DIR / "ieq_primary_trained_transfer_summary.csv",
        "folds": TABLE_DIR / "ieq_primary_trained_transfer_fold_metrics.csv",
        "predictions": TABLE_DIR / "ieq_primary_trained_transfer_predictions.csv",
        "baseline": TABLE_DIR / "ieq_all_school_extra_trees_group_summary.csv",
        "note": NOTE_DIR / "ieq_primary_trained_transfer_note.md",
    }

    transfer_summary.to_csv(paths["summary"], index=False)
    fold_metrics.to_csv(paths["folds"], index=False)
    transfer_predictions.to_csv(paths["predictions"], index=False)
    baseline_summary.to_csv(paths["baseline"], index=False)
    write_note(transfer_summary, baseline_summary, paths)

    display_columns = [
        "evaluation_population",
        "rows",
        "accuracy",
        "macro_f1",
        "ordinal_mae",
        "accuracy_delta_vs_all_school",
        "macro_f1_delta_vs_all_school",
        "ordinal_mae_delta_vs_all_school",
    ]
    print("\nPrimary-trained transfer-style summary")
    print(transfer_summary[display_columns].to_string(index=False))
    print("\nAll-school Extra Trees baseline group summary")
    print(baseline_summary[["evaluation_population", "rows", "accuracy", "macro_f1", "ordinal_mae"]].to_string(index=False))
    for label, path in paths.items():
        print(f"Saved {label}: {path}")


if __name__ == "__main__":
    main()
