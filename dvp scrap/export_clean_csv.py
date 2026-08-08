#!/usr/bin/env python3
"""
Export first sheet of an Excel workbook to CSV,
dropping any rows above the real header row (e.g., the row containing Code/Name/Status).

Usage:
  python export_clean_csv.py "ACME Travels.xlsx" "ACME Travels.csv"
"""

import sys
import pandas as pd


# ✅ Update these to match the column headers you expect in the real header row.
REQUIRED_HEADERS = ["Code", "Name", "Status"]  # add more if you want (e.g. "Start Date", "Amount", etc.)

xlsx_path = "ACME Travels.xlsx"
csv_path = "ACME Travels.csv"

def find_header_row(raw_df: pd.DataFrame, required_headers) -> int:
    """
    Find the row index in raw_df (read with header=None) that contains all required_headers.
    Returns the integer row index if found, raises ValueError otherwise.
    """
    req = {h.strip().lower() for h in required_headers}

    for i in range(len(raw_df)):
        row_values = raw_df.iloc[i].astype(str).str.strip().str.lower().tolist()
        row_set = set(row_values)
        if req.issubset(row_set):
            return i

    raise ValueError(
        f"Could not find a header row containing all required headers: {required_headers}"
    )


#def main(xlsx_path: str, csv_path: str):
# 1) Read ONLY the first sheet, with no header so we can detect it ourselves
raw = pd.read_excel(xlsx_path, sheet_name=0, header=None, engine="openpyxl")

# 2) Detect which row is the real header
header_idx = find_header_row(raw, REQUIRED_HEADERS)

# 3) Re-read using that header row (skip everything above it)
df = pd.read_excel(
	xlsx_path,
	sheet_name=0,
	header=header_idx,
	engine="openpyxl"
)

# 4) Optional: drop completely empty rows (common after messy exports)
df = df.dropna(how="all")

# 5) Export to CSV
df.to_csv(csv_path, index=False, encoding="utf-8-sig")

print(f"✅ Wrote cleaned CSV to: {csv_path}")
print(f"   Header row detected at Excel row: {header_idx + 1} (1-based)")


#if __name__ == "__main__":
#    if len(sys.argv) < 3:
#        print("Usage: python export_clean_csv.py <input.xlsx> <output.csv>")
#        sys.exit(1)
#
#    main(sys.argv[1], sys.argv[2])
