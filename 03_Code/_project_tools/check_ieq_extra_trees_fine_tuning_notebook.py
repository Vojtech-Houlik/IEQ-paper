from __future__ import annotations

import json
from pathlib import Path
import time


PROJECT_ROOT = Path(__file__).resolve().parents[2]
NOTEBOOK_PATH = PROJECT_ROOT / "03_Code" / "ieq_paper" / "01_notebook" / "04_ieq_extra_trees_fine_tuning.ipynb"
SMOKE_ROOT = PROJECT_ROOT / "03_Code" / "ieq_paper" / "02_outputs" / "supplementary_experiments" / "smoke" / f"run_{int(time.time())}"


def notebook_code() -> str:
    notebook = json.loads(NOTEBOOK_PATH.read_text(encoding="utf-8"))
    return "\n\n".join(
        "".join(cell["source"])
        for cell in notebook["cells"]
        if cell["cell_type"] == "code"
    )


def smoke_code(code: str) -> str:
    code = code.replace(
        "import matplotlib.pyplot as plt",
        'import matplotlib\nmatplotlib.use("Agg")\nimport matplotlib.pyplot as plt',
    )
    code = code.replace("N_SPLITS = 5", "N_SPLITS = 2")
    code = code.replace("TEN_FOLD_SPLITS = 10", "TEN_FOLD_SPLITS = 2")
    code = code.replace("THRESHOLD_INNER_SPLITS = 3", "THRESHOLD_INNER_SPLITS = 2")
    code = code.replace("CALIBRATION_INNER_CV = 3", "CALIBRATION_INNER_CV = 2")
    code = code.replace(
        'OUTPUT_DIR = PROJECT_ROOT / "03_Code" / "ieq_paper" / "02_outputs" / "supplementary_experiments" / "tables"',
        f'OUTPUT_DIR = Path("{(SMOKE_ROOT / "tables").as_posix()}")',
    )
    code = code.replace(
        'FIGURE_DIR = PROJECT_ROOT / "03_Code" / "ieq_paper" / "02_outputs" / "supplementary_experiments" / "figures"',
        f'FIGURE_DIR = Path("{(SMOKE_ROOT / "figures").as_posix()}")',
    )
    code = code.replace(
        'RANDOM_FOREST_PARAMS = best_params["Random Forest"]',
        (
            'RANDOM_FOREST_PARAMS = best_params["Random Forest"]\n\n'
            'EXTRA_TREES_PARAMS["model__n_estimators"] = 20\n'
            'RANDOM_FOREST_PARAMS["model__n_estimators"] = 20'
        ),
    )
    return code


def main() -> None:
    code = smoke_code(notebook_code())
    compile(code, str(NOTEBOOK_PATH), "exec")
    exec(code, {"__name__": "__main__"})
    print(f"Smoke outputs written under {SMOKE_ROOT}")


if __name__ == "__main__":
    main()
