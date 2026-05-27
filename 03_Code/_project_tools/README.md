# Project Tools

Internal helper scripts for project maintenance and one-off reproducible exports.

These scripts are not paper-facing materials for supervisors. Paper-ready outputs, notebooks, datasets, figures, tables, and progress notes stay inside `thermal_comfort_paper` and `ieq_paper`.

## Scripts

- `create_article_figures.py`: regenerates the manuscript-ready figures directly in the relevant `../04_Figures` subfolder.
- `create_step1_clean_paper_datasets.py`: regenerates the clean Excel datasets in `../02_Datasets/clean` from the raw Belgian classrooms dataset.
- `create_step2_imputed_model_datasets.py`: reads `../02_Datasets/clean` and writes model-ready imputed datasets to `../02_Datasets/model_ready`.
- `create_step2_completeness_graphs.py`: regenerates the Step 2 completeness figures and source tables for both papers.
- `export_project_docs_to_pdf.py`: exports the root roadmap and paper progress logs from Markdown to PDF.
- `paper_style.py`: shared plotting helper for all paper figures.
- `tu_hri_paper.mplstyle`: shared Matplotlib style file for notebooks or quick plots.

## Notebook Versions

Notebook versions of the Python tools are stored next to the scripts with the same base name and the `.ipynb` extension. They keep the script logic intact but split it into smaller sections with short markdown explanations, so the workflow can be read and run step by step.

Use the `.py` files for reproducible command-line regeneration, and use the `.ipynb` files when exploring or explaining the workflow.
