# Thermal Comfort Modeling Results Notes

## Current Tuned Model-Comparison Result

The current paper-facing thermal comfort model comparison uses the model-ready dataset in `Prism/02_Datasets/model_ready/thermal_comfort_model_dataset.xlsx`. The primary model-selection metric is macro F1, because the three-class target is imbalanced and raw accuracy can overemphasize the majority `satisfied` class.

The strongest current tuned model is Random Forest:

- Random Forest: accuracy=0.669, balanced accuracy=0.594, macro F1=0.593, weighted F1=0.667, ordinal MAE=0.396.
- Extra Trees: accuracy=0.643, balanced accuracy=0.596, macro F1=0.577, weighted F1=0.650, ordinal MAE=0.435.

## Rejected Missingness Indicator Ablation

Broad missingness indicators were temporarily tested in the model-ready dataset: `Imputed CLO`, `Imputed Age`, `Imputed Gender`, `Imputed Location`, and `Imputed Ttrend`, alongside the more specific `Estimated Age` flag.

The best Random Forest result improved only slightly in a fixed-parameter 5-fold comparison:

- Previous Random Forest: macro F1=0.593, accuracy=0.669, ordinal MAE=0.396.
- Random Forest with missingness indicators: macro F1=0.597, accuracy=0.674, ordinal MAE=0.389.

The gain was small relative to the extra metadata-like feature complexity, so the broad indicators were removed from the model-ready workbook and were not adopted.

## Class-Imbalance Strategy Ablation

Additional strategies were tested to improve minority-class behavior without using a two-stage classifier:

- Fold-internal thermal synthetic sampling: random oversampling to 50% of the majority class, interpolation-style synthetic rows to 50%, and interpolation-style synthetic rows to full class balance.
- Sample-weighted fitting with balanced or square-root-balanced weights.
- Inner-fold probability multiplier calibration for `dissatisfied` and `neutral` class probabilities.

The strongest alternatives were very close to the current Random Forest baseline:

- Random Forest with balanced sample weights and model `class_weight` removed: macro F1=0.594, accuracy=0.670, ordinal MAE=0.394.
- Random Forest with probability multiplier calibration: macro F1=0.594, accuracy=0.671, ordinal MAE=0.389.
- Best synthetic-sampling result by macro F1: Random Forest with random oversampling to 50% of the majority class, macro F1=0.592, accuracy=0.667, ordinal MAE=0.400.

Some synthetic variants increased raw accuracy and reduced ordinal MAE, for example Random Forest with interpolation to full balance reached accuracy=0.685 and ordinal MAE=0.373. However, its macro F1 decreased to 0.580, so it was not adopted under the primary macro F1 selection rule.

Overall, the imbalance strategies did not provide a robust enough macro F1 improvement to replace the tuned Random Forest baseline. Temporary experiment tables and helper scripts were removed after these conclusions were recorded.

## Primary-School-Only Training Ablation

A subset experiment was run using only `Primary school` rows. The subset contains 5,101 rows with the following thermal target distribution: 500 dissatisfied, 1,610 neutral, and 2,991 satisfied.

Two comparisons were made:

- Existing full-dataset tuned CV predictions evaluated only on primary-school rows.
- New 5-fold CV trained and evaluated only within the primary-school subset, using the existing tuned model configurations without retuning.

The primary-only training did not improve the best thermal model:

- Full-dataset Random Forest evaluated on primary rows: macro F1=0.602, accuracy=0.690, ordinal MAE=0.363.
- Primary-only Random Forest: macro F1=0.600, accuracy=0.687, ordinal MAE=0.366.
- Primary-only Extra Trees: macro F1=0.601, accuracy=0.668, ordinal MAE=0.404.

Some weaker model families improved when trained only on primary-school data, especially gradient boosting, but they remained below Random Forest and Extra Trees. Primary-only training is therefore not recommended as the main thermal comfort model strategy. The experiment outputs are stored in `04_outputs/supplementary_experiments/tables/primary_only_model_experiment_summary.csv`, `04_outputs/supplementary_experiments/tables/primary_only_model_experiment_folds.csv`, and `04_outputs/supplementary_experiments/tables/primary_only_target_distribution.csv`.
