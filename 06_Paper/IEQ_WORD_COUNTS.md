# IEQ Manuscript Length Plan

Generated from `06_Paper/IEQ.tex` on 2026-06-08 13:12.

Counting rule: prose only. The script excludes references, figures, tables, captions, LaTeX commands, and `\supervisornote{...}` draft notes.

Regenerate this file after edits with:

```powershell
python .\03_Code\_project_tools\update_ieq_word_counts.py
```

## Recommended Structure

| Part | Ideal words | Role | What to write in this paper |
|---|---:|---|---|
| Abstract | 150-250 | Short summary of the whole paper. | Problem, Belgian classroom dataset, three-class target, model comparison, best result, and practical decision-support value. |
| Introduction | 1300-2000 | Motivate why the study matters and place it in the literature. | Two main paragraphs under one heading: first practical use and energy-aware IEQ trade-offs; second review gaps and how this paper follows from them. Research questions and contributions can remain directly after it. |
| Dataset Description | 1500-2200 | Make the empirical basis clear and reproducible. | Dataset origin, classroom types, occupants, measured IEQ domains, survey scale, target definition, predictor groups, missingness, imputation, and leakage prevention. |
| Analysis | 900-1300 | Explain exactly how the models were trained and compared. | Model families, preprocessing pipeline, cross-validation design, tuning strategy, metrics, why macro F1 is primary, and how feature importance is evaluated. |
| Results | 1200-1800 | Report the evidence without over-interpreting it. | Main benchmark, confusion matrices, best hyperparameters, feature importance, sensitivity checks, and what the results show about difficulty of individual classroom IEQ prediction. |
| Preliminary Literature Benchmark | 300-600 | Compare results with related work carefully. | Explain why some papers report higher scores and why this task is harder: individual votes, three classes, classroom setting, sensor/context inputs, mixed school types. |
| Transfer Learning | 600-1000 | Show whether the approach generalizes beyond one setting. | Describe school-type transfer, domain shift, primary-only results, possible external dataset, and what this means for model reuse across schools. |
| Discussion | 1000-1500 | Convert results into meaning, limitations, and practical implications. | Energy-aware decision support, why separate thresholds are insufficient, where the model is useful, where it is not reliable enough, limitations, and implications for monitoring design. |
| Future Work | 300-600 | Define what must happen before real-world use. | Prospective classroom deployment, dashboard testing, occupied-building validation, calibration, transfer to other schools/seasons, and autonomous control only as future work. |
| Conclusion | 250-450 | Close the paper with the main claim and evidence. | One compact recap: dataset, best model, main finding, practical value, limitations, and next step toward real operation. |

## Current vs Ideal Length

| Part | Current words | Ideal words | Status | Gap |
|---|---:|---:|---|---:|
| Abstract | 197 | 150-250 | ok | within range |
| Introduction | 753 | 1300-2000 | short | +547 to minimum |
| Introduction / opening argument | 433 | 900-1300 | short | +467 to minimum |
| Introduction / Research Questions | 51 | 100-200 | short | +49 to minimum |
| Introduction / Contribution | 269 | 300-500 | short | +31 to minimum |
| Dataset Description | 444 | 1500-2200 | short | +1056 to minimum |
| Dataset Description / opening text | 135 | 700-1000 | short | +565 to minimum |
| Dataset Description / Data Cleaning and Imputation | 309 | 800-1200 | short | +491 to minimum |
| Analysis | 161 | 900-1300 | short | +739 to minimum |
| Analysis / Modeling Setup | 91 | 500-800 | short | +409 to minimum |
| Analysis / Tuning Workflow | 70 | 300-500 | short | +230 to minimum |
| Results | 535 | 1200-1800 | short | +665 to minimum |
| Results / Main Tuned Benchmark | 219 | 700-1000 | short | +481 to minimum |
| Results / Best Hyperparameters | 1 | 150-300 | short | +149 to minimum |
| Results / Fine-Tuning Results | 315 | 500-800 | short | +185 to minimum |
| Preliminary Literature Benchmark | 251 | 300-600 | short | +49 to minimum |
| Transfer Learning | 0 | 600-1000 | short | +600 to minimum |
| Discussion | 0 | 1000-1500 | short | +1000 to minimum |
| Future Work | 182 | 300-600 | short | +118 to minimum |
| Conclusion | 0 | 250-450 | short | +250 to minimum |
| Publishable total | 2523 | 6000-8000 | short | +3477 to minimum |

## Draft-only Sections

| Section | Current words |
|---|---:|
| My Questions | 0 |

## Practical Interpretation

- The manuscript is still short mainly because Discussion, Transfer Learning, and Conclusion are not developed yet.
- The current Introduction is now structurally close to the desired shape, but can still grow slightly if more detailed review synthesis is needed.
- The publishable target is roughly 6,000-8,000 prose words before references.
