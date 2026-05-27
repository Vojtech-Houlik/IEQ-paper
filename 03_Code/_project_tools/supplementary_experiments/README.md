# Supplementary Model Experiments

This folder keeps model checks, rejected variants, and sensitivity outputs that are useful for discussion but should not be treated as the main paper-facing model comparison.

Main model comparison outputs remain in each paper's outputs folder. Supplementary CSV outputs were moved to:

- `../thermal_comfort_paper/04_outputs/supplementary_experiments/tables`
- `../ieq_paper/02_outputs/supplementary_experiments/tables`

The quick SVM and CatBoost screens from 2026-05-11 were run as exploratory checks and are summarized in `model_family_screening_notes.md`; no fold-level CSV outputs were retained for those screens.

The reproducible IEQ threshold feature-engineering rerun is stored in `run_ieq_threshold_feature_experiment.py`. It writes its outputs to `../ieq_paper/02_outputs/supplementary_experiments/tables` and `../ieq_paper/02_outputs/supplementary_experiments/notes`.

The IEQ primary-school transfer check is stored in `run_ieq_primary_trained_transfer_experiment.py`. It trains the tuned Extra Trees model on primary-school rows only, evaluates primary rows out-of-fold, and applies the primary-trained fold ensemble to secondary-school and test-lecture-room rows.

The IEQ five-class target check is stored in `run_ieq_five_class_extra_trees_experiment.py`. It keeps the same model-ready predictors and tuned Extra Trees hyperparameters, but uses the original five-point `IEQ satisfaction` target instead of the three-class collapsed target.

The IEQ 5,240-row three-class versus five-class comparison is stored in `run_ieq_5240_three_vs_five_class_extra_trees.py`. It uses the current Prism model-ready predictors, restricts rows to the earlier complete-case benchmark row mask, and exports matching confusion matrices for the three-class model, the five-class model, and the five-class predictions collapsed back to three classes.
