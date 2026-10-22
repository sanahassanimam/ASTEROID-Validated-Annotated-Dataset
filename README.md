# ASTEROID: Validated Annotated Dataset of Graph Theory-Based fMRI Analytical Decisions

[![ASTEROID interactive viewer](https://img.shields.io/badge/ASTEROID-Interactive%20Viewer-blue)](https://asteroid.shinyapps.io/asteroid/)

## Overview

**ASTEROID** is a structured, expert-reviewed annotation dataset describing analytical decisions reported in published graph theory-based human functional magnetic resonance imaging (fMRI) research. It supports the systematic examination of methodological choices in fMRI preprocessing, functional-connectivity analysis, and graph-theoretical network analysis.

The accompanying manuscript describes annotations from **160 studies** using a schema of **125 labels**: **61 methodological labels** and **64 labels** covering study characteristics and experimental design. The annotations were produced through an LLM-assisted workflow, followed by automated quality-control procedures and human expert review. The final annotations include methodological steps, software, algorithms/types, parameters, and links to supporting text spans where available.

> **Release verification:** Confirm that `Annotated_Files/all_annotations.json` contains the 160 unique final study records described in the manuscript before publishing this README. Earlier internal documentation listed 170 and 175 files; those numbers may refer to other stages of the corpus, but should not be used for the final dataset without verification.

## Contents

- Final human-reviewed annotations in Label Studio-compatible JSON format
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

**Source studies:** [ADD LINK TO A MANIFEST OF THE 160 SOURCE STUDIES, INCLUDING DOI OR OTHER IDENTIFIERS, IF AVAILABLE]

**Data dictionary/schema:** [ADD THE EXISTING SCHEMA DOCUMENTATION PATH OR PROVIDE A MACHINE-READABLE SCHEMA FILE]

## Repository organization

The following layout is based on the project documentation. **Check all names and file extensions against the actual repository before release.**

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
│   └── all_annotations.json
├── Python_Scripts/
│   ├── combine_summary.py
│   ├── mismatch_checker.py
│   ├── merge_json_file.py
│   └── review_newversion.py
├── Schema_Viewer/
│   └── schema_viewer.html
└── Images/
    └── benchmarking_workflow.html
```

### Intermediate JSON outputs

`JSON_Files/` contains LLM-generated pre-annotation outputs:

- `JSON_Firstprompt_files/`: outputs from the initial broad extraction prompt.
- `JSON_GAprompt_files/`: outputs from the graph-analysis-focused extraction prompt.
- `JSON_Combined_files/`: outputs combining first-prompt and graph-analysis annotations.
- `JSON_Finalprompt_files/`: outputs from the refined single-pass prompt.

The manuscript describes a staged extraction process: initial and graph-analysis prompting with merged outputs for the first 100 studies, followed by a refined prompt for the remaining 60. These intermediate files should **not** be confused with the final human-reviewed dataset in `Annotated_Files/`.

### Prompt specifications

`Prompts/` documents the extraction instructions for the First Prompt, GA Prompt, and Final Prompt. These record the development of the LLM-assisted annotation workflow. **Confirm the actual filenames and extensions before release.**

### Python scripts

`Python_Scripts/` includes:

| Script | Function |
| --- | --- |
| `combine_summary.py` | Produces summaries of annotation and validation results. |
| `mismatch_checker.py` | Compares structured annotations with the manually curated reference information. |
| `merge_json_file.py` | Integrates first-prompt and graph-analysis outputs. |
| `review_newversion.py` | Supports inspection and review of validation discrepancies. |

The manuscript reports that these scripts were developed and tested using **Python 3.10**. To reproduce script execution, provide the tested dependencies and exact example commands below once verified.

```bash
# Installation (replace only after testing the requirements file)
python -m venv .venv
python -m pip install -r Python_Scripts/requirements.txt
```

> **To complete:** Add the verified `requirements.txt` path; specify the input files, command-line arguments or configuration, and outputs for each script. If a script depends on a manually curated reference database that cannot be shared, document that limitation precisely.

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

The app is a visualization and inspection tool; the downloadable, archived JSON dataset remains the authoritative data record. **Before release, confirm that all tabs, JSON upload, and report generation work for a visitor who is not logged into your accounts.**

## Dataset creation and validation

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
- **Archived dataset:** [ADD ZENODO RECORD URL AFTER THE DEPOSIT IS READY]
- **Version-specific DOI:** [ADD RESERVED OR REGISTERED DATASET DOI WHEN AVAILABLE]
- **Dataset version/release:** [ADD RELEASE TAG OR VERSION]
- **Online viewer:** https://asteroid.shinyapps.io/asteroid/

For scholarly citation, use the exact archived dataset version and its DOI once registered. The GitHub repository may evolve independently of the archived version used in the manuscript.

## Licence and third-party source material

**Data licence:** [CONFIRM WITH CO-AUTHORS AFTER REVIEWING RIGHTS IN PUBLISHED SOURCE-TEXT EXCERPTS]

**Code licence:** [SPECIFY THE EXISTING APPROVED CODE LICENCE]

Annotations may contain passages derived from third-party publications. Do not assume that licensing the annotation dataset automatically grants permission to redistribute third-party copyrighted article text. Review the source licences and permissions before public release.

## Citation

**Dataset:** [ADD EXACT ZENODO CITATION AND DOI AFTER RECORD CREATION]

**Related Data Descriptor:** [ADD PUBLICATION CITATION WHEN AVAILABLE]

## Contact

**Sana Hassan Imam**  
Carl von Ossietzky Universität Oldenburg  
GitHub: [sanahassanimam](https://github.com/sanahassanimam)  
Email: sana.hassan.imam@uni-oldenburg.de
