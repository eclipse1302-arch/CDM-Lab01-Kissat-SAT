#!/usr/bin/env python3
"""Reproducible timing + statistics harness for the CourseSAT lab.

Timing uses the official build (configure --competition, same flags as the
grader).  Counters (decisions/conflicts/propagations/restarts/memory) come
from a second build of the *same source* that only differs by omitting
-DQUIET, because CaDiCaL prints statistics only when QUIET is undefined.

usage:
  measure.py --label baseline --out experiments/baseline.csv \
             --stats-binary /tmp/base-stats/build/coursesat
"""
import argparse
import csv
import json
import os
import re
import signal
import statistics
import subprocess
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PERF = ROOT / "test" / "performance"


def run(binary, cnf, limit, proof, extra):
    started = time.monotonic()
    with open(os.devnull, "wb") as null:
        p = subprocess.Popen([str(binary), str(cnf), str(proof), *extra],
                             stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                             start_new_session=True)
        timed_out = False
        try:
            out, _ = p.communicate(timeout=limit)
        except subprocess.TimeoutExpired:
            timed_out = True
            os.killpg(p.pid, signal.SIGKILL)
            out, _ = p.communicate()
    elapsed = min(time.monotonic() - started, limit)
    return p.returncode, elapsed, timed_out, out.decode("utf-8", "replace")


def parse_stats(text):
    def grab(pattern):
        m = re.search(pattern, text, re.MULTILINE)
        return int(m.group(1)) if m else ""

    return {
        "decisions": grab(r"^c decisions:\s+(\d+)"),
        "conflicts": grab(r"^c conflicts:\s+(\d+)"),
        "propagations": grab(r"^c propagations:\s+(\d+)"),
        "restarts": grab(r"^c restarts:\s+(\d+)"),
        "process_time": grab(r"^c total process time since initialization:\s+(\d+)"),
        "peak_memory_mb": grab(r"^c maximum resident set size of process:\s+(\d+)"),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--label", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--binary", default=str(ROOT / "build" / "coursesat"))
    ap.add_argument("--stats-binary", default="")
    ap.add_argument("--limit", type=float, default=15.0)
    ap.add_argument("--repeats", type=int, default=3)
    ap.add_argument("--opts", default="",
                    help="extra solver options, space separated")
    args = ap.parse_args()
    extra = args.opts.split()

    manifest = json.loads((PERF / "manifest.json").read_text())
    rows = []
    par2 = 0.0
    solved = 0
    proof = Path("/tmp/measure-proof.out")

    for entry in manifest:
        cnf = PERF / entry["file"]
        runs = []
        for _ in range(args.repeats):
            rc, elapsed, timed_out, out = run(args.binary, cnf, args.limit,
                                              proof, extra)
            runs.append((rc, elapsed, timed_out, out))
        ok = [r for r in runs if not r[2] and r[0] in (10, 20)]

        if ok:
            solved += 1
            times = sorted(r[1] for r in ok)
            median = statistics.median(times)
            best = times[0]
            par2 += median
            rc = ok[0][0]
            result = "SAT" if rc == 10 else "UNSAT"
            status = "ok"
        else:
            median = best = args.limit
            par2 += 2 * args.limit
            result = "UNKNOWN"
            status = "timeout" if any(r[2] for r in runs) else "error"

        stats = {k: "" for k in
                 ("decisions", "conflicts", "propagations", "restarts",
                  "process_time", "peak_memory_mb")}
        if args.stats_binary and ok:
            _, _, _, text = run(args.stats_binary, cnf, args.limit * 4, proof,
                                extra + ["--stats"])
            stats = parse_stats(text)

        rows.append({
            "version": args.label,
            "instance": entry["file"],
            "expected": entry["expected"],
            "result": result,
            "status": status,
            "time_median_sec": f"{median:.3f}",
            "time_best_sec": f"{best:.3f}",
            "repeats": len(ok) if ok else 0,
            "decisions": stats["decisions"],
            "conflicts": stats["conflicts"],
            "propagations": stats["propagations"],
            "restarts": stats["restarts"],
            "peak_memory_mb": stats["peak_memory_mb"],
            "seed": 0,
        })
        print(f"{entry['file']:<16} {status:<8} median {median:6.2f}s "
              f"best {best:6.2f}s", flush=True)

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(f"{args.label}: solved {solved}/{len(manifest)}  PAR-2 {par2:.3f}s")
    print(f"written {out}")


if __name__ == "__main__":
    main()
