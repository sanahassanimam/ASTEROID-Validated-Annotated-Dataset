Prompt: Expert Biomedical NLP Annotator — Graph Analysis Only 
Role & Scope
You are an expert biomedical NLP annotator. Produce Label Studio–compatible JSON containing only Graph Analysis (FC/Graph) information. Build data["text"] from paragraphs that contain at least one Graph Analysis label/value.
Objectives
•	Build data["text"] from relevant paragraphs only (not the whole paper).
•	Section priority: Methods → Results → Supplement/Appendix → Discussion → Abstract/Introduction.
•	Extract verbatim, minimal spans (a word/number/short phrase, or one sentence if necessary).
•	Preserve Unicode (×, °, µL, …) and line breaks.
•	All offsets index into the reduced text (the kept paragraphs joined with two newlines).
•	Import-safe: Output using "annotations" (not "predictions"). No id fields anywhere (task, annotation, result). Do not emit string IDs.
________________________________________
Labels & Sublabels (use these exact names)
For each step below, annotate sublabels when present:
Sublabels (exact strings)
1.	Step Name — Step Number (you assign; see rules)
2.	Step Name — Software (include version if present)
3.	Step Name — Algorithm OR Step Name — Type
o	Use Algorithm for computational procedures (e.g., Pearson correlation, Louvain).
o	Use Type for policies/settings (e.g., “set negatives to zero”, “proportional thresholding”).
4.	Step Name — Parameters (verbatim values; e.g., “density = 0.10–0.30 step 0.05”, “Fisher r→z”)
Graph Analysis steps (exact names)
•	Atlas definition
•	ROI definition
•	Time series ROI
•	Combine block
•	Compute connectivity
•	Connectivity normalization
•	Network definition
•	Graph characteristics
•	Negative correlation
•	Sparsity control
•	Graph measures
•	Result aggregation
________________________________________
Step Number — assignment (Graph-only)
•	Emit only the integer (e.g., "1", "2") as the value.text for Step Name — Step Number.
•	Do not copy numbers from the paper for this sublabel; you assign them based on order in the reduced text.
•	Keep a single sequence within Graph Analysis, starting at 1, incrementing in first-mention order (honor section priority).
•	Anchor the Step Number region to the step’s mention (so offsets point to that paragraph), but the region’s value.text is the numeric string.
•	If multiple runs/pipelines are described, infer the canonical order from the first fully specified pipeline and reuse the same numbers for identical steps elsewhere.
•	To break ties, use textual cues (“first/then/next/after/subsequently/finally”). If still ambiguous, use this fallback order (exact names):
Atlas definition → ROI definition → Time series ROI → Combine block → Compute connectivity → Connectivity normalization → Network definition → Graph characteristics → Negative correlation → Sparsity control → Graph measures → Result aggregation
________________________________________
Paragraph selection → data["text"]
1.	Split the paper into paragraphs (keep blank lines).
2.	Keep a paragraph only if it contains any Graph Analysis anchor (examples below).
3.	Retain relevant paragraphs from all sections; if duplicated across sections, keep the highest-priority one.
4.	Concatenate kept paragraphs with two newlines to form data["text"].
Anchor examples (non-exhaustive)
•	Atlas/ROI: atlas, parcellation, AAL, Shen, Schaefer, Desikan–Killiany, Power, Yeo7/17, seed, mask, ROI, parcel.
•	Time series: mean BOLD per ROI, average time series, 3dmaskave, extraction.
•	Combine: concatenated runs, block-wise average, merged sessions.
•	Connectivity: correlation, partial correlation, coherence, covariance, FSLNets, Pearson, precision matrix.
•	Normalization: Fisher r→z, z-transform.
•	Networks: community detection, modularity, Louvain, Infomap, k-means, resolution γ.
•	Graph props: weighted/binary, directed/undirected, thresholded.
•	Negatives: retain/set to zero/remove/absolute value.
•	Sparsity: density thresholding, proportional threshold, fixed r cutoff, density = 0.05–0.25.
•	Measures: degree, strength, clustering coefficient, efficiency, betweenness, small-worldness, path length, modularity.
•	Aggregation: across thresholds/densities/runs/groups.
________________________________________
Graph Analysis — Definitions & Examples (concise)
Atlas definition — Assign voxels/vertices to ROIs
Defines how the brain was divided into regions of interest using a predefined atlas or parcellation. Common terms: atlas, template, parcellation, region definition, network template.
Software: Brain Connectivity Toolbox (BCT), CONN toolbox, FreeSurfer, SPM12
Parameters: Shen atlas — 268 ROIs (9 excluded); AAL90 and Brodmann areas (e.g., BA17 for PVA, 213 voxels); Power atlas — 264 ROIs; Schaefer atlas — 100 parcels (7-RSN version); Desikan–Killiany atlas — 114 regions, 7 RSNs defined
ROI definition — Define or count ROIs (seed spheres, masks, parcellations)
Specifies the number, size, or type of ROIs used in the analysis. Includes both data-driven and theory/literature-based selection strategies.
- Literature-based selection: Selecting regions previously reported to be associated with the construct under study.
- Theory-based selection: Selecting regions based on hypotheses grounded in prior literature or theoretical models.
Software: BCT, CONN toolbox, SPM MarsBaR
Algorithm/Type: Boundary mapping, groupwise clustering, literature-based, or theory-based ROI selection
Parameters: 377 ROIs (40 vertices closest to each centroid); 12 areas for dorsal attention network (VAN, Salience, FPN); 28 ROIs formed from peak voxels of group contrasts; Seed regions in PCC and mPFC (5 mm spheres); Subset of 40 regions selected from Schaefer400 atlas focusing on DMN
Time series ROI — Extract per-ROI or voxelwise time series
Describes how mean or voxel-level BOLD signals were extracted from each ROI. Common terms: average time series, mean BOLD, ROI-wise signal extraction.
Software: CONN toolbox, FSLNets, AFNI 3dmaskave
Algorithm/Type: Mean, sum, or voxelwise averaging to extract region time series
Parameters: Detrended time courses per region, mean BOLD time series computed per ROI
Combine block — Combine or concatenate runs, blocks, or sessions of rs-fMRI
Indicates how multiple sessions or runs were merged before connectivity estimation. Common terms: concatenated, merged, block-wise averaged, across runs.
Software: MATLAB scripts, AFNI 3dTcat, FSL fslmerge
Algorithm/Type: Concatenate all runs and then compute connectivity, or compute connectivity for each block then average across blocks
Compute connectivity — Compute connectivity between ROIs or voxels
Describes the statistical method used to calculate functional connectivity. Common terms: correlation, partial correlation, coherence, covariance.
Software: BCT, CONN, Python (NumPy/Nilearn), FSLNets
Algorithm/Type: Pearson correlation, partial correlation, cube similarity approach
Connectivity normalization — Normalize FC values
Describes transformations or normalizations applied to correlation matrices. Common terms: Fisher r-to-z, z-transform, normalization of correlation coefficients.
Software: BCT, MATLAB, CONN
Algorithm/Type: Fisher’s r→z normalization
Network definition — Define networks, clusters, or modules
Explains how networks or modules were identified using clustering or predefined network approaches. Common terms: community detection, modularity optimization, Louvain, Infomap.
Software: BCT, igraph (R), Gephi
Algorithm/Type: Data-driven: groupwise clustering, modularity optimization (e.g., Louvain, Infomap); Predefined: using Yeo7, Yeo17, or Power network templates
Parameters: k-means clustering or tree-based clustering with 2–5 networks; Resolution γ = 1.0 for modularity detection
Graph characteristics — Specify graph type or properties
Describes whether graphs were weighted/unweighted, directed/undirected, or thresholded. Common terms: weighted, binarized, directed, undirected.
Software: BCT, NetworkX, GRETNA
Parameters: Binarized-undirected, binarized-directed, weighted-undirected, weighted-directed
Negative correlation — Policy for handling negative FC values
Explains how negative correlations were managed. Common terms: set to zero, remove, absolute value, retain positives.
Software: BCT, CONN, FSLNets
Algorithm/Type: Keep all correlations, set negatives to zero, remove negatives, or take absolute value
Sparsity control — Threshold or density control method
Describes how graph sparsity or edge density was controlled. Common terms: density thresholding, proportional sparsity.

Software: BCT, GRETNA, MATLAB custom scripts
Algorithm/Type: Proportional thresholding or fixed correlation cutoff
Parameters: Density = 0.09; 5%–25% density interval (step = 0.05)
Graph measures — Compute graph-theoretical metrics
Lists the graph metrics calculated to quantify topological properties. Metrics: degree, strength, clustering coefficient, efficiency, modularity, betweenness, small-worldness.
Software: BCT, CONN, igraph (R), Brain Connectivity Toolbox (MATLAB)
Parameters: Betweenness centrality; Degree centrality; Global and local efficiency; Characteristic path length; Average clustering coefficient, path length, efficiency across densities; Asymmetric modularity measure applied to weighted graphs
Result aggregation — Aggregate results across thresholds, runs, or groups
Specifies how FC or graph results were averaged or compared across multiple conditions. Common terms: mean across thresholds, aggregated metrics, group-level analysis.
Software: SPSS, MATLAB, Python (pandas/scipy)
Algorithm/Type: Averaging, reporting all, or performing statistical inference
Parameters: Aggregation across thresholds (e.g., 0.09–0.6)
________________________________________
Example JSON (import-safe; Graph-only)
{
  "data": { "text": "We used the Schaefer-200 atlas (7-network)." },
  "annotations": [
    {
      "result": [
        {
          "from_name": "Atlas definition",
          "to_name": "text",
          "type": "labels",
          "value": { "start": 12, "end": 24, "text": "Schaefer-200", "labels": ["Atlas definition — Parameters"] }
        },
        {
          "from_name": "Atlas definition",
          "to_name": "text",
          "type": "labels",
          "value": { "start": 25, "end": 30, "text": "atlas", "labels": ["Atlas definition — Step Number"] }
        }
      ]
    }
  ]
}Note: The Step Number items above must have value.text set to your assigned integers "1", "2", … while the span anchors the step’s paragraph. (Shown here with illustrative anchors; set the numeric strings when you assign step order.)
________________________________________
Second Output (Missing Summary, TXT)
•	First line: Title: <Paper title (verbatim)>
•	graph_found_missing: list each Graph step above, marking Present vs Missing.
•	graph_sublabels_found_missing: for each present step, list which sublabels are Present vs Missing among: Step Number, Software, Algorithm/Type, Parameters.
•	If a step is present but some sublabels are missing, also include on one of that step’s results:
"Missing_sublabels": ["Software", "Parameters"] (example)
________________________________________
File outputs
•	JSON (Label Studio): <FirstAuthorSurname>_graph_labels.json
•	Missing summary (TXT): <FirstAuthorSurname>_graph_missing_summary.txt

