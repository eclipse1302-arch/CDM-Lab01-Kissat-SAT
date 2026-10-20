#!/usr/bin/env python3
"""Print a per-instance comparison table from measure.py CSV files."""
import csv
import sys
from pathlib import Path


def load(path):
    with open(path) as f:
        return {r["instance"]: r for r in csv.DictReader(f)}


def main():
    files = sys.argv[1:]
    if not files:
        files = ["experiments/baseline.csv"]
    data = [(Path(f).stem, load(f)) for f in files]
    names = list(data[0][1])

    header = f"{'instance':<16}" + "".join(f"{n:>22}" for n, _ in data)
    print(header)
    for inst in names:
        row = f"{inst:<16}"
        for _, table in data:
            r = table.get(inst, {})
            value = r.get("time_median_sec", "")
            status = r.get("status", "")
            cell = f"{value}s {status}" if value else status
            row += f"{cell:>22}"
        print(row)

    print()
    for name, table in data:
        solved = sum(1 for r in table.values() if r["status"] == "ok")
        limit = 15.0
        par2 = sum(float(r["time_median_sec"]) if r["status"] == "ok"
                   else 2 * limit for r in table.values())
        print(f"{name:<24} solved {solved}/{len(table)}  PAR-2 {par2:8.3f}s")


if __name__ == "__main__":
    main()
