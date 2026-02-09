#!/usr/bin/env python3
"""
TXT Missing ▶ Excel Present (value) report — robust & case-insensitive
- Excel sheet: Seed2
- Match by Title (case-insensitive). If Title absent or messy, fallback to:
    (a) DOI exact match; else
    (b) author surname from TXT filename; and prefer candidates with matching Year/Journal;
        if still tied then
    (c) pick the row with highest overlap to TXT preprocessing step names
- Compare ONLY items that TXT marks as Missing; if Excel has a value -> report it
- Preprocessing: CONTENT ONLY (Software / Algorithm(Function) / Type / Parameters), ignores "Step Number"
- Swap allowed ONLY between Algorithm ↔ Type
- Output: "<author>_mismatch_report.txt"
"""

import argparse, os, re, difflib, glob, sys
from typing import Dict, List, Tuple, Optional, Any
import pandas as pd
import numpy as np

# ---------------- Alias tables ----------------
STEP_EQUIVALENCE = {
    "spatial normalization": [
        "spatial normalization (functional)", "functional normalization", "normalization (functional)"
    ],
    "slice timing correction": ["slice time correction", "slice-timing correction"],
    "alignment head motion est": ["motion correction", "realignment", "head motion correction", "realign"],
    "coregistration": ["coreg", "registration", "alignment", "coregistration (func->anat)", "coregister"],
    "temporal filt": ["bandpass filtering", "temporal filtering", "bandpass filter"],
    "spatial smooth": ["spatial smoothing", "smoothing", "spatial smooth"],
    "graph measures": ["network measures", "graph metrics", "graph analysis"],
    "atlas definition": ["atlas", "atlas creation"],
    "roi definition": ["region definition", "seed definition"],
    "result aggregation": ["aggregation", "summary step", "result summary"],
    # NEW common steps seen in your exports
    "skull stripping": [
        "skull stripping / brain extraction", "brain extraction", "skullstrip", "skull-strip"
    ],
    "removal of initial volumes": [
        "removal init vol", "discard initial volumes", "dummy scans removal", "remove first volumes",
        "remove initial volumes", "discard initial trs", "drop initial volumes"
    ],
}

# TXT family lines often end with "_found missing" or variants
FAMILY_SUFFIXES_TO_DROP = [
    "found missing", "found_missing", "_found missing", "_found_missing", "found  missing"
]
# NEW: common noisy prefixes in exports
FAMILY_PREFIXES_TO_DROP = [
    "family_found", "family found"
]

# Family name aliases (normalized → normalized)
FAMILY_ALIASES = {
    "functional scan information": [
        "functional_scan_information", "functional scan info", "functional mri information",
    ],
    "publication": ["publication info", "paper info"],
    "availability": ["data/code availability", "availability info"],
    "design specification": ["design_specification"],
    "task specification": ["task_specification"],
    "planned comparisons": ["planned_comparisons"],
    "human subjects": ["human_subjects", "participants"],
    "ethics approval": ["ethics_approval", "ethics"],
    "behavioral performance": ["behavioral_performance", "behavioural performance"],
}

# Label aliases (normalized → list of variants, all matched in normalized/paren-stripped space)
LABEL_ALIASES = {
    "multicenter study": ["multicenter study y n", "multicenter", "multi center study", "multi centre study"],
    "slice thickness": ["slice thick", "thickness"],
    "inter slice gap": ["inter slice interval", "inter slice", "slice gap", "gap"],
    "eyes open closed": ["eyes open closed", "eyes open", "eyes closed"],
    "resting or task": ["resting or task if task what task", "resting task", "task if task what task"],
    "number of slices": ["number of slice", "num slices", "slices"],
    "field of view": ["field of view cm", "fov", "fov cm"],
    "flip angle": ["flip-angle", "flipangle"],
    "voxel size": ["voxel size mm x mm x mm", "voxel size mm mm mm", "voxel size mm", "voxel"],
    "duration": ["duration s", "scan duration", "time seconds"],
    "most used software for preprocessing": ["most used software", "most used preprocessing software", "preprocessing software main"],
    "number of individuals for final analyses": [
        "number of individuals for final analysis", "final n", "n final", "number of subjects for final analyses"
    ],
    "software": ["softw", "pkg", "package"],
    "parameters": ["parameter", "params", "setting", "settings"],
    "algorithm": ["function", "method", "approach"],
    "type": ["data type", "type of", "category"],
}

CONTENT_SUBLABELS = {"Software", "Algorithm", "Type", "Parameters"}
EMPTY_TOKENS = {"", "—", "-", "nan", "n/a", "na", "none", "not available"}

# ---------------- Normalize / utils ----------------
def strip_bom(s: str) -> str:
    return s.replace("\ufeff", "")

def remove_paren_content(s: str) -> str:
    # remove any (...) groups
    return re.sub(r"\([^)]*\)", " ", s)

def normalize_name(s: Any) -> str:
    if s is None:
        return ""
    s = str(s)
    s = strip_bom(s)
    s = s.replace("—", "-")
    s = re.sub(r"[\u200b\u200c\u200d]", "", s)  # zero-width
    s = s.lower().strip()
    s = s.replace("_", " ").replace("×", "x").replace("°", " ").replace("µ", "u")
    s = remove_paren_content(s)
    s = re.sub(r"[^\w\s]", " ", s)
    s = re.sub(r"\s+", " ", s)
    return s

def tokens(s: str) -> List[str]:
    return [t for t in normalize_name(s).split() if t]

def jaccard(a: List[str], b: List[str]) -> float:
    sa, sb = set(a), set(b)
    if not sa and not sb: return 1.0
    if not sa or not sb: return 0.0
    return len(sa & sb) / len(sa | sb)

def norm_family_key(s: str) -> str:
    s0 = normalize_name(s)
    # drop known prefixes like "family_found ..."
    for pre in FAMILY_PREFIXES_TO_DROP:
        s0 = re.sub(rf"^{re.escape(pre)}\s+", "", s0)
    # drop trailing "... found missing"
    for suf in FAMILY_SUFFIXES_TO_DROP:
        s0 = re.sub(rf"\s*{re.escape(suf)}\s*$", "", s0)
    return s0.strip()

def alias_family(s: str) -> str:
    sn = norm_family_key(s)
    for canon, variants in FAMILY_ALIASES.items():
        if sn == canon: return canon
        if sn in [normalize_name(v) for v in variants]: return canon
    return sn

def alias_label(s: str) -> str:
    sn = normalize_name(s)
    for canon, variants in LABEL_ALIASES.items():
        if sn == canon: return canon
        if sn in [normalize_name(v) for v in variants]: return canon
    return sn

def slugify_basic(s: str) -> str:
    s = re.sub(r"[^\w\-]+", "_", str(s).strip())
    s = re.sub(r"_+", "_", s).strip("_")
    return s or "unknown"

def is_step_number_label(label: str) -> bool:
    return "step number" in normalize_name(label)

def is_present(value) -> bool:
    if pd.isna(value):
        return False
    if isinstance(value, str):
        return value.strip().lower() not in EMPTY_TOKENS
    return True

def fuzzy_best(target: str, candidates: List[str]) -> Tuple[Optional[str], float]:
    best, best_score = None, 0.0
    t = normalize_name(target)
    for c in candidates:
        score = difflib.SequenceMatcher(None, t, normalize_name(c)).ratio()
        if score > best_score:
            best, best_score = c, score
    return best, best_score

# ---- NEW helpers for labels/steps ----
UNIT_TOKENS = {"ms", "s", "sec", "secs", "cm", "mm", "hz"}

def label_core_tokens(s: str) -> List[str]:
    """Normalize & tokenize a label, dropping units and keeping signal words."""
    toks = [t for t in normalize_name(s).split() if t]
    toks = [t for t in toks if t not in UNIT_TOKENS]
    expanded = []
    for t in toks:
        if t == "fov":
            expanded.extend(["field", "of", "view"])
            continue
        expanded.append(t)
    return expanded

STEP_PREFIX_RE = re.compile(r"^[fs]-\s*", re.I)  # e.g., F-Temporal_filt or S-BBR_...

def step_core_name(s: str) -> str:
    """Make Excel/TXT step names comparable (strip F-/S- prefixes, underscores, etc.)."""
    s = STEP_PREFIX_RE.sub("", str(s).strip(), count=1)
    return normalize_name(s)

# ---------------- Excel (Seed2) ----------------
def load_excel_structured(excel_path: str, sheet_name: str = "Seed2") -> Tuple[pd.DataFrame, Dict[str, List[str]]]:
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
    return df.reset_index(drop=True), family_to_labels

# ---------------- TXT parsing (robust, no divider needed) ----------------
TITLE_RE = re.compile(r"^\s*title\s*[:\-–—]\s*(.+)$", re.I | re.M)
_LIST_RE = re.compile(r"\[([^\]]*)\]")
_QUOTED_ITEM_RE = re.compile(r"'([^']*)'")
DOI_RE = re.compile(r"\b10\.\d{4,9}/[^\s,;()<>]+", re.I)
YEAR_RE = re.compile(r"\b(19|20)\d{2}\b")

def _parse_list_field(s: str) -> List[str]:
    if s is None: return []
    s = s.strip()
    if not s or s.lower() == "none": return []
    m = _LIST_RE.search(s)
    if m:
        inside = m.group(1)
        items = _QUOTED_ITEM_RE.findall(inside)
        if items: return [x.strip() for x in items if x.strip()]
        return [x.strip(" '\"") for x in inside.split(",") if x.strip(" '\"")]
    return [x.strip(" '\"") for x in s.split(",") if x.strip(" '\"")]

def derive_author_key_from_filename(path: str) -> str:
    stem = os.path.splitext(os.path.basename(path))[0]
    token = re.split(r"[ _\-]+", stem)[0]
    token = re.sub(r"[^A-Za-z0-9]+", "", token)
    return token or "unknown"

def extract_doi_year_journal(txt: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    txt = strip_bom(txt)
    # DOI
    doi = None
    m = DOI_RE.search(txt)
    if m:
        doi = m.group(0).strip().rstrip(").,;")
    # Year
    y = None
    ym = YEAR_RE.search(txt)
    if ym:
        y = ym.group(0)
    # Journal heuristic: search lines with known tokens (extend as needed)
    journal = None
    for line in txt.splitlines():
        ln = line.strip()
        ln_l = ln.lower()
        if any(k in ln_l for k in [
            "neuroimage", "cerebral cortex", "neuroscience", "human brain mapping",
            "frontiers", "plos", "journal", "brain", "neuropsychologia", "nature", "science"
        ]):
            journal = ln
            break
    return doi, y, journal

def parse_missing_summary(txt: str, txt_path: Optional[str] = None):
    txt = strip_bom(txt)
    # Title (optional)
    m = TITLE_RE.search(txt)
    title = m.group(1).strip() if m else None

    # Author key from filename (fallback)
    txt_author_key = slugify_basic(derive_author_key_from_filename(txt_path or "unknown.txt"))

    # Parse every "Name: Present=... | Missing=..." line uniformly
    line_re = re.compile(
        r"^([^:\n]+):\s*present\s*=\s*(.+?)\s*\|\s*missing\s*=\s*(.+)$",
        re.I | re.M
    )
    items = []  # list of dicts: {name, present[], missing[]}
    for m in line_re.finditer(txt):
        name_raw, present_raw, missing_raw = m.groups()
        items.append({
            "name_raw": name_raw.strip(),
            "present": [x for x in _parse_list_field(present_raw) if not is_step_number_label(x)],
            "missing": [x for x in _parse_list_field(missing_raw) if not is_step_number_label(x)],
        })
    return title, txt_author_key, items

# ---------------- Title/Author lookup ----------------
def find_row(
    df: pd.DataFrame,
    title_hint: Optional[str],
    author_key: str,
    pp_steps_from_txt: List[str],
    debug=False,
    doi_hint: Optional[str]=None,
    year_hint: Optional[str]=None,
    journal_hint: Optional[str]=None
) -> Tuple[int, Dict[str, str]]:

    def find_col(want):
        for c in df.columns:
            if normalize_name(c) == normalize_name(want):
                return c
        return want

    title_col = find_col("Publication|Title")
    author_col = find_col("Publication|Author")
    doi_col = find_col("Publication|DOI")
    journal_col = find_col("Publication|Publisher")  # in your sheet, "Publisher" holds the journal
    year_col = find_col("Publication|Year")

    titles = df[title_col].astype(str).fillna("")
    authors = df[author_col].astype(str).fillna("")

    # 0) DOI exact match
    if doi_hint and doi_col in df.columns:
        doi_series = df[doi_col].astype(str).fillna("")
        idxs = doi_series[doi_series.apply(lambda d: normalize_name(d) == normalize_name(doi_hint))].index
        if len(idxs) > 0:
            idx = int(idxs[0])
            return idx, {"title": str(df.loc[idx, title_col]), "author": str(df.loc[idx, author_col])}

    # 1) Exact normalized title
    if title_hint:
        exact_idx = titles[titles.apply(lambda t: normalize_name(t) == normalize_name(title_hint))].index
        if len(exact_idx) > 0:
            idx = int(exact_idx[0])
            return idx, {"title": str(df.loc[idx, title_col]), "author": str(df.loc[idx, author_col])}

    # 2) Fuzzy title
    if title_hint:
        sims = titles.apply(lambda t: difflib.SequenceMatcher(None, normalize_name(t), normalize_name(title_hint)).ratio())
        if sims.max() >= 0.78:
            idx = int(sims.idxmax())
            return idx, {"title": str(df.loc[idx, title_col]), "author": str(df.loc[idx, author_col])}

    # 3) Fallback by author surname + meta (year/journal) before step overlap
    surname = normalize_name(author_key).split("_")[0]
    candidates = []
    if surname:
        mask = authors.apply(lambda a: surname in normalize_name(a))
        candidates = list(authors[mask].index)

    if not candidates:
        raise ValueError(f"No match found in Excel for title '{title_hint or '<<missing in TXT>>'}'")

    def row_meta_score(i: int) -> float:
        score = 0.0
        if year_hint and year_col in df.columns:
            row_year = str(df.loc[i, year_col])
            if normalize_name(row_year) == normalize_name(year_hint):
                score += 0.4
        if journal_hint and journal_col in df.columns:
            row_j = str(df.loc[i, journal_col])
            if row_j and normalize_name(journal_hint) in normalize_name(row_j):
                score += 0.4
        return score

    # Prepare step tokens
    txt_step_tokens = set(tokens(" ".join(pp_steps_from_txt)))
    for s in pp_steps_from_txt:
        ns = normalize_name(s)
        for base, aliases in STEP_EQUIVALENCE.items():
            if ns == base or ns in [normalize_name(a) for a in aliases]:
                txt_step_tokens |= set(tokens(base))

    best_idx, best_meta, best_overlap = None, -1.0, -1.0
    for i in candidates:
        meta_sc = row_meta_score(i)
        # compute overlap
        row_tok = set()
        for n in range(1, 101):
            sc = f"Preprocessing|Step{n}"
            if sc in df.columns:
                v = df.loc[i, sc]
                if is_present(v):
                    row_tok |= set(tokens(str(v)))
        overlap = jaccard(list(txt_step_tokens), list(row_tok))
        if meta_sc > best_meta or (meta_sc == best_meta and overlap > best_overlap):
            best_idx, best_meta, best_overlap = i, meta_sc, overlap

    if best_idx is not None:
        if debug:
            print(f"[fallback] picked row {best_idx} by meta={best_meta:.2f}, step-overlap={best_overlap:.2f}", file=sys.stderr)
        idx = int(best_idx)
        return idx, {"title": str(df.loc[idx, title_col]), "author": str(df.loc[idx, author_col])}

    raise ValueError(f"No match found in Excel for title '{title_hint or '<<missing in TXT>>'}'")

# ---------------- Build maps from Excel row ----------------
def excel_presence_map_for_row(df: pd.DataFrame, row_idx: int):
    row = df.iloc[row_idx]
    out: Dict[str, Dict[str, Tuple[bool, Any, str, str]]] = {}
    for col in df.columns:
        fam, lab = (col.split("|", 1) if "|" in col else ("", col))
        fam_n, lab_n = normalize_name(fam), normalize_name(lab)
        val = row[col]
        out.setdefault(fam_n, {})[lab_n] = (is_present(val), val, fam, lab)
    return out

def preprocess_steps_from_excel(df: pd.DataFrame, row_idx: int):
    row = df.iloc[row_idx]
    steps: Dict[str, Dict[str, Any]] = {}
    for n in range(1, 101):
        sc = f"Preprocessing|Step{n}"
        if sc not in df.columns:
            continue
        step_name = row.get(sc, np.nan)
        if pd.isna(step_name) or str(step_name).strip() in ["", "nan"]:
            continue
        core = step_core_name(str(step_name))
        entry = {
            "Type": row.get(f"Preprocessing|Type{n}", np.nan),
            "Algorithm": row.get(f"Preprocessing|Function{n}", np.nan),  # Function == Algorithm
            "Software": row.get(f"Preprocessing|Software{n}", np.nan),
            "Parameters": row.get(f"Preprocessing|Parameter{n}", np.nan),
            "_orig_step_name": str(step_name),
        }
        steps[core] = entry
    return steps

# ---------------- Field mapping ----------------
def preferred_fields_for_missing(label: str) -> List[str]:
    ln = alias_label(label)  # apply label alias then normalize internally
    if "software" in ln:
        return ["Software"]
    if "parameters" in ln:
        return ["Parameters"]
    if "algorithm/type" in ln or ("algorithm" in ln and "type" in ln):
        return ["Algorithm", "Type"]
    if "algorithm" in ln:
        return ["Algorithm", "Type"]
    if "type" in ln:
        return ["Type", "Algorithm"]
    for k in CONTENT_SUBLABELS:
        if normalize_name(k) == ln:
            return [k]
    return []

def resolve_excel_value_for_missing(excel_entry: Dict[str, Any], missing_label: str) -> Optional[Tuple[str, Any]]:
    if is_step_number_label(missing_label):
        return None
    for field in preferred_fields_for_missing(missing_label):
        v = excel_entry.get(field)
        if is_present(v):
            return field, v
    return None

# ---------------- Family/label matching (robust) ----------------
def best_family_match(txt_family_key: str, excel_family_keys: List[str]) -> Optional[str]:
    txt_alias = alias_family(txt_family_key)
    # exact on alias
    for c in excel_family_keys:
        if alias_family(c) == txt_alias:
            return c
    # token Jaccard on alias
    t = set(tokens(txt_alias))
    best, best_j = None, 0.0
    for c in excel_family_keys:
        cj = set(tokens(alias_family(c)))
        j = len(t & cj) / len(t | cj) if t or cj else 1.0
        if j > best_j:
            best, best_j = c, j
    if best_j >= 0.5:
        return best
    # fuzzy on alias
    fb, sc = fuzzy_best(txt_alias, [alias_family(c) for c in excel_family_keys])
    if fb and sc >= 0.75:
        # map back to original key
        for c in excel_family_keys:
            if alias_family(c) == fb:
                return c
    return None

def best_label_match(txt_label: str, excel_labels: List[str]) -> Optional[str]:
    """
    Robust label match:
    - alias normalize
    - exact (normalized)
    - containment/prefix (handles truncated headers)
    - directional overlap: require >=60% of TXT tokens to appear in Excel label (or subset either way)
    - Jaccard (low threshold for mashed headers)
    - fuzzy last resort
    """
    tl_alias = alias_label(txt_label)
    tl_norm = normalize_name(tl_alias)
    tl_tokens = label_core_tokens(tl_alias)

    # 1) exact normalized
    for c in excel_labels:
        if normalize_name(c) == tl_norm:
            return c

    # 2) containment / prefix / suffix
    for c in excel_labels:
        cn = normalize_name(c)
        if tl_norm.startswith(cn) or cn.startswith(tl_norm) or tl_norm in cn or cn in tl_norm:
            return c

    # 3) directional token overlap
    for c in excel_labels:
        ctoks = set(label_core_tokens(c))
        ttoks = set(tl_tokens)
        if not ttoks:
            continue
        overlap = len(ttoks & ctoks)
        if overlap >= 1 and (overlap / max(1, len(ttoks)) >= 0.60 or ttoks.issubset(ctoks) or ctoks.issubset(ttoks)):
            return c

    # 4) Jaccard on tokens (low threshold for mashed headers)
    best, best_j = None, 0.0
    ttoks = set(tl_tokens)
    for c in excel_labels:
        ctoks = set(label_core_tokens(c))
        if not ttoks and not ctoks:
            return c
        if not ttoks or not ctoks:
            continue
        j = len(ttoks & ctoks) / len(ttoks | ctoks)
        if j > best_j:
            best, best_j = c, j
    if best_j >= 0.34:
        return best

    # 5) fuzzy
    fb, sc = fuzzy_best(tl_alias, excel_labels)
    return fb if sc >= 0.80 else None

# ---------------- Core report ----------------
def build_missing_in_txt_but_present_in_excel_report(excel_path: str, txt_path: str, debug: bool=False) -> Tuple[str, Dict]:
    df, _ = load_excel_structured(excel_path, sheet_name="Seed2")
    with open(txt_path, "r", encoding="utf-8") as f:
        txt = f.read()

    title_hint, txt_author_key, items = parse_missing_summary(txt, txt_path=txt_path)
    doi_hint, year_hint, journal_hint = extract_doi_year_journal(txt)

    # Used for title/author fallback logic
    pp_step_candidates_from_txt = [it["name_raw"] for it in items]

    row_idx, meta = find_row(
        df, title_hint, txt_author_key, pp_step_candidates_from_txt,
        debug=debug, doi_hint=doi_hint, year_hint=year_hint, journal_hint=journal_hint
    )
    title, author_excel = meta["title"], meta["author"]

    fam_label_map = excel_presence_map_for_row(df, row_idx)
    pp_steps = preprocess_steps_from_excel(df, row_idx)
    excel_family_keys = list(fam_label_map.keys())
    excel_pp_core_names = list(pp_steps.keys())

    lines = [
        f"Paper matched by Title: {title}",
        f"Excel Author(s): {author_excel}",
        f"TXT Author Key: {txt_author_key}",
        "",
        "=== TXT Missing ► Excel Present (showing Excel value) ==="
    ]

    for it in items:
        raw_name = it["name_raw"]
        missing_list = it["missing"] or []
        if not missing_list:
            continue

        # Decide if this line is a FAMILY or a PREPROCESSING step:
        # 1) Try family match
        fam_key_alias = alias_family(raw_name)
        fam_match = best_family_match(fam_key_alias, excel_family_keys)

        if fam_match:
            excel_labels = fam_label_map.get(fam_match, {})
            for label in missing_list:
                lab_match = best_label_match(label, list(excel_labels.keys()))
                if not lab_match:
                    if debug:
                        print(f"[debug] No label match in family '{fam_match}' for TXT label '{label}'", file=sys.stderr)
                    continue
                present, val, orig_fam, orig_lab = excel_labels.get(lab_match, (False, None, None, None))
                if present:
                    lines.append(
                        f"Category: {orig_fam} → {orig_lab}\n"
                        f"TXT Missing: '{label}'\n"
                        f"Excel Value: {val}\n"
                    )
            continue  # handled as family

        # 2) Otherwise treat it as a PREPROCESSING step
        nst = step_core_name(raw_name)

        # alias mapping first
        step_match = None
        for k, aliases in STEP_EQUIVALENCE.items():
            k_norm = normalize_name(k)
            alias_norms = [normalize_name(a) for a in aliases]
            if nst == k_norm or nst in alias_norms:
                cand, sc = fuzzy_best(k_norm, excel_pp_core_names)
                if cand and sc >= 0.75:  # lowered from 0.80
                    step_match = cand
                    break

        # fallback: fuzzy on core names
        if not step_match:
            cand, score = fuzzy_best(nst, excel_pp_core_names)
            if cand and score >= 0.75:  # lowered from 0.80
                step_match = cand

        if not step_match:
            if debug:
                print(f"[debug] No preprocessing step match for '{raw_name}'", file=sys.stderr)
            continue

        excel_entry = pp_steps[step_match]
        excel_step_print = excel_entry.get("_orig_step_name", step_match)

        for sub in missing_list:
            if is_step_number_label(sub):
                continue
            hit = resolve_excel_value_for_missing(excel_entry, sub)
            if hit is not None:
                which, value = hit
                lines.append(
                    f"Category: Preprocessing → {excel_step_print} — {which}\n"
                    f"TXT Missing: '{sub}'\n"
                    f"Excel Value: {value}\n"
                )

    if len(lines) == 5:
        lines.append("✅ No cases where TXT marked Missing but Excel has a value.")

    meta_info = {
        "row_index": row_idx,
        "title": title,
        "author_excel": author_excel,
        "author_txt_key": txt_author_key
    }
    return "\n".join(lines), meta_info

# ---------------- Batch runner ----------------
def should_skip_file(path: str) -> bool:
    name = os.path.basename(path).lower()
    return "mismatch_report" in name  # skip generated outputs

def process_single(excel_path: str, txt_path: str, out_path: Optional[str] = None, debug: bool=False) -> Optional[str]:
    try:
        report_text, meta = build_missing_in_txt_but_present_in_excel_report(excel_path, txt_path, debug=debug)
        author_key = meta.get("author_txt_key") or slugify_basic(derive_author_key_from_filename(txt_path))
        if out_path is None:
            out_dir = os.path.dirname(txt_path)
            out_path = os.path.join(out_dir, f"{author_key}_mismatch_report.txt")
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(report_text)
        print(f"[OK] {os.path.basename(txt_path)} → {os.path.basename(out_path)}")
        return out_path
    except Exception as e:
        print(f"[FAIL] {os.path.basename(txt_path)} :: {e}", file=sys.stderr)
        return None

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--excel", required=True, help="Path to Excel file (Seed2 sheet inside)")
    ap.add_argument("--txt", help="Path to a single TXT summary file")
    ap.add_argument("--txt_dir", help="Directory containing TXT files to process")
    ap.add_argument("--out", default=None, help="Output path (only for --txt). In batch mode each TXT writes '<author>_mismatch_report.txt' next to it.")
    ap.add_argument("--debug", action="store_true", help="Print debug reasons for non-matches to stderr")
    args = ap.parse_args()

    if args.txt_dir:
        all_txts = sorted(glob.glob(os.path.join(args.txt_dir, "*.txt")))
        # Skip generated reports; prefer *_missing_summary*.txt if present
        candidates = [p for p in all_txts if not should_skip_file(p)]
        ms = [p for p in candidates if re.search(r"_missing_summary", os.path.basename(p), re.I)]
        files = ms if ms else candidates

        if not files:
            print(f"No usable .txt files found in: {args.txt_dir}")
            return
        print(f"Found {len(files)} TXT files in {args.txt_dir}. Processing...\n")
        for txt_path in files:
            process_single(args.excel, txt_path, out_path=None, debug=args.debug)
        print("\nDone.")
    elif args.txt:
        if should_skip_file(args.txt):
            print(f"Input looks like an output report; refusing: {args.txt}")
            return
        process_single(args.excel, args.txt, out_path=args.out, debug=args.debug)
    else:
        print("Please provide either --txt for a single file or --txt_dir for a folder of TXT files.")
        sys.exit(1)

if __name__ == "__main__":
    main()
