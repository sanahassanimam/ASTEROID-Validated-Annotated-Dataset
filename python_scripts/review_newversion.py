#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Create a comparison table between an Excel report and Gao-style *_extracted_labels.json files.

What this script does (finalized):
- Robustly parses Label Studio JSON (including choices + TextArea notes).
- Strips "Family — ..." prefixes so sublabels compare cleanly to Excel headers.
- Bridges Excel "graph theory"-style family fields (e.g., atlas, density threshold, connection measure)
  to JSON *preprocessing steps* by comparing against a composite of Type/Algorithm/Software/Parameters.
- Fixes similarity to a consistent 0–100 scale.
- Output columns:
    • Source: "Excel only", "JSON only", or "Both"
    • Match_quality: "Match", "Not match", "Excel only", or "JSON only"
    • Similarity: 0–100 only when Source == "Both", else blank

Usage example:
  python compare_excel_json.py ^
    --excel "C:\\path\\to\\Workbook.xlsx" ^
    --sheet "Seed2" ^
    --json_root "C:\\path\\to\\jsons" ^
    --show_values

Outputs a CSV next to each JSON: <name>_table.csv
"""

import argparse
import os
import re
import json
import difflib
from typing import Dict, List, Tuple, Optional, Any

import pandas as pd
import numpy as np


# ------------ Config (includes graph-theory aliases) ------------
STEP_EQUIVALENCE = {
    "spatial normalization": ["spatial normalization (functional)", "functional normalization", "normalization (functional)"],
    "slice timing correction": ["slice time correction", "slice-timing correction"],
    "alignment head motion est": ["motion correction", "realignment", "head motion correction", "realign"],
    "coregistration": ["registration", "coreg", "alignment"],
    "temporal filt": ["bandpass filtering", "temporal filtering", "bandpass filter"],

    # graph theory related
    "graph measures": ["network measures", "graph metrics", "graph analysis", "graph analyses", "graph theory"],
    "sparsity control": ["density threshold", "cost threshold", "graph density", "thresholding", "sparsity"],
    "compute connectivity": ["connection measure", "connectivity measure", "edge weight", "correlation matrix", "connectivity computation"],
    "negative correlation": ["negative corr", "absolute correlation handling", "sign handling", "negative correlations"],
    "time series roi": ["time series roi definition", "roi time series", "regional mean time series", "rois", "time-series roi"],
    "graph characteristics": ["weighted binarized", "binarized", "unweighted", "undirected", "graph type", "weighting"],
    "atlas definition": ["atlas", "parcellation", "atlas creation", "desikan", "parcellation scheme"],

    # other analysis families
    "roi definition": ["region definition", "seed definition", "time series roi"],
    "result aggregation": ["aggregation", "summary step", "result summary", "result aggregation"],
}
EMPTY_TOKENS = {"", "—", "-", "nan", "n/a", "na", "none", "not available"}
SUBLABEL_SET = {"type", "algorithm", "software", "parameters"}


# ------------ Utils ------------
def normalize_name(s: Any) -> str:
    if s is None or (isinstance(s, float) and np.isnan(s)):
        return ""
    s = str(s)
    s = s.replace("—", "-")
    s = re.sub(r"[\u200b\u200c\u200d]", "", s).lower().strip()
    s = s.replace("_", " ").replace("×", "x").replace("°", " ").replace("µ", "u")
    s = re.sub(r"[^\w\s-]", " ", s)
    s = re.sub(r"\s+", " ", s)
    return s.strip()


def is_present(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, float) and np.isnan(value):
        return False
    s = normalize_name(value)
    return s not in EMPTY_TOKENS and s != ""


def similarity(a: Any, b: Any) -> int:
    """Return 0–100 consistently; token-set Jaccard first, then char similarity."""
    sa = normalize_name(a)
    sb = normalize_name(b)
    ta = set(re.split(r"\W+", sa)) - {""}
    tb = set(re.split(r"\W+", sb)) - {""}
    if ta and tb:
        inter = len(ta & tb)
        union = len(ta | tb)
        return int(round(100 * inter / union))
    return int(round(100 * difflib.SequenceMatcher(None, sa, sb).ratio()))


def fuzzy_match(target: str, candidates: List[str], threshold: float = 0.75, allow_fuzzy: bool = True) -> Tuple[Optional[str], str]:
    if not target or not candidates:
        return None, "NoMatch"
    target_n = normalize_name(target)

    # Exact with alias set for known steps
    for k, aliases in STEP_EQUIVALENCE.items():
        eqs = {normalize_name(k), *[normalize_name(a) for a in aliases]}
        for c in candidates:
            if target_n in eqs and normalize_name(c) in eqs:
                return c, "Exact"

    # Direct exact
    for c in candidates:
        if normalize_name(c) == target_n:
            return c, "Exact"

    if not allow_fuzzy:
        return None, "NoMatch"

    best, best_score = None, 0.0
    for c in candidates:
        score = difflib.SequenceMatcher(None, target_n, normalize_name(c)).ratio()
        if score > best_score:
            best, best_score = c, score
    return (best, "Fuzzy") if (best and best_score >= threshold) else (None, "NoMatch")


# --- Label helpers ---
def strip_family_prefix(family_display: str, label_display: str) -> str:
    """Strip 'Family — X' to 'X' when possible."""
    fam_n = normalize_name(family_display)
    lab_n = normalize_name(label_display)
    if not fam_n or not lab_n:
        return lab_n
    pattern = r"^\s*" + re.escape(fam_n) + r"\s*[-–—:]?\s*(.+)$"
    m = re.match(pattern, lab_n)
    if m and m.group(1).strip():
        return m.group(1).strip()
    if lab_n.startswith(fam_n + " "):
        remainder = lab_n[len(fam_n):].strip()
        remainder = re.sub(r"^[-–—:]\s*", "", remainder)
        return remainder if remainder else lab_n
    return lab_n


# ------------ Excel I/O ------------
def load_excel_structured(excel_path: str, sheet_name: str = "Seed2"):
    raw = pd.read_excel(excel_path, sheet_name=sheet_name, header=None)
    fam_row = raw.iloc[0].astype(str).replace("nan", np.nan)
    label_row = raw.iloc[1].astype(str)
    fam_row_ffill = fam_row.ffill()

    cols, family_to_labels = [], {}
    for fam, lab in zip(fam_row_ffill, label_row):
        fam_clean = str(fam) if pd.notna(fam) else ""
        lab_clean = str(lab)
        colname = f"{fam_clean}|{lab_clean}" if fam_clean else lab_clean
        cols.append(colname)
        family_to_labels.setdefault(fam_clean, []).append(lab_clean)

    df = raw.iloc[2:].copy()
    df.columns = cols

    norm_to_original = {}
    for c in cols:
        fam, lab = (c.split("|", 1) if "|" in c else ("", c))
        norm_to_original[(normalize_name(fam), normalize_name(lab))] = c

    return df.reset_index(drop=True), family_to_labels, norm_to_original


# ------------ JSON parse (robust) ------------
def parse_gao_json(json_path: str):
    with open(json_path, "r", encoding="utf-8") as f:
        J = json.load(f)

    task = J[0] if isinstance(J, list) and J else (J if isinstance(J, dict) else {})
    annotations = task.get("annotations") or []

    results_raw = None
    if annotations and isinstance(annotations, list):
        first_ann = annotations[0] or {}
        results_raw = first_ann.get("result")
    if results_raw is None:
        results_raw = task.get("result")

    if results_raw is None:
        results = []
    elif isinstance(results_raw, list):
        results = results_raw
    else:
        results = [results_raw]

    meta = {"title": "", "author": "", "doi": "", "year": "", "publisher": ""}
    families_json, preprocessing_json = {}, {}
    family_values, preprocessing_values = {}, {}

    def add_family_label(fam: str, lab: str, present=True, value: Any = ""):
        fam_key = (fam or "").strip()
        sub_key = (lab or "").strip()
        families_json.setdefault(fam_key, {"Found": [], "Missing": []})
        bucket = "Found" if present else "Missing"
        if sub_key and sub_key not in families_json[fam_key][bucket]:
            families_json[fam_key][bucket].append(sub_key)
        if present and sub_key:
            fn, ln = normalize_name(fam_key), normalize_name(sub_key)
            family_values.setdefault(fn, {})
            if value and ln not in family_values[fn]:
                family_values[fn][ln] = value

    def add_pp_label(step: str, sub: str, present=True, value: Any = ""):
        step_key = (step or "").strip()
        sub_key = (sub or "").strip()
        preprocessing_json.setdefault(step_key, {"Present": [], "Missing": []})
        bucket = "Present" if present else "Missing"
        if sub_key and sub_key not in preprocessing_json[step_key][bucket]:
            preprocessing_json[step_key][bucket].append(sub_key)
        if present and sub_key:
            sn, subn = normalize_name(step_key), normalize_name(sub_key)
            preprocessing_values.setdefault(sn, {})
            if value and subn not in preprocessing_values[sn]:
                preprocessing_values[sn][subn] = value

    def is_preproc_family(fam_n: str) -> bool:
        for k, aliases in STEP_EQUIVALENCE.items():
            all_eq = {normalize_name(k), *[normalize_name(a) for a in aliases]}
            if fam_n in all_eq:
                return True
        return any(tok in fam_n for tok in [
            "alignment", "coreg", "normalization", "temporal",
            "global signal", "atlas", "roi", "connectivity",
            "regression", "filter", "compcor", "retroicor",
            "ica", "scrubbing", "despiking", "tcompcor", "acompcor",
            "smoothing", "smooth", "detrending",
            "graph", "sparsity", "connectivity", "correlation"
        ])

    for r in results:
        if not isinstance(r, dict):
            continue

        fam = (r.get("from_name") or "").strip()
        val = r.get("value") or {}
        labels = val.get("labels") or []
        text_value = val.get("text") or ""

        # Publication meta
        if fam.lower() == "publication" and labels:
            raw_lab = (labels[0] or "").strip()
            lab_n = normalize_name(raw_lab)
            if lab_n == "title":
                meta["title"] = (text_value or "").strip()
            elif lab_n == "author":
                meta["author"] = (text_value or "").strip()
            elif lab_n == "doi":
                meta["doi"] = (text_value or "").strip()
            elif lab_n == "year":
                meta["year"] = (text_value or "").strip()
            elif lab_n == "publisher":
                meta["publisher"] = (text_value or "").strip()

        # Labeled selections
        if fam and labels:
            raw_lab = (labels[0] or "").strip()
            if "step number" in normalize_name(raw_lab):
                pass
            else:
                fam_disp = fam
                fam_n = normalize_name(fam_disp)
                sub_disp = strip_family_prefix(fam_disp, raw_lab)
                captured_value = text_value if is_present(text_value) else raw_lab
                if is_preproc_family(fam_n):
                    add_pp_label(fam_disp, sub_disp, True, captured_value)
                else:
                    add_family_label(fam_disp, sub_disp, True, captured_value)

            # Also capture multi-choice selections as values
            if isinstance(val.get("choices"), list) and val["choices"]:
                fam_disp = fam
                fam_n = normalize_name(fam_disp)
                sub_disp = strip_family_prefix(fam_disp, labels[0])
                captured_value = "; ".join(val["choices"])
                if is_preproc_family(fam_n):
                    add_pp_label(fam_disp, sub_disp, True, captured_value)
                else:
                    add_family_label(fam_disp, sub_disp, True, captured_value)

            # Missing_sublabels bookkeeping
            missing_list = r.get("Missing_sublabels") or []
            for miss in missing_list:
                miss_sub = strip_family_prefix(fam, miss)
                if "step number" in normalize_name(miss_sub):
                    continue
                if is_preproc_family(normalize_name(fam)):
                    add_pp_label(fam, miss_sub, False, "")
                else:
                    add_family_label(fam, miss_sub, False, "")

        # Capture TextArea-only regions (Label Studio free-text)
        if fam and not labels and isinstance(val.get("text"), list) and val["text"]:
            desc_text = (val["text"][0] or "").strip()
            parts = [p for p in re.split(r"__+", fam) if p]
            if len(parts) >= 2:
                fam_guess = parts[0].replace("_", " ").strip()
                sub_guess = re.sub(r"(_?desc)?$", "", parts[-1], flags=re.I).replace("_", " ").strip()
                fam_guess_n = normalize_name(fam_guess)
                if is_preproc_family(fam_guess_n):
                    add_pp_label(fam_guess, sub_guess, True, desc_text)
                else:
                    add_family_label(fam_guess, sub_guess, True, desc_text)

    return meta, families_json, preprocessing_json, family_values, preprocessing_values


# ------------ Row matching ------------
def find_row_in_excel(df: pd.DataFrame, meta: Dict[str, str], author_hint_from_filename: str = "", allow_fuzzy=True):
    def pick(h):
        m, _ = fuzzy_match(h, list(df.columns), allow_fuzzy=allow_fuzzy)
        return m or h

    title_col = pick("Publication|Title")
    author_col = pick("Publication|Author")
    doi_col = pick("Publication|DOI")

    nn = normalize_name
    title = meta.get("title", "") or ""
    author = (meta.get("author", "") or author_hint_from_filename or "").strip()
    doi = meta.get("doi", "") or ""

    def best_idx_by_col(colname: str, target: str, fuzzy_thresh: float) -> Optional[int]:
        if not target or colname not in df.columns:
            return None
        series = df[colname].astype(str).fillna("")
        ratios = series.apply(lambda t: difflib.SequenceMatcher(None, nn(t), nn(target)).ratio())
        if len(ratios) and ratios.max() >= fuzzy_thresh:
            return int(ratios.idxmax())
        mask = series.apply(lambda t: nn(target) in nn(t))
        if mask.any():
            return int(mask[mask].index[0])
        return None

    idx = best_idx_by_col(author_col, author, 0.78) if author else None
    if idx is not None:
        return idx, {"basis": "Author",
                     "title": str(df.loc[idx, title_col]) if title_col in df.columns else "",
                     "author": str(df.loc[idx, author_col]) if author_col in df.columns else ""}

    idx = best_idx_by_col(doi_col, doi, 0.90) if doi else None
    if idx is not None:
        return idx, {"basis": "DOI",
                     "title": str(df.loc[idx, title_col]) if title_col in df.columns else "",
                     "author": str(df.loc[idx, author_col]) if author_col in df.columns else ""}

    if title_col in df.columns and author_col in df.columns and (title or author):
        combo_target = f"{nn(title)} {nn(author)}".strip()
        combo_series = (df[title_col].astype(str).fillna("") + " " +
                        df[author_col].astype(str).fillna("")).apply(nn)
        ratios = combo_series.apply(lambda t: difflib.SequenceMatcher(None, t, combo_target).ratio())
        if len(ratios) and ratios.max() >= 0.70:
            idx = int(ratios.idxmax())
            return idx, {"basis": "Title+Author",
                         "title": str(df.loc[idx, title_col]),
                         "author": str(df.loc[idx, author_col])}
        mask = combo_series.apply(lambda t: combo_target in t if combo_target else False)
        if mask.any():
            idx = int(mask[mask].index[0])
            return idx, {"basis": "Title+Author (contains)",
                         "title": str(df.loc[idx, title_col]),
                         "author": str(df.loc[idx, author_col])}

    idx = best_idx_by_col(title_col, title, 0.72) if title else None
    if idx is not None:
        return idx, {"basis": "Title",
                     "title": str(df.loc[idx, title_col]),
                     "author": str(df.loc[idx, author_col]) if author_col in df.columns else ""}

    raise ValueError("No reliable Excel row match (Author/DOI/Title+Author/Title).")


# ------------ Excel content extract ------------
def excel_presence_map_for_row(df: pd.DataFrame, row_idx: int):
    row = df.iloc[row_idx]
    out: Dict[str, Dict[str, Tuple[bool, Any]]] = {}
    for col in df.columns:
        fam, lab = (col.split("|", 1) if "|" in col else ("", col))
        out.setdefault(normalize_name(fam), {})[normalize_name(lab)] = (is_present(row[col]), row[col])
    return out


def _pp_pick_col(cols: List[str], n: int, want: str) -> Optional[str]:
    want_n = normalize_name(want)
    pat_num = re.compile(rf"\b{n}\b")
    synonyms_map = {
        "step": ["step", "step number", "n", "idx"],
        "type": ["type", "kind", "category"],
        "function": ["function", "func", "algo", "algorithm", "operation"],
        "software": ["software", "tool", "package"],
        "parameter": ["parameter", "parameters", "param", "paramete"],
    }
    if want_n not in synonyms_map:
        return None
    synonyms = synonyms_map[want_n]
    for c in cols:
        fam, lab = (c.split("|", 1) if "|" in c else ("", c))
        if normalize_name(fam) != "preprocessing":
            continue
        labn = normalize_name(lab)
        if any(x in labn for x in synonyms) and pat_num.search(labn):
            return c
    return None


def preprocess_steps_from_excel(df: pd.DataFrame, row_idx: int):
    row = df.iloc[row_idx]
    cols = list(df.columns)
    steps: Dict[str, Dict[str, Any]] = {}
    for n in range(1, 101):
        step_col = _pp_pick_col(cols, n, "step")
        if not step_col:
            continue
        step_name = row.get(step_col, np.nan)
        if not is_present(step_name):
            continue

        def get_part(which: str):
            c = _pp_pick_col(cols, n, which)
            return row.get(c, np.nan) if (c and c in row.index) else np.nan

        steps[str(step_name)] = {
            "Type": get_part("type"),
            "Algorithm": get_part("function"),
            "Software": get_part("software"),
            "Parameters": get_part("parameter"),
        }
    return steps


# ------------ Swap-tolerant presence ------------
def info_equivalent(excel_entry: Dict[str, Any], sublabel: str):
    sub_n = normalize_name(sublabel)
    exact_key = None
    for k in excel_entry.keys():
        if normalize_name(k) == sub_n:
            exact_key = k
            break
    if exact_key and is_present(excel_entry.get(exact_key)):
        return True, False, exact_key
    if sub_n in (SUBLABEL_SET - {"software"}):
        for k in ["Type", "Algorithm", "Parameters"]:
            if k in excel_entry and is_present(excel_entry[k]):
                return False, True, k
    return False, False, ""


# ------------ Build comparison table ------------
def build_comparison_table_for_json(
    df: pd.DataFrame,
    json_path: str,
    sheet: str,
    allow_fuzzy: bool,
    show_values: bool,
    norm_to_original: Dict[Tuple[str, str], str],
):
    meta, families_json, preprocessing_json, family_values, preprocessing_values = parse_gao_json(json_path)

    # composites (Type/Algorithm/Software/Parameters) per preprocessing step
    def make_step_composites(preproc_vals: Dict[str, Dict[str, Any]]) -> Dict[str, str]:
        comps = {}
        for step_norm, vals in preproc_vals.items():
            parts = []
            for key in ("type", "algorithm", "software", "parameters"):
                v = vals.get(key, "")
                if is_present(v):
                    parts.append(str(v))
            comps[step_norm] = "; ".join(parts)
        return comps

    step_composites = make_step_composites(preprocessing_values)
    preproc_disp_keys = list(preprocessing_json.keys())
    preproc_keys_norm = [normalize_name(k) for k in preproc_disp_keys]

    fname = os.path.basename(json_path)
    m = re.match(r"^(.+?)_extracted_labels_lastprompt\.json$", fname, flags=re.I)
    author_hint = m.group(1) if m else ""

    row_idx, matched = find_row_in_excel(df, meta, author_hint_from_filename=author_hint, allow_fuzzy=allow_fuzzy)
    fam_label_map = excel_presence_map_for_row(df, row_idx)

    title = matched.get("title", "")
    author = matched.get("author", "") or meta.get("author", "") or author_hint

    rows = []

    def add_row(section, group, field,
                excel_has, excel_value, json_status, json_value, _ignored_verdict,
                match_quality="Exact", excel_col=""):

        excel_present = is_present(excel_value)
        json_present = is_present(json_value)

        # Source + Match_quality unified
        if excel_present and json_present:
            source = "Both"
            sim = similarity(excel_value, json_value)
            match_quality = "Match" if (
                normalize_name(excel_value) == normalize_name(json_value)
                or (isinstance(sim, int) and sim >= 50)
            ) else "Not match"
        elif excel_present and not json_present:
            source = "Excel only"
            sim = ""
            match_quality = "Excel only"
        elif (not excel_present) and json_present:
            source = "JSON only"
            sim = ""
            match_quality = "JSON only"
        else:
            source = ""
            sim = ""
            match_quality = ""

        rows.append({
            "Section": section,
            "Group": group,
            "Field": field,
            "Excel_has": "Yes" if excel_has else "No",
            "JSON_status": json_status,
            "Excel_value": (excel_value if (show_values and excel_present) else ""),
            "JSON_value": (json_value if json_present else ""),
            "Similarity": sim,
            "Source": source,
            "Match_quality": match_quality,  # final single field requested
            "Excel_column": excel_col
        })

    # Publication meta
    add_row("Publication", "Meta", "Title",
            True, title, "—", meta.get("title", ""),
            None, excel_col="Publication|Title")

    add_row("Publication", "Meta", "Author",
            True, author, "—", (meta.get("author", "") or author_hint),
            None, excel_col="Publication|Author")

    cand, _ = fuzzy_match("Publication|DOI", list(df.columns), allow_fuzzy=True)
    doi_col = cand or "Publication|DOI"
    doi_val = df.iloc[row_idx].get(doi_col, "") if doi_col in df.columns else ""
    add_row("Publication", "Meta", "DOI",
            True, doi_val, "—", meta.get("doi", ""),
            None, excel_col=doi_col)

    # Families (non-preprocessing) + bridge to preprocessing
    for fam_n, labels in fam_label_map.items():
        if fam_n == normalize_name("Preprocessing"):
            continue

        fam_match_norm, fqual = fuzzy_match(fam_n, list(map(normalize_name, families_json.keys())), threshold=0.78, allow_fuzzy=allow_fuzzy)
        fam_key_disp = next((k for k in families_json.keys() if normalize_name(k) == fam_match_norm), None) if fam_match_norm else None

        json_found = families_json.get(fam_key_disp, {"Found": [], "Missing": []}) if fam_key_disp else {"Found": [], "Missing": []}
        json_all_norm = [normalize_name(x) for x in (json_found["Found"] + json_found["Missing"])]
        json_vals_map = family_values.get(fam_n if fam_key_disp is None else normalize_name(fam_key_disp), {})

        for label_n, (present, val) in labels.items():
            # skip publication fields in families
            if label_n in {normalize_name(x) for x in ["title", "author", "doi", "year", "publisher"]}:
                continue

            # Bridge Excel family field to preprocessing step if it matches
            step_match_norm, mqual2 = fuzzy_match(label_n, preproc_keys_norm, threshold=0.72, allow_fuzzy=allow_fuzzy)
            if step_match_norm:
                step_disp = next((k for k in preproc_disp_keys if normalize_name(k) == step_match_norm), label_n)
                json_comp_val = step_composites.get(step_match_norm, "")
                js = "Found" if is_present(json_comp_val) else "Not mentioned"
                excel_col = norm_to_original.get((fam_n, label_n), f"{fam_n}|{label_n}")
                add_row("Preprocessing", step_disp, "Composite (Type/Alg/Soft/Params)",
                        present, val, js, json_comp_val, None,
                        match_quality=mqual2, excel_col=excel_col)
                continue

            # Regular Families handling
            json_val = json_vals_map.get(label_n, "")
            excel_col = norm_to_original.get((fam_n, label_n), f"{fam_n}|{label_n}")

            if present:
                if label_n in json_all_norm:
                    if normalize_name(label_n) in [normalize_name(x) for x in json_found["Found"]]:
                        add_row("Families", fam_key_disp or fam_n, label_n, True, val, "Found", json_val, None,
                                match_quality=fqual, excel_col=excel_col)
                    else:
                        add_row("Families", fam_key_disp or fam_n, label_n, True, val, "Missing", json_val, None,
                                match_quality=fqual, excel_col=excel_col)
                else:
                    add_row("Families", fam_key_disp or fam_n, label_n, True, val, "Not mentioned", "", None,
                            match_quality=fqual, excel_col=excel_col)
            else:
                if normalize_name(label_n) in [normalize_name(x) for x in json_found["Found"]]:
                    add_row("Families", fam_key_disp or fam_n, label_n, False, "", "Found", json_val, None,
                            match_quality=fqual, excel_col=excel_col)

        # Extras only in JSON
        for label in json_found["Found"]:
            lab_n = normalize_name(label)
            if lab_n not in labels:
                add_row("Families", fam_key_disp or fam_n, lab_n, False, "", "Found",
                        family_values.get(normalize_name(fam_key_disp or fam_n), {}).get(lab_n, ""),
                        None, match_quality=fqual, excel_col="")

    # Preprocessing (structured 4-sublabel comparison)
    pp_steps = preprocess_steps_from_excel(df, row_idx)
    for step_name, excel_entry in pp_steps.items():
        step_match_norm, mqual = fuzzy_match(step_name, list(map(normalize_name, preprocessing_json.keys())), threshold=0.68, allow_fuzzy=allow_fuzzy)
        step_key_disp = next((k for k in preprocessing_json.keys() if normalize_name(k) == step_match_norm), None) if step_match_norm else None

        json_entry = preprocessing_json.get(step_key_disp, {"Present": [], "Missing": []}) if step_key_disp else {"Present": [], "Missing": []}
        json_present = [normalize_name(x) for x in json_entry["Present"]]
        json_vals_map = preprocessing_values.get(normalize_name(step_key_disp or step_name), {})

        for sub in ["Type", "Algorithm", "Software", "Parameters"]:
            excel_val = excel_entry.get(sub, np.nan)
            excel_has = is_present(excel_val)
            js = "Found" if normalize_name(sub) in json_present else "Not mentioned"
            add_row("Preprocessing", step_key_disp or step_name, sub,
                    (excel_has), excel_val, js,
                    json_vals_map.get(normalize_name(sub), ""), None,
                    match_quality=mqual, excel_col=f"Preprocessing|{sub}")

        # Non-standard JSON-only sublabels
        for sub in json_entry["Present"]:
            if normalize_name(sub) not in {normalize_name(x) for x in ["Type", "Algorithm", "Software", "Parameters"]}:
                add_row("Preprocessing", step_key_disp or step_name, sub, False, "", "Found",
                        json_vals_map.get(normalize_name(sub), ""), None,
                        match_quality=mqual, excel_col="")

    table = pd.DataFrame(rows).sort_values(["Section", "Group", "Field"])
    order = [
        "Section", "Group", "Field",
        "Excel_has", "JSON_status",
        "Excel_value", "JSON_value", "Similarity",
        "Source", "Match_quality", "Excel_column"
    ]
    return table.reindex(columns=order), {"title": title, "author": author, "fname": fname}


# ------------ Discover JSONs ------------
def discover_jsons(root: str, recursive: bool) -> List[str]:
    hits: List[str] = []

    def is_target(fn: str) -> bool:
        fl = fn.lower()
        return fl.endswith("_extracted_labels_lastprompt.json") or fl.endswith("_extracted_labels.json")or fl.endswith("_combined_labels.json")

    if recursive:
        for dirpath, _, files in os.walk(root):
            for fn in files:
                if is_target(fn):
                    hits.append(os.path.join(dirpath, fn))
    else:
        for fn in os.listdir(root):
            path = os.path.join(root, fn)
            if os.path.isfile(path) and is_target(fn):
                hits.append(path)
    hits.sort()
    return hits


# ------------ Main ------------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--excel", required=True, help="Path to Excel file")
    ap.add_argument("--sheet", default="Seed2", help="Excel sheet name (default: Seed2)")
    ap.add_argument("--json_root", required=True, help="Folder containing many extracted label JSONs")
    ap.add_argument("--recursive", action="store_true", help="Search subfolders recursively")
    ap.add_argument("--show_values", action="store_true", help="Include Excel & JSON values in the table")
    ap.add_argument("--no_fuzzy", action="store_true", help="Disable fuzzy/alias matching")
    args = ap.parse_args()

    df, _, norm_to_original = load_excel_structured(args.excel, sheet_name=args.sheet)
    targets = discover_jsons(args.json_root, args.recursive)
    if not targets:
        raise SystemExit(f"No '*_extracted_labels_lastprompt.json' or '*_extracted_labels.json' or '*_combined_labels.json' files found under: {args.json_root}")

    for jp in targets:
        try:
            table_df, meta = build_comparison_table_for_json(
                df=df, json_path=jp, sheet=args.sheet,
                allow_fuzzy=not args.no_fuzzy, show_values=args.show_values,
                norm_to_original=norm_to_original
            )
            base = os.path.splitext(os.path.basename(jp))[0]
            out_csv = os.path.join(os.path.dirname(jp), f"{base}_table.csv")
            table_df.replace({np.nan: ""}).to_csv(out_csv, index=False, encoding="utf-8")
            print(f"✓ {meta['author']}: saved {out_csv}")
        except Exception as e:
            err_path = os.path.join(os.path.dirname(jp), f"{os.path.splitext(os.path.basename(jp))[0]}_table.ERROR.txt")
            with open(err_path, "w", encoding="utf-8") as fh:
                fh.write(f"Error for {jp}:\n{str(e)}\n")
            print(f"✗ Error for {jp}. See: {err_path}")


if __name__ == "__main__":
    pd.options.display.max_colwidth = 200
    main()
