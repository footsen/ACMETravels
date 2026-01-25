#!/usr/bin/env python3
"""
geojson_schema_audit_and_fix.py

Audit ALL field type inconsistencies across multiple GeoJSON files (FeatureCollections),
ignoring nulls. Optionally write normalized copies of the GeoJSON files where selected
fields are cast to string or number.

Typical use:
  python geojson_schema_audit_and_fix.py *.geojson --csv schema_report.csv --keep keep_fields.txt
  python geojson_schema_audit_and_fix.py *.geojson --cast-to-string FIPS,ZIP --outdir fixed/

Notes:
- Designed for GeoJSON FeatureCollections.
- Treats int/float as "number" (like JavaScript).
- Ignores nulls for type detection.
"""

import glob
import argparse
import csv
import json
import os
from collections import defaultdict

def norm_type(v):
    if v is None:
        return None
    if isinstance(v, bool):
        return "boolean"
    if isinstance(v, (int, float)) and not isinstance(v, bool):
        return "number"
    if isinstance(v, str):
        return "string"
    if isinstance(v, list):
        return "array"
    if isinstance(v, dict):
        return "object"
    return type(v).__name__

def scan_file(path, max_features=None):
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, dict) or data.get("type") != "FeatureCollection":
        raise ValueError(f"{path}: expected GeoJSON FeatureCollection")

    feats = data.get("features", [])
    field_types = defaultdict(set)

    for i, feat in enumerate(feats):
        if max_features is not None and i >= max_features:
            break
        props = (feat or {}).get("properties") or {}
        if not isinstance(props, dict):
            continue
        for k, v in props.items():
            t = norm_type(v)
            if t is not None:
                field_types[k].add(t)

    return field_types

def audit(paths, max_features=None):
    per_file = {}
    for p in paths:
        per_file[os.path.basename(p)] = scan_file(p, max_features=max_features)

    all_fields = set()
    for schema in per_file.values():
        all_fields.update(schema.keys())
    all_fields = sorted(all_fields)

    # matrix: field -> file -> set(types)
    matrix = {f: {} for f in all_fields}
    for f in all_fields:
        for fname, schema in per_file.items():
            matrix[f][fname] = schema.get(f, set())

    conflicts = []        # fields with multiple different non-empty type-sets
    missing = []          # fields missing (or all-null) in some files
    keep_fields = []      # present everywhere and consistent

    for f, row in matrix.items():
        missing_files = [fn for fn, ts in row.items() if not ts]
        if missing_files:
            missing.append((f, missing_files))

        non_empty = {tuple(sorted(ts)) for ts in row.values() if ts}
        if len(non_empty) > 1:
            conflicts.append((f, row))
        else:
            if not missing_files and len(non_empty) == 1:
                keep_fields.append(f)

    return per_file, matrix, conflicts, missing, keep_fields

def cast_value(v, mode):
    if v is None:
        return None
    if mode == "string":
        # Preserve booleans as "true/false"? up to you; here we stringify everything.
        return str(v)
    if mode == "number":
        # Try to coerce strings like "12.3" to float; integers stay int if clean.
        if isinstance(v, (int, float)) and not isinstance(v, bool):
            return v
        if isinstance(v, str):
            s = v.strip()
            if s == "":
                return None
            try:
                n = float(s)
                # convert 12.0 -> 12 for cleanliness
                return int(n) if n.is_integer() else n
            except ValueError:
                return None
        return None
    raise ValueError(f"Unknown cast mode: {mode}")

def write_fixed_files(paths, outdir, cast_to_string=None, cast_to_number=None):
    os.makedirs(outdir, exist_ok=True)
    cast_to_string = set([f.strip() for f in (cast_to_string or []) if f.strip()])
    cast_to_number = set([f.strip() for f in (cast_to_number or []) if f.strip()])

    if cast_to_string & cast_to_number:
        overlap = ", ".join(sorted(cast_to_string & cast_to_number))
        raise ValueError(f"Fields listed in both --cast-to-string and --cast-to-number: {overlap}")

    written = []
    for p in paths:
        with open(p, "r", encoding="utf-8") as f:
            data = json.load(f)

        if not isinstance(data, dict) or data.get("type") != "FeatureCollection":
            raise ValueError(f"{p}: expected GeoJSON FeatureCollection")

        for feat in data.get("features", []):
            props = (feat or {}).get("properties")
            if not isinstance(props, dict):
                continue
            for k in list(props.keys()):
                if k in cast_to_string:
                    props[k] = cast_value(props.get(k), "string")
                elif k in cast_to_number:
                    props[k] = cast_value(props.get(k), "number")

        out_path = os.path.join(outdir, os.path.basename(p))
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)
        written.append(out_path)

    return written

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("inputs", nargs="+", help="Input GeoJSON FeatureCollection files")
    ap.add_argument("--max-features", type=int, default=None, help="Limit scan to first N features per file")
    ap.add_argument("--csv", default=None, help="Write field-by-file type matrix to CSV")
    ap.add_argument("--keep", default=None, help="Write comma-separated keep list to text file")
    ap.add_argument("--cast-to-string", default=None, help="Comma-separated fields to cast to string in output copies")
    ap.add_argument("--cast-to-number", default=None, help="Comma-separated fields to cast to number in output copies")
    ap.add_argument("--outdir", default=None, help="If set, write fixed copies to this folder")
    args = ap.parse_args()

    # Expand wildcards like *.geojson (PowerShell/VS Code often pass these literally)
    expanded = []
    for pat in args.inputs:
        matches = glob.glob(pat)
        if matches:
            expanded.extend(matches)
        else:
            expanded.append(pat)
    args.inputs = expanded

    if not args.inputs:
        raise SystemExit("No input files found. Check your path or pattern (e.g., *.geojson).")


    per_file, matrix, conflicts, missing, keep_fields = audit(args.inputs, max_features=args.max_features)
    files = [os.path.basename(p) for p in args.inputs]

    print(f"\nScanned {len(files)} GeoJSON files.")
    print(f"Unique fields across all files: {len(matrix)}")
    print(f"Fields missing/all-null in ≥1 file: {len(missing)}")
    print(f"Fields with type conflicts: {len(conflicts)}")
    print(f"Fields safe to keep (present everywhere + consistent): {len(keep_fields)}")

    if conflicts:
        print("\nType conflicts (field: types -> files):")
        for field, row in conflicts[:100]:
            buckets = defaultdict(list)
            for fn, ts in row.items():
                if ts:
                    buckets["|".join(sorted(ts))].append(fn)
                else:
                    buckets["(missing/all-null)"].append(fn)
            bucket_str = " ; ".join([f"{t}: {len(fns)} file(s)" for t, fns in buckets.items()])
            print(f"  - {field}: {bucket_str}")
        if len(conflicts) > 100:
            print(f"  ... ({len(conflicts)-100} more)")

    if args.csv:
        with open(args.csv, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["field"] + files)
            for field, row in matrix.items():
                w.writerow([field] + [
                    "" if not row.get(fn) else "|".join(sorted(row[fn]))
                    for fn in files
                ])
        print(f"\nWrote CSV report to: {args.csv}")

    if args.keep:
        with open(args.keep, "w", encoding="utf-8") as f:
            f.write(",".join(keep_fields))
        print(f"Wrote keep-fields list to: {args.keep}")

    # Optional fix outputs
    if args.outdir:
        cast_str = args.cast_to_string.split(",") if args.cast_to_string else []
        cast_num = args.cast_to_number.split(",") if args.cast_to_number else []
        written = write_fixed_files(args.inputs, args.outdir, cast_to_string=cast_str, cast_to_number=cast_num)
        print(f"\nWrote {len(written)} fixed files to: {args.outdir}")

if __name__ == "__main__":
    main()
