# IEQ Five-Class Extra Trees Check

This supplementary experiment reruns the current best IEQ Extra Trees model with the original five-point `IEQ satisfaction` target instead of the paper-facing three-class target.

Design:

- Same model-ready predictor table as the three-class IEQ model.
- Same tuned Extra Trees hyperparameters as the current best three-class model.
- Five-fold stratified cross-validation on the five-class target.
- No five-class-specific hyperparameter retuning.

Target distribution:

- Class 1: 99 rows (1.4%), maps to `dissatisfied`.
- Class 2: 385 rows (5.6%), maps to `dissatisfied`.
- Class 3: 1855 rows (27.1%), maps to `neutral`.
- Class 4: 2456 rows (35.9%), maps to `satisfied`.
- Class 5: 2039 rows (29.8%), maps to `satisfied`.

Headline result:

- Five-class Extra Trees: accuracy=0.585, macro F1=0.475, weighted F1=0.584, ordinal MAE=0.556.
- The same five-class predictions collapsed back to three classes: accuracy=0.722, macro F1=0.595, ordinal MAE=0.320.

Output files:

- `ieq_paper\02_outputs\supplementary_experiments\tables\ieq_five_class_extra_trees_summary.csv`
- `ieq_paper\02_outputs\supplementary_experiments\tables\ieq_five_class_extra_trees_folds.csv`
- `ieq_paper\02_outputs\supplementary_experiments\tables\ieq_five_class_extra_trees_predictions.csv`
- `ieq_paper\02_outputs\supplementary_experiments\tables\ieq_five_class_target_distribution.csv`
- `ieq_paper\02_outputs\supplementary_experiments\tables\ieq_five_class_extra_trees_per_class_metrics.csv`
- `ieq_paper\02_outputs\supplementary_experiments\tables\ieq_five_class_extra_trees_confusion_matrix.csv`
