# CourseSAT performance experiments

Experiment log for the reproducible performance work.  Every number below
comes from a real run on this machine; nothing is estimated.

## 1. Environment

| item | value |
|---|---|
| OS | Ubuntu 24.04 on WSL2, kernel 6.6.87.2-microsoft-standard-WSL2, x86_64 |
| CPU | 32 logical cores, single solver thread per run |
| compiler | g++ (Ubuntu 13.3.0-6ubuntu2~24.04.1) 13.3.0 |
| build system | GNU make 4.3, `./configure --competition` |
| python | 3.12.3 |
| source version | `VERSION = course-2026` |

The tree is a renamed CaDiCaL (namespace `CourseSAT`, `cadical` ->
`coursesat`), not Kissat: 155 source files are byte-identical to upstream
CaDiCaL master after normalising the rename.  Only `src/kitten.c` comes from
Kissat.  So the restart implementation to analyse is CaDiCaL's
`src/restart.cpp`, not Kissat's `restart.c`.

## 2. Builds

Timing build (identical to the grader):

```
./configure --competition && make -j8
# FLAGS: -Wall -Wextra -O3 -DNDEBUG -DQUIET -DNCONTRACTS -DNTRACING -DNCONTRIB
```

Statistics build of the *same source* (only `-DQUIET` omitted, because
CaDiCaL prints statistics only when `QUIET` is undefined):

```
mkdir /tmp/base-stats && cp -a src scripts test contrib configure makefile.in VERSION /tmp/base-stats/
cd /tmp/base-stats && ./configure && make -j8
# FLAGS: -Wall -Wextra -O3 -DNDEBUG
```

The statistics build is used only to read decisions/conflicts/propagations/
restarts/peak RSS.  All timings come from the official `--competition` build.

## 3. Test set and protocol

- Performance instances: `test/performance/public-01..08.cnf`
  (`manifest.json` gives the expected SAT/UNSAT result).
- Correctness suite: `test/cnf/case-001..085.cnf` (85 cases x 4 variants:
  `--check`, DRAT, LRAT, simplify+extend) plus the 4 `regressions/` files.
- Command: `build/coursesat <input.cnf> <proof.out>` (the official command,
  no extra options for the measured versions).
- Limit: 15 s per instance (public limit; the private evaluation uses 180 s).
- Repeats: 3 per instance, median reported; the best run is kept in the CSV.
- Exit codes: 10 = SAT, 20 = UNSAT, anything else is UNKNOWN/error.
- PAR-2 = sum of median times of solved instances + 2 x 15 s per unsolved
  instance.
- Seed: the solver is deterministic with its default seed (0); repeated runs
  confirm this.

## 4. Versions

| version | source state | change |
|---|---|---|
| `baseline` | commit `09481d3` | only the Part 1 `backtrack.cpp` correctness fix, original option defaults |
| `candidate_h1` | baseline | `--restartmarginfocused=15` (default 10) |
| `candidate_h2` | baseline + this commit | `probe=0` (default 1), `src/options.hpp` |

## 5. Results (15 s limit, 3 repeats, median)

| instance | baseline | candidate_h1 | candidate_h2 |
|---|---:|---:|---:|
| public-01.cnf | 0.623 s | 0.844 s | 0.598 s |
| public-02.cnf | 1.721 s | 1.669 s | 1.675 s |
| public-03.cnf | 2.173 s | 2.101 s | 2.121 s |
| public-04.cnf | 0.707 s | 0.603 s | 0.570 s |
| public-05.cnf | 6.593 s | 6.585 s | **5.593 s** |
| public-06.cnf | 0.030 s | 0.029 s | 0.017 s |
| public-07.cnf | 14.065 s | **timeout** | **4.897 s** |
| public-08.cnf | timeout | timeout | timeout |
| **solved** | **7/8** | 6/8 | **7/8** |
| **PAR-2** | **55.912 s** | 71.831 s | **45.471 s** |

Official `make public_test` (single run) with `candidate_h2`:
`Public performance: 7/8, PAR-2=45.824s`.

Counters for the baseline (statistics build, see `baseline.csv`):

| instance | decisions | conflicts | propagations | restarts |
|---|---:|---:|---:|---:|
| public-01 | 29254 | 15235 | 1207970 | 316 |
| public-02 | 74745 | 28015 | 3539508 | 492 |
| public-03 | 109820 | 28019 | 4711593 | 612 |
| public-04 | 59776 | 51727 | 656132 | 1667 |
| public-05 | 427834 | 370842 | 4822164 | 13361 |
| public-07 | 1117378 | 873090 | 2640411 | 31910 |

## 6. Correctness

- `make part1_test` on the final tree: `282 ok, 0 failed`;
  `public CDCL regressions: 4 ok, 0 failed`.
- That suite independently validates SAT models (`dimocheck`), DRAT proofs
  (`drat-trim`) and LRAT proofs (`lrat-trim`) for every case.
- Every solved performance instance reports the expected SAT/UNSAT result.
- `public-08` is unsolved in all versions; a separate long run of the
  baseline needed more than 830 s, so it is out of reach of the 180 s limit.

## 7. Conclusions

- **H1 rejected.** Raising the focused restart margin from 10 % to 15 % made
  public-07 exceed the 15 s limit, dropping the score to 6/8 and PAR-2 71.83 s.
  Reverted.
- **H2 accepted.** Disabling failed-literal probing (`probe=0`) keeps all
  correctness tests green and reduces PAR-2 from 55.91 s to 45.47 s (-18.7 %),
  with public-07 14.07 s -> 4.90 s and public-05 6.59 s -> 5.59 s.  No
  instance became slower outside run-to-run noise.

The restart direction was investigated first as requested; the measurements
show it is highly sensitive here (a 5-point margin change flips an instance
from solved to timeout), while probing was the actual dead weight on these
structured instances.

## 8. Reproduction

```
python3 experiments/measure.py --label baseline \
    --out experiments/baseline.csv \
    --stats-binary /tmp/base-stats/build/coursesat \
    --limit 15 --repeats 3

python3 experiments/measure.py --label candidate_h1_rmf15 \
    --out experiments/candidate_h1.csv \
    --stats-binary /tmp/base-stats/build/coursesat \
    --limit 15 --repeats 3 --opts=--restartmarginfocused=15

python3 experiments/measure.py --label candidate_h2_probe0 \
    --out experiments/candidate_h2.csv \
    --stats-binary /tmp/base-stats/build/coursesat \
    --limit 15 --repeats 3 --opts=--probe=0

python3 experiments/summarize.py experiments/baseline.csv \
    experiments/candidate_h1.csv experiments/candidate_h2.csv
```
