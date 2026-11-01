# WellSense
**A Hybrid Knowledge-Based System for Fault Diagnosis and Maintenance Decision Support in Offshore Oil Wells**
KBS (CT-359) Complex Computing Problem, NED University of Engineering & Technology · Section B (AI) · Submitted to Miss Mehar Fatima

| Roll No. | Name |
|---|---|
| CT-24161 | Sadia Khan |
| CT-24168 | Zehra Kazmi |
| CT-24172 | Haseeb Yaqoob |
| CT-24192 | Roman Aziz |

📄 Project report: [`docs/WellSense_CCP_Report.docx`](docs/WellSense_CCP_Report.docx)

## How to run in Google Colab
1. Download this repository (green **Code** button → **Download ZIP**), unzip it, and upload the whole folder to **My Drive** (e.g. `My Drive/WellSense`; the notebooks find it automatically, even if it is called `WellSense-main`).
2. Open each notebook from Drive with *Open with → Google Colaboratory* and click **Runtime → Run all** (allow Drive access).
3. Run them **in this order**:

| # | Notebook | What it does | Time |
|---|---|---|---|
| 0 | `00_Data_Preparation.ipynb` | *Optional.* Downloads Petrobras's official files and re-creates the dataset; proves it is identical to the approved file. Also creates `data/3W_real_instances_1min.csv` (all 1,119 instances) needed for re-running the full evaluation. | ~5 min, 500 MB download |
| 1 | `01_ETL.ipynb` | Extract → Transform → Load: cleans the data, tags quality, builds symbolic facts, creates `db/wellsense.db` | ~1 min |
| 2 | `02_Knowledge_Base.ipynb` | Knowledge sources, ontology (+ OWL export), data evidence, rule base, consistency checks | ~1 min |
| 3 | `03_Inference_and_Diagnosis.ipynb` | The KBS on 5 real cases: forward/backward chaining, explanations, safety-aware recommendations, knowledge refinement, plus a **live consultation** (Section 9): describe what you see and get a diagnosis, questions, explanation and safe actions | ~3 min |
| 4 | `04_Evaluation.ipynb` | Held-out evaluation, error analysis, ablation, robustness, backward chaining, ML comparison | ~25 min (or instant with saved results) |

**Every notebook already contains its outputs**, so it can be read without running anything.

**Notebook 4 and the full dataset:** the held-out experiments need `db/wellsense_full.db`. To recompute them: run Notebook 0, then Notebook 1 with `USE_FULL_DATA = True` (≈2 min, ≈5 GB RAM), then Notebook 4. Without it, Notebook 4 automatically loads the saved results from `outputs/tables/`.

**Different Google account for Colab?** Put the folder in that account's Drive, or set `SOURCE = 'upload'` in the first code cell of each notebook and upload this zip.

**Live consultation:** Notebook 3, Section 9 — run the cell, choose what you observe from the menus (or load an example) and click **Diagnose**. The KBS asks questions with clickable Yes / No / Don't know buttons, then explains and recommends safe actions.

## Folder layout
```
WellSense/
├── 00…04 notebooks
├── data/            3W_real_small.csv (approved dataset), data dictionary, README
├── knowledge_base/  ontology, rules, questions, actions, safety constraints, profiles, settings, sources (JSON)
│                    + wellsense_ontology.ttl (open in Protégé)
├── wellsense/       the inference engine package (our own code)
│                    kb.py · engine.py · explain.py · decision.py · monitor.py · refine.py · evaluate.py
├── src/kb_source.py script that writes the knowledge-base JSON files
├── db/              created by Notebook 1 (not stored in the repository)
├── docs/            project report
└── outputs/         figures/ and tables/ used in the report
```

## Key results (held-out, 959 instances never used during development)
* Accuracy 52.1 %, balanced accuracy 57.4 %; spurious DHSV closures 7/7 (median 7 min after onset); severe slugging 14/17
* False alarms on normal wells 15.7 % (1.3 % excluding one well)
* A Random Forest baseline is more accurate (75.4 %) but cannot explain, detect faulty sensors, apply safety constraints or recommend actions — see the report, Section 8.6 and 9.1

## Data source
Petrobras 3W Dataset v2.0.0, https://github.com/petrobras/3W (CC BY 4.0).
Vargas et al., *3W Dataset 2.0.0: a realistic and public dataset with rare undesirable real events in oil wells*, 2025, https://arxiv.org/abs/2507.01048
