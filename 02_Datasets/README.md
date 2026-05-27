# Dataset Workflow

This folder separates the two dataset stages used in the papers.

## Folder Structure

- `clean/`: cleaned datasets before missing-value imputation.
- `model_ready/`: datasets after missing-value imputation, intended for modeling and supervisor handoff.
- `raw/`: unchanged original Belgian classroom dataset files.

## Files

Clean datasets:

- `raw/FullDataset_CombinedSimple.csv`
- `clean/thermal_comfort_clean_dataset.xlsx`
- `clean/ieq_clean_dataset.xlsx`

Model-ready datasets:

- `model_ready/thermal_comfort_model_dataset.xlsx`
- `model_ready/ieq_model_dataset.xlsx`

For modeling or supervisor handoff, use the `data` sheet in the files under `model_ready/`.

The clean datasets include the original five-class target and an explicit three-class target:

- `Thermal satisfaction` and `Thermal satisfaction 3-class`
- `IEQ satisfaction` and `IEQ satisfaction 3-class`

The three-class target uses `dissatisfied` for votes 1-2, `neutral` for vote 3, and `satisfied` for votes 4-5.

The papers will use the three-class target as the primary modeling target:

- thermal comfort paper: `Thermal satisfaction 3-class`
- IEQ paper: `IEQ satisfaction 3-class`

The original five-class target is retained in the clean datasets for descriptive distributions, traceability to the source questionnaire, and optional sensitivity checks. In the IEQ model-ready `data` sheet, `IEQ satisfaction` is removed and `IEQ satisfaction 3-class` is retained as the modeling target.

The model-ready `data` sheets remove trace/context columns that should not be used as model inputs: `source_row_number`, `Occupant ID`, `Group`, and `Subgroup`.

The model-ready `data` sheets also exclude imputation metadata columns such as `Estimated Age`.

Missingness indicator columns such as `Imputed CLO`, `Imputed Ttrend`, `Imputed Lighting`, and `Imputed Sound` were tested as a rejected ablation on 2026-05-07. They were not retained in the model-ready `data` sheets because the performance gains were small relative to the added feature complexity and did not clearly improve the main paper-facing model narrative.

## Reproducible Scripts

From `Prism/03_Code`, run:

- `_project_tools/create_step1_clean_paper_datasets.py`: builds the clean datasets from the raw Belgian classroom dataset.
- `_project_tools/create_step2_imputed_model_datasets.py`: reads the clean datasets and writes the model-ready datasets with imputed missing values.
