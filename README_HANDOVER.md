# Prism handover guide

Tento soubor slouzi jako rychla mapa pro predani slozky vedoucimu. Hlavni
pracovni cast je IEQ paper, ne cely historicky obsah slozky.

## Nejdulezitejsi soubory

1. Dataset pro modelovani:
   - `02_Datasets/model_ready/ieq_model_dataset.xlsx`

2. Hlavni notebooky:
   - `03_Code/ieq_paper/01_notebook/04_ieq_final_extra_trees_supervisor.ipynb`
   - `03_Code/ieq_paper/01_notebook/05_ieq_final_all_models_supervisor.ipynb`

3. Vystupy z hlavni analyzy:
   - `03_Code/ieq_paper/01_notebook/ieq_final_model_outputs/`
   - `03_Code/ieq_paper/01_notebook/ieq_all_models_outputs/`

4. Vystupy pouzite v clanku:
   - `03_Code/ieq_paper/02_outputs/tables/`
   - `04_Figures/ieq_paper/`
   - `04_Figures/both_papers/`

5. LaTeX draft:
   - `06_Paper/IEQ.tex`
   - `06_Paper/IEQ.pdf`
   - `06_Paper/references.bib`

## Co je vhodne nechat kvuli dohledatelnosti

- `02_Datasets/raw/` obsahuje puvodni dataset a dokumentaci.
- `02_Datasets/clean/` obsahuje mezikrok mezi raw daty a model-ready datasetem.
- `05_Related_papers/` obsahuje literaturu. Pro IEQ clanek jsou nejdulezitejsi:
  - `05_Related_papers/01_Core_Overall_IEQ/`
  - `05_Related_papers/03_Classroom_IEQ/`
  - `05_Related_papers/04_Methods_Standards/`
  - `05_Related_papers/05_Reviews/`

## Co neni nutne pro rychlou orientaci

- `03_Code/thermal_comfort_paper/` a thermal-comfort datasety/figury jsou pro
  druhy paper. Pro IEQ paper nejsou potreba.
- `03_Code/ieq_paper/01_notebook/02_ieq_model_comparison.ipynb`,
  `03_ieq_hyperparameter_tuning.ipynb` a `ieq_workflow.ipynb` jsou starsi nebo
  pomocne notebooky. Nechal bych je jen jako historii.
- `03_Code/ieq_paper/02_outputs/supplementary_experiments/` je doplnkova
  analyza. Neni to prvni misto, kam by se mel vedouci divat.
- `01_Texts/` obsahuje poznamky, podporne exporty a prezentace. Neni nutne pro
  reprodukci IEQ modelu.

## Soubory, ktere lze pred predanim smazat nebo ignorovat

Tyto soubory nejsou zdrojova data, notebooky ani clanek:

- `03_Code/_project_tools/**/__pycache__/`
- vsechny `*.pyc`
- LaTeX pomocne soubory v `06_Paper/`: `*.aux`, `*.bcf`, `*.blg`, `*.fdb_latexmk`,
  `*.fls`, `*.log`, `*.run.xml`, `*.synctex.gz`
- root slozky `ieq_all_models_outputs/` a `ieq_final_model_outputs/`, pokud
  zustanou aktualni vystupy v `03_Code/ieq_paper/01_notebook/`
- `main.tex` a `Preferences.xml` v koreni slozky, pokud uz nejsou pouzivane
- `04_Figures/ieq_paper/output.png`, pokud nejde o zamerne vlozeny obrazek
- `04_Figures/_legacy_article_figures_flat/` je jen archiv puvodni slozky
  `03_Code/article_figures`; LaTeX na ni neodkazuje.

Pred definitivnim mazanim je rozumne udelat ZIP aktualni slozky nebo mazat az v
kopii urcene k predani.

## Jak zkompilovat clanek

Z adresare `06_Paper`:

```powershell
latexmk -pdf IEQ.tex
```

LaTeX draft pouziva grafy relativne ke koreni projektu, proto je dulezite
nechat zachovanou strukturu slozek `03_Code/`, `04_Figures/` a `06_Paper/`.
