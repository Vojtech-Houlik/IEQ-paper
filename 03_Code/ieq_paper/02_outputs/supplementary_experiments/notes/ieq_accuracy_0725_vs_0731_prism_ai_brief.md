# Why the IEQ Extra Trees Accuracy Changed from 0.725 to 0.731

Date: 2026-05-12

This note explains why the IEQ Extra Trees accuracy is sometimes reported as 0.725 and sometimes as 0.731. These two numbers come from different evaluation populations and should not be treated as the same headline result.

## Short Answer

The value 0.725 is the main paper-facing three-class Extra Trees result on the full IEQ model-ready dataset with 6,834 rows.

The value 0.731 is a supplementary complete-case subset result. It uses the same current Prism model-ready predictors and the same tuned Extra Trees hyperparameters, but the evaluation is restricted to the 5,240 rows used by the earlier complete-case benchmark.

Therefore, 0.731 is not a replacement for the main 0.725 result. It is a matched-subset sensitivity result.

## What Was Compared

Main IEQ model:

- Target: IEQ satisfaction collapsed into three classes.
- Rows: 6,834.
- Predictors: 21 current Prism model-ready predictors.
- Model: tuned Extra Trees.
- Cross-validation: 5-fold stratified CV.
- Accuracy: 0.725.
- Macro F1: 0.598.
- Ordinal MAE: 0.312.

Complete-case subset comparison:

- Target: IEQ satisfaction collapsed into three classes.
- Rows: 5,240.
- Predictors: the same 21 current Prism model-ready predictors.
- Model: the same tuned Extra Trees configuration.
- Cross-validation: 5-fold stratified CV, retrained within the 5,240-row subset.
- Accuracy: 0.731.
- Macro F1: 0.622.
- Ordinal MAE: 0.304.

The 5,240-row mask comes from the earlier IEQ benchmark dataset. It was used only to select rows by source_row_number. No old predictor columns were added to the current Prism dataset.

## Why the Difference Happens

The comparison changes the evaluation population. The full 6,834-row dataset includes 1,594 rows that were not part of the earlier complete-case benchmark. Those rows are kept in the main Prism pipeline because the current model-ready dataset uses imputation and transfer-safe preprocessing.

The 5,240-row subset is closer to the old complete-case benchmark. It excludes rows that were dropped in the old benchmark because required core environmental features were missing.

There is also a training difference. The 0.731 result is not just the original 0.725 model evaluated on fewer rows. It is a new cross-validation run trained and evaluated within the 5,240-row subset.

As a check, the original full-row Extra Trees predictions were evaluated only on the same 5,240-row mask:

- Full-row Extra Trees on all 6,834 rows: accuracy 0.725, macro F1 0.598, ordinal MAE 0.312.
- Full-row Extra Trees predictions restricted to the 5,240-row subset: accuracy 0.724, macro F1 0.612, ordinal MAE 0.311.
- New subset-trained Extra Trees on the 5,240-row subset: accuracy 0.731, macro F1 0.622, ordinal MAE 0.304.

This means the 0.731 result reflects a small subset-specific specialization gain, not a change in the main all-row model.

## Relation to the Five-Class Experiment

The same 5,240-row subset was used to compare three-class and five-class classification.

Three-class Extra Trees on 5,240 rows:

- Accuracy: 0.731.
- Macro F1: 0.622.
- Ordinal MAE: 0.304.

Five-class Extra Trees on 5,240 rows:

- Accuracy: 0.605.
- Macro F1: 0.510.
- Ordinal MAE: 0.540.

Five-class predictions collapsed back to three classes:

- Accuracy: 0.728.
- Macro F1: 0.613.
- Ordinal MAE: 0.309.

The five-class target preserves the original response scale, but it is a harder and more imbalanced task. Even after collapsing five-class predictions back to three classes, the result remains slightly below the directly trained three-class model.

## Recommended Interpretation for the Article

The main article result should remain the full-dataset three-class Extra Trees score:

- Accuracy: 0.725.
- Macro F1: 0.598.
- Ordinal MAE: 0.312.

The 5,240-row result can be reported as a sensitivity analysis showing that the model performs slightly better on the complete-case subset:

- Accuracy: 0.731.
- Macro F1: 0.622.
- Ordinal MAE: 0.304.

The increase from 0.725 to 0.731 is small, around 0.6 percentage points in accuracy. It should not be presented as a direct improvement of the main model, because the row set changed.

## Article-Ready Paragraph

As a sensitivity analysis, the IEQ model was also evaluated on the 5,240-row complete-case subset used by the earlier benchmark, while keeping the current Prism model-ready predictors and tuned Extra Trees configuration. The main three-class Extra Trees model evaluated on all 6,834 rows achieved 0.725 accuracy, 0.598 macro F1, and 0.312 ordinal MAE. When the model was retrained and evaluated within the 5,240-row complete-case subset, performance increased slightly to 0.731 accuracy, 0.622 macro F1, and 0.304 ordinal MAE. This improvement should be interpreted as a subset sensitivity result rather than a replacement for the main full-dataset estimate, because the evaluation population changed.

## Generated Evidence Files

- Summary table: `03_Code/ieq_paper/02_outputs/supplementary_experiments/tables/ieq_5240_three_vs_five_extra_trees_summary.csv`
- Fold-level table: `03_Code/ieq_paper/02_outputs/supplementary_experiments/tables/ieq_5240_three_vs_five_extra_trees_folds.csv`
- Confusion-matrix table: `03_Code/ieq_paper/02_outputs/supplementary_experiments/tables/ieq_5240_three_vs_five_extra_trees_confusion_matrices.csv`
- Confusion-matrix figure: `03_Code/ieq_paper/02_outputs/supplementary_experiments/figures/ieq_5240_three_vs_five_extra_trees_confusion_matrices.png`
