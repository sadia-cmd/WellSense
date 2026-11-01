# 🛢️ WellSense

**A Hybrid Knowledge-Based System for Fault Diagnosis and Maintenance Decision Support in Offshore Oil Wells**

Knowledge-Based Systems (CT-359) Complex Computing Problem, NED University of Engineering & Technology
Section B (AI) · Submitted to Miss Mehar Fatima

| Roll No. | Name |
|---|---|
| CT-24161 | Sadia Khan |
| CT-24168 | Zehra Kazmi |
| CT-24172 | Haseeb Yaqoob |
| CT-24192 | Roman Aziz |

📄 Report: [docs/WellSense_CCP_Report.docx](docs/WellSense_CCP_Report.docx)

## About

WellSense watches real offshore oil well sensors (the public Petrobras 3W dataset), diagnoses which of 9 faults is happening, explains how it reached its answer, asks the operator questions when the sensors are not enough, and recommends maintenance actions for different stakeholders without ever suggesting an unsafe one. When too few sensors can be trusted, it says "undetermined" instead of guessing.

It combines an ontology of the well, 153 IF THEN rules with certainty factors, and our own inference engine using forward and backward chaining.

## How to run

1. Download this repository (Code → Download ZIP) and unzip it.
2. Upload the folder to My Drive in Google Drive.
3. Open each notebook with Google Colaboratory and click Runtime → Run all.

| # | Notebook | What it does |
|---|---|---|
| 0 | `00_Data_Preparation.ipynb` | Optional: rebuilds the dataset from the official Petrobras files |
| 1 | `01_ETL.ipynb` | Cleans the data and turns readings into facts |
| 2 | `02_Knowledge_Base.ipynb` | Ontology, rules, questions, actions and safety constraints |
| 3 | `03_Inference_and_Diagnosis.ipynb` | Real cases, explanations, recommendations and the live consultation |
| 4 | `04_Evaluation.ipynb` | Results on unseen data and comparison with machine learning |

Every notebook already contains its outputs, so you can read it on GitHub without running it.

**Live consultation:** in Notebook 3, Section 9, choose what you observe from the menus, click Diagnose, and answer the system's questions with the buttons.

## Results

Tested on 959 real recordings that were never used while building the system:

| Measure | Result |
|---|---|
| Accuracy | 52.1 % (balanced 57.4 %) |
| Safety valve closures caught | 7 of 7, median 7 minutes after onset |
| Severe slugging caught | 14 of 17 |
| False alarms on normal wells | 15.7 % (1.3 % without one noisy well) |

A Random Forest baseline is more accurate (75.4 %) but cannot explain its answers, detect a frozen sensor, apply safety rules or recommend actions.

## Repository structure

```text
WellSense/
├── 00 to 04 notebooks
├── data/            approved dataset and data dictionary
├── knowledge_base/  ontology, rules, questions, actions, safety constraints (JSON)
├── wellsense/       our inference engine
├── src/             script that writes the knowledge base files
├── outputs/         figures and tables
└── docs/            project report
```

## Data

Petrobras 3W Dataset v2.0.0, [github.com/petrobras/3W](https://github.com/petrobras/3W) (CC BY 4.0).
Vargas et al., *3W Dataset 2.0.0: a realistic and public dataset with rare undesirable real events in oil wells*, 2025, [arXiv:2507.01048](https://arxiv.org/abs/2507.01048).
