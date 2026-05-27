# IEQ Primary-Trained Transfer Check

This supplementary experiment tests the reverse of the earlier primary-row evaluation: models are trained only on primary-school observations and then applied to the whole IEQ dataset.

Evaluation design:

- Model family: tuned Extra Trees configuration from the main IEQ comparison.
- Training population: primary-school rows only.
- Primary-school rows are evaluated with out-of-fold predictions.
- Secondary-school and test-lecture-room rows are predicted by averaging probabilities across the five primary-trained fold models.

Headline result:

- All-school tuned Extra Trees baseline on all rows: accuracy=0.725, macro F1=0.598, ordinal MAE=0.312.
- Primary-trained transfer-style model on all rows: accuracy=0.702, macro F1=0.547, ordinal MAE=0.348.
- All-row macro F1 delta versus all-school baseline: -0.051.

Non-primary transfer performance:

- Secondary school: accuracy=0.406, macro F1=0.318, ordinal MAE=0.704.
- Test lecture room: accuracy=0.636, macro F1=0.344, ordinal MAE=0.432.

Output files:

- `ieq_paper\02_outputs\supplementary_experiments\tables\ieq_primary_trained_transfer_summary.csv`
- `ieq_paper\02_outputs\supplementary_experiments\tables\ieq_primary_trained_transfer_fold_metrics.csv`
- `ieq_paper\02_outputs\supplementary_experiments\tables\ieq_primary_trained_transfer_predictions.csv`
- `ieq_paper\02_outputs\supplementary_experiments\tables\ieq_all_school_extra_trees_group_summary.csv`
