# Thermal Comfort Paper Progress

## 2026-05-04

### Done
- Created the thermal comfort paper workspace.
- Added the standard folder structure.
- Added the main workflow notebook placeholder.
- Defined the Step 1 thermal comfort target and inputs.
- Created `../../02_Datasets/clean/thermal_comfort_clean_dataset.xlsx`.
- Kept all 6,834 source rows; no rows were removed because of missing input values.
- Moved internal helper scripts to `_project_tools`.
- Generated feature completeness and complete-case availability plots.

### Decisions
- Thermal comfort will be handled as a separate paper from overall IEQ.
- Work should be documented continuously in Markdown and exported to PDF.
- Thermal comfort output is `Thermal satisfaction`.
- Thermal comfort inputs are `Temperature`, `RH`, `CLO`, `Age`, `Gender`, `EA`, `LocationBack`, `LocationFront`, `LocationLeft`, `LocationRight`, `LocationMiddle`, `Ttrend`, `Vote hour`, `Vote weekday`, `Moment`, and `AC on/off`.
- Helper scripts are internal project tools and should not be treated as paper-facing materials.
- Complete-case availability is diagnostic only at this stage; missing values have not been imputed or filtered out.

### Results
- Clean thermal comfort Excel created with 6,834 rows and 15 columns, including 2 metadata columns.
- Planned thermal comfort inputs are all complete in 2,219 rows, or 32.5% of the dataset.
- `Ttrend` is the main missingness bottleneck, with 41.0% completeness.
- Completeness outputs were saved in `04_outputs/figures` and `04_outputs/tables`.

### Open Questions
- Resolved on 2026-05-05: the main paper target is the unified three-class target.
- Resolved on 2026-05-05: missing values are handled by the documented model-ready imputation script.

### Next Actions
- Generate target distribution plots.
- Decide imputation strategy.
- Write the first missingness paragraph.

## 2026-05-05

### Done
- Added the shared project figure style guide.
- Added reusable Matplotlib style files in `_project_tools`.
- Regenerated completeness figures using the shared paper style.
- Added the shared `article_figures` folder for manuscript-ready figure exports.
- Added a paper-facing thermal satisfaction target distribution figure comparing the original five-class and unified three-class scales.
- Moved the clean thermal dataset to the central `../../02_Datasets/clean` folder and removed the duplicate Excel copy from `03_Code`.
- Added `Occupant ID`, `Group`, `Subgroup`, and `Student` metadata to the central clean dataset.
- Added `Thermal satisfaction 3-class` as an explicit derived target column.
- Added a separate imputation script that reads the clean dataset and writes a model-ready dataset to `../../02_Datasets/model_ready`.
- Added model-ready imputed values and retained only `Estimated Age` as compact metadata in the model-ready `data` sheet.
- Documented the imputation method and article paragraph draft.

### Decisions
- All new thermal comfort figures should follow `PAPER_FIGURE_STYLE_GUIDE.md`.
- The default paper plotting helper is `_project_tools/paper_style.py`.
- Manuscript-ready figure exports should be collected in `article_figures`.
- The primary modeling target for the thermal comfort paper is `Thermal satisfaction 3-class`; the original five-class `Thermal satisfaction` scale remains available for descriptive reporting and optional sensitivity checks.
- Unknown classroom location is defaulted to `LocationMiddle`; detailed imputation counts remain in workbook support sheets.
- Trace/context columns (`source_row_number`, `Occupant ID`, `Group`, `Subgroup`) are removed from the model-ready `data` sheet.
- Replaced the collapsed classroom-position feature with the raw classroom location flags: `LocationBack`, `LocationFront`, `LocationLeft`, `LocationRight`, and `LocationMiddle`.

### Results
- Existing completeness figures now use the shared TU Berlin / HRI inspired scientific style.
- Thermal feature completeness was exported to the shared article figure folder.
- The thermal satisfaction distribution figure was exported as `article_figures/fig_thermal_satisfaction_vote_distribution_original_unified`.
- The PDF copy is available in `Prism/04_Figures/thermal_comfort_paper`.
- The clean thermal dataset source is `Prism/02_Datasets/clean/thermal_comfort_clean_dataset.xlsx`.
- The supervisor-facing model-ready thermal dataset is `Prism/02_Datasets/model_ready/thermal_comfort_model_dataset.xlsx`.
- The model-ready thermal dataset has no missing values in the defined target/input columns after imputation.
- Clean thermal dataset shape: 6,834 rows and 24 columns.
- Model-ready thermal dataset shape: 6,834 rows and 40 columns.
- Clean thermal target/input missing cells before imputation: 6,480.
- Model-ready thermal target/input missing cells after imputation: 0.
- Thermal three-class target distribution: 799 dissatisfied, 2,099 neutral, 3,936 satisfied.

### Open Questions
- Should any target journal template override this style later?

### Next Actions
- Build the first thermal baseline model comparison on the model-ready dataset.
- Use the shared style for model comparison and feature importance figures.

## 2026-05-07

### Missingness Indicator Experiment
- Tested compact missingness indicators in the model-ready thermal comfort dataset: `Imputed CLO`, `Imputed Age`, `Imputed Gender`, `Imputed Location`, and `Imputed Ttrend`.
- Ran a fixed-parameter 5-fold comparison using the existing tuned model configurations, without retuning hyperparameters.
- Removed the missingness indicators from the model-ready dataset after review; only `Estimated Age` remains as compact imputation metadata.
- Regenerated `../../02_Datasets/model_ready/thermal_comfort_model_dataset.xlsx`; the `data` sheet is back to 21 columns.

### Results
- Random Forest remained the best thermal model: accuracy increased from 0.669 to 0.674, macro F1 from 0.593 to 0.597, and ordinal MAE decreased from 0.396 to 0.389.
- Extra Trees benefited most by macro F1: accuracy increased from 0.643 to 0.656, macro F1 from 0.577 to 0.591, and ordinal MAE decreased from 0.435 to 0.419.
- The gains were small relative to the extra feature complexity, so broad missingness indicators were not adopted for the paper-facing model-ready dataset.
- Temporary experiment tables were removed after the numeric conclusion was recorded here and in `06_manuscript/modeling_results_notes.md`.

### Class-Imbalance Strategy Experiment
- Tested three additional non-two-stage imbalance strategies: fold-internal thermal synthetic sampling, sample-weighted fitting, and inner-fold probability multiplier calibration.
- Synthetic sampling variants included random oversampling to 50% of the majority class, interpolation-style synthetic rows to 50%, and interpolation-style synthetic rows to full class balance.
- The best sample-weighted Random Forest variant removed model `class_weight` and used balanced sample weights: accuracy=0.670, macro F1=0.594, ordinal MAE=0.394.
- Probability multiplier calibration for Random Forest was similarly small: accuracy=0.671, macro F1=0.594, ordinal MAE=0.389.
- The best synthetic-sampling variant by macro F1 was random oversampling to 50% of the majority class with Random Forest: accuracy=0.667, macro F1=0.592, ordinal MAE=0.400.
- Some synthetic variants improved accuracy and ordinal MAE but reduced macro F1, so they were not adopted under the primary macro F1 selection rule.
- Added manuscript-facing notes in `06_manuscript/modeling_results_notes.md`.
- Temporary experiment tables and helper scripts were removed after the numeric conclusion was recorded in the information files.

### Primary-School-Only Training Experiment
- Tested training and evaluating models only on `Primary school` rows.
- The primary-school subset contains 5,101 rows: 500 dissatisfied, 1,610 neutral, and 2,991 satisfied.
- Also evaluated the existing full-dataset tuned CV predictions only on primary-school rows, so the primary-only model can be compared against the current model on the same population.
- Full-dataset Random Forest on primary rows: accuracy=0.690, macro F1=0.602, ordinal MAE=0.363.
- Primary-only Random Forest: accuracy=0.687, macro F1=0.600, ordinal MAE=0.366.
- Primary-only Extra Trees: accuracy=0.668, macro F1=0.601, ordinal MAE=0.404.
- Conclusion: primary-only training does not improve the best thermal comfort model, although weaker model families improve.
- Added details to `06_manuscript/modeling_results_notes.md`.
- Saved experiment outputs to `04_outputs/supplementary_experiments/tables/primary_only_model_experiment_summary.csv`, `04_outputs/supplementary_experiments/tables/primary_only_model_experiment_folds.csv`, and `04_outputs/supplementary_experiments/tables/primary_only_target_distribution.csv`.
