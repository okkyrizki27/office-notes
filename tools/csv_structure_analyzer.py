"""
CSV Structure Analyzer
Reads CSV files, detects when structure changed, and maps old columns to new columns
based on both column names AND data content analysis.

Usage:
    python csv_structure_analyzer.py --files file1.csv file2.csv file3.csv
    python csv_structure_analyzer.py --dir ./data --pattern "*.csv"
    python csv_structure_analyzer.py --single large_file.csv --date-col tanggal
"""

import argparse
import os
import re
import csv
import json
from pathlib import Path
from collections import defaultdict, Counter
from datetime import datetime
from difflib import SequenceMatcher
import statistics


# ─────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────

DELIMITER = ";"          # per project convention
ENCODING  = "utf-8-sig"  # handles BOM from Excel exports
SAMPLE_ROWS = 200        # rows per column for data fingerprinting
SIMILARITY_THRESHOLD = 0.55  # minimum score to consider a column match


# ─────────────────────────────────────────────
# CSV READER
# ─────────────────────────────────────────────

def read_csv(path: str) -> tuple[list[str], list[dict]]:
    """Return (headers, rows) from a CSV file."""
    path = Path(path)
    # Try multiple encodings
    for enc in [ENCODING, "utf-8", "latin-1", "cp1252"]:
        try:
            with open(path, newline="", encoding=enc) as f:
                reader = csv.DictReader(f, delimiter=DELIMITER)
                rows = list(reader)
                headers = reader.fieldnames or []
                return list(headers), rows
        except (UnicodeDecodeError, csv.Error):
            continue
    raise ValueError(f"Cannot read {path} with any known encoding")


# ─────────────────────────────────────────────
# DATA FINGERPRINTING
# ─────────────────────────────────────────────

def _classify_value(val: str) -> str:
    """Classify a cell value into a rough type."""
    val = val.strip()
    if not val or val in ("-", "N/A", "null", "NULL", "None", ""):
        return "null"
    # Date patterns
    if re.match(r"\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4}", val):
        return "date"
    if re.match(r"\d{4}[\/\-\.]\d{1,2}[\/\-\.]\d{1,2}", val):
        return "date"
    # Pure number
    cleaned = val.replace(".", "").replace(",", "").replace(" ", "")
    if re.match(r"^-?\d+$", cleaned):
        return "integer"
    if re.match(r"^-?\d+[.,]\d+$", val.replace(" ", "")):
        return "float"
    # Boolean-like
    if val.lower() in ("true", "false", "ya", "tidak", "yes", "no", "1", "0"):
        return "boolean"
    # ID-like: alphanumeric with fixed structure
    if re.match(r"^[A-Z0-9\-_/]{3,20}$", val):
        return "id"
    return "text"


def fingerprint_column(values: list[str]) -> dict:
    """Build a statistical fingerprint of a column's data."""
    sample = [v for v in values if v and v.strip()][:SAMPLE_ROWS]
    if not sample:
        return {"type_dist": {}, "null_ratio": 1.0, "uniqueness": 0.0,
                "avg_len": 0, "top_values": [], "numeric_stats": None}

    types = Counter(_classify_value(v) for v in sample)
    total = len(sample)
    null_count = sum(1 for v in values if not v or not v.strip())

    # Uniqueness ratio
    uniqueness = len(set(sample)) / total if total else 0

    # Average string length
    avg_len = statistics.mean(len(v) for v in sample) if sample else 0

    # Top values (for low-cardinality columns)
    value_counts = Counter(v.strip() for v in sample)
    top_values = [v for v, _ in value_counts.most_common(10)]

    # Numeric stats if mostly numbers
    num_vals = []
    for v in sample:
        try:
            num_vals.append(float(v.replace(",", ".").replace(" ", "")))
        except ValueError:
            pass

    numeric_stats = None
    if len(num_vals) / total > 0.7:
        numeric_stats = {
            "mean":   statistics.mean(num_vals),
            "stdev":  statistics.stdev(num_vals) if len(num_vals) > 1 else 0,
            "min":    min(num_vals),
            "max":    max(num_vals),
        }

    return {
        "type_dist":    {t: c / total for t, c in types.items()},
        "null_ratio":   null_count / len(values) if values else 1.0,
        "uniqueness":   uniqueness,
        "avg_len":      avg_len,
        "top_values":   top_values,
        "numeric_stats": numeric_stats,
    }


# ─────────────────────────────────────────────
# COLUMN SIMILARITY SCORING
# ─────────────────────────────────────────────

def _name_similarity(a: str, b: str) -> float:
    """Fuzzy name similarity between two column names."""
    a, b = a.lower().strip(), b.lower().strip()
    if a == b:
        return 1.0
    # Remove common noise
    noise = re.compile(r"[\s_\-\.]+")
    a_clean = noise.sub("", a)
    b_clean = noise.sub("", b)
    if a_clean == b_clean:
        return 0.95
    return SequenceMatcher(None, a_clean, b_clean).ratio()


def _type_similarity(fp_a: dict, fp_b: dict) -> float:
    """How similar are the type distributions of two columns."""
    types = set(fp_a["type_dist"]) | set(fp_b["type_dist"])
    if not types:
        return 0.5
    score = 0.0
    for t in types:
        score += 1 - abs(fp_a["type_dist"].get(t, 0) - fp_b["type_dist"].get(t, 0))
    return score / len(types)


def _value_overlap(fp_a: dict, fp_b: dict) -> float:
    """Overlap of top values between two columns (catches renamed enum columns)."""
    a_vals = set(fp_a["top_values"])
    b_vals = set(fp_b["top_values"])
    if not a_vals or not b_vals:
        return 0.0
    intersection = a_vals & b_vals
    union = a_vals | b_vals
    return len(intersection) / len(union)


def _numeric_similarity(fp_a: dict, fp_b: dict) -> float:
    """For numeric columns: how close are their distributions."""
    a, b = fp_a.get("numeric_stats"), fp_b.get("numeric_stats")
    if not a or not b:
        return 0.0
    # Normalize mean difference by max of the two
    max_mean = max(abs(a["mean"]), abs(b["mean"]), 1e-9)
    mean_sim = 1 - min(abs(a["mean"] - b["mean"]) / max_mean, 1)
    # Range overlap
    range_sim = 1 - min(
        abs(a["max"] - b["max"]) / (max(abs(a["max"]), abs(b["max"]), 1e-9)), 1
    )
    return (mean_sim + range_sim) / 2


def column_similarity(
    name_a: str, fp_a: dict,
    name_b: str, fp_b: dict,
) -> tuple[float, dict]:
    """Combined similarity score and breakdown between two columns."""
    name_score    = _name_similarity(name_a, name_b)
    type_score    = _type_similarity(fp_a, fp_b)
    value_score   = _value_overlap(fp_a, fp_b)
    numeric_score = _numeric_similarity(fp_a, fp_b)

    # Structural signals
    len_sim = 1 - abs(fp_a["avg_len"] - fp_b["avg_len"]) / max(
        fp_a["avg_len"], fp_b["avg_len"], 1
    )
    uniq_sim = 1 - abs(fp_a["uniqueness"] - fp_b["uniqueness"])

    # Weighted combination
    weights = {
        "name":    0.30,
        "type":    0.20,
        "value":   0.25,
        "numeric": 0.10,
        "length":  0.08,
        "uniq":    0.07,
    }
    breakdown = {
        "name":    round(name_score,    3),
        "type":    round(type_score,    3),
        "value":   round(value_score,   3),
        "numeric": round(numeric_score, 3),
        "length":  round(len_sim,       3),
        "uniq":    round(uniq_sim,      3),
    }
    total = sum(weights[k] * breakdown[k] for k in weights)
    return round(total, 4), breakdown


# ─────────────────────────────────────────────
# STRUCTURE SNAPSHOT
# ─────────────────────────────────────────────

class StructureSnapshot:
    """Represents the column structure + fingerprints of one CSV (or one time-window)."""

    def __init__(self, label: str, headers: list[str], rows: list[dict]):
        self.label = label
        self.headers = headers
        self.fingerprints: dict[str, dict] = {}
        for col in headers:
            vals = [r.get(col, "") or "" for r in rows]
            self.fingerprints[col] = fingerprint_column(vals)

    def __repr__(self):
        return f"<Snapshot '{self.label}' cols={self.headers}>"


# ─────────────────────────────────────────────
# CHANGE DETECTION
# ─────────────────────────────────────────────

def detect_structure_changes(snapshots: list[StructureSnapshot]) -> list[dict]:
    """
    Compare consecutive snapshots and detect column additions,
    removals, renames, and type changes.
    Returns a list of change events.
    """
    events = []
    for i in range(1, len(snapshots)):
        prev = snapshots[i - 1]
        curr = snapshots[i]

        prev_cols = set(prev.headers)
        curr_cols = set(curr.headers)

        added   = curr_cols - prev_cols
        removed = prev_cols - curr_cols
        kept    = prev_cols & curr_cols

        event = {
            "from":    prev.label,
            "to":      curr.label,
            "added":   sorted(added),
            "removed": sorted(removed),
            "renames": [],          # filled below
            "type_changes": [],     # filled below
        }

        # Try to match removed → added as renames using similarity
        unmatched_removed = list(removed)
        unmatched_added   = list(added)
        rename_candidates = []

        for r_col in unmatched_removed:
            for a_col in unmatched_added:
                score, breakdown = column_similarity(
                    r_col, prev.fingerprints[r_col],
                    a_col, curr.fingerprints[a_col],
                )
                if score >= SIMILARITY_THRESHOLD:
                    rename_candidates.append((score, r_col, a_col, breakdown))

        # Greedy best-match assignment
        rename_candidates.sort(reverse=True)
        used_removed, used_added = set(), set()
        for score, r_col, a_col, breakdown in rename_candidates:
            if r_col in used_removed or a_col in used_added:
                continue
            event["renames"].append({
                "old": r_col, "new": a_col,
                "score": score, "breakdown": breakdown,
            })
            used_removed.add(r_col)
            used_added.add(a_col)

        # Refine: remove confirmed renames from added/removed lists
        confirmed_old = {r["old"] for r in event["renames"]}
        confirmed_new = {r["new"] for r in event["renames"]}
        event["added"]   = [c for c in event["added"]   if c not in confirmed_new]
        event["removed"] = [c for c in event["removed"] if c not in confirmed_old]

        # Detect type changes in kept columns
        for col in sorted(kept):
            prev_fp = prev.fingerprints[col]
            curr_fp = curr.fingerprints[col]
            type_sim = _type_similarity(prev_fp, curr_fp)
            if type_sim < 0.7:
                prev_dominant = max(prev_fp["type_dist"], key=prev_fp["type_dist"].get, default="?")
                curr_dominant = max(curr_fp["type_dist"], key=curr_fp["type_dist"].get, default="?")
                if prev_dominant != curr_dominant:
                    event["type_changes"].append({
                        "col":      col,
                        "from_type": prev_dominant,
                        "to_type":   curr_dominant,
                        "similarity": round(type_sim, 3),
                    })

        events.append(event)
    return events


# ─────────────────────────────────────────────
# FULL MAPPING REPORT
# ─────────────────────────────────────────────

def build_full_mapping(
    snapshots: list[StructureSnapshot],
) -> dict[str, list[tuple[str, float, dict]]]:
    """
    For the LATEST snapshot, map every column back to the oldest snapshot it came from.
    Returns { current_col: [(old_col, score, breakdown), ...] }
    """
    if len(snapshots) < 2:
        return {}

    first = snapshots[0]
    last  = snapshots[-1]

    mapping = {}
    for curr_col in last.headers:
        candidates = []
        for old_col in first.headers:
            score, breakdown = column_similarity(
                old_col, first.fingerprints[old_col],
                curr_col, last.fingerprints[curr_col],
            )
            candidates.append((old_col, score, breakdown))
        candidates.sort(key=lambda x: x[1], reverse=True)
        mapping[curr_col] = candidates[:3]  # top 3 guesses
    return mapping


# ─────────────────────────────────────────────
# SINGLE-FILE TIME SERIES MODE
# ─────────────────────────────────────────────

def split_by_date(
    headers: list[str],
    rows: list[dict],
    date_col: str,
    freq: str = "month",
) -> list[tuple[str, list[dict]]]:
    """
    Split a single CSV into time windows by date column.
    freq: 'month' | 'quarter' | 'year'
    """
    buckets = defaultdict(list)
    for row in rows:
        raw = row.get(date_col, "") or ""
        # Try to parse a date
        dt = None
        for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%m/%d/%Y", "%Y/%m/%d"):
            try:
                dt = datetime.strptime(raw.strip(), fmt)
                break
            except ValueError:
                continue
        if dt is None:
            continue
        if freq == "month":
            key = dt.strftime("%Y-%m")
        elif freq == "quarter":
            q = (dt.month - 1) // 3 + 1
            key = f"{dt.year}-Q{q}"
        else:
            key = str(dt.year)
        buckets[key].append(row)

    return sorted(buckets.items())


# ─────────────────────────────────────────────
# OUTPUT FORMATTING
# ─────────────────────────────────────────────

def _bar(score: float, width: int = 20) -> str:
    filled = int(score * width)
    return "█" * filled + "░" * (width - filled)


def print_report(
    snapshots: list[StructureSnapshot],
    events: list[dict],
    full_mapping: dict,
):
    sep = "=" * 70

    print(f"\n{sep}")
    print("  CSV STRUCTURE ANALYSIS REPORT")
    print(f"  Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(sep)

    # ── Snapshots summary ──
    print("\n[ SNAPSHOTS ]\n")
    for s in snapshots:
        print(f"  {s.label:30s}  {len(s.headers)} columns")

    # ── Change timeline ──
    print(f"\n{sep}")
    print("[ CHANGE TIMELINE ]\n")

    any_change = False
    for ev in events:
        changes = ev["added"] or ev["removed"] or ev["renames"] or ev["type_changes"]
        if not changes:
            print(f"  {ev['from']} → {ev['to']}  (no structural change)")
            continue
        any_change = True
        print(f"\n  ┌─ {ev['from']} → {ev['to']}")

        if ev["added"]:
            print(f"  │  ➕ ADDED   : {', '.join(ev['added'])}")
        if ev["removed"]:
            print(f"  │  ➖ REMOVED : {', '.join(ev['removed'])}")
        if ev["renames"]:
            for r in ev["renames"]:
                bar = _bar(r["score"])
                print(f"  │  🔄 RENAME  : '{r['old']}' → '{r['new']}'  [{bar}] {r['score']:.2f}")
                bd = r["breakdown"]
                print(f"  │             name={bd['name']:.2f} type={bd['type']:.2f} "
                      f"values={bd['value']:.2f} numeric={bd['numeric']:.2f}")
        if ev["type_changes"]:
            for tc in ev["type_changes"]:
                print(f"  │  ⚠️  TYPE CHG: '{tc['col']}' {tc['from_type']} → {tc['to_type']}")
        print(f"  └{'─'*50}")

    if not any_change:
        print("  No structural changes detected across all snapshots.")

    # ── Full mapping (first → last) ──
    if full_mapping and len(snapshots) > 1:
        print(f"\n{sep}")
        print(f"[ COLUMN MAPPING: '{snapshots[0].label}' → '{snapshots[-1].label}' ]\n")
        print(f"  {'CURRENT COLUMN':<30} {'BEST MATCH (OLD)':<30} SCORE")
        print(f"  {'─'*30} {'─'*30} {'─'*20}")

        for curr_col, candidates in full_mapping.items():
            if candidates:
                best_old, best_score, _ = candidates[0]
                bar = _bar(best_score)
                label = best_old if best_score >= SIMILARITY_THRESHOLD else "(new / no match)"
                print(f"  {curr_col:<30} {label:<30} [{bar}] {best_score:.2f}")
            else:
                print(f"  {curr_col:<30} {'(no data)':<30}")

    print(f"\n{sep}\n")


def export_json(
    snapshots: list[StructureSnapshot],
    events: list[dict],
    full_mapping: dict,
    output_path: str,
):
    data = {
        "generated": datetime.now().isoformat(),
        "snapshots": [
            {"label": s.label, "columns": s.headers} for s in snapshots
        ],
        "change_events": events,
        "full_mapping": {
            col: [
                {"old_col": old, "score": score, "breakdown": bd}
                for old, score, bd in candidates
            ]
            for col, candidates in full_mapping.items()
        },
    }
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"JSON report saved → {output_path}")


# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Analyze CSV structure changes across files or time."
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--files", nargs="+", metavar="FILE",
        help="Two or more CSV files to compare in order (oldest first).",
    )
    group.add_argument(
        "--dir", metavar="DIR",
        help="Directory containing CSV files (compared in filename order).",
    )
    group.add_argument(
        "--single", metavar="FILE",
        help="Single CSV with a date column; split into time windows for analysis.",
    )
    parser.add_argument(
        "--pattern", default="*.csv",
        help="Glob pattern when using --dir (default: *.csv).",
    )
    parser.add_argument(
        "--date-col", metavar="COL",
        help="Date column name for --single mode.",
    )
    parser.add_argument(
        "--freq", choices=["month", "quarter", "year"], default="month",
        help="Time window for --single mode (default: month).",
    )
    parser.add_argument(
        "--delimiter", default=DELIMITER,
        help=f"CSV delimiter (default: '{DELIMITER}').",
    )
    parser.add_argument(
        "--threshold", type=float, default=SIMILARITY_THRESHOLD,
        help=f"Minimum similarity score to treat as rename (default: {SIMILARITY_THRESHOLD}).",
    )
    parser.add_argument(
        "--export-json", metavar="PATH",
        help="Export full analysis to a JSON file.",
    )

    args = parser.parse_args()

    global DELIMITER, SIMILARITY_THRESHOLD
    DELIMITER = args.delimiter
    SIMILARITY_THRESHOLD = args.threshold

    snapshots: list[StructureSnapshot] = []

    # ── Load data ──
    if args.files:
        for fp in args.files:
            print(f"Reading {fp} ...")
            headers, rows = read_csv(fp)
            label = Path(fp).stem
            snapshots.append(StructureSnapshot(label, headers, rows))

    elif args.dir:
        files = sorted(Path(args.dir).glob(args.pattern))
        if not files:
            print(f"No files matching '{args.pattern}' in {args.dir}")
            return
        for fp in files:
            print(f"Reading {fp} ...")
            headers, rows = read_csv(str(fp))
            snapshots.append(StructureSnapshot(fp.stem, headers, rows))

    elif args.single:
        if not args.date_col:
            parser.error("--single requires --date-col")
        print(f"Reading {args.single} ...")
        headers, rows = read_csv(args.single)
        windows = split_by_date(headers, rows, args.date_col, args.freq)
        if not windows:
            print("No parseable dates found in date column.")
            return
        print(f"Found {len(windows)} time windows.")
        for label, window_rows in windows:
            snapshots.append(StructureSnapshot(label, headers, window_rows))

    if len(snapshots) < 2:
        print("Need at least 2 snapshots to compare. Nothing to do.")
        return

    # ── Analyze ──
    print("\nAnalyzing structure changes...")
    events = detect_structure_changes(snapshots)

    print("Building full column mapping (first → last)...")
    full_mapping = build_full_mapping(snapshots)

    # ── Report ──
    print_report(snapshots, events, full_mapping)

    if args.export_json:
        export_json(snapshots, events, full_mapping, args.export_json)


if __name__ == "__main__":
    main()
