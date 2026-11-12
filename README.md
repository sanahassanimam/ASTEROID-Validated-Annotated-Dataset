# ASTEROID: Validated Annotated Dataset of Graph Theory-Based fMRI Analytical Decisions

[![ASTEROID interactive viewer](https://img.shields.io/badge/ASTEROID-Interactive%20Viewer-blue)](https://asteroid.shinyapps.io/asteroid/)

## Overview

**ASTEROID** is a structured, expert-reviewed annotation dataset describing analytical decisions reported in published graph theory-based human functional magnetic resonance imaging (fMRI) research. It supports the systematic examination of methodological choices in fMRI preprocessing, functional-connectivity analysis, and graph-theoretical network analysis.

The accompanying manuscript describes annotations from **156 studies** using a schema of **125 labels**: **61 methodological labels** and **64 labels** covering study characteristics and experimental design. The annotations were produced through an LLM-assisted workflow, followed by automated quality-control procedures and human expert review. The final annotations include methodological steps, software, algorithms/types, parameters, and links to supporting text spans where available.

## Contents

- Final human-reviewed annotations in Label Studio-compatible JSON format
- Source-study bibliography and schema-labeled supporting text spans in Excel format
- Intermediate JSON outputs from different prompting strategies
- Prompt specifications used for LLM-assisted pre-annotation
- Scripts supporting merging, mismatch assessment, summary generation, and review
- Interactive ASTEROID application for exploring the schema and annotations
- Supporting images and workflow visualizations

## Main dataset

**Path:** [`Annotated_Files/all_annotations.json`](Annotated_Files/all_annotations.json)

The consolidated JSON contains structured records representing the reviewed source studies. Its annotations cover:

1. **Study characteristics:** bibliographic and participant/study information.
2. **Experimental design:** functional-scan and experimental-design information.
3. **Analytical pipeline:** methodological decisions involving structural and functional preprocessing, noise removal/filtering, functional connectivity, and graph analysis.

Methodological annotations include standardized attributes such as step number, software, algorithm/type, and parameters. Source text spans are provided where available. Missing or ambiguous fields should be interpreted in the context of the original studies' reporting, not automatically as evidence that an analysis step was not performed.

**Data format:** JSON, structured for compatibility with Label Studio annotation import. The contents should be inspected using the included schema documentation and/or the ASTEROID viewer.

**Source studies and annotation spans:** [`Annotated_Files/source_studies_with_annotations.xlsx`](Annotated_Files/source_studies_with_annotations.xlsx)

The Excel workbook provides a searchable overview of the 156 source studies, including bibliographic metadata, DOI links, identified schema labels, and supporting annotated text spans. The **Source Studies** sheet summarizes labels and text evidence per study; **Annotation Text Spans** lists individual spans with their schema groups, labels, and start/end offsets; and **Schema Labels** summarizes label frequencies. Offsets are character positions in the text imported for annotation, **not** PDF page numbers or page coordinates. The validated JSON above remains the primary annotation dataset.

**Data dictionary/schema:** [`Schema_Viewer/Schema.html`](Schema_Viewer/Schema.html)

`Schema.html` contains the Label Studio annotation schema used for ASTEROID. It organizes labels for study characteristics, experimental design, fMRI preprocessing, functional connectivity, and graph analysis, and defines methodological sublabels such as step number, software, algorithm/type, and parameters. It can be used to interpret the labels in the JSON dataset and Excel workbook.


## Repository organization

The following layout is based on the project documentation. 

```text
ASTEROID-Validated-Annotated-Dataset/
├── README.md
├── Prompts/
│   ├── First Prompt.md
│   ├── GA Prompt.md
│   └── Final Prompt.md
├── JSON_Files/
│   ├── Firstprompt/
│   ├── GAprompt/
│   ├── Finalprompt/
│   └── Combined JSON/
├── Annotated_Files/
│   ├── all_annotations.json
│   └── source_studies_with_annotations.xlsx
├── Python_Scripts/
│   ├── combine_summary.py
│   ├── mismatch_checker.py
│   ├── merge_json_files.py
│   ├── requirements.txt
│   └── review_newversion.py
├── Schema_Viewer/
│   ├── ASTEROID.html
│   └── Schema.html
└── Images/
    ├── workflow.png
    ├── explorer1.jpeg
    ├── explorer2.jpeg
    └── explorer3.jpeg

    
```

### Intermediate JSON outputs

`JSON_Files/` contains LLM-generated pre-annotation outputs:

- `Firstprompt/`: outputs from the initial broad extraction prompt.
- `GAprompt/`: outputs from the graph-analysis-focused extraction prompt.
- `Finalprompt/`: outputs from the refined single-pass prompt.
- `Combined JSON/`: outputs combining first-prompt and graph-analysis annotations.


The manuscript describes a staged extraction process: initial and graph-analysis prompting with merged outputs for the first 100 studies, followed by a refined prompt for the remaining 60. These intermediate files should **not** be confused with the final human-reviewed dataset in `Annotated_Files/`.

### Prompt specifications

`Prompts/` contains the schema-guided prompts used for LLM-assisted pre-annotation of the source studies:

- **First Prompt:** Initial extraction of publication details, study characteristics, and methodological information.
- **GA Prompt:** Focused extraction of functional-connectivity and graph-analysis decisions to supplement the initial output.
- **Final Prompt:** Refined prompt combining the extraction requirements into a more consistent single-pass workflow.

These prompts document how the extraction strategy evolved. Their outputs were subsequently checked and reviewed; the final human-validated annotations are provided in `Annotated_Files/all_annotations.json`. **Confirm the actual prompt filenames and extensions before release.**

### Python scripts

`Python_Scripts/` includes:

| Script | Function |
| --- | --- |
| `combine_summary.py` | Produces summaries of annotation and validation results. |
| `mismatch_checker.py` | Compares structured annotations with the manually curated reference information. |
| `merge_json_files.py` | Integrates first-prompt and graph-analysis outputs. |
| `review_newversion.py` | Supports inspection and review of validation discrepancies. |

The scripts are provided to document the processing and validation workflow. Some require the original intermediate inputs and the manually curated reference workbook; they do not regenerate the human-reviewed final annotations on their own.

### Software requirements and reproduction

The workflow is documented as having been developed using **Python 3.10**. The four supplied utility scripts import the external packages `pandas`, `numpy`, and `openpyxl`; the listed dependency versions were checked for availability in a Python environment, but **the complete workflow has not been end-to-end tested against the original project inputs**.

From the repository root, create an environment and install dependencies:

```bash
python3.10 -m venv .venv
# Linux/macOS: source .venv/bin/activate
# Windows (PowerShell): .venv\Scripts\Activate.ps1
python -m pip install -r Python_Scripts/requirements.txt
```

Usage examples (substitute the actual local input paths):

```bash
# Combine comparison-report CSVs and produce an Excel summary
python Python_Scripts/combine_summary.py --folder "path/to/comparison_csvs"

# Check entries marked missing in TXT summaries against the reference workbook
python Python_Scripts/mismatch_checker.py --excel "path/to/reference.xlsx" --txt_dir "path/to/missing_summaries"

# Compare LLM JSON outputs against the same reference workbook
python Python_Scripts/review_newversion.py --excel "path/to/reference.xlsx" --sheet Seed2 --json_root "path/to/json_outputs" --recursive

# Merge initial and graph-only JSON exports (see directory requirements below)
python Python_Scripts/merge_json_files.py
```

**Inputs and outputs:**

- `combine_summary.py` accepts a directory of comparison CSV files with columns such as `Verdict`, `Category`, and `Match_quality` and writes `Combined_Verdict_Category_Match_Summary.xlsx` to that directory.
- `mismatch_checker.py` accepts `--excel` plus either `--txt` (one missing-summary TXT file) or `--txt_dir` (a directory of TXT summaries). It writes per-paper mismatch reports in TXT format.
- `review_newversion.py` reads an Excel worksheet (default `Seed2`) and matching `*_extracted_labels*.json` or `*_combined_labels.json` files and writes per-paper `*_table.csv` comparison reports next to the JSON files. Optional flags include `--show_values` and `--no_fuzzy`.
- `merge_json_files.py` has no command-line arguments. Its input/output directories are currently configured relative to the **working directory** as `JSON_firstprompt_files/`, `JSON_Graph_only_files/`, and `JSON_Combined_files/`. Create/populate these directories or edit `BASE_DIR`, `GRAPH_DIR`, and `OUT_DIR` in the script to match your local layout. It also writes `merge_report.txt` and `merge_report.csv` to the working directory. The expected filenames end in `_extracted_labels.json` and `_graph_labels.json`.

**Reference-workbook limitation:** Both comparison scripts expect the original reference Excel workbook with a `Seed2` worksheet and two header rows (family and label), including preprocessing step columns. The publication overview `Annotated_Files/source_studies_with_annotations.xlsx` is **not** that reference workbook and must not be supplied as its replacement. Include the reference workbook if its redistribution is authorized, or document its access restrictions.

These are **code-derived usage instructions**. Before public release, run the commands using the actual repository inputs, verify the generated files, and confirm the documented Python/package versions on the supported platform.


## Interactive ASTEROID application

**Open the online ASTEROID viewer:** https://asteroid.shinyapps.io/asteroid/

The interactive application supports three core activities:

1. **Schema Graph:** Explore the relationships among annotation families, groups, steps, and sublabels, including descriptions and hierarchy.
2. **Annotations Explorer:** Load compatible annotation JSON and inspect the supporting text and label assignments.
3. **Generate Report:** Select reported analysis steps and provide corresponding step numbers, software, algorithms/types, and parameters to create a structured summary.

**Using the viewer:**

1. Open the application URL in a modern browser.
2. Select the relevant tab.
3. To examine final annotations, download `Annotated_Files/all_annotations.json` and upload it through the viewer's file selector, if prompted.
4. Use the Schema Graph and reporting interface to explore the annotation framework.

The app is a visualization and inspection tool; the downloadable, archived JSON dataset remains the authoritative data record. 

### Application screenshots

#### Tab 1 — Schema Graph

Explore the hierarchical annotation schema and inspect
relationships between label groups, steps, and sublabels.

![ASTEROID Schema Graph](Images/explorer1.jpeg)

#### Tab 2 — Annotations Explorer

Load compatible JSON annotation files and examine
highlighted text spans and assigned labels.

![ASTEROID Annotations Explorer](Images/explorer2.jpeg)

#### Tab 3 — Generate Report

Create structured summaries of preprocessing and
graph-analysis decisions.

![ASTEROID Report Generator](Images/explorer3.jpeg)


## Dataset creation and validation

### ASTEROID Dataset Construction Workflow

The following diagram illustrates the ASTEROID dataset
construction process, including literature collection,
PDF-to-JSON conversion, LLM-assisted pre-annotation,
automated quality control, and expert human review.

![ASTEROID dataset construction workflow](Images/workflow.png)

The manuscript describes the following workflow:

1. Compile a corpus of published graph theory-based human fMRI studies.
2. Convert source PDFs to structured text/JSON.
3. Produce initial schema-guided annotations using LLM prompts.
4. Run automated checks for missing/duplicated decisions, parameter formatting, step numbering, and span offsets.
5. Compare annotation outputs with a previously compiled manual extraction resource.
6. Review flagged and ambiguous records using human expertise, and export the validated annotation dataset.

The PDF-to-JSON conversion tool is documented separately in [Annotation-buddy](https://github.com/sanahassanimam/Annotation-buddy).

The manual comparison is an evaluation resource, not absolute ground truth. The manuscript reports targeted expert review and discussion to resolve uncertain cases; it does **not** report an independent parallel annotation study or inter-annotator agreement statistic. Consult the accompanying manuscript for the precise validation methodology and limitations.

## Reuse and limitations

ASTEROID is intended for examining reported methodological decisions in graph theory-based human fMRI studies, supporting comparisons across studies, identifying plausible choices for multiverse analyses, and evaluating automated scientific information-extraction workflows.

The dataset records information **as reported** in source publications. An unreported annotation does not necessarily mean the corresponding method was not used. Ordering information and source-text support should be interpreted according to the annotation definitions and documented workflow. Use caution in applying the schema outside its source domain without additional validation.

## Data availability and versioning

- **GitHub project:** https://github.com/sanahassanimam/ASTEROID-Validated-Annotated-Dataset
- **Archived dataset:** Zenodo record in preparation; a permanent DOI will be added upon publication.
- **Version-specific DOI:** Zenodo record in preparation; a permanent DOI will be added upon publication.
- **Dataset version/release:** Zenodo record in preparation; a permanent DOI will be added upon publication.
- **Online viewer:** https://asteroid.shinyapps.io/asteroid/

For scholarly citation, use the exact archived dataset version and its DOI once registered. The GitHub repository may evolve independently of the archived version used in the manuscript.

## Licence and third-party source material

**Data licence:** To be confirmed before public release, following review of third-party source-text rights.

**Code licence:** To be confirmed before public release, following review of third-party source-text rights.

Annotations may contain passages derived from third-party publications, including excerpts in the Excel workbook. Do not assume that licensing the annotation dataset automatically grants permission to redistribute third-party copyrighted article text. Review the source licences and permissions before public release. If needed, distribute bibliographic metadata and annotation labels separately from restricted excerpts.

## Citation

**Dataset:** ASTEROID — Validated Annotated Dataset of Graph Theory-Based fMRI Analytical Decisions. Zenodo dataset archive (DOI to be added upon publication of the record).

**Related Data Descriptor:** Imam et al., "ASTEROID: A Validated Annotated Dataset of Graph Theory–Based fMRI Analytical Decisions Derived by LLM-Assisted Literature Mining." Manuscript in preparation.


## Contact

**Sana Hassan Imam**  
Carl von Ossietzky Universität Oldenburg  
GitHub: [sanahassanimam](https://github.com/sanahassanimam)  
Email: sana.hassan.imam@uni-oldenburg.de
