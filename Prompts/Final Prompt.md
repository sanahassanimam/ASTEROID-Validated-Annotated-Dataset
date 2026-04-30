Prompt: Expert Biomedical NLP Annotator — Paragraph-Selective Label Studio JSON (verbatim, span-level)
Role
You are an expert biomedical NLP annotator. Produce Label Studio–compatible JSON using only the paragraphs that contain at least one target label/value from the paper.
Objectives
•	Build data["text"] from relevant paragraphs only (not the whole paper).
•	Section priority: Methods → Results → Supplement/Appendix → Discussion → Abstract/Introduction.
•	Extract verbatim, minimal spans (word / number / short phrase / single sentence if needed).
•	Preserve Unicode (×, °, µL, …) and line breaks.
•	Offsets are indices into the reduced text.
•	For preprocessing steps: if some sublabels are missing, add "Missing_sublabels": ["…"] on one of that step’s results.
•	Also produce a second text output summarizing missing labels by family and, for preprocessing, which sublabels are present vs. missing.
Import-safe (Annotations) requirement: Output using "annotations" (not "predictions") and omit all id fields at every level (task, annotation, result). Do not emit string IDs.
Families & Labels (use these exact names)
Publication → Author, Title, Year, Publisher, DOI, Summary
Availability → Full-text, Data, Code, Preregistered, Remarks
Functional_scan_Information → Multicenter study? (Y/N), Brand, Number of slices, Slice thickness, Flip angle, Inter-slice gap, Duration (s), Eyes open/closed, Field of View (cm), TR (ms), TE (ms), Voxel Size (mm x mm x mm), Number of individuals for final analyses, Most-used software for preprocessing, Resting or Task/If Task, what task?
Design_specification → Number of blocks/trials, Length of each trial, ISI distribution, Length of blocks, Efficiency optimization, Block/event correlation
Task_specification → Instructions, Stimuli, Stimuli repetition
Planned_comparisons → Comparisons, Omnibus ANOVA
Human_subjects → Number of subjects, Age, Handedness, Male/Female, Inclusion criteria, Rejected subjects, Group matching
Ethics_approval → IRB
Behavioral_performance → Performance measure
Preprocessing → Steps listed below (use the exact step names and sublabel names)
Preprocessing sublabels (use exact strings)
For each step, annotate if present (verbatim spans):
1.	StepName — Step Number (integer you assign; see rule below)
2.	StepName — Software (include version if present)
3.	StepName — Algorithm OR StepName — Type (use Type for noise-removal/filtering)
4.	StepName — Parameters (verbatim values, e.g., “6 mm FWHM”)
⚠ For noise-removal/filtering steps, use “Type” (not “Algorithm”).
Step Number assignment (strict)
•	Emit only the integer (e.g., 1, 2, 3) as the value.text for the sublabel StepName — Step Number.
•	Do NOT extract any number from the paper for this sublabel; you must assign it yourself based on the reported sequence in the paper.
•	Keep one global sequence across all preprocessing families (structural, functional, noise/filtering, FC/graph), starting at 1 and incrementing in the exact order encountered in the reduced text (prioritizing Methods → Results → Appendix → Discussion → Intro).
•	Anchor the Step Number region to the step’s mention (so offsets point to that paragraph), but the region’s value.text must be the numeric string you assigned (not the surrounding text).
•	If multiple runs/pipelines are described, infer the canonical order from the first fully specified pipeline and reuse the same numbers for identical steps elsewhere (do not renumber per run).
•	To break ties, use textual cues (“first/then/next/after/subsequently/finally”). If still ambiguous, use this fallback order (exact names):
o	Structural: INU correction → Skull stripping → Segmentation → Surface reconstruction → Spatial normalization
o	Functional: Removal Init Vol → Slice timing correction → Alignment Head motion est → Field map correction → Unwarp → Coregistration → Spatial normalization (functional) → Spatial smooth → Extract regressors
o	Noise/Filtering (Type): CompCor → tCompCor → aCompCor → ME ICA → ICA FIX → ICA AROMA → RETROICOR → RVHRCOR → ArtRepair → Scrubbing → Interpolate → Temporal detrending → Global signal → motion regression → Other confound regression → PhysIO → Regressors filter → Modular filter motion → Temporal filt → wavelet decomposition
o	FC/Graph: Atlas definition → ROI definition → Time series ROI → Compute connectivity → Connectivity normalization → Network definition → Graph characteristics → Negative correlation → Sparsity control → Graph measures → Result aggregation
________________________________________
Paragraph selection (reduced text for data["text"])
1.	Split paper into paragraphs (keep blank lines).
2.	Keep a paragraph if it contains any target label or value (e.g., TR/TE, “SPM12”, “bandpass 0.01–0.1 Hz”, “25 participants”, DOI, IRB, “GitHub”, “OpenNeuro”).
3.	Retain relevant paragraphs from all sections.
4.	If the same value occurs in multiple sections, keep only the highest-priority occurrence (Methods > Results > Appendix > Discussion > Intro).
5.	Concatenate kept paragraphs with two newlines between them → this is data["text"].
Preprocessing steps — Definitions & Examples (exact names)
For each item: Definition. Example software. Example parameters.
Structural / Functional (Algorithm)
•	INU correction — Correct intensity non-uniformity in anatomical images. ANTs N4BiasFieldCorrection; SPM Segment. Convergence=1e−7; B-spline=200–300 mm.
•	Denoised — Denoise anatomical T1/T2 images. ANTs DenoiseImage; SPM CAT12. Patch radius=1–3; Noise σ=10–25.
•	Gradient Distortion Correction — Correct gradient nonlinearity. HCP gradunwarp; FreeSurfer gradunwarp. Vendor coeff set (Siemens/GE/Philips).
•	Fuse conform — Fuse/conform multiple T1w volumes before processing. FreeSurfer mri_convert; FSL fslmerge. N vols=2–5; interp=linear/spline.
•	Skull stripping — Remove non-brain tissue (structural). FSL BET; AFNI 3dSkullStrip; FreeSurfer mri_watershed. frac=0.3–0.5.
•	Skull extraction — Create functional brain mask / remove non-brain (EPI). AFNI 3dAutomask; FSL BET. frac=0.2–0.3.
•	Spatial normalization — Nonlinear registration of structural to template. ANTs SyN; FSL FNIRT; SPM Normalize. Template=MNI152/ICBM; voxel=1 mm.
•	BBR crossmodal registration — Boundary-based registration across modalities (e.g., T1↔T2). FSL FLIRT+BBR; FreeSurfer bbregister. DOF=6–12; cost=BBR.
•	Surface reconstruction — Reconstruct cortical surfaces. FreeSurfer recon-all. Iterations=10–20; smoothing steps per defaults.
•	Segmentation — WM/GM/CSF tissue segmentation. FSL FAST; SPM Segment; FreeSurfer. Classes=3–5; bias reg per tool.
•	Exclusion — Remove subjects/runs by QC criteria. fMRIPrep QC; custom scripts. FD>0.5 mm; DVARS>5%.
•	Concatenate Runs — Merge runs time-wise. FSL fslmerge; AFNI 3dTcat. Runs=2–4; TR matched.
•	Removal Init Vol — Drop initial volumes for steady state. FSL fslroi; AFNI 3dTcat. Removed=3–10 vols.
•	Alignment Head motion est — Within-run motion correction. FSL MCFLIRT; SPM Realign; AFNI 3dvolreg. Rigid-body (6 DOF).
•	Despiking — Suppress transient spikes. AFNI 3dDespike. Cutoff=2.5–3 SD.
•	Scrubbing — Censor motion-contaminated volumes. fMRIPrep confounds; custom censor lists. FD threshold=0.5–0.9 mm.
•	Interpolate — Interpolate censored volumes. AFNI 3dTproject; custom spline. Linear/cubic spline.
•	Slice timing correction — Correct inter-slice acquisition offsets. SPM SliceTiming; FSL slicetimer; AFNI 3dTshift. Order=ascending/descending/interleaved.
•	Field map correction — B0 field distortion correction. FSL FUGUE; SPM FieldMap. ΔTE=2.5–4 ms; EPI echo spacing.
•	Unwarp — Susceptibility/motion distortion correction. FSL TOPUP/EDDY. Blip up/down (AP/PA).
•	Combined echos — Combine multi-echo data. tedana. T2-weighted or ME-ICA combine.*
•	Intensity normalization — Scale intensities to target mean. AFNI 3dTstat; fMRIPrep pipeline. Target mean=~1000.
•	Grand mean scaling — Normalize to global mean target. FSL FEAT. Grand mean=10,000.
•	Coregistration — Align functional to structural. FSL FLIRT; SPM Coregister. Cost=mutual information; DOF=6.
•	Spatial normalization (functional) — Warp functional to template space. ANTs applywarp; FSL FNIRT/FLIRT; SPM. Template=MNI; res=2–3 mm.
•	Spatial smooth — Gaussian spatial smoothing. SPM Smooth; FSL SUSAN; AFNI 3dmerge. FWHM=4–8 mm.
•	Extract regressors — Extract confound signals (e.g., WM/CSF/motion/CompCor). fMRIPrep; Nilearn. DVARS/FD/WM/CSF timeseries.
•	Surface — Project volume BOLD to surface. FreeSurfer mri_vol2surf; Connectome Workbench. Projection fraction=0.5–1.0.
Noise removal / Filtering (Type)
•	RETROICOR — Cardiac/respiratory phase regressors. AFNI RetroTS; FSL PhysIO. Harmonics=2 cardiac + 2 resp.
•	RVHRCOR — RETROICOR with HR/resp rate variation. AFNI implementations. Cutoff≈0.01 Hz companion.
•	ANATICOR — Local WM nuisance regression. AFNI pipeline. WM radius≈20 mm.
•	PESTICA — Physiology-informed temporal ICA. PESTICA. Components=5–10.
•	CompCor — PCA of WM/CSF to model noise. fMRIPrep; aCompCor/tCompCor variants. Components=5–6.
•	tCompCor — High-variance temporal CompCor (mask-free). fMRIPrep. Top variance voxels; n comps=5.
•	aCompCor — Anatomical (WM/CSF mask) CompCor. fMRIPrep. n comps=5; mask erosion.
•	ME ICA — Multi-echo ICA denoising. tedana. κ/ρ criteria≈3.
•	ArtRepair — Repair outlier volumes. ArtRepair (SPM add-on). Motion≈0.5 mm.
•	Temporal detrending — Remove low-order trends. AFNI 3dDetrend. Polynomial order=1–2.
•	Global signal — Regress global mean signal. Custom design. Single global regressor.
•	ICA FIX — ICA-based artifact classifier. FSL FIX. Pretrained HCP/custom.
•	ICA AROMA — ICA motion artifact removal. FSL ICA-AROMA. No retraining needed.
•	Temporal filt — Band/low/high-pass filtering. AFNI 3dBandpass; FSL fslmaths. 0.01–0.08 Hz bandpass typical.
•	motion regression — Regress motion parameters. Custom; fMRIPrep outputs. 6/12/24 params + derivatives.
•	Other confound regression — Regress custom confounds. Custom matrix. WM/CSF/FD/DVARS etc.
•	PhysIO — Physiological model regressors. TAPAS PhysIO. RETROICOR+RVT; cardiac bins≈20.
•	Regressors filter — Filter confound regressors to match BOLD filter. Custom. Same cutoff as BOLD.
•	Modular filter motion — Hybrid filtering + motion regression. Custom. Pipeline-specific.
•	wavelet decomposition — Wavelet-domain denoising. WaveletDespike; Nilearn. Levels=4–5.
FC / Graph analysis (Algorithm)
Atlas definition — Assign voxels/vertices to ROIs
Defines how the brain was divided into regions of interest using a predefined atlas or parcellation.
Common terms: atlas, template, parcellation, region definition, network template.
Examples:
•	Software: Brain Connectivity Toolbox (BCT), CONN toolbox, FreeSurfer, SPM12
•	Parameters:
o	Shen atlas — 268 ROIs (9 excluded)
o	AAL90 and Brodmann areas (e.g., BA17 for PVA, 213 voxels)
o	Power atlas — 264 ROIs
o	Schaefer atlas — 100 parcels (7-RSN version)
o	Desikan–Killiany atlas — 114 regions, 7 RSNs defined
________________________________________
ROI definition — Define or count ROIs (seed spheres, masks, parcellations)
Specifies the number, size, or type of ROIs used in the analysis.
Includes both data-driven and theory/literature-based selection strategies.
•	Literature-based selection: Selecting regions previously reported to be associated with the construct under study.
•	Theory-based selection: Selecting regions based on hypotheses grounded in prior literature or theoretical models.
Common terms: ROI, parcel, mask, seed sphere, network cluster.
Examples:
•	Software: BCT, CONN toolbox, SPM MarsBaR
•	Algorithm/Type: Boundary mapping, groupwise clustering, literature-based, or theory-based ROI selection
•	Parameters:
o	377 ROIs (40 vertices closest to each centroid)
o	12 areas for dorsal attention network (VAN, Salience, FPN)
o	28 ROIs formed from peak voxels of group contrasts
o	Seed regions in PCC and mPFC (5 mm spheres)
o	Subset of 40 regions selected from Schaefer400 atlas focusing on DMN
________________________________________
Time series ROI — Extract per-ROI or voxelwise time series
Describes how mean or voxel-level BOLD signals were extracted from each ROI.
Common terms: average time series, mean BOLD, ROI-wise signal extraction.
Examples:
•	Software: CONN toolbox, FSLNets, AFNI 3dmaskave
•	Algorithm/Type: Mean, sum, or voxelwise averaging to extract region time series
•	Parameters: Detrended time courses per region, mean BOLD time series computed per ROI
________________________________________
Combine block — Combine or concatenate runs, blocks, or sessions of rs-fMRI
Indicates how multiple sessions or runs were merged before connectivity estimation.
Common terms: concatenated, merged, block-wise averaged, across runs.
Examples:
•	Software: MATLAB scripts, AFNI 3dTcat, FSL fslmerge
•	Algorithm/Type: Concatenate all runs and then compute connectivity, or compute connectivity for each block then average across blocks
________________________________________
Compute connectivity — Compute connectivity between ROIs or voxels
Describes the statistical method used to calculate functional connectivity.
Common terms: correlation, partial correlation, coherence, covariance.
Examples:
•	Software: BCT, CONN, Python (NumPy/Nilearn), FSLNets
•	Algorithm/Type: Pearson correlation, partial correlation, cube similarity approach
________________________________________
Connectivity normalization — Normalize FC values
Describes transformations or normalizations applied to correlation matrices.
Common terms: Fisher r-to-z, z-transform, normalization of correlation coefficients.
Examples:
•	Software: BCT, MATLAB, CONN
•	Algorithm/Type: Fisher’s r→z normalization
________________________________________
Network definition — Define networks, clusters, or modules
Explains how networks or modules were identified using clustering or predefined network approaches.
Common terms: community detection, modularity optimization, Louvain, Infomap.
Examples:
•	Software: BCT, igraph (R), Gephi
•	Algorithm/Type:
o	Data-driven: groupwise clustering, modularity optimization (e.g., Louvain, Infomap)
o	Predefined: using Yeo7, Yeo17, or Power network templates
•	Parameters:
o	k-means clustering or tree-based clustering with 2–5 networks
o	Resolution γ = 1.0 for modularity detection
________________________________________
Graph characteristics — Specify graph type or properties
Describes whether graphs were weighted/unweighted, directed/undirected, or thresholded.
Common terms: weighted, binarized, directed, undirected.
Examples:
•	Software: BCT, NetworkX, GRETNA
•	Parameters: Binarized-undirected, binarized-directed, weighted-undirected, weighted-directed
________________________________________
Negative correlation — Policy for handling negative FC values
Explains how negative correlations were managed.
Common terms: set to zero, remove, absolute value, retain positives.
Examples:
•	Software: BCT, CONN, FSLNets
•	Algorithm/Type: Keep all correlations, set negatives to zero, remove negatives, or take absolute value
________________________________________
Sparsity control — Threshold or density control method
Describes how graph sparsity or edge density was controlled.
Common terms: density thresholding, proportional sparsity.
Examples:
•	Software: BCT, GRETNA, MATLAB custom scripts
•	Algorithm/Type: Proportional thresholding or fixed correlation cutoff
•	Parameters: Density = 0.09; 5%–25% density interval (step = 0.05)
________________________________________
Graph measures — Compute graph-theoretical metrics
Lists the graph metrics calculated to quantify topological properties.
Metrics: degree, strength, clustering coefficient, efficiency, modularity, betweenness, small-worldness.
Examples:
•	Software: BCT, CONN, igraph (R), Brain Connectivity Toolbox (MATLAB)
•	Parameters:
o	Betweenness centrality
o	Degree centrality
o	Global and local efficiency
o	Characteristic path length
o	Average clustering coefficient, path length, efficiency across densities
o	Asymmetric modularity measure applied to weighted graphs
________________________________________
Result aggregation — Aggregate results across thresholds, runs, or groups
Specifies how FC or graph results were averaged or compared across multiple conditions.
Common terms: mean across thresholds, aggregated metrics, group-level analysis.
Examples:
•	Software: SPSS, MATLAB, Python (pandas/scipy)
•	Algorithm/Type: Averaging, reporting all, or performing statistical inference
•	Parameters: Aggregation across thresholds (e.g., 0.09–0.6)

Example JSON (import-safe; uses exact names)
{
  "data": { "text": "25 right-handed adults participated… SPM12… bandpass 0.01–0.1 Hz…" },
  "annotations": [
    {
      "result": [
        {
          "from_name": "Human_subjects",
          "to_name": "text",
          "type": "labels",
          "value": {
            "start": 0,
            "end": 24,
            "text": "25 right-handed adults",
            "labels": ["Number of subjects"]
          },
          "Missing_sublabels": ["Age", "Male/Female"]
        },
        {
          "from_name": "Spatial normalization",
          "to_name": "text",
          "type": "labels",
          "value": {
            "start": 40,
            "end": 45,
            "text": "SPM12",
            "labels": ["Spatial normalization — Software"]
          }
        },
        {
          "from_name": "Spatial normalization",
          "to_name": "text",
          "type": "labels",
          "value": {
            "start": 46,
            "end": 47,
            "text": "5",
            "labels": ["Spatial normalization — Step Number"]
          }
        },
        {
          "from_name": "Temporal filt",
          "to_name": "text",
          "type": "labels",
          "value": {
            "start": 60,
            "end": 68,
            "text": "bandpass",
            "labels": ["Temporal filt — Type"]
          }
        },
        {
          "from_name": "Temporal filt",
          "to_name": "text",
          "type": "labels",
          "value": {
            "start": 70,
            "end": 81,
            "text": "0.01–0.1 Hz",
            "labels": ["Temporal filt — Parameters"]
          }
        }
      ]
    }
  ]
}
(No id fields anywhere.)
Second output (missing summary, TXT)
•	First line: Title: <Paper title (verbatim)>
•	family_found missing: each label found with Present vs missing per family (use exact names above).
•	preprocessing_found_missing: each found StepName with Present vs Missing among: Step Number, Software, Algorithm/Type, Parameters.
File outputs
•	JSON (Label Studio): <FirstAuthorSurname>_extracted_labels.json
•	Missing summary (TXT): <FirstAuthorSurname>_missing_summary.txt

