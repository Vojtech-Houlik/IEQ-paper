# IEQ Three-Class vs Five-Class Classification Brief

Date: 2026-05-12

Purpose: one compact note for deciding whether the IEQ article should continue with the three-class target or switch to the original five-class satisfaction scale.

## Main Conclusion

The three-class formulation should remain the main article-facing result. The five-class formulation is useful as a sensitivity analysis because it preserves the original response scale, but it gives weaker headline metrics and does not outperform the directly trained three-class model after collapsing predictions back to three classes.

## Why Accuracy Is Sometimes 0.725 and Sometimes 0.731

The value 0.725 is the main IEQ Extra Trees result on the full model-ready dataset:

- Target: IEQ satisfaction collapsed into three classes.
- Rows: 6,834.
- Predictors: 21 current Prism model-ready predictors.
- Model: tuned Extra Trees.
- Cross-validation: 5-fold stratified CV.
- Accuracy: 0.725.
- Macro F1: 0.598.
- Ordinal MAE: 0.312.

The value 0.731 comes from a supplementary complete-case subset comparison:

- Target: IEQ satisfaction collapsed into three classes.
- Rows: 5,240.
- Predictors: the same 21 current Prism model-ready predictors.
- Model: the same tuned Extra Trees configuration.
- Cross-validation: 5-fold stratified CV, retrained within the 5,240-row subset.
- Accuracy: 0.731.
- Macro F1: 0.622.
- Ordinal MAE: 0.304.

The 5,240-row subset is defined by the source_row_number mask from the earlier complete-case benchmark. The old benchmark file was used only to select rows. No old predictor columns were added to the current Prism dataset.

Therefore, 0.731 should not replace the main 0.725 result. It is a matched-subset sensitivity result.

## Check Separating Row-Set Effect from Retraining Effect

The original full-row Extra Trees predictions were also evaluated only on the same 5,240-row mask:

- Full-row Extra Trees on all 6,834 rows: accuracy 0.725, macro F1 0.598, ordinal MAE 0.312.
- Full-row Extra Trees predictions restricted to the 5,240-row subset: accuracy 0.724, macro F1 0.612, ordinal MAE 0.311.
- New subset-trained Extra Trees on the 5,240-row subset: accuracy 0.731, macro F1 0.622, ordinal MAE 0.304.

This means the 0.731 result reflects a small subset-specific specialization gain from retraining within the complete-case subset. It is not a change in the main all-row model.

## Three-Class vs Five-Class Results on the Same 5,240 Rows

The following comparison uses the same current Prism model-ready predictors, the same tuned Extra Trees model family, and the same 5,240-row subset.

Three-class Extra Trees:

- Accuracy: 0.731.
- Balanced accuracy: 0.623.
- Macro F1: 0.622.
- Weighted F1: 0.730.
- Ordinal MAE: 0.304.

Five-class Extra Trees:

- Accuracy: 0.605.
- Balanced accuracy: 0.533.
- Macro F1: 0.510.
- Weighted F1: 0.604.
- Ordinal MAE: 0.540.

Five-class predictions collapsed back to three classes:

- Accuracy: 0.728.
- Balanced accuracy: 0.622.
- Macro F1: 0.613.
- Weighted F1: 0.728.
- Ordinal MAE: 0.309.

The five-class target is clearly more difficult. Exact five-class accuracy is lower because the model must distinguish adjacent satisfaction levels such as 4 versus 5, even though both map to satisfied in the three-class article target.

## Target Distributions on the 5,240-Row Subset

Three-class target:

- Dissatisfied: 382 rows, 7.3%.
- Neutral: 1,528 rows, 29.2%.
- Satisfied: 3,330 rows, 63.5%.

Five-class target:

- Class 1: 81 rows, 1.5%.
- Class 2: 301 rows, 5.7%.
- Class 3: 1,528 rows, 29.2%.
- Class 4: 1,727 rows, 33.0%.
- Class 5: 1,603 rows, 30.6%.

The rare class 1 is a major reason why five-class macro F1 is weaker.

## Interpretation for the Article

The five-class model preserves more detail from the original questionnaire, which is conceptually attractive. However, the cost is a harder and more imbalanced prediction problem. On the matched 5,240-row subset, the five-class model reached 0.605 exact accuracy and 0.510 macro F1. When its predictions were collapsed back into the three article-facing classes, the result was still slightly below the directly trained three-class model.

The three-class formulation is easier to communicate, more stable, and more aligned with the article's interpretation of dissatisfied, neutral, and satisfied responses. It also avoids overemphasizing minor distinctions between adjacent positive classes that may not be central to the paper's research question.

## Article-Ready Paragraph

As a sensitivity analysis, the IEQ classification task was also evaluated on the original five-point satisfaction scale using the same Extra Trees model, predictor set, and 5,240-row complete-case subset as the three-class comparison. The three-class formulation achieved 0.731 accuracy, 0.622 macro F1, and 0.304 ordinal MAE. The five-class formulation preserved the original response resolution but was more difficult, reaching 0.605 accuracy, 0.510 macro F1, and 0.540 ordinal MAE. When the five-class predictions were collapsed back into the three article-facing classes, performance was 0.728 accuracy, 0.613 macro F1, and 0.309 ordinal MAE, which remained below the directly trained three-class model. These results indicate that the five-class target is useful as a robustness check, but the three-class target gives a clearer and more stable headline model for the article.

## Recommended Reporting Strategy

Recommended main result:

- Full-dataset three-class Extra Trees: accuracy 0.725, macro F1 0.598, ordinal MAE 0.312.

Recommended sensitivity result:

- Complete-case subset three-class Extra Trees: accuracy 0.731, macro F1 0.622, ordinal MAE 0.304.
- Complete-case subset five-class Extra Trees: accuracy 0.605, macro F1 0.510, ordinal MAE 0.540.
- Collapsed five-class predictions: accuracy 0.728, macro F1 0.613, ordinal MAE 0.309.

Recommended conclusion:

- Continue with three-class classification as the main article formulation.
- Mention five-class classification as a sensitivity check that preserves the original scale but gives weaker and less stable headline metrics.

## Evidence Files

- Summary table: `03_Code/ieq_paper/02_outputs/supplementary_experiments/tables/ieq_5240_three_vs_five_extra_trees_summary.csv`
- Fold-level table: `03_Code/ieq_paper/02_outputs/supplementary_experiments/tables/ieq_5240_three_vs_five_extra_trees_folds.csv`
- Confusion-matrix table: `03_Code/ieq_paper/02_outputs/supplementary_experiments/tables/ieq_5240_three_vs_five_extra_trees_confusion_matrices.csv`
- Confusion-matrix figure: `03_Code/ieq_paper/02_outputs/supplementary_experiments/figures/ieq_5240_three_vs_five_extra_trees_confusion_matrices.png`
