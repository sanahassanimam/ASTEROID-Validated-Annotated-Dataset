# 📊 Benchmarked Annotation Dataset for LLM-Based Information Extraction

## 🔒 Repository Access
This is a **private repository** containing a **benchmarked and curated dataset** used for evaluating and comparing multiple LLM prompting strategies for structured information extraction from scientific literature.

The repository is intended for **internal use and controlled collaboration only**.

---

## 📌 Overview

This repository contains:

- A **fully annotated benchmark dataset** (170 documents)  
- Outputs from **multiple LLM prompting strategies**
- **Comparison, merging, and validation scripts**
- A visual **workflow of the benchmarking pipeline**

The dataset enables:
- Systematic comparison of *initial*, *refined*, and *GA-based* prompts  
- Quantitative mismatch analysis between LLM outputs and a reference database  
- Reproducible benchmarking and error analysis  

---

## 📂 Repository Structure

```
├── Annotated_Files_Combined/
│   └── all_annotations_combined.json
│
├── Images/
│   └── benchmarking_workflow.png
│
├── JSON_Files/
│   ├── JSON_firstprompt_files/
│   ├── JSON_finalprompt_files/
│   ├── JSON_GAprompt_files/
│   └── JSON_Combined_files/
│
├── Python_Scripts/
│   ├── combine_summary.py
│   ├── mismatch_checker.py
│   ├── merge_json_file.py
│   └── review_newversion.py
│
└── README.md
```

---

## 1️⃣ Annotated Files (Combined)

**Path:**  
`Annotated_Files_Combined/all_annotations_combined.json`

**Description:**  
- Contains **all 170 annotated JSON files merged into a single file**
- Each document retains its **full annotation structure**
- Designed for **direct import into any annotation viewer** (e.g., Label Studio or compatible tools)

**Usage:**  
- Download the file  
- Import into your annotation/inspection tool  
- Instantly browse all documents and their complete annotations  

---

## 2️⃣ Images (Benchmarking Workflow)

**Path:**  
`Images/benchmarking_workflow.png`

**Description:**  
- Visual overview of the **benchmarking and extraction pipeline**
- Illustrates prompt variants, JSON generation, merging logic, mismatch analysis, and review cycles

---

## 3️⃣ JSON Files (Prompt-wise Outputs)

**Path:**  
`JSON_Files/`

### Subfolders

- **JSON_firstprompt_files/**  
  JSON files produced using the initial baseline prompt.

- **JSON_finalprompt_files/**  
  JSON files generated using the final refined prompt.

- **JSON_GAprompt_files/**  
  JSON files produced using a Graph-Analysis (GA)–focused prompt.

- **JSON_Combined_files/**  
  JSON files created by merging outputs from the initial and GA-based prompts.

---

## 4️⃣ Python Scripts

**Path:**  
`Python_Scripts/`

### Script Descriptions

- **combine_summary.py**  
  Generates a global mismatch summary and outputs Excel/CSV files.

- **mismatch_checker.py**  
  Compares LLM-extracted JSON files with a reference Excel database.

- **merge_json_file.py**  
  Combines JSON outputs from initial and GA-based prompts.

- **review_newversion.py**  
  Supports review, validation, and correction of mismatches.

---

## 🔁 Benchmarking Workflow (Summary)

1. Run LLM extraction with different prompts  
2. Store prompt-specific JSON outputs  
3. Merge selected outputs  
4. Compare against the reference database  
5. Generate mismatch summaries  
6. Review and correct inconsistencies  
7. Produce final benchmark-ready dataset  

---

## 📎 Notes

- All data is **benchmarked against a curated reference**
- Intended for **research and methodological evaluation**
- Redistribution is **not permitted** without authorization

---

## License
See the LICENSE file in this repository.

---

## Contact
Sana Hassan Imam  
GitHub: sanahassanimam
Email:sana.hassan.imam@uni-oldenburg.de
