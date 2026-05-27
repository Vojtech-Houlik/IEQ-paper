# IEQ Threshold Feature Engineering Note

This supplementary experiment reruns a compact, article-readable feature-engineering check for the IEQ model.

Engineered thresholds:

- `CO2_gt_1000ppm`: CO2 > 1000 ppm.
- `Temperature_lt_18C`: Temperature < 18 deg C.
- `Temperature_gt_24C`: Temperature > 24 deg C.

Main result:

- Baseline Extra Trees macro F1 = 0.597, accuracy = 0.727, ordinal MAE = 0.310.
- Three-threshold variant macro F1 = 0.594, accuracy = 0.722, ordinal MAE = 0.315.
- Three-threshold macro F1 delta versus baseline = -0.003.

Threshold prevalence in the model-ready IEQ dataset:

- `CO2_gt_1000ppm`: 240 rows (3.5%).
- `Temperature_lt_18C`: 1474 rows (21.6%).
- `Temperature_gt_24C`: 609 rows (8.9%).

Output files:

- `ieq_paper\02_outputs\supplementary_experiments\tables\ieq_threshold_feature_engineering_summary.csv`
- `ieq_paper\02_outputs\supplementary_experiments\tables\ieq_threshold_feature_engineering_folds.csv`
- `ieq_paper\02_outputs\supplementary_experiments\tables\ieq_threshold_feature_definitions.csv`
- `ieq_paper\02_outputs\supplementary_experiments\tables\ieq_threshold_feature_sets.csv`
