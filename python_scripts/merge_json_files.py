import os
import json
import re
import csv
from copy import deepcopy
from typing import Dict, Any, Optional, List, Tuple

BASE_DIR = "JSON_firstprompt_files"
GRAPH_DIR = "JSON_Graph_only_files"
OUT_DIR = "JSON_Combined_files"

SEPARATOR = "\n\n"
ADD_SEQUENTIAL_IDS = True

# Output filename format:
# authorname_combined_labels.json
OUTPUT_SUFFIX = "_combined_labels.json"

REPORT_TXT = "merge_report.txt"
REPORT_CSV = "merge_report.csv"   # optional (easy to open in Excel)

# ----------------------------
# Title extraction heuristics
# ----------------------------

def extract_title(js: Dict[str, Any]) -> Optional[str]:
    """
    Try multiple likely locations for a title.
    If none exists, return None.
    """
    # Common possibilities — extend if your schema differs
    candidates = [
        js.get("data", {}).get("title"),
        js.get("data", {}).get("meta", {}).get("title"),
        js.get("meta", {}).get("title"),
        js.get("metadata", {}).get("title"),
    ]
    for c in candidates:
        if isinstance(c, str) and c.strip():
            return c.strip()
    return None

def norm_title(t: str) -> str:
    t = t.lower().strip()
    t = re.sub(r"[^\w\s]", " ", t)   # remove punctuation
    t = re.sub(r"\s+", " ", t).strip()
    return t

def title_similarity(a: str, b: str) -> float:
    A = set(norm_title(a).split())
    B = set(norm_title(b).split())
    if not A or not B:
        return 0.0
    return len(A & B) / len(A | B)

# ----------------------------
# JSON load/save
# ----------------------------

def load_json(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(obj: Dict[str, Any], path: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False)

# ----------------------------
# Merge logic (same as before)
# ----------------------------

def merge_one(base: Dict[str, Any], graph: Dict[str, Any]) -> Dict[str, Any]:
    base_text = base["data"]["text"]
    graph_text = graph["data"]["text"]

    combined_text = base_text + SEPARATOR + graph_text
    offset = len(base_text + SEPARATOR)

    base_results = deepcopy(base["annotations"][0]["result"])
    graph_results = deepcopy(graph["annotations"][0]["result"])

    # Shift all graph spans
    shifted_graph_results = []
    for r in graph_results:
        r2 = deepcopy(r)
        v = r2.get("value", {})
        if isinstance(v.get("start"), int) and isinstance(v.get("end"), int):
            v["start"] += offset
            v["end"] += offset
        r2["value"] = v
        shifted_graph_results.append(r2)

    graph_from_names = {r["from_name"] for r in shifted_graph_results}

    # Remove graph labels from base (by from_name overlap)
    filtered_base_results = [
        r for r in base_results if r.get("from_name") not in graph_from_names
    ]

    combined_results = filtered_base_results + shifted_graph_results

    if ADD_SEQUENTIAL_IDS:
        for i, r in enumerate(combined_results, start=1):
            r["id"] = f"m{i:04d}"

    out = deepcopy(base)
    out["data"]["text"] = combined_text
    out["annotations"][0]["result"] = combined_results
    return out

# ----------------------------
# Matching logic
# ----------------------------

def build_graph_index(graph_files: List[str]) -> Tuple[Dict[str, str], List[Tuple[str, str]]]:
    """
    Returns:
      - exact normalized title -> filepath
      - list of (title, filepath) for fuzzy matching
    """
    exact = {}
    all_titles = []
    for fp in graph_files:
        js = load_json(fp)
        title = extract_title(js)
        if title:
            nt = norm_title(title)
            exact.setdefault(nt, fp)
            all_titles.append((title, fp))
    return exact, all_titles

def find_best_graph_for_base(
    base_js: Dict[str, Any],
    base_filename: str,
    graph_exact: Dict[str, str],
    graph_titles: List[Tuple[str, str]],
    graph_dir: str,
    fuzzy_threshold: float = 0.35
) -> Tuple[Optional[str], str]:
    """
    Returns (graph_path or None, reason string)

    Matching tries:
      1) exact title match
      2) fuzzy title match
      3) filename fallback: author_graph_labels.json
    """
    base_title = extract_title(base_js)

    # 1) exact title
    if base_title:
        nt = norm_title(base_title)
        if nt in graph_exact:
            return graph_exact[nt], "Matched by exact title"

        # 2) fuzzy title
        best_fp = None
        best_score = 0.0
        for gt, fp in graph_titles:
            score = title_similarity(base_title, gt)
            if score > best_score:
                best_score = score
                best_fp = fp

        if best_fp is not None and best_score >= fuzzy_threshold:
            return best_fp, f"Matched by fuzzy title (score={best_score:.2f})"

    # 3) filename fallback
    author = base_filename.replace("_extracted_labels.json", "")
    candidate = os.path.join(graph_dir, f"{author}_graph_labels.json")
    if os.path.exists(candidate):
        return candidate, "Matched by filename fallback"

    if not base_title:
        return None, "No title found in base JSON, and filename fallback graph not found"
    return None, "No title match found and filename fallback graph not found"

# ----------------------------
# Main batch runner
# ----------------------------

def main():
    os.makedirs(OUT_DIR, exist_ok=True)

    base_files = [
        os.path.join(BASE_DIR, f)
        for f in os.listdir(BASE_DIR)
        if f.endswith("_extracted_labels.json")
    ]
    graph_files = [
        os.path.join(GRAPH_DIR, f)
        for f in os.listdir(GRAPH_DIR)
        if f.endswith("_graph_labels.json")
    ]

    skipped: List[Dict[str, str]] = []
    merged: List[Dict[str, str]] = []

    if not base_files:
        print(f"[ERROR] No *_extracted_labels.json files found in {BASE_DIR}")
        return
    if not graph_files:
        print(f"[ERROR] No *_graph_labels.json files found in {GRAPH_DIR}")
        return

    graph_exact, graph_titles = build_graph_index(graph_files)

    for base_path in sorted(base_files):
        base_filename = os.path.basename(base_path)
        author = base_filename.replace("_extracted_labels.json", "")

        try:
            base_js = load_json(base_path)
        except Exception as e:
            skipped.append({
                "author": author,
                "base_file": base_filename,
                "graph_file": "",
                "reason": f"Failed to read base JSON: {e}"
            })
            continue

        graph_path, match_reason = find_best_graph_for_base(
            base_js=base_js,
            base_filename=base_filename,
            graph_exact=graph_exact,
            graph_titles=graph_titles,
            graph_dir=GRAPH_DIR,
        )

        if not graph_path:
            skipped.append({
                "author": author,
                "base_file": base_filename,
                "graph_file": "",
                "reason": match_reason
            })
            print(f"[SKIP] {base_filename} -> {match_reason}")
            continue

        graph_filename = os.path.basename(graph_path)

        try:
            graph_js = load_json(graph_path)
        except Exception as e:
            skipped.append({
                "author": author,
                "base_file": base_filename,
                "graph_file": graph_filename,
                "reason": f"Failed to read graph JSON: {e}"
            })
            print(f"[SKIP] {base_filename} -> graph read error")
            continue

        # Graph file sanity checks
        if not graph_js.get("data", {}).get("text"):
            skipped.append({
                "author": author,
                "base_file": base_filename,
                "graph_file": graph_filename,
                "reason": "Graph JSON missing data.text"
            })
            print(f"[SKIP] {base_filename} -> graph missing data.text ({graph_filename})")
            continue

        ann = graph_js.get("annotations", [])
        if not ann or not ann[0].get("result"):
            skipped.append({
                "author": author,
                "base_file": base_filename,
                "graph_file": graph_filename,
                "reason": "Graph JSON has no labels in annotations[0].result"
            })
            print(f"[SKIP] {base_filename} -> graph has no labels ({graph_filename})")
            continue

        # Merge
        out_js = merge_one(base_js, graph_js)

        out_file = f"{author}{OUTPUT_SUFFIX}"
        out_path = os.path.join(OUT_DIR, out_file)
        save_json(out_js, out_path)

        merged.append({
            "author": author,
            "base_file": base_filename,
            "graph_file": graph_filename,
            "reason": match_reason
        })

        print(f"[OK] {author} -> {out_file} ({match_reason})")

    # ----------------------------
    # Final report output
    # ----------------------------
    print("\n==== FINAL SUMMARY ====")
    print(f"Merged : {len(merged)}")
    print(f"Skipped: {len(skipped)}")

    if skipped:
        print("\nSkipped files:")
        for s in skipped:
            print(f"- {s['base_file']} | graph: {s['graph_file'] or 'N/A'} | reason: {s['reason']}")

    # Write reports
    with open(REPORT_TXT, "w", encoding="utf-8") as f:
        f.write("==== MERGE REPORT ====\n\n")
        f.write(f"Merged : {len(merged)}\n")
        f.write(f"Skipped: {len(skipped)}\n\n")

        f.write("---- MERGED ----\n")
        for m in merged:
            f.write(f"{m['author']} | base={m['base_file']} | graph={m['graph_file']} | {m['reason']}\n")

        f.write("\n---- SKIPPED ----\n")
        for s in skipped:
            f.write(f"{s['author']} | base={s['base_file']} | graph={s['graph_file'] or 'N/A'} | {s['reason']}\n")

    with open(REPORT_CSV, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["status", "author", "base_file", "graph_file", "reason"])
        writer.writeheader()
        for m in merged:
            writer.writerow({"status": "merged", **m})
        for s in skipped:
            writer.writerow({"status": "skipped", **s})

    print(f"\n[REPORT] Written: {REPORT_TXT}")
    print(f"[REPORT] Written: {REPORT_CSV}")


if __name__ == "__main__":
    main()
