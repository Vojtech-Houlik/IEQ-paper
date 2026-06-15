from __future__ import annotations

import json
from textwrap import dedent
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
NOTEBOOK_PATH = PROJECT_ROOT / "03_Code" / "ieq_paper" / "01_notebook" / "06_ieq_extra_trees_fine_tuning.ipynb"


def markdown_cell(source: str) -> dict:
    return {
        "cell_type": "markdown",
        "metadata": {},
        "source": dedent(source).strip().splitlines(keepends=True),
    }


def code_cell(source: str) -> dict:
    return {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": dedent(source).strip().splitlines(keepends=True),
    }


cells = [
    markdown_cell(
        """
        # IEQ Extra Trees Fine Tuning

        This notebook reproduces the fine-tuning checks reported in Section 4.2 of the IEQ paper. It starts from the tuned Extra Trees model selected in the benchmark comparison and tests whether additional steps improve performance.

        The notebook is written as an audit trail for readers of the paper. It keeps the validation protocol fixed, fits preprocessing inside each training fold, and reports macro F1 as the main metric. Accuracy, balanced accuracy, and ordinal MAE are reported as secondary metrics.
        """
    ),
    markdown_cell(
        """
        ## Experiment overview

        The following variants are evaluated:

        1. Establish the main all-school Extra Trees baseline.
        2. Add simple operational threshold features for CO2 and temperature.
        3. Add missingness indicators that mark values filled during imputation.
        4. Test whether a small Random Forest contribution improves Extra Trees through soft voting.
        5. Test class-weight and fold-internal threshold tuning for the imbalanced target.
        6. Restrict evaluation to records with originally complete sensor values.
        7. Test class balancing applied only inside the training folds.

        Complete-case filters change the evaluated row population, so they are interpreted as data-quality checks rather than direct replacements for the main model.

        After each optimization step, the notebook reports the main metric values and the change relative to the all-school Extra Trees baseline.
        """
    ),
    code_cell(
        """
        from __future__ import annotations

        import json
        import time
        from pathlib import Path
        from typing import Callable

        import matplotlib.pyplot as plt
        import numpy as np
        import pandas as pd
        try:
            from IPython.display import display
        except ImportError:
            def display(value):
                print(value)

        from sklearn.base import clone
        from sklearn.compose import ColumnTransformer
        from sklearn.ensemble import ExtraTreesClassifier, RandomForestClassifier
        from sklearn.metrics import accuracy_score, balanced_accuracy_score, confusion_matrix, f1_score, mean_absolute_error, recall_score
        from sklearn.model_selection import StratifiedKFold
        from sklearn.pipeline import Pipeline
        from sklearn.preprocessing import OneHotEncoder, StandardScaler

        pd.set_option("display.max_columns", 120)
        pd.set_option("display.width", 160)
        """
    ),
    code_cell(
        """
        SEED = 20260507
        N_SPLITS = 5
        TEN_FOLD_SPLITS = 10
        THRESHOLD_INNER_SPLITS = 3
        N_JOBS = 1

        TARGET = "IEQ satisfaction 3-class"
        DROP_FROM_FEATURES = [TARGET, "TimeVote"]

        CLASS_ORDER = ["dissatisfied", "neutral", "satisfied"]
        CLASS_TO_NUMBER = {label: i for i, label in enumerate(CLASS_ORDER)}

        PRIMARY_METRIC = "macro_f1"
        REPORT_METRICS = ["macro_f1", "accuracy", "balanced_accuracy", "ordinal_mae"]

        # Set to False when you want a fast notebook check without the heaviest resampling variants.
        RUN_SYNTHETIC_SAMPLING = True
        RUN_TEN_FOLD_VALIDATION = True

        SOFT_VOTE_ET_WEIGHTS = [0.80, 0.86, 0.90, 0.95]
        """
    ),
    markdown_cell(
        """
        ## Paths and data

        The notebook can be run either from the repository root or from the notebook directory. It uses the model-ready dataset for model inputs and the clean dataset only to define complete-case filters before imputation.
        """
    ),
    code_cell(
        """
        def find_project_root(start: Path | None = None) -> Path:
            start = Path.cwd() if start is None else start
            for candidate in [start, *start.parents]:
                if (candidate / "02_Datasets").exists() and (candidate / "06_Paper").exists():
                    return candidate
            raise FileNotFoundError("Could not find project root containing 02_Datasets and 06_Paper.")


        PROJECT_ROOT = find_project_root()
        DATASET_PATH = PROJECT_ROOT / "02_Datasets" / "model_ready" / "ieq_model_dataset.xlsx"
        CLEAN_DATASET_PATH = PROJECT_ROOT / "02_Datasets" / "clean" / "ieq_clean_dataset.xlsx"
        BEST_PARAMS_PATH = PROJECT_ROOT / "03_Code" / "ieq_paper" / "02_outputs" / "tables" / "hyperparameter_tuning_best_params.csv"
        OUTPUT_DIR = PROJECT_ROOT / "03_Code" / "ieq_paper" / "02_outputs" / "supplementary_experiments" / "tables"
        FIGURE_DIR = PROJECT_ROOT / "03_Code" / "ieq_paper" / "02_outputs" / "supplementary_experiments" / "figures"

        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        FIGURE_DIR.mkdir(parents=True, exist_ok=True)

        model_data = pd.read_excel(DATASET_PATH)
        clean_data = pd.read_excel(CLEAN_DATASET_PATH)

        if len(model_data) != len(clean_data):
            raise ValueError("Model-ready and clean datasets must have the same row count for complete-case filters.")

        print("Project root:", PROJECT_ROOT)
        print("Model-ready data:", model_data.shape)
        print("Clean data:", clean_data.shape)
        """
    ),
    code_cell(
        """
        feature_columns = [column for column in model_data.columns if column not in DROP_FROM_FEATURES]

        X_base = model_data[feature_columns].copy()
        y = model_data[TARGET].astype(str)

        numeric_features = X_base.select_dtypes(include=["number"]).columns.tolist()
        categorical_features = [column for column in X_base.columns if column not in numeric_features]

        class_distribution = y.value_counts().reindex(CLASS_ORDER).rename("rows").to_frame()
        class_distribution["percent"] = class_distribution["rows"] / len(y) * 100

        print("Target:", TARGET)
        print("Rows:", len(y))
        print("Predictors:", len(feature_columns))
        print("Numeric predictors:", numeric_features)
        print("Categorical or boolean predictors:", categorical_features)
        display(class_distribution)
        """
    ),
    markdown_cell(
        """
        ## Tuned model parameters

        Hyperparameters are loaded from the tuning notebook output. This avoids copying parameter values by hand and keeps this fine-tuning notebook aligned with the benchmark.
        """
    ),
    code_cell(
        """
        best_params_table = pd.read_csv(BEST_PARAMS_PATH)
        best_params = {
            row["model"]: json.loads(row["best_params_json"])
            for _, row in best_params_table.iterrows()
        }

        EXTRA_TREES_PARAMS = best_params["Extra Trees"]
        RANDOM_FOREST_PARAMS = best_params["Random Forest"]

        display(
            pd.DataFrame(
                [
                    {"model": "Extra Trees", **EXTRA_TREES_PARAMS},
                    {"model": "Random Forest", **RANDOM_FOREST_PARAMS},
                ]
            )
        )
        """
    ),
    markdown_cell(
        """
        ## Shared validation and reporting functions

        All variants use the same stratified five-fold split. Numeric scaling and categorical conversion are fitted inside the pipeline, so preprocessing is learned only from the training part of each fold.
        """
    ),
    code_cell(
        """
        def dense_one_hot_encoder() -> OneHotEncoder:
            try:
                return OneHotEncoder(handle_unknown="ignore", sparse_output=False)
            except TypeError:
                return OneHotEncoder(handle_unknown="ignore", sparse=False)


        def make_preprocessor(X: pd.DataFrame) -> ColumnTransformer:
            numeric = X.select_dtypes(include=["number"]).columns.tolist()
            categorical = [column for column in X.columns if column not in numeric]
            transformers = []
            if numeric:
                transformers.append(("numeric", StandardScaler(), numeric))
            if categorical:
                transformers.append(("categorical", dense_one_hot_encoder(), categorical))
            return ColumnTransformer(transformers=transformers)


        def make_model(model_name: str, seed: int) -> ExtraTreesClassifier | RandomForestClassifier:
            if model_name == "Extra Trees":
                return ExtraTreesClassifier(n_jobs=N_JOBS, random_state=seed)
            if model_name == "Random Forest":
                return RandomForestClassifier(n_jobs=N_JOBS, random_state=seed)
            raise ValueError(f"Unsupported model: {model_name}")


        def make_pipeline(X: pd.DataFrame, model_name: str, params: dict, seed: int) -> Pipeline:
            pipeline = Pipeline(
                steps=[
                    ("preprocess", make_preprocessor(X)),
                    ("model", make_model(model_name, seed)),
                ]
            )
            pipeline.set_params(**params)
            return pipeline


        def ordinal_mae(y_true: pd.Series, y_pred: pd.Series | np.ndarray) -> float:
            true_values = pd.Series(y_true).map(CLASS_TO_NUMBER).to_numpy()
            pred_values = pd.Series(y_pred).map(CLASS_TO_NUMBER).to_numpy()
            return float(mean_absolute_error(true_values, pred_values))


        def metric_row(y_true: pd.Series, y_pred: pd.Series | np.ndarray) -> dict[str, float]:
            return {
                "macro_f1": float(f1_score(y_true, y_pred, average="macro", zero_division=0)),
                "accuracy": float(accuracy_score(y_true, y_pred)),
                "balanced_accuracy": float(balanced_accuracy_score(y_true, y_pred)),
                "ordinal_mae": ordinal_mae(y_true, y_pred),
            }


        def class_ordered_probabilities(pipeline: Pipeline, X: pd.DataFrame) -> np.ndarray:
            raw_probabilities = pipeline.predict_proba(X)
            output = np.zeros((len(X), len(CLASS_ORDER)))
            class_to_column = {label: index for index, label in enumerate(pipeline.named_steps["model"].classes_)}
            for output_column, label in enumerate(CLASS_ORDER):
                if label in class_to_column:
                    output[:, output_column] = raw_probabilities[:, class_to_column[label]]
            return output
        """
    ),
    code_cell(
        """
        SamplingFunction = Callable[[pd.DataFrame, pd.Series, int], tuple[pd.DataFrame, pd.Series]]


        def evaluate_cv_variant(
            experiment: str,
            variant: str,
            X: pd.DataFrame,
            y_values: pd.Series,
            *,
            model_name: str = "Extra Trees",
            params: dict | None = None,
            sampling_fn: SamplingFunction | None = None,
            note: str = "",
            n_splits: int | None = None,
        ) -> pd.DataFrame:
            n_splits = N_SPLITS if n_splits is None else n_splits
            params = EXTRA_TREES_PARAMS if params is None else params
            rows = []
            cv = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=SEED)

            for fold, (train_index, test_index) in enumerate(cv.split(X, y_values), start=1):
                X_train, X_test = X.iloc[train_index].copy(), X.iloc[test_index].copy()
                y_train, y_test = y_values.iloc[train_index].copy(), y_values.iloc[test_index].copy()

                if sampling_fn is not None:
                    X_train, y_train = sampling_fn(X_train, y_train, fold)

                pipeline = make_pipeline(X, model_name=model_name, params=params, seed=SEED + fold)

                start = time.perf_counter()
                pipeline.fit(X_train, y_train)
                fit_seconds = time.perf_counter() - start

                start = time.perf_counter()
                y_pred = pd.Series(pipeline.predict(X_test), index=y_test.index)
                predict_seconds = time.perf_counter() - start

                rows.append(
                    {
                        "experiment": experiment,
                        "variant": variant,
                        "fold": fold,
                        "cv_splits": n_splits,
                        "model": model_name,
                        "rows": len(X),
                        "train_rows_after_sampling": len(X_train),
                        "predictors": X.shape[1],
                        "fit_seconds": fit_seconds,
                        "predict_seconds": predict_seconds,
                        "total_seconds": fit_seconds + predict_seconds,
                        "note": note,
                        **metric_row(y_test, y_pred),
                    }
                )

            return pd.DataFrame(rows)


        def summarize_folds(folds: pd.DataFrame) -> pd.DataFrame:
            group_columns = ["experiment", "variant", "cv_splits", "model", "rows", "predictors", "note"]
            metric_columns = REPORT_METRICS + ["fit_seconds", "predict_seconds", "total_seconds", "train_rows_after_sampling"]
            summary = folds.groupby(group_columns, dropna=False)[metric_columns].agg(["mean", "std"]).reset_index()
            summary.columns = [
                "_".join(column).rstrip("_") if isinstance(column, tuple) else column
                for column in summary.columns
            ]
            return summary


        def result_table(summary: pd.DataFrame) -> pd.DataFrame:
            columns = [
                "variant",
                "cv_splits",
                "rows",
                "predictors",
                "macro_f1_mean",
                "accuracy_mean",
                "balanced_accuracy_mean",
                "ordinal_mae_mean",
            ]
            table = summary[columns].copy()
            for column in table.select_dtypes(include=["float"]).columns:
                table[column] = table[column].round(6)
            return table


        def metric_change_table(
            summary: pd.DataFrame,
            baseline_summary: pd.DataFrame,
            baseline_variant: str = "main_all_school_extra_trees",
        ) -> pd.DataFrame:
            baseline = baseline_summary[baseline_summary["variant"].eq(baseline_variant)].iloc[0]
            rows = []
            for _, row in summary.iterrows():
                rows.append(
                    {
                        "variant": row["variant"],
                        "same_population_as_main": bool(row["rows"] == baseline["rows"]),
                        "macro_f1_delta": row["macro_f1_mean"] - baseline["macro_f1_mean"],
                        "accuracy_delta": row["accuracy_mean"] - baseline["accuracy_mean"],
                        "balanced_accuracy_delta": row["balanced_accuracy_mean"] - baseline["balanced_accuracy_mean"],
                        "ordinal_mae_delta": row["ordinal_mae_mean"] - baseline["ordinal_mae_mean"],
                    }
                )
            table = pd.DataFrame(rows)
            for column in table.select_dtypes(include=["float"]).columns:
                table[column] = table[column].round(6)
            return table
        """
    ),
    markdown_cell(
        """
        ## 1. Main Extra Trees baseline

        This step re-evaluates the tuned Extra Trees model selected in the benchmark comparison. It is the reference point for the rest of the notebook.

        The baseline uses all 6,834 observations in the cleaned and imputed all-school dataset. Later experiments are interpreted as improvements only when they use the same row population. If an experiment removes rows, it is treated as a data-quality check rather than a direct replacement.
        """
    ),
    code_cell(
        """
        baseline_folds = evaluate_cv_variant(
            "baseline",
            "main_all_school_extra_trees",
            X_base,
            y,
            note="Tuned Extra Trees on the full imputed all-school dataset.",
        )

        baseline_summary = summarize_folds(baseline_folds)

        display(result_table(baseline_summary))
        """
    ),
    markdown_cell(
        """
        ## 2. Manual temperature and CO2 threshold features

        This step tests whether simple rule-based indicators add useful information beyond the continuous sensor values already used by the model.

        Three binary features are added:

        - CO2 > 1000 ppm,
        - Temperature < 18 deg C,
        - Temperature > 24 deg C.

        The row population and cross-validation folds remain unchanged, so the deltas can be read directly against the baseline.
        """
    ),
    code_cell(
        """
        def add_threshold_features(frame: pd.DataFrame) -> pd.DataFrame:
            output = frame.copy()
            output["CO2_gt_1000ppm"] = output["CO2"].gt(1000.0).astype(int)
            output["Temperature_lt_18C"] = output["Temperature"].lt(18.0).astype(int)
            output["Temperature_gt_24C"] = output["Temperature"].gt(24.0).astype(int)
            return output


        X_threshold = add_threshold_features(X_base)

        threshold_folds = evaluate_cv_variant(
            "feature_engineering",
            "threshold_flags_co2_1000_t18_t24",
            X_threshold,
            y,
            note="Adds binary CO2 and temperature threshold indicators.",
        )

        threshold_summary = summarize_folds(threshold_folds)

        print("Metric values")
        display(result_table(threshold_summary))
        print("Change relative to main Extra Trees baseline")
        display(metric_change_table(threshold_summary, baseline_summary))
        """
    ),
    markdown_cell(
        """
        ## 3. Imputation indicator columns

        This step tests whether the model benefits from knowing which values were originally missing and later filled by imputation. In other words, the imputed value is kept, but the model also receives an additional 0/1 column identifying that the value was imputed.

        For every model predictor with at least one missing value in the clean dataset, a binary indicator is added. A value of 1 means that the original value was missing before imputation. A summary count of imputed predictors per row is also added.

        This keeps the same row population and validation folds as the baseline. The experiment tests whether missingness itself carries useful information about the observation or measurement context.
        """
    ),
    code_cell(
        """
        def add_missingness_indicators(frame: pd.DataFrame, clean_frame: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
            output = frame.copy()
            indicator_columns = []

            for column in frame.columns:
                if column not in clean_frame.columns:
                    continue
                missing_mask = clean_frame[column].isna()
                if not missing_mask.any():
                    continue
                indicator = f"{column}_was_imputed"
                output[indicator] = missing_mask.astype(int).to_numpy()
                indicator_columns.append(indicator)

            if indicator_columns:
                output["n_imputed_predictors"] = output[indicator_columns].sum(axis=1)
                indicator_columns.append("n_imputed_predictors")

            return output, indicator_columns


        X_missingness, missingness_indicator_columns = add_missingness_indicators(X_base, clean_data)

        print("Added missingness indicators:")
        display(pd.Series(missingness_indicator_columns, name="indicator").to_frame())

        missingness_folds = evaluate_cv_variant(
            "missingness_indicators",
            "imputation_indicators",
            X_missingness,
            y,
            note="Adds binary flags for predictors that were missing before imputation, plus a per-row missingness count.",
        )

        missingness_summary = summarize_folds(missingness_folds)

        print("Metric values")
        display(result_table(missingness_summary))
        print("Change relative to main Extra Trees baseline")
        display(metric_change_table(missingness_summary, baseline_summary))
        """
    ),
    markdown_cell(
        """
        ## 4. Soft-voting ensembles

        This step checks whether the selected Extra Trees model benefits from a small contribution from Random Forest.

        In each fold, both models are trained on the same training data. Their predicted class probabilities are then averaged using fixed weights. For example, `soft_vote_et_0.90_rf_0.10` means 90 percent Extra Trees probability and 10 percent Random Forest probability.

        This is a direct same-population comparison with the baseline, but it increases model complexity because two models must be trained and combined.
        """
    ),
    code_cell(
        """
        def evaluate_soft_vote_weights(X: pd.DataFrame, y_values: pd.Series, weights: list[float]) -> pd.DataFrame:
            rows = []
            cv = StratifiedKFold(n_splits=N_SPLITS, shuffle=True, random_state=SEED)

            for fold, (train_index, test_index) in enumerate(cv.split(X, y_values), start=1):
                X_train, X_test = X.iloc[train_index].copy(), X.iloc[test_index].copy()
                y_train, y_test = y_values.iloc[train_index].copy(), y_values.iloc[test_index].copy()

                et_pipeline = make_pipeline(X, "Extra Trees", EXTRA_TREES_PARAMS, SEED + fold)
                rf_pipeline = make_pipeline(X, "Random Forest", RANDOM_FOREST_PARAMS, SEED + fold)

                start = time.perf_counter()
                et_pipeline.fit(X_train, y_train)
                rf_pipeline.fit(X_train, y_train)
                fit_seconds = time.perf_counter() - start

                start = time.perf_counter()
                et_prob = class_ordered_probabilities(et_pipeline, X_test)
                rf_prob = class_ordered_probabilities(rf_pipeline, X_test)
                predict_seconds = time.perf_counter() - start

                for et_weight in weights:
                    combined = et_weight * et_prob + (1.0 - et_weight) * rf_prob
                    y_pred = pd.Series([CLASS_ORDER[index] for index in np.argmax(combined, axis=1)], index=y_test.index)
                    rows.append(
                        {
                            "experiment": "soft_voting",
                            "variant": f"soft_vote_et_{et_weight:.2f}_rf_{1.0 - et_weight:.2f}",
                            "fold": fold,
                            "cv_splits": N_SPLITS,
                            "model": "Extra Trees + Random Forest",
                            "rows": len(X),
                            "train_rows_after_sampling": len(X_train),
                            "predictors": X.shape[1],
                            "fit_seconds": fit_seconds,
                            "predict_seconds": predict_seconds,
                            "total_seconds": fit_seconds + predict_seconds,
                            "note": "Soft-voting ensemble of tuned Extra Trees and tuned Random Forest probabilities.",
                            **metric_row(y_test, y_pred),
                        }
                    )
            return pd.DataFrame(rows)


        soft_vote_folds = evaluate_soft_vote_weights(X_base, y, SOFT_VOTE_ET_WEIGHTS)

        display(
            result_table(
                summarize_folds(soft_vote_folds)
                .sort_values("macro_f1_mean", ascending=False)
            )
        )
        print("Change relative to main Extra Trees baseline")
        display(
            metric_change_table(
                summarize_folds(soft_vote_folds).sort_values("macro_f1_mean", ascending=False),
                baseline_summary,
            )
        )
        """
    ),
    markdown_cell(
        """
        ## Ordinal classification experiment

        The three-class satisfaction target is ordered: dissatisfied < neutral < satisfied. This experiment tests whether making that order explicit improves the current Extra Trees result.

        The ordinal decomposition trains two binary classifiers inside each cross-validation fold:

        1. IEQ satisfaction > dissatisfied,
        2. IEQ satisfaction > neutral.

        Both binary models are trained only on the training fold. Their validation-fold probabilities are converted back to three-class probabilities:

        - P(dissatisfied) = 1 - P(y > dissatisfied),
        - P(neutral) = P(y > dissatisfied) - P(y > neutral),
        - P(satisfied) = P(y > neutral).

        Because the two binary models are fitted independently, the cumulative probabilities are clipped to maintain a valid ordered probability distribution. The experiment is run with Extra Trees and, as a secondary check, Random Forest.
        """
    ),
    code_cell(
        """
        def positive_class_probability(pipeline: Pipeline, X: pd.DataFrame) -> np.ndarray:
            raw_probabilities = pipeline.predict_proba(X)
            classes = list(pipeline.named_steps["model"].classes_)
            if True not in classes:
                return np.zeros(len(X))
            return raw_probabilities[:, classes.index(True)]


        def reconstruct_ordinal_probabilities(
            probability_gt_dissatisfied: np.ndarray,
            probability_gt_neutral: np.ndarray,
        ) -> np.ndarray:
            p_gt_dissatisfied = np.clip(probability_gt_dissatisfied, 0.0, 1.0)
            p_gt_neutral = np.clip(probability_gt_neutral, 0.0, 1.0)
            p_gt_neutral = np.minimum(p_gt_neutral, p_gt_dissatisfied)

            probabilities = np.column_stack(
                [
                    1.0 - p_gt_dissatisfied,
                    p_gt_dissatisfied - p_gt_neutral,
                    p_gt_neutral,
                ]
            )
            probabilities = np.clip(probabilities, 0.0, 1.0)
            row_sums = probabilities.sum(axis=1, keepdims=True)
            return probabilities / np.where(row_sums == 0.0, 1.0, row_sums)


        def evaluate_ordinal_decomposition(
            X: pd.DataFrame,
            y_values: pd.Series,
            *,
            model_name: str,
            params: dict,
            variant: str,
        ) -> tuple[pd.DataFrame, pd.DataFrame]:
            rows = []
            predictions = []
            y_numeric = y_values.map(CLASS_TO_NUMBER)
            cv = StratifiedKFold(n_splits=N_SPLITS, shuffle=True, random_state=SEED)

            for fold, (train_index, test_index) in enumerate(cv.split(X, y_values), start=1):
                X_train, X_test = X.iloc[train_index].copy(), X.iloc[test_index].copy()
                y_train, y_test = y_values.iloc[train_index].copy(), y_values.iloc[test_index].copy()
                y_train_numeric = y_numeric.iloc[train_index]

                gt_dissatisfied_pipeline = make_pipeline(X, model_name, params, SEED + fold)
                gt_neutral_pipeline = make_pipeline(X, model_name, params, SEED + 100 + fold)

                start = time.perf_counter()
                gt_dissatisfied_pipeline.fit(X_train, y_train_numeric.gt(CLASS_TO_NUMBER["dissatisfied"]))
                gt_neutral_pipeline.fit(X_train, y_train_numeric.gt(CLASS_TO_NUMBER["neutral"]))
                fit_seconds = time.perf_counter() - start

                start = time.perf_counter()
                p_gt_dissatisfied = positive_class_probability(gt_dissatisfied_pipeline, X_test)
                p_gt_neutral = positive_class_probability(gt_neutral_pipeline, X_test)
                class_probabilities = reconstruct_ordinal_probabilities(p_gt_dissatisfied, p_gt_neutral)
                y_pred = pd.Series(
                    [CLASS_ORDER[index] for index in np.argmax(class_probabilities, axis=1)],
                    index=y_test.index,
                )
                predict_seconds = time.perf_counter() - start

                rows.append(
                    {
                        "experiment": "ordinal_classification",
                        "variant": variant,
                        "fold": fold,
                        "cv_splits": N_SPLITS,
                        "model": model_name,
                        "rows": len(X),
                        "train_rows_after_sampling": len(X_train),
                        "predictors": X.shape[1],
                        "fit_seconds": fit_seconds,
                        "predict_seconds": predict_seconds,
                        "total_seconds": fit_seconds + predict_seconds,
                        "note": "Two-threshold ordinal decomposition with fold-internal binary classifiers.",
                        **metric_row(y_test, y_pred),
                    }
                )

                predictions.append(
                    pd.DataFrame(
                        {
                            "variant": variant,
                            "fold": fold,
                            "row_id": y_test.index,
                            "y_true": y_test.to_numpy(),
                            "y_pred": y_pred.to_numpy(),
                            "prob_dissatisfied": class_probabilities[:, 0],
                            "prob_neutral": class_probabilities[:, 1],
                            "prob_satisfied": class_probabilities[:, 2],
                            "prob_y_gt_dissatisfied": p_gt_dissatisfied,
                            "prob_y_gt_neutral": p_gt_neutral,
                        }
                    )
                )

            return pd.DataFrame(rows), pd.concat(predictions, ignore_index=True)


        ordinal_specs = [
            ("ordinal_extra_trees_decomposition", "Extra Trees", EXTRA_TREES_PARAMS),
            ("ordinal_random_forest_decomposition", "Random Forest", RANDOM_FOREST_PARAMS),
        ]

        ordinal_fold_tables = []
        ordinal_prediction_tables = []

        for variant, model_name, params in ordinal_specs:
            folds, predictions = evaluate_ordinal_decomposition(
                X_base,
                y,
                model_name=model_name,
                params=params,
                variant=variant,
            )
            ordinal_fold_tables.append(folds)
            ordinal_prediction_tables.append(predictions)

        ordinal_folds = pd.concat(ordinal_fold_tables, ignore_index=True)
        ordinal_predictions = pd.concat(ordinal_prediction_tables, ignore_index=True)
        ordinal_summary = summarize_folds(ordinal_folds).sort_values("macro_f1_mean", ascending=False).reset_index(drop=True)

        ordinal_comparison = pd.concat([baseline_summary, ordinal_summary], ignore_index=True)
        ordinal_baseline_row = ordinal_comparison[ordinal_comparison["variant"].eq("main_all_school_extra_trees")].iloc[0]
        for metric in REPORT_METRICS:
            ordinal_comparison[f"{metric}_delta_vs_main"] = (
                ordinal_comparison[f"{metric}_mean"] - ordinal_baseline_row[f"{metric}_mean"]
            )
        ordinal_comparison["same_population_as_main"] = ordinal_comparison["rows"].eq(int(ordinal_baseline_row["rows"]))

        ordinal_comparison_table = ordinal_comparison[
            [
                "variant",
                "model",
                "cv_splits",
                "rows",
                "predictors",
                "same_population_as_main",
                "macro_f1_mean",
                "macro_f1_delta_vs_main",
                "accuracy_mean",
                "accuracy_delta_vs_main",
                "balanced_accuracy_mean",
                "balanced_accuracy_delta_vs_main",
                "ordinal_mae_mean",
                "ordinal_mae_delta_vs_main",
            ]
        ].copy()

        for column in ordinal_comparison_table.select_dtypes(include=["float"]).columns:
            ordinal_comparison_table[column] = ordinal_comparison_table[column].round(6)

        print("Ordinal decomposition comparison")
        display(ordinal_comparison_table)

        best_ordinal_variant = ordinal_summary.iloc[0]["variant"]
        best_ordinal_predictions = ordinal_predictions[ordinal_predictions["variant"].eq(best_ordinal_variant)].copy()
        best_ordinal_confusion = pd.DataFrame(
            confusion_matrix(best_ordinal_predictions["y_true"], best_ordinal_predictions["y_pred"], labels=CLASS_ORDER),
            index=CLASS_ORDER,
            columns=CLASS_ORDER,
        )

        print("Best ordinal variant by macro F1:", best_ordinal_variant)
        display(best_ordinal_confusion)

        ordinal_folds_path = OUTPUT_DIR / "ieq_ordinal_classification_folds.csv"
        ordinal_predictions_path = OUTPUT_DIR / "ieq_ordinal_classification_predictions.csv"
        ordinal_summary_path = OUTPUT_DIR / "ieq_ordinal_classification_summary.csv"
        ordinal_comparison_path = OUTPUT_DIR / "ieq_ordinal_classification_comparison.csv"
        ordinal_confusion_path = OUTPUT_DIR / "ieq_ordinal_classification_best_confusion_matrix.csv"

        ordinal_folds.to_csv(ordinal_folds_path, index=False)
        ordinal_predictions.to_csv(ordinal_predictions_path, index=False)
        ordinal_summary.to_csv(ordinal_summary_path, index=False)
        ordinal_comparison_table.to_csv(ordinal_comparison_path, index=False)
        best_ordinal_confusion.to_csv(ordinal_confusion_path)

        fig, ax = plt.subplots(figsize=(4.8, 4.2), constrained_layout=True)
        image = ax.imshow(best_ordinal_confusion.to_numpy(), cmap="Blues")
        ax.set_xticks(np.arange(len(CLASS_ORDER)), labels=CLASS_ORDER, rotation=30, ha="right")
        ax.set_yticks(np.arange(len(CLASS_ORDER)), labels=CLASS_ORDER)
        ax.set_xlabel("Predicted class")
        ax.set_ylabel("True class")
        ax.set_title(best_ordinal_variant.replace("_", " "))
        for row in range(len(CLASS_ORDER)):
            for column in range(len(CLASS_ORDER)):
                value = int(best_ordinal_confusion.iloc[row, column])
                ax.text(column, row, value, ha="center", va="center", color="black")
        fig.colorbar(image, ax=ax, fraction=0.046, pad=0.04)

        ordinal_confusion_figure_path = FIGURE_DIR / "ieq_ordinal_classification_best_confusion_matrix.png"
        fig.savefig(ordinal_confusion_figure_path, dpi=220, bbox_inches="tight")
        print("Saved ordinal fold-level results to:", ordinal_folds_path)
        print("Saved ordinal predictions to:", ordinal_predictions_path)
        print("Saved ordinal summary to:", ordinal_summary_path)
        print("Saved ordinal comparison table to:", ordinal_comparison_path)
        print("Saved best ordinal confusion matrix to:", ordinal_confusion_path)
        print("Saved best ordinal confusion figure to:", ordinal_confusion_figure_path)
        plt.show()
        """
    ),
    markdown_cell(
        """
        ## Class-weight and threshold tuning

        This section tests two imbalance-focused strategies while keeping the main Extra Trees baseline unchanged.

        Part A searches several class-weight settings for the three ordered labels. The numeric shorthand follows the ordinal target coding: 0 = dissatisfied, 1 = neutral, and 2 = satisfied. The model itself receives label-based class weights.

        Part B takes the best class-weight setting from Part A and tunes simple class-specific probability multipliers. To avoid evaluating a threshold on the same predictions used to choose it, the multipliers are selected inside each outer training fold using an inner cross-validation loop. The selected multipliers are then applied to the held-out outer validation fold.
        """
    ),
    code_cell(
        """
        RECALL_COLUMNS = [f"recall_{label}" for label in CLASS_ORDER]


        def class_weight_from_numeric(numeric_weights: dict[int, float]) -> dict[str, float]:
            return {CLASS_ORDER[class_number]: weight for class_number, weight in numeric_weights.items()}


        CLASS_WEIGHT_SPECS = [
            {
                "variant": "class_weight_balanced",
                "class_weight": "balanced",
                "description": "Baseline Extra Trees balanced class weights.",
            },
            {
                "variant": "class_weight_equal_1_1_1",
                "class_weight": class_weight_from_numeric({0: 1, 1: 1, 2: 1}),
                "description": "Manual equal class weights: {0: 1, 1: 1, 2: 1}.",
            },
            {
                "variant": "class_weight_dissatisfied_2_neutral_1_5",
                "class_weight": class_weight_from_numeric({0: 2, 1: 1.5, 2: 1}),
                "description": "Manual class weights: {0: 2, 1: 1.5, 2: 1}.",
            },
            {
                "variant": "class_weight_dissatisfied_3_neutral_2",
                "class_weight": class_weight_from_numeric({0: 3, 1: 2, 2: 1}),
                "description": "Manual class weights: {0: 3, 1: 2, 2: 1}.",
            },
            {
                "variant": "class_weight_dissatisfied_4_neutral_2",
                "class_weight": class_weight_from_numeric({0: 4, 1: 2, 2: 1}),
                "description": "Manual class weights: {0: 4, 1: 2, 2: 1}.",
            },
            {
                "variant": "class_weight_dissatisfied_5_neutral_2",
                "class_weight": class_weight_from_numeric({0: 5, 1: 2, 2: 1}),
                "description": "Manual class weights: {0: 5, 1: 2, 2: 1}.",
            },
            {
                "variant": "class_weight_stronger_dissatisfied",
                "class_weight": class_weight_from_numeric({0: 4, 1: 1, 2: 1}),
                "description": "Stronger dissatisfied weight only.",
            },
            {
                "variant": "class_weight_stronger_neutral",
                "class_weight": class_weight_from_numeric({0: 1, 1: 2.5, 2: 1}),
                "description": "Stronger neutral weight only.",
            },
            {
                "variant": "class_weight_stronger_dissatisfied_neutral",
                "class_weight": class_weight_from_numeric({0: 4, 1: 2.5, 2: 1}),
                "description": "Stronger dissatisfied and neutral weights.",
            },
        ]

        CLASS_WEIGHT_SPEC_BY_VARIANT = {spec["variant"]: spec for spec in CLASS_WEIGHT_SPECS}


        def extra_trees_params_with_class_weight(class_weight: str | dict[str, float]) -> dict:
            params = EXTRA_TREES_PARAMS.copy()
            params["model__class_weight"] = class_weight
            return params


        def per_class_recall_row(y_true: pd.Series, y_pred: pd.Series | np.ndarray) -> dict[str, float]:
            recalls = recall_score(y_true, y_pred, labels=CLASS_ORDER, average=None, zero_division=0)
            return {f"recall_{label}": float(value) for label, value in zip(CLASS_ORDER, recalls)}


        def evaluate_class_weight_variant(
            X: pd.DataFrame,
            y_values: pd.Series,
            *,
            variant: str,
            class_weight: str | dict[str, float],
            note: str,
        ) -> tuple[pd.DataFrame, pd.DataFrame]:
            params = extra_trees_params_with_class_weight(class_weight)
            rows = []
            predictions = []
            cv = StratifiedKFold(n_splits=N_SPLITS, shuffle=True, random_state=SEED)

            for fold, (train_index, test_index) in enumerate(cv.split(X, y_values), start=1):
                X_train, X_test = X.iloc[train_index].copy(), X.iloc[test_index].copy()
                y_train, y_test = y_values.iloc[train_index].copy(), y_values.iloc[test_index].copy()

                pipeline = make_pipeline(X, model_name="Extra Trees", params=params, seed=SEED + fold)

                start = time.perf_counter()
                pipeline.fit(X_train, y_train)
                fit_seconds = time.perf_counter() - start

                start = time.perf_counter()
                probabilities = class_ordered_probabilities(pipeline, X_test)
                y_pred = pd.Series([CLASS_ORDER[index] for index in np.argmax(probabilities, axis=1)], index=y_test.index)
                predict_seconds = time.perf_counter() - start

                rows.append(
                    {
                        "experiment": "class_weight_search",
                        "variant": variant,
                        "fold": fold,
                        "cv_splits": N_SPLITS,
                        "model": "Extra Trees",
                        "rows": len(X),
                        "train_rows_after_sampling": len(X_train),
                        "predictors": X.shape[1],
                        "fit_seconds": fit_seconds,
                        "predict_seconds": predict_seconds,
                        "total_seconds": fit_seconds + predict_seconds,
                        "note": note,
                        "class_weight": str(class_weight),
                        **metric_row(y_test, y_pred),
                        **per_class_recall_row(y_test, y_pred),
                    }
                )

                predictions.append(
                    pd.DataFrame(
                        {
                            "variant": variant,
                            "fold": fold,
                            "row_id": y_test.index,
                            "y_true": y_test.to_numpy(),
                            "y_pred": y_pred.to_numpy(),
                            "prob_dissatisfied": probabilities[:, 0],
                            "prob_neutral": probabilities[:, 1],
                            "prob_satisfied": probabilities[:, 2],
                        }
                    )
                )

            return pd.DataFrame(rows), pd.concat(predictions, ignore_index=True)


        def summarize_class_weight_folds(folds: pd.DataFrame) -> pd.DataFrame:
            group_columns = ["experiment", "variant", "cv_splits", "model", "rows", "predictors", "note"]
            metric_columns = REPORT_METRICS + RECALL_COLUMNS + ["fit_seconds", "predict_seconds", "total_seconds", "train_rows_after_sampling"]
            summary = folds.groupby(group_columns, dropna=False)[metric_columns].agg(["mean", "std"]).reset_index()
            summary.columns = [
                "_".join(column).rstrip("_") if isinstance(column, tuple) else column
                for column in summary.columns
            ]
            return summary


        class_weight_fold_tables = []
        class_weight_prediction_tables = []

        for spec in CLASS_WEIGHT_SPECS:
            folds, predictions = evaluate_class_weight_variant(
                X_base,
                y,
                variant=spec["variant"],
                class_weight=spec["class_weight"],
                note=spec["description"],
            )
            class_weight_fold_tables.append(folds)
            class_weight_prediction_tables.append(predictions)

        class_weight_folds = pd.concat(class_weight_fold_tables, ignore_index=True)
        class_weight_predictions = pd.concat(class_weight_prediction_tables, ignore_index=True)
        class_weight_summary = (
            summarize_class_weight_folds(class_weight_folds)
            .sort_values("macro_f1_mean", ascending=False)
            .reset_index(drop=True)
        )
        best_class_weight_variant = class_weight_summary.iloc[0]["variant"]

        class_weight_display_columns = [
            "variant",
            "macro_f1_mean",
            "accuracy_mean",
            "balanced_accuracy_mean",
            "ordinal_mae_mean",
            "recall_dissatisfied_mean",
            "recall_neutral_mean",
            "recall_satisfied_mean",
        ]
        class_weight_display = class_weight_summary[class_weight_display_columns].copy()
        for column in class_weight_display.select_dtypes(include=["float"]).columns:
            class_weight_display[column] = class_weight_display[column].round(6)

        print("Class-weight search results, sorted by macro F1")
        display(class_weight_display)
        print("Best class-weight variant:", best_class_weight_variant)
        """
    ),
    code_cell(
        """
        PROBABILITY_MULTIPLIER_GRID = [
            {"dissatisfied": m0, "neutral": m1, "satisfied": 1.0}
            for m0 in [1.0, 1.2, 1.5, 2.0, 2.5]
            for m1 in [1.0, 1.2, 1.5, 2.0]
        ]


        def apply_probability_multipliers(probabilities: np.ndarray, multipliers: dict[str, float]) -> np.ndarray:
            multiplier_array = np.array([multipliers[label] for label in CLASS_ORDER])
            adjusted = probabilities * multiplier_array
            row_sums = adjusted.sum(axis=1, keepdims=True)
            return adjusted / np.where(row_sums == 0.0, 1.0, row_sums)


        def labels_from_probabilities(probabilities: np.ndarray) -> np.ndarray:
            return np.array([CLASS_ORDER[index] for index in np.argmax(probabilities, axis=1)])


        def select_probability_multipliers(
            probabilities: np.ndarray,
            y_true: pd.Series,
            grid: list[dict[str, float]],
        ) -> tuple[dict[str, float], pd.DataFrame]:
            rows = []
            for multipliers in grid:
                adjusted = apply_probability_multipliers(probabilities, multipliers)
                y_pred = labels_from_probabilities(adjusted)
                rows.append(
                    {
                        "multiplier_dissatisfied": multipliers["dissatisfied"],
                        "multiplier_neutral": multipliers["neutral"],
                        "multiplier_satisfied": multipliers["satisfied"],
                        **metric_row(y_true, y_pred),
                        **per_class_recall_row(y_true, y_pred),
                    }
                )
            grid_results = pd.DataFrame(rows).sort_values(
                ["macro_f1", "balanced_accuracy", "ordinal_mae"],
                ascending=[False, False, True],
            )
            best = grid_results.iloc[0]
            return (
                {
                    "dissatisfied": float(best["multiplier_dissatisfied"]),
                    "neutral": float(best["multiplier_neutral"]),
                    "satisfied": float(best["multiplier_satisfied"]),
                },
                grid_results,
            )


        def inner_oof_probabilities_for_threshold_tuning(
            X_train_outer: pd.DataFrame,
            y_train_outer: pd.Series,
            *,
            params: dict,
            outer_fold: int,
        ) -> tuple[np.ndarray, pd.Series]:
            probabilities = np.zeros((len(X_train_outer), len(CLASS_ORDER)))
            inner_cv = StratifiedKFold(
                n_splits=THRESHOLD_INNER_SPLITS,
                shuffle=True,
                random_state=SEED + 1000 + outer_fold,
            )

            for inner_fold, (inner_train_index, inner_valid_index) in enumerate(
                inner_cv.split(X_train_outer, y_train_outer),
                start=1,
            ):
                X_inner_train = X_train_outer.iloc[inner_train_index].copy()
                X_inner_valid = X_train_outer.iloc[inner_valid_index].copy()
                y_inner_train = y_train_outer.iloc[inner_train_index].copy()

                pipeline = make_pipeline(
                    X_train_outer,
                    model_name="Extra Trees",
                    params=params,
                    seed=SEED + outer_fold * 100 + inner_fold,
                )
                pipeline.fit(X_inner_train, y_inner_train)
                probabilities[inner_valid_index, :] = class_ordered_probabilities(pipeline, X_inner_valid)

            return probabilities, y_train_outer.reset_index(drop=True)


        def evaluate_nested_threshold_adjustment(
            X: pd.DataFrame,
            y_values: pd.Series,
            *,
            base_variant: str,
            class_weight: str | dict[str, float],
        ) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
            params = extra_trees_params_with_class_weight(class_weight)
            rows = []
            predictions = []
            grid_rows = []
            cv = StratifiedKFold(n_splits=N_SPLITS, shuffle=True, random_state=SEED)

            for fold, (train_index, test_index) in enumerate(cv.split(X, y_values), start=1):
                X_train, X_test = X.iloc[train_index].copy(), X.iloc[test_index].copy()
                y_train, y_test = y_values.iloc[train_index].copy(), y_values.iloc[test_index].copy()

                inner_probabilities, inner_y = inner_oof_probabilities_for_threshold_tuning(
                    X_train.reset_index(drop=True),
                    y_train.reset_index(drop=True),
                    params=params,
                    outer_fold=fold,
                )
                selected_multipliers, grid_results = select_probability_multipliers(
                    inner_probabilities,
                    inner_y,
                    PROBABILITY_MULTIPLIER_GRID,
                )
                grid_results = grid_results.copy()
                grid_results["outer_fold"] = fold
                grid_results["base_variant"] = base_variant
                grid_rows.append(grid_results)

                pipeline = make_pipeline(X, model_name="Extra Trees", params=params, seed=SEED + 2000 + fold)

                start = time.perf_counter()
                pipeline.fit(X_train, y_train)
                fit_seconds = time.perf_counter() - start

                start = time.perf_counter()
                probabilities = class_ordered_probabilities(pipeline, X_test)
                adjusted_probabilities = apply_probability_multipliers(probabilities, selected_multipliers)
                y_pred = pd.Series(labels_from_probabilities(adjusted_probabilities), index=y_test.index)
                predict_seconds = time.perf_counter() - start

                rows.append(
                    {
                        "experiment": "class_weight_threshold_tuning",
                        "variant": "best_class_weight_nested_threshold",
                        "fold": fold,
                        "cv_splits": N_SPLITS,
                        "model": "Extra Trees",
                        "rows": len(X),
                        "train_rows_after_sampling": len(X_train),
                        "predictors": X.shape[1],
                        "fit_seconds": fit_seconds,
                        "predict_seconds": predict_seconds,
                        "total_seconds": fit_seconds + predict_seconds,
                        "note": f"Nested inner-fold probability multiplier tuning applied to {base_variant}.",
                        "base_class_weight_variant": base_variant,
                        "multiplier_dissatisfied": selected_multipliers["dissatisfied"],
                        "multiplier_neutral": selected_multipliers["neutral"],
                        "multiplier_satisfied": selected_multipliers["satisfied"],
                        **metric_row(y_test, y_pred),
                        **per_class_recall_row(y_test, y_pred),
                    }
                )

                predictions.append(
                    pd.DataFrame(
                        {
                            "variant": "best_class_weight_nested_threshold",
                            "fold": fold,
                            "row_id": y_test.index,
                            "y_true": y_test.to_numpy(),
                            "y_pred": y_pred.to_numpy(),
                            "prob_dissatisfied": probabilities[:, 0],
                            "prob_neutral": probabilities[:, 1],
                            "prob_satisfied": probabilities[:, 2],
                            "adjusted_prob_dissatisfied": adjusted_probabilities[:, 0],
                            "adjusted_prob_neutral": adjusted_probabilities[:, 1],
                            "adjusted_prob_satisfied": adjusted_probabilities[:, 2],
                            "multiplier_dissatisfied": selected_multipliers["dissatisfied"],
                            "multiplier_neutral": selected_multipliers["neutral"],
                            "multiplier_satisfied": selected_multipliers["satisfied"],
                        }
                    )
                )

            return pd.DataFrame(rows), pd.concat(predictions, ignore_index=True), pd.concat(grid_rows, ignore_index=True)


        best_class_weight_spec = CLASS_WEIGHT_SPEC_BY_VARIANT[best_class_weight_variant]
        class_weight_threshold_folds, threshold_predictions, threshold_grid_results = evaluate_nested_threshold_adjustment(
            X_base,
            y,
            base_variant=best_class_weight_variant,
            class_weight=best_class_weight_spec["class_weight"],
        )
        class_weight_threshold_summary = summarize_class_weight_folds(class_weight_threshold_folds)

        class_weight_best_summary = class_weight_summary[
            class_weight_summary["variant"].eq(best_class_weight_variant)
        ].copy()

        class_weight_threshold_comparison = pd.concat(
            [
                baseline_summary,
                class_weight_best_summary,
                class_weight_threshold_summary,
            ],
            ignore_index=True,
            sort=False,
        )
        baseline_for_threshold = class_weight_threshold_comparison[
            class_weight_threshold_comparison["variant"].eq("main_all_school_extra_trees")
        ].iloc[0]
        for metric in REPORT_METRICS:
            class_weight_threshold_comparison[f"{metric}_delta_vs_main"] = (
                class_weight_threshold_comparison[f"{metric}_mean"] - baseline_for_threshold[f"{metric}_mean"]
            )
        class_weight_threshold_comparison["same_population_as_main"] = class_weight_threshold_comparison["rows"].eq(
            int(baseline_for_threshold["rows"])
        )

        threshold_display_columns = [
            "variant",
            "macro_f1_mean",
            "macro_f1_delta_vs_main",
            "accuracy_mean",
            "accuracy_delta_vs_main",
            "balanced_accuracy_mean",
            "balanced_accuracy_delta_vs_main",
            "ordinal_mae_mean",
            "ordinal_mae_delta_vs_main",
            "recall_dissatisfied_mean",
            "recall_neutral_mean",
            "recall_satisfied_mean",
        ]
        threshold_display = class_weight_threshold_comparison[threshold_display_columns].copy()
        for column in threshold_display.select_dtypes(include=["float"]).columns:
            threshold_display[column] = threshold_display[column].round(6)

        print("Baseline vs best class-weight vs nested threshold-adjusted Extra Trees")
        display(threshold_display)
        print("Selected multipliers by outer fold")
        display(
            class_weight_threshold_folds[
                ["fold", "base_class_weight_variant", "multiplier_dissatisfied", "multiplier_neutral", "multiplier_satisfied"]
            ]
        )
        """
    ),
    code_cell(
        """
        def confusion_matrix_for_predictions(predictions: pd.DataFrame, variant: str) -> pd.DataFrame:
            selected = predictions[predictions["variant"].eq(variant)].copy()
            return pd.DataFrame(
                confusion_matrix(selected["y_true"], selected["y_pred"], labels=CLASS_ORDER),
                index=CLASS_ORDER,
                columns=CLASS_ORDER,
            )


        baseline_class_weight_variant = "class_weight_balanced"
        class_weight_best_predictions = class_weight_predictions[
            class_weight_predictions["variant"].eq(best_class_weight_variant)
        ].copy()

        class_weight_threshold_predictions = pd.concat(
            [
                class_weight_predictions[
                    class_weight_predictions["variant"].isin([baseline_class_weight_variant, best_class_weight_variant])
                ],
                threshold_predictions,
            ],
            ignore_index=True,
            sort=False,
        )

        confusion_variants = [
            ("Main all-school Extra Trees baseline", baseline_class_weight_variant),
            ("Best class-weight Extra Trees", best_class_weight_variant),
            ("Best class-weight + nested threshold", "best_class_weight_nested_threshold"),
        ]

        confusion_tables = []
        for label, variant in confusion_variants:
            matrix = confusion_matrix_for_predictions(class_weight_threshold_predictions, variant)
            long_matrix = matrix.reset_index(names="true_class").melt(
                id_vars="true_class",
                var_name="predicted_class",
                value_name="count",
            )
            long_matrix.insert(0, "label", label)
            long_matrix.insert(1, "variant", variant)
            confusion_tables.append(long_matrix)

        class_weight_threshold_confusions = pd.concat(confusion_tables, ignore_index=True)

        fig, axes = plt.subplots(1, 3, figsize=(12.5, 3.8), constrained_layout=True)
        max_count = 0
        confusion_matrices = []
        for _, variant in confusion_variants:
            matrix = confusion_matrix_for_predictions(class_weight_threshold_predictions, variant)
            confusion_matrices.append(matrix)
            max_count = max(max_count, int(matrix.to_numpy().max()))

        for ax, (label, _), matrix in zip(axes, confusion_variants, confusion_matrices):
            image = ax.imshow(matrix.to_numpy(), cmap="Blues", vmin=0, vmax=max_count)
            ax.set_title(label)
            ax.set_xticks(np.arange(len(CLASS_ORDER)), labels=CLASS_ORDER, rotation=30, ha="right")
            ax.set_yticks(np.arange(len(CLASS_ORDER)), labels=CLASS_ORDER)
            ax.set_xlabel("Predicted class")
            ax.set_ylabel("True class")
            for row in range(len(CLASS_ORDER)):
                for column in range(len(CLASS_ORDER)):
                    ax.text(column, row, int(matrix.iloc[row, column]), ha="center", va="center", color="black")
        fig.colorbar(image, ax=axes, fraction=0.025, pad=0.02)

        class_weight_folds_path = OUTPUT_DIR / "ieq_class_weight_search_folds.csv"
        class_weight_summary_path = OUTPUT_DIR / "ieq_class_weight_search_summary.csv"
        class_weight_predictions_path = OUTPUT_DIR / "ieq_class_weight_search_predictions.csv"
        threshold_folds_path = OUTPUT_DIR / "ieq_class_weight_threshold_folds.csv"
        threshold_grid_path = OUTPUT_DIR / "ieq_class_weight_threshold_inner_grid.csv"
        threshold_predictions_path = OUTPUT_DIR / "ieq_class_weight_threshold_predictions.csv"
        threshold_comparison_path = OUTPUT_DIR / "ieq_class_weight_threshold_comparison.csv"
        threshold_confusions_path = OUTPUT_DIR / "ieq_class_weight_threshold_confusion_matrices.csv"
        threshold_figure_path = FIGURE_DIR / "ieq_class_weight_threshold_confusion_matrices.png"

        class_weight_folds.to_csv(class_weight_folds_path, index=False)
        class_weight_summary.to_csv(class_weight_summary_path, index=False)
        class_weight_predictions.to_csv(class_weight_predictions_path, index=False)
        class_weight_threshold_folds.to_csv(threshold_folds_path, index=False)
        threshold_grid_results.to_csv(threshold_grid_path, index=False)
        threshold_predictions.to_csv(threshold_predictions_path, index=False)
        threshold_display.to_csv(threshold_comparison_path, index=False)
        class_weight_threshold_confusions.to_csv(threshold_confusions_path, index=False)
        fig.savefig(threshold_figure_path, dpi=220, bbox_inches="tight")

        print("Saved class-weight folds to:", class_weight_folds_path)
        print("Saved class-weight summary to:", class_weight_summary_path)
        print("Saved class-weight predictions to:", class_weight_predictions_path)
        print("Saved nested threshold folds to:", threshold_folds_path)
        print("Saved nested threshold inner-grid results to:", threshold_grid_path)
        print("Saved nested threshold predictions to:", threshold_predictions_path)
        print("Saved comparison table to:", threshold_comparison_path)
        print("Saved confusion matrices to:", threshold_confusions_path)
        print("Saved confusion-matrix figure to:", threshold_figure_path)
        plt.show()
        """
    ),
    markdown_cell(
        """
        ## Complete-case data-quality checks

        This step tests whether performance changes when the model is evaluated only on records with originally observed sensor values.

        Two filters are used:

        - complete main IEQ sensors: Temperature, RH, CO2, Lighting, and Sound were all originally present;
        - complete Lighting, Sound, and Ttrend: the most incomplete sensor/context variables were originally present.

        These experiments do not use the same row population as the baseline. A higher macro F1 therefore indicates that prediction is easier on this restricted subset, not necessarily that the main model should discard incomplete rows.
        """
    ),
    code_cell(
        """
        complete_main_sensor_mask = clean_data[["Temperature", "RH", "CO2", "Lighting", "Sound"]].notna().all(axis=1)
        complete_lighting_sound_ttrend_mask = clean_data[["Lighting", "Sound", "Ttrend"]].notna().all(axis=1)

        complete_case_specs = [
            (
                "complete_main_ieq_sensors",
                complete_main_sensor_mask,
                "Rows with originally observed Temperature, RH, CO2, Lighting, and Sound.",
            ),
            (
                "complete_lighting_sound_ttrend",
                complete_lighting_sound_ttrend_mask,
                "Rows with originally observed Lighting, Sound, and Ttrend.",
            ),
        ]

        complete_case_folds = []
        for variant, mask, note in complete_case_specs:
            X_filtered = X_base.loc[mask].reset_index(drop=True)
            y_filtered = y.loc[mask].reset_index(drop=True)
            print(variant, "rows:", len(y_filtered))
            complete_case_folds.append(
                evaluate_cv_variant(
                    "complete_case_filter",
                    variant,
                    X_filtered,
                    y_filtered,
                    note=note,
                )
            )

        complete_case_folds = pd.concat(complete_case_folds, ignore_index=True)

        display(
            result_table(
                summarize_folds(complete_case_folds)
                .sort_values("macro_f1_mean", ascending=False)
            )
        )
        print("Change relative to main Extra Trees baseline")
        display(
            metric_change_table(
                summarize_folds(complete_case_folds).sort_values("macro_f1_mean", ascending=False),
                baseline_summary,
            )
        )
        """
    ),
    markdown_cell(
        """
        ## Train-fold-only class balancing

        This step tests whether the minority classes benefit from balancing the training data.

        The validation folds are never resampled. Only the training part of each fold is modified, so duplicated or synthetic records cannot enter the validation data. Three variants are screened:

        - random oversampling of minority classes up to 50 percent of the majority class;
        - synthetic interpolation up to 50 percent of the majority class;
        - synthetic interpolation up to full class balance.

        The comparison uses the same validation rows as the baseline, but the training distribution is altered inside each fold.
        """
    ),
    code_cell(
        """
        CONTINUOUS_SYNTHETIC_COLUMNS = [
            "Temperature",
            "RH",
            "CLO",
            "CO2",
            "Lighting",
            "Sound",
            "Age",
            "EA",
            "Ttrend",
            "Vote hour",
        ]


        def target_count_for_class(y_train: pd.Series, class_label: str, fraction_of_majority: float) -> int:
            counts = y_train.value_counts()
            majority_count = int(counts.max())
            current_count = int(counts.get(class_label, 0))
            return max(current_count, int(np.ceil(majority_count * fraction_of_majority)))


        def random_oversample_to_fraction(fraction_of_majority: float) -> SamplingFunction:
            def sampler(X_train: pd.DataFrame, y_train: pd.Series, fold: int) -> tuple[pd.DataFrame, pd.Series]:
                rng = np.random.default_rng(SEED + fold * 100)
                X_parts = [X_train]
                y_parts = [y_train]

                for class_label in CLASS_ORDER:
                    class_indices = np.flatnonzero(y_train.to_numpy() == class_label)
                    if len(class_indices) == 0:
                        continue
                    target_count = target_count_for_class(y_train, class_label, fraction_of_majority)
                    add_count = target_count - len(class_indices)
                    if add_count <= 0:
                        continue
                    chosen_positions = rng.choice(class_indices, size=add_count, replace=True)
                    X_parts.append(X_train.iloc[chosen_positions].copy())
                    y_parts.append(y_train.iloc[chosen_positions].copy())

                return pd.concat(X_parts, ignore_index=True), pd.concat(y_parts, ignore_index=True)

            return sampler


        def synthetic_interpolate_to_fraction(fraction_of_majority: float) -> SamplingFunction:
            def sampler(X_train: pd.DataFrame, y_train: pd.Series, fold: int) -> tuple[pd.DataFrame, pd.Series]:
                rng = np.random.default_rng(SEED + fold * 1000)
                synthetic_rows = []
                synthetic_labels = []
                continuous_columns = [column for column in CONTINUOUS_SYNTHETIC_COLUMNS if column in X_train.columns]

                for class_label in CLASS_ORDER:
                    class_positions = np.flatnonzero(y_train.to_numpy() == class_label)
                    if len(class_positions) < 2:
                        continue
                    target_count = target_count_for_class(y_train, class_label, fraction_of_majority)
                    add_count = target_count - len(class_positions)
                    if add_count <= 0:
                        continue

                    first_positions = rng.choice(class_positions, size=add_count, replace=True)
                    second_positions = rng.choice(class_positions, size=add_count, replace=True)
                    alpha = rng.random(add_count)

                    first_rows = X_train.iloc[first_positions].reset_index(drop=True)
                    second_rows = X_train.iloc[second_positions].reset_index(drop=True)
                    generated = first_rows.copy()

                    for column in continuous_columns:
                        generated[column] = first_rows[column].to_numpy() + alpha * (
                            second_rows[column].to_numpy() - first_rows[column].to_numpy()
                        )

                    non_continuous = [column for column in X_train.columns if column not in continuous_columns]
                    for column in non_continuous:
                        choose_second = rng.random(add_count) < 0.5
                        generated.loc[choose_second, column] = second_rows.loc[choose_second, column].to_numpy()

                    synthetic_rows.append(generated)
                    synthetic_labels.extend([class_label] * add_count)

                if not synthetic_rows:
                    return X_train.copy(), y_train.copy()

                X_augmented = pd.concat([X_train, *synthetic_rows], ignore_index=True)
                y_augmented = pd.concat([y_train.reset_index(drop=True), pd.Series(synthetic_labels)], ignore_index=True)
                return X_augmented, y_augmented

            return sampler
        """
    ),
    code_cell(
        """
        sampling_folds = pd.DataFrame()

        if RUN_SYNTHETIC_SAMPLING:
            sampling_specs = [
                (
                    "random_oversample_to_50pct_majority",
                    random_oversample_to_fraction(0.50),
                    "Randomly duplicates minority-class training records up to 50 percent of the majority-class count.",
                ),
                (
                    "synthetic_interpolate_to_50pct_majority",
                    synthetic_interpolate_to_fraction(0.50),
                    "Creates fold-internal synthetic minority-class training rows up to 50 percent of the majority-class count.",
                ),
                (
                    "synthetic_interpolate_to_majority",
                    synthetic_interpolate_to_fraction(1.00),
                    "Creates fold-internal synthetic minority-class training rows up to the majority-class count.",
                ),
            ]

            sampling_folds = pd.concat(
                [
                    evaluate_cv_variant(
                        "train_fold_class_balancing",
                        variant,
                        X_base,
                        y,
                        sampling_fn=sampler,
                        note=note,
                    )
                    for variant, sampler, note in sampling_specs
                ],
                ignore_index=True,
            )

            display(
                result_table(
                    summarize_folds(sampling_folds)
                    .sort_values("macro_f1_mean", ascending=False)
                ).merge(
                    summarize_folds(sampling_folds)[["variant", "train_rows_after_sampling_mean"]],
                    on="variant",
                    how="left",
                )
            )
            print("Change relative to main Extra Trees baseline")
            display(
                metric_change_table(
                    summarize_folds(sampling_folds).sort_values("macro_f1_mean", ascending=False),
                    baseline_summary,
                )
            )
        else:
            print("Synthetic sampling experiments skipped because RUN_SYNTHETIC_SAMPLING is False.")
        """
    ),
    markdown_cell(
        """
        ## 7. Ten-fold validation sensitivity check

        This section is placed before the final combined comparison so that all optimization and validation checks are shown before the concluding table.

        The paper uses five-fold cross-validation as the main validation protocol. This step checks whether the main conclusion remains similar when the selected baseline and the strongest same-population variant are evaluated with ten folds instead.

        The ten-fold check is not used to tune the model again. It reruns only:

        - the main all-school Extra Trees baseline,
        - the Extra Trees model with imputation indicators.

        If the imputation-indicator model remains better under ten-fold validation, its improvement is less likely to be an artifact of the original fold split.
        """
    ),
    code_cell(
        """
        ten_fold_folds = pd.DataFrame()
        ten_fold_summary = pd.DataFrame()
        ten_fold_article_table = pd.DataFrame()

        if RUN_TEN_FOLD_VALIDATION:
            ten_fold_baseline_folds = evaluate_cv_variant(
                "ten_fold_validation",
                "main_all_school_extra_trees_10fold",
                X_base,
                y,
                note="Ten-fold sensitivity check for the tuned Extra Trees baseline.",
                n_splits=TEN_FOLD_SPLITS,
            )

            ten_fold_missingness_folds = evaluate_cv_variant(
                "ten_fold_validation",
                "imputation_indicators_10fold",
                X_missingness,
                y,
                note="Ten-fold sensitivity check for Extra Trees with imputation indicators.",
                n_splits=TEN_FOLD_SPLITS,
            )

            ten_fold_folds = pd.concat([ten_fold_baseline_folds, ten_fold_missingness_folds], ignore_index=True)
            ten_fold_summary = summarize_folds(ten_fold_folds)

            ten_fold_baseline = ten_fold_summary[
                ten_fold_summary["variant"].eq("main_all_school_extra_trees_10fold")
            ].iloc[0]

            for metric in REPORT_METRICS:
                ten_fold_summary[f"{metric}_delta_vs_10fold_baseline"] = (
                    ten_fold_summary[f"{metric}_mean"] - ten_fold_baseline[f"{metric}_mean"]
                )

            ten_fold_summary["same_population_as_10fold_baseline"] = ten_fold_summary["rows"].eq(
                int(ten_fold_baseline["rows"])
            )

            ten_fold_article_columns = [
                "experiment",
                "variant",
                "cv_splits",
                "rows",
                "predictors",
                "same_population_as_10fold_baseline",
                "macro_f1_mean",
                "macro_f1_delta_vs_10fold_baseline",
                "accuracy_mean",
                "accuracy_delta_vs_10fold_baseline",
                "balanced_accuracy_mean",
                "balanced_accuracy_delta_vs_10fold_baseline",
                "ordinal_mae_mean",
                "ordinal_mae_delta_vs_10fold_baseline",
                "note",
            ]
            ten_fold_article_table = ten_fold_summary[ten_fold_article_columns].copy()

            for column in ten_fold_article_table.select_dtypes(include=["float"]).columns:
                ten_fold_article_table[column] = ten_fold_article_table[column].round(6)

            print("Ten-fold metric values")
            display(result_table(ten_fold_summary))
            print("Change relative to ten-fold Extra Trees baseline")
            display(
                metric_change_table(
                    ten_fold_summary[
                        ten_fold_summary["variant"].ne("main_all_school_extra_trees_10fold")
                    ],
                    ten_fold_summary,
                    baseline_variant="main_all_school_extra_trees_10fold",
                )
            )
            display(ten_fold_article_table)

            ten_fold_folds_path = OUTPUT_DIR / "ieq_extra_trees_10fold_validation_folds.csv"
            ten_fold_summary_path = OUTPUT_DIR / "ieq_extra_trees_10fold_validation_summary.csv"
            ten_fold_article_path = OUTPUT_DIR / "ieq_extra_trees_10fold_validation_article_table.csv"

            ten_fold_folds.to_csv(ten_fold_folds_path, index=False)
            ten_fold_summary.to_csv(ten_fold_summary_path, index=False)
            ten_fold_article_table.to_csv(ten_fold_article_path, index=False)

            print("Saved ten-fold fold-level results to:", ten_fold_folds_path)
            print("Saved ten-fold summary to:", ten_fold_summary_path)
            print("Saved ten-fold article table to:", ten_fold_article_path)
        else:
            print("Ten-fold validation skipped because RUN_TEN_FOLD_VALIDATION is False.")
        """
    ),
    markdown_cell(
        """
        ## Combined fine-tuning summary

        The table below is the notebook's main output. Delta columns are computed against the main all-school Extra Trees baseline. Rows with fewer observations are marked as a different evaluation population and should not be treated as direct replacements for the main model.
        """
    ),
    code_cell(
        """
        fold_tables = [
            baseline_folds,
            threshold_folds,
            missingness_folds,
            soft_vote_folds,
            ordinal_folds,
            class_weight_folds,
            class_weight_threshold_folds,
            complete_case_folds,
        ]
        if not sampling_folds.empty:
            fold_tables.append(sampling_folds)

        fine_tuning_folds = pd.concat(fold_tables, ignore_index=True)
        fine_tuning_summary = summarize_folds(fine_tuning_folds)

        baseline_row = fine_tuning_summary[fine_tuning_summary["variant"].eq("main_all_school_extra_trees")].iloc[0]

        for metric in REPORT_METRICS:
            fine_tuning_summary[f"{metric}_delta_vs_main"] = fine_tuning_summary[f"{metric}_mean"] - baseline_row[f"{metric}_mean"]

        fine_tuning_summary["same_population_as_main"] = fine_tuning_summary["rows"].eq(int(baseline_row["rows"]))

        variant_order = [
            "main_all_school_extra_trees",
            "threshold_flags_co2_1000_t18_t24",
            "imputation_indicators",
            "soft_vote_et_0.90_rf_0.10",
            "soft_vote_et_0.86_rf_0.14",
            "soft_vote_et_0.80_rf_0.20",
            "soft_vote_et_0.95_rf_0.05",
            "ordinal_extra_trees_decomposition",
            "ordinal_random_forest_decomposition",
            "class_weight_balanced",
            "class_weight_equal_1_1_1",
            "class_weight_dissatisfied_2_neutral_1_5",
            "class_weight_dissatisfied_3_neutral_2",
            "class_weight_dissatisfied_4_neutral_2",
            "class_weight_dissatisfied_5_neutral_2",
            "class_weight_stronger_dissatisfied",
            "class_weight_stronger_neutral",
            "class_weight_stronger_dissatisfied_neutral",
            "best_class_weight_nested_threshold",
            "complete_main_ieq_sensors",
            "complete_lighting_sound_ttrend",
            "random_oversample_to_50pct_majority",
            "synthetic_interpolate_to_50pct_majority",
            "synthetic_interpolate_to_majority",
        ]
        order_map = {variant: index for index, variant in enumerate(variant_order)}
        fine_tuning_summary["display_order"] = fine_tuning_summary["variant"].map(order_map).fillna(999).astype(int)
        fine_tuning_summary = fine_tuning_summary.sort_values(["display_order", "variant"]).reset_index(drop=True)

        article_columns = [
            "experiment",
            "variant",
            "cv_splits",
            "rows",
            "predictors",
            "same_population_as_main",
            "macro_f1_mean",
            "macro_f1_delta_vs_main",
            "accuracy_mean",
            "accuracy_delta_vs_main",
            "balanced_accuracy_mean",
            "balanced_accuracy_delta_vs_main",
            "ordinal_mae_mean",
            "ordinal_mae_delta_vs_main",
            "note",
        ]
        article_table = fine_tuning_summary[article_columns].copy()

        for column in article_table.select_dtypes(include=["float"]).columns:
            article_table[column] = article_table[column].round(6)

        display(article_table)
        """
    ),
    code_cell(
        """
        folds_path = OUTPUT_DIR / "ieq_extra_trees_fine_tuning_folds.csv"
        summary_path = OUTPUT_DIR / "ieq_extra_trees_fine_tuning_summary.csv"
        article_table_path = OUTPUT_DIR / "ieq_extra_trees_fine_tuning_article_table.csv"

        fine_tuning_folds.to_csv(folds_path, index=False)
        fine_tuning_summary.to_csv(summary_path, index=False)
        article_table.to_csv(article_table_path, index=False)

        print("Saved fold-level results to:", folds_path)
        print("Saved full summary to:", summary_path)
        print("Saved article table to:", article_table_path)
        """
    ),
    markdown_cell(
        """
        ## Visual check

        This plot separates the main macro F1 comparison from ordinal MAE. Lower ordinal MAE is better. Complete-case rows are shown with a hatch because they are based on a different evaluation population.
        """
    ),
    code_cell(
        """
        plot_data = article_table.copy()
        plot_data["label"] = plot_data["variant"].str.replace("_", " ", regex=False)

        fig, axes = plt.subplots(1, 2, figsize=(12, 4.8), constrained_layout=True)

        for ax, metric, title in [
            (axes[0], "macro_f1_mean", "Macro F1"),
            (axes[1], "ordinal_mae_mean", "Ordinal MAE"),
        ]:
            bars = ax.barh(plot_data["label"], plot_data[metric], color="#4C78A8")
            for bar, same_population in zip(bars, plot_data["same_population_as_main"]):
                if not same_population:
                    bar.set_hatch("//")
                    bar.set_alpha(0.75)
            ax.invert_yaxis()
            ax.set_title(title)
            ax.grid(axis="x", alpha=0.25)
            ax.spines["top"].set_visible(False)
            ax.spines["right"].set_visible(False)

        axes[0].set_xlabel("Higher is better")
        axes[1].set_xlabel("Lower is better")

        figure_path = FIGURE_DIR / "ieq_extra_trees_fine_tuning_summary.png"
        fig.savefig(figure_path, dpi=220, bbox_inches="tight")
        print("Saved figure to:", figure_path)
        plt.show()
        """
    ),
    markdown_cell(
        """
        ## Interpretation template

        Use this final cell to generate a short text summary after rerunning the notebook. The sentence is intentionally conservative: it separates small same-population gains from complete-case checks that change the evaluated dataset.
        """
    ),
    code_cell(
        """
        same_population = article_table[article_table["same_population_as_main"]].copy()
        same_population = same_population[same_population["variant"].ne("main_all_school_extra_trees")]

        best_same_population = same_population.sort_values("macro_f1_mean", ascending=False).iloc[0]
        best_overall = article_table.sort_values("macro_f1_mean", ascending=False).iloc[0]

        print(
            "Best same-population variant:",
            best_same_population["variant"],
            f"(macro F1 = {best_same_population['macro_f1_mean']:.3f}, "
            f"delta = {best_same_population['macro_f1_delta_vs_main']:+.3f}).",
        )
        print(
            "Best numeric macro F1 overall:",
            best_overall["variant"],
            f"(macro F1 = {best_overall['macro_f1_mean']:.3f}, "
            f"rows = {int(best_overall['rows'])}).",
        )

        if not bool(best_overall["same_population_as_main"]):
            print(
                "The best numeric result uses a different row population, so it should be treated as a data-quality check rather than a direct replacement for the main model."
            )
        """
    ),
]


notebook = {
    "cells": cells,
    "metadata": {
        "kernelspec": {
            "display_name": "Python 3",
            "language": "python",
            "name": "python3",
        },
        "language_info": {
            "name": "python",
            "pygments_lexer": "ipython3",
        },
    },
    "nbformat": 4,
    "nbformat_minor": 5,
}


def main() -> None:
    NOTEBOOK_PATH.parent.mkdir(parents=True, exist_ok=True)
    NOTEBOOK_PATH.write_text(json.dumps(notebook, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {NOTEBOOK_PATH}")


if __name__ == "__main__":
    main()
