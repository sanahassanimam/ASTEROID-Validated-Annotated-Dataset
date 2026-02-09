#!/usr/bin/env python3
"""
combine_verdict_summary_with_category_match.py

Combine multiple CSV reports, summarize 'Verdict', 'Category', and 'Match_quality',
and export a clean Excel report with correct counts and percentages.
"""

import pandas as pd
import os
import argparse
from glob import glob

def main(folder: str):
    if not os.path.exists(folder):
        raise FileNotFoundError(f"Folder not found: {folder}")

    files = glob(os.path.join(folder, "*.csv"))
    if not files:
        raise FileNotFoundError(f"No .csv files found in {folder}")

    print(f"🔍 Found {len(files)} CSV files.")

    # Combine all CSV files
    df_list = []
    for f in files:
        try:
            df = pd.read_csv(f)
            df["Source_File"] = os.path.basename(f)
            df_list.append(df)
        except Exception as e:
            print(f"⚠️ Skipping {f}: {e}")

    combined = pd.concat(df_list, ignore_index=True)
    print(f"✅ Combined {len(combined)} total rows.")

    # Normalize column names
    combined.columns = [c.strip().lower().replace(" ", "_") for c in combined.columns]

    # Summarize Verdict column
    if "verdict" in combined.columns:
        verdict_summary = (
            combined["verdict"]
            .astype(str)
            .str.strip()
            .value_counts(dropna=False)
            .reset_index()
        )
        verdict_summary.columns = ["Verdict", "Count"]
        total_rows = len(combined)
        verdict_summary["Percentage"] = (
            (verdict_summary["Count"].astype(float) / total_rows * 100).round(2)
        )
    else:
        verdict_summary = pd.DataFrame(columns=["Verdict", "Count", "Percentage"])
        print("⚠️ No 'Verdict' column found — skipping Verdict summary.")

    # Summarize Category and Match_quality columns (if present)
    summary_tables = []
    for col in ["category", "match_quality"]:
        if col in combined.columns:
            s = (
                combined[col]
                .astype(str)
                .str.strip()
                .value_counts(dropna=False)
                .reset_index()
            )
            s.columns = [col.capitalize(), "Count"]
            s["Percentage"] = (s["Count"].astype(float) / len(combined) * 100).round(2)
            summary_tables.append(s)
        else:
            print(f"⚠️ No '{col}' column found — skipping.")

    # Merge Category and Match_quality summaries (if both exist)
    if len(summary_tables) == 2:
        category_match_summary = pd.merge(
            summary_tables[0], summary_tables[1], left_index=True, right_index=True, how="outer"
        )
    elif len(summary_tables) == 1:
        category_match_summary = summary_tables[0]
    else:
        category_match_summary = pd.DataFrame()

    # Save outputs
    out_path = os.path.join(folder, "Combined_Verdict_Category_Match_Summary.xlsx")
    with pd.ExcelWriter(out_path) as writer:
        combined.to_excel(writer, index=False, sheet_name="All_Combined")
        verdict_summary.to_excel(writer, index=False, sheet_name="Verdict_Summary")
        category_match_summary.to_excel(writer, index=False, sheet_name="Category_MatchQuality_Summary")

    print("\n✅ Summary created successfully!")
    print(f"📁 Output saved to: {out_path}")
    print("\n📊 Verdict Summary:\n", verdict_summary.head())
    print("\n📊 Category & Match_quality Summary:\n", category_match_summary.head())

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Combine multiple CSV files and summarize key columns robustly.")
    parser.add_argument("--folder", required=True, help="Path to folder containing CSV files.")
    args = parser.parse_args()
    main(args.folder)
