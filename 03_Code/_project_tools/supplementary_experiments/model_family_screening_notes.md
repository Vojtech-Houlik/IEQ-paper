# Supplementary Model-Family Screening Notes

These checks were run as exploratory screens only. They are not part of the main paper-facing model comparison tables.

## SVM Screen

Date: 2026-05-11

Evaluation setup:

- model-ready datasets
- 5-fold stratified cross-validation
- same label mapping and metrics as the main model comparison
- numeric scaling and one-hot encoding for categorical predictors

Best screened SVM variant:

- `RBF SVM`, `class_weight="balanced"`, `C=10`, `gamma="scale"`

Results:

| Dataset | Accuracy | Macro F1 | Ordinal MAE | Current tuned baseline | Macro F1 delta |
|---|---:|---:|---:|---|---:|
| Thermal comfort | 0.586 | 0.531 | 0.506 | Random Forest, macro F1 0.593 | -0.062 |
| IEQ | 0.643 | 0.525 | 0.421 | Extra Trees, macro F1 0.597 | -0.073 |

Conclusion: SVM was clearly weaker than the current Random Forest / Extra Trees baselines and should not be included in the main comparison.

## CatBoost Screen

Date: 2026-05-11

Evaluation setup:

- model-ready datasets
- 5-fold stratified cross-validation
- categorical predictors passed directly to CatBoost
- no `catboost_info` output retained

Best screened CatBoost variant:

- `CatBoostClassifier`
- `loss_function="MultiClass"`
- `auto_class_weights="SqrtBalanced"`
- `iterations=500`
- `depth=6`
- `learning_rate=0.04`
- `l2_leaf_reg=3`

Results:

| Dataset | Accuracy | Macro F1 | Ordinal MAE | Current tuned baseline | Macro F1 delta |
|---|---:|---:|---:|---|---:|
| Thermal comfort | 0.664 | 0.578 | 0.398 | Random Forest, macro F1 0.593 | -0.014 |
| IEQ | 0.719 | 0.579 | 0.318 | Extra Trees, macro F1 0.597 | -0.019 |

Additional screened variants included `Balanced` class weights, shorter runs, stronger regularization, shallower trees, and `MultiClassOneVsAll`. None surpassed the tuned Random Forest / Extra Trees baselines by macro F1.

Conclusion: CatBoost is a plausible supplementary model-family check and much stronger than SVM, but it did not beat the current paper-facing baselines under the same 5-fold setup.
