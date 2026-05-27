# IEQ 3-Class vs 5-Class Extra Trees on 5,240 Rows

This supplementary experiment uses the current Prism IEQ model-ready data and restricts the row set to the 5,240 `source_row_number` values used by the earlier complete-case benchmark. The old benchmark file is used only as a row mask; no old predictor columns are added.

Headline results:

- Three-class Extra Trees: accuracy=0.731, macro F1=0.622, ordinal MAE=0.304.
- Five-class Extra Trees: accuracy=0.605, macro F1=0.510, ordinal MAE=0.540.
- Five-class predictions collapsed to three classes: accuracy=0.728, macro F1=0.613, ordinal MAE=0.309.

Article paragraph:

As a sensitivity analysis, the IEQ classification task was also evaluated on the original five-point satisfaction scale using the same Extra Trees model, predictor set, and 5,240-row complete-case subset as the three-class comparison. The three-class formulation achieved 0.731 accuracy, 0.622 macro F1, and 0.304 ordinal MAE. The five-class formulation preserved the original response resolution but was more difficult, reaching 0.605 accuracy, 0.510 macro F1, and 0.540 ordinal MAE. When the five-class predictions were collapsed back into the three article-facing classes, performance was 0.728 accuracy, 0.613 macro F1, and 0.309 ordinal MAE, which remained below the directly trained three-class model. These results indicate that the five-class target is useful as a robustness check, but the three-class target gives a clearer and more stable headline model for the article.

Target distributions:

- three_class class `dissatisfied`: 382 rows (7.3%).
- three_class class `neutral`: 1528 rows (29.2%).
- three_class class `satisfied`: 3330 rows (63.5%).
- five_class class `1`: 81 rows (1.5%).
- five_class class `2`: 301 rows (5.7%).
- five_class class `3`: 1528 rows (29.2%).
- five_class class `4`: 1727 rows (33.0%).
- five_class class `5`: 1603 rows (30.6%).

Output files:

- `ieq_paper\02_outputs\supplementary_experiments\tables\ieq_5240_three_vs_five_extra_trees_summary.csv`
- `ieq_paper\02_outputs\supplementary_experiments\tables\ieq_5240_three_vs_five_extra_trees_folds.csv`
- `ieq_paper\02_outputs\supplementary_experiments\tables\ieq_5240_three_vs_five_extra_trees_predictions.csv`
- `ieq_paper\02_outputs\supplementary_experiments\tables\ieq_5240_three_vs_five_extra_trees_confusion_matrices.csv`
- `ieq_paper\02_outputs\supplementary_experiments\tables\ieq_5240_three_vs_five_extra_trees_per_class_metrics.csv`
- `ieq_paper\02_outputs\supplementary_experiments\tables\ieq_5240_three_vs_five_target_distribution.csv`
- `ieq_paper\02_outputs\supplementary_experiments\figures\ieq_5240_three_vs_five_extra_trees_confusion_matrices.png`
- `ieq_paper\02_outputs\supplementary_experiments\figures\ieq_5240_three_vs_five_extra_trees_confusion_matrices.pdf`
