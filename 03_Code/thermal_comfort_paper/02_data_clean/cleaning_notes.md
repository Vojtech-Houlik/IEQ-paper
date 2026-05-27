# Thermal Comfort Cleaning Notes

## Dataset Definition

- Raw source: `../../02_Datasets/raw/FullDataset_CombinedSimple.csv`
- Clean dataset file: `../../02_Datasets/clean/thermal_comfort_clean_dataset.xlsx`
- Model-ready dataset file: `../../02_Datasets/model_ready/thermal_comfort_model_dataset.xlsx`
- Target variable: `Thermal satisfaction`
- Derived target variable: `Thermal satisfaction 3-class`
- Primary modeling target: `Thermal satisfaction 3-class`
- Number of rows: 6,834
- Number of model input features: 16
- Metadata columns retained: `source_row_number`, `TimeVote`, `Occupant ID`, `Group`, `Subgroup`, `Student`

## Included Columns

- Output: `Thermal satisfaction`
- Derived output: `Thermal satisfaction 3-class`, using `dissatisfied` for votes 1-2, `neutral` for vote 3, and `satisfied` for votes 4-5.
- Modeling target: `Thermal satisfaction 3-class`; the original five-class scale remains available for descriptive reporting and optional sensitivity checks.
- Inputs: `Temperature`, `RH`, `CLO`, `Age`, `Gender`, `EA`, `LocationBack`, `LocationFront`, `LocationLeft`, `LocationRight`, `LocationMiddle`, `Ttrend`, `Vote hour`, `Vote weekday`, `Moment`, `AC on/off`

## Missing Data Strategy

- Numeric imputation: applied only by `_project_tools/create_step2_imputed_model_datasets.py`.
- Categorical imputation: applied only by `_project_tools/create_step2_imputed_model_datasets.py`.
- The clean dataset in `02_Datasets/clean` keeps missing values unchanged.
- The model-ready `data` sheet in `02_Datasets/model_ready` contains imputed values and excludes imputation metadata columns such as `Estimated Age`.
- Trace/context columns not intended as model inputs are removed from the model-ready `data` sheet: `source_row_number`, `Occupant ID`, `Group`, and `Subgroup`.
- `CLO`: imputed using the median within `Group`, falling back to the global median.
- `Age`: transferred from matching `Occupant ID` records when possible; otherwise estimated using `Group` + `Student`, `Group`, and global medians.
- `Gender`: transferred from matching `Occupant ID` records when possible; otherwise assigned by a seeded random draw from the observed gender distribution within `Group`.
- `LocationBack`, `LocationFront`, `LocationLeft`, `LocationRight`, and `LocationMiddle`: retained as raw binary classroom-location flags; unknown classroom location is defaulted to `LocationMiddle`.
- `Ttrend`: imputed using the median within `Group` + `Subgroup`, falling back to `Group` and global medians.
- Detailed imputation counts and strategies are retained in the support sheets, while the model-ready `data` sheet avoids redundant missingness-indicator columns.
- Excluded variables: all variables outside the Step 1 target/input definition.
- Row filtering: no rows were removed because of missing input values.
- Rejected ablation: broad missingness indicators (`Imputed CLO`, `Imputed Age`, `Imputed Gender`, `Imputed Location`, and `Imputed Ttrend`) were tested on 2026-05-07 and then removed from the model-ready dataset. They gave only a small fixed-parameter improvement for the best Random Forest model (accuracy 0.669 to 0.674; macro F1 0.593 to 0.597), so they were not adopted.

## Completeness Results

- The target variable is complete for all 6,834 rows.
- All planned input variables are complete in 2,219 rows, which is 32.5% of the dataset.
- The main missingness bottleneck is `Ttrend`, available in 41.0% of rows.
- Other incomplete variables are `Age` and `Gender` at 91.9%, `CLO` at 95.2%, and the location flags except `LocationRight` at 96.3%.
- The complete-case count is diagnostic only; no rows have been removed at this stage.

Generated outputs:

- `04_outputs/figures/01_feature_completeness_thermal_comfort.png`
- `04_outputs/figures/02_complete_case_availability_thermal_comfort.png`
- `04_outputs/tables/feature_completeness_thermal_comfort.csv`
- `04_outputs/tables/complete_case_availability_thermal_comfort.csv`

## Paper Paragraph Draft

Missing values were imputed using conservative, reproducible rules designed to preserve the ordinal satisfaction targets while avoiding avoidable row loss. Occupant ID, educational group, subgroup, and student status were used during preprocessing so that missing demographic values could be filled from the most relevant available context: age and gender were first transferred from other records of the same occupant; remaining missing age values were estimated from the median for the corresponding educational group and student-status combination, with group and global medians used as fallbacks, while remaining missing gender values were assigned by a seeded random draw from the observed gender distribution within the same educational group. For numeric exposure or context variables, clothing insulation was imputed by the group median, while temperature trend was imputed by subgroup-within-group medians where available and by broader medians otherwise. Classroom position was retained as the original set of front/back/left/right/middle binary location flags rather than collapsed into a single category; unknown classroom position was defaulted to middle. The final model-ready data sheet excludes trace columns and imputation metadata, while detailed imputation counts and strategies are retained in the workbook support sheets.
