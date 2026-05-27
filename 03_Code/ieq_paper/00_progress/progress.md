# IEQ Paper Progress

## 2026-05-04

### Done
- Created the IEQ paper workspace.
- Added the standard folder structure.
- Added the main workflow notebook placeholder.
- Identified existing IEQ modeling baselines from the previous workflow.
- Defined the Step 1 IEQ target and inputs.
- Created `../../02_Datasets/clean/ieq_clean_dataset.xlsx`.
- Kept all 6,834 source rows; no rows were removed because of missing input values.
- Moved internal helper scripts to `_project_tools`.
- Generated feature completeness and complete-case availability plots.

### Decisions
- Overall IEQ will be handled as a separate paper from thermal comfort.
- Existing Random Forest and CatBoost work can be reused as historical starting context, but the paper workflow should be cleaned and consolidated around the current paper-facing comparison.
- Work should be documented continuously in Markdown and exported to PDF.
- IEQ output is `IEQ satisfaction`.
- IEQ inputs are `Temperature`, `RH`, `CLO`, `CO2`, `Lighting`, `Sound`, `Age`, `Gender`, `EA`, `LocationBack`, `LocationFront`, `LocationLeft`, `LocationRight`, `LocationMiddle`, `Ttrend`, `Vote hour`, `Vote weekday`, `Moment`, and `AC on/off`.
- Helper scripts are internal project tools and should not be treated as paper-facing materials.
- Complete-case availability is diagnostic only at this stage; missing values have not been imputed or filtered out.

### Results
- Current RF `v04` five-class exact accuracy is about 61.3%.
- Current RF `v09` improves minority-class behavior through balanced class weights.
- Historical CatBoost exact accuracy was about 60.4%; current CatBoost/SVM screens are kept as supplementary notes outside the main comparison.
- Clean IEQ Excel created with 6,834 rows and 18 columns, including 2 metadata columns.
- Planned IEQ inputs are all complete in 2,047 rows, or 30.0% of the dataset.
- `Ttrend` is the main missingness bottleneck, with 41.0% completeness; `Lighting` is the strongest IEQ-specific bottleneck, with 78.3% completeness.
- Completeness outputs were saved in `02_outputs/figures` and `02_outputs/tables`.

### Open Questions
- Resolved on 2026-05-05: the main IEQ paper target is the unified three-class target.
- Which context features should be included in the final paper-facing model?
- Should feature importance be presented at encoded-indicator level or grouped source-feature level?
- Resolved on 2026-05-05: missing values are handled by the documented model-ready imputation script.

### Next Actions
- Generate target distribution plots inside the new IEQ notebook.
- Decide imputation strategy.
- Write the first missingness paragraph.
- Rebuild the model comparison in the new paper workflow.

## 2026-05-05

### Done
- Added the shared project figure style guide.
- Added reusable Matplotlib style files in `_project_tools`.
- Regenerated completeness figures using the shared paper style.
- Added the shared `article_figures` folder for manuscript-ready figure exports.
- Added a unified three-category satisfaction distribution figure using `1-2`, `3`, and `4-5` categories.
- Mirrored manuscript-ready PDF figures to `../04_Figures` for direct use in the LaTeX article.
- Added a paper-facing overall IEQ target distribution figure comparing the original five-class and unified three-class scales.
- Moved the clean IEQ dataset to the central `../../02_Datasets/clean` folder and removed the duplicate Excel copy from `03_Code`.
- Added `Occupant ID`, `Group`, `Subgroup`, and `Student` metadata to the central clean dataset.
- Added `IEQ satisfaction 3-class` as an explicit derived target column.
- Added a separate imputation script that reads the clean dataset and writes a model-ready dataset to `../../02_Datasets/model_ready`.
- Added model-ready imputed values and retained only `Estimated Age` as compact metadata in the model-ready `data` sheet.
- Documented the imputation method and article paragraph draft.

### Decisions
- All new IEQ figures should follow `PAPER_FIGURE_STYLE_GUIDE.md`.
- The default paper plotting helper is `_project_tools/paper_style.py`.
- Manuscript-ready figure exports should be collected in `article_figures`.
- The primary modeling target for the IEQ paper is `IEQ satisfaction 3-class`; the original five-class `IEQ satisfaction` scale remains available in the clean dataset but is removed from the model-ready `data` sheet.
- Unknown classroom location is defaulted to `LocationMiddle`; detailed imputation counts remain in workbook support sheets.
- Trace/context columns (`source_row_number`, `Occupant ID`, `Group`, `Subgroup`) are removed from the model-ready `data` sheet.
- Replaced the collapsed classroom-position feature with the raw classroom location flags: `LocationBack`, `LocationFront`, `LocationLeft`, `LocationRight`, and `LocationMiddle`.

### Results
- Existing completeness figures now use the shared TU Berlin / HRI inspired scientific style.
- IEQ feature completeness, raw column completeness, satisfaction distribution, and environmental boxplots were exported to the shared article figure folder.
- The unified satisfaction category distribution was exported as `article_figures/fig_04b_unified_satisfaction_category_distribution`.
- Current article PDF figures are also available in `Prism/04_Figures`.
- The overall IEQ distribution figure was exported as `article_figures/fig_overall_ieq_satisfaction_vote_distribution_original_unified`.
- The PDF copy is available in `Prism/04_Figures/ieq_paper`.
- The clean IEQ dataset source is `Prism/02_Datasets/clean/ieq_clean_dataset.xlsx`.
- The supervisor-facing model-ready IEQ dataset is `Prism/02_Datasets/model_ready/ieq_model_dataset.xlsx`.
- The model-ready IEQ dataset has no missing values in the defined target/input columns after imputation.
- Clean IEQ dataset shape: 6,834 rows and 27 columns.
- Model-ready IEQ dataset shape: 6,834 rows and 46 columns.
- Clean IEQ target/input missing cells before imputation: 8,452.
- Model-ready IEQ target/input missing cells after imputation: 0.
- IEQ three-class target distribution: 484 dissatisfied, 1,855 neutral, 4,495 satisfied.

### Open Questions
- Should any target journal template override this style later?

### Next Actions
- Build the first IEQ baseline model comparison on the model-ready dataset.
- Use the shared style for model comparison and feature importance figures.

## 2026-05-07

### Done
- Propagated the tuned IEQ model comparison into the standard model-comparison table and figure exports.
- Updated the tuned plotting notebook so `Extra Trees` uses the primary best-model color after hyperparameter tuning.
- Regenerated tuned and standard IEQ model comparison figures from the tuned 5-fold summary and predictions.

### Results
- Tuned `Extra Trees` is the best model by macro F1 (0.590) and weighted F1 (0.717).
- Tuned `Random Forest` remains marginally highest in raw accuracy (0.715), so macro F1 stays the main selection metric for the imbalanced three-class target.

### Extra Trees Refinement
- Ran a wider Extra Trees-only search including `criterion`, `bootstrap`, `max_samples`, wider `max_features`, and higher `n_estimators`.
- Updated the paper workflow to use the refined Extra Trees configuration: entropy criterion, bootstrap sampling, 700 trees, full feature consideration, `max_samples=0.9`, and balanced class weights.
- Regenerated IEQ model-comparison tables and figures with the refined Extra Trees rows.
- Inner-fold class-threshold tuning was tested but did not improve macro F1, so it was not added to the final comparison.
- Added article-facing modeling notes in `06_manuscript/modeling_results_notes.md` and transfer-safe feature notes in `07_transfer_learning/transfer_safe_feature_notes.md`.

### Refined Results
- Refined `Extra Trees`: accuracy=0.725, macro F1=0.597, weighted F1=0.723, ordinal MAE=0.312.
- Previous tuned `Extra Trees`: accuracy=0.710, macro F1=0.590, weighted F1=0.717, ordinal MAE=0.334.

### Temperature and CO2 Feature Engineering Check
- Tested transfer-safe manual features based on temperature and CO2: threshold flags, excess-above-threshold values, categorical bands, absolute temperature deviations, and temperature-by-CO2 interactions.
- Fixed-parameter Extra Trees experiments did not improve the primary macro F1 metric. The baseline refined Extra Trees remained best with macro F1=0.597.
- The interaction-only variant slightly improved accuracy and ordinal MAE, but macro F1 decreased to 0.596, so it was not adopted.
- A compact engineered feature set was also retuned with Extra Trees; its best randomized-search macro F1 was 0.589, below the refined baseline.
- Saved the ablation summary to `02_outputs/supplementary_experiments/tables/extra_trees_feature_engineering_experiment.csv`.

### Ensemble and Ordinal Modeling Check
- Tested transfer-safe alternatives that do not add new predictors: Extra Trees + Random Forest soft-voting, ordinal Extra Trees/Random Forest regressors with inner-fold threshold calibration, and screened `HistGradientBoostingClassifier` variants.
- The best candidate was a soft-voting ensemble with 90% refined Extra Trees probabilities and 10% tuned Random Forest probabilities.
- Soft-voting result: accuracy=0.725, macro F1=0.599, weighted F1=0.722, ordinal MAE=0.312.
- The gain over refined single-model Extra Trees was small: macro F1 increased from 0.597 to 0.599.
- Ordinal regression reduced ordinal MAE slightly but decreased macro F1 substantially, so it was not adopted.
- Saved the experiment summary to `02_outputs/supplementary_experiments/tables/ensemble_ordinal_model_experiment.csv`.

### Data Quality and Synthetic Sampling Check
- Tested data-quality filtering as a single-model-compatible alternative to ensembles. `Temperature`, `RH`, and `CO2` are complete in the IEQ model-ready workbook before imputation; the main missing sensor fields are `Lighting` (1,485 rows, 21.7%) and `Sound` (487 rows, 7.1%).
- Filtering to rows with complete original `Temperature`, `RH`, `CO2`, `Lighting`, and `Sound` values retained 5,349 of 6,834 rows and improved refined Extra Trees macro F1 to 0.612 in the 700-tree check.
- A stricter complete-case filter requiring `Lighting`, `Sound`, and `Ttrend` retained only 2,314 rows and gave the highest Extra Trees macro F1 in the filter screen (0.615), but it changes the dataset much more strongly and reduced accuracy/ordinal error metrics.
- Re-ran the tuned single-model comparison on the two filtered datasets. Extra Trees remained the best standalone model on both filtered datasets; Random Forest was second.
- Synthetic minority-class sampling inside the training folds was screened with 250-tree Extra Trees. Random oversampling and interpolation-style synthetic rows did not improve macro F1 over the same 250-tree baseline, so synthetic data were not adopted.
- Saved the ablation summaries to `02_outputs/supplementary_experiments/tables/ieq_data_strategy_experiment.csv`, `02_outputs/supplementary_experiments/tables/ieq_filtered_sensor_model_comparison_experiment.csv`, and `02_outputs/supplementary_experiments/tables/ieq_synthetic_sampling_experiment.csv`.

### Missingness Indicator Experiment
- Tested compact missingness indicators in the model-ready IEQ dataset: `Imputed CLO`, `Imputed Age`, `Imputed Gender`, `Imputed Location`, `Imputed Ttrend`, `Imputed Lighting`, and `Imputed Sound`.
- Ran a fixed-parameter 5-fold comparison using the existing tuned model configurations, without retuning hyperparameters.
- Extra Trees improved only slightly: accuracy increased from 0.725 to 0.728, macro F1 from 0.597 to 0.602, and ordinal MAE decreased from 0.312 to 0.309.
- IEQ Random Forest accuracy slightly decreased from 0.715 to 0.713, so the benefit was model-dependent rather than clearly robust.
- Removed the missingness indicators from the model-ready dataset after review; only `Estimated Age` remains as compact imputation metadata.
- Regenerated `../../02_Datasets/model_ready/ieq_model_dataset.xlsx`; the `data` sheet is back to 23 columns.
- Temporary experiment tables were removed after the numeric conclusion was recorded here and in `06_manuscript/modeling_results_notes.md`.

### Class-Imbalance Strategy Experiment
- Tested two additional non-two-stage imbalance strategies for IEQ: sample-weighted fitting and inner-fold probability multiplier calibration.
- Sample weighting was tested with balanced and square-root-balanced weights, including variants where model-level `class_weight` was removed.
- The best sample-weighted Extra Trees variant did not beat the refined baseline by macro F1: accuracy=0.727, macro F1=0.597, ordinal MAE=0.310.
- Extra Trees probability multiplier calibration reduced performance: accuracy=0.715, macro F1=0.596, ordinal MAE=0.317.
- Sample weighting substantially improved weak gradient boosting macro F1 from 0.464 to 0.532, but it remained below Extra Trees and Random Forest.
- These imbalance strategies were not adopted for the main IEQ model.
- Updated `06_manuscript/modeling_results_notes.md` and `07_transfer_learning/transfer_safe_feature_notes.md`.
- Temporary experiment tables and helper scripts were removed after the numeric conclusion was recorded in the information files.

### Primary-School-Only Training Experiment
- Tested training and evaluating models only on `Primary school` rows.
- The primary-school subset contains 5,101 rows: 336 dissatisfied, 1,193 neutral, and 3,572 satisfied.
- Also evaluated the existing full-dataset tuned CV predictions only on primary-school rows, so the primary-only model can be compared against the current model on the same population.
- All-school refined Extra Trees baseline across all rows: accuracy=0.725, macro F1=0.597, ordinal MAE=0.312.
- Full-dataset Extra Trees on primary rows: accuracy=0.758, macro F1=0.614, ordinal MAE=0.282.
- Primary-only Extra Trees: accuracy=0.762, macro F1=0.624, ordinal MAE=0.275.
- Primary-only Random Forest: accuracy=0.749, macro F1=0.607, ordinal MAE=0.292.
- Headline comparison versus the all-school baseline: primary-only Extra Trees improves accuracy by 3.74 percentage points, macro F1 by 0.026, and ordinal MAE by -0.037.
- Same-population comparison against the full-dataset model evaluated only on primary rows: primary-only Extra Trees improves accuracy by 0.45 percentage points, macro F1 by 0.010, and ordinal MAE by -0.007.
- Conclusion: school-level heterogeneity appears relevant for IEQ. Primary-school-specific IEQ modeling is worth presenting as a subset/sensitivity result, while the all-school model remains the main general model.
- Updated `06_manuscript/modeling_results_notes.md` and added `06_manuscript/primary_school_subset_summary.md` for supervisor-facing discussion.
- Saved experiment outputs to `02_outputs/supplementary_experiments/tables/primary_only_model_experiment_summary.csv`, `02_outputs/supplementary_experiments/tables/primary_only_model_experiment_folds.csv`, and `02_outputs/supplementary_experiments/tables/primary_only_target_distribution.csv`.
