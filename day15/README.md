# FAULTLINE — Day 15: Q2 — detection accuracy per fault

Measure per-fault precision, recall, and confusion against injection truth — and
refuse to let any false positive or false negative hide behind an aggregate. Every
class gets its own confusion matrix and Wilson interval; every miss gets a trace.

> **Fail condition:** false positives or false negatives are hidden by aggregate
> metrics.
> **Status: not triggered** — results are reported per class with intervals; a
> reconciliation proves every FP/FN appears in the failure list (nothing averaged
> away); and each failing sample is investigated trace by trace in
> `evidence/q2_failures.json` and `evidence/traces/`. See [CHECKPOINT-15.md](CHECKPOINT-15.md).

## The one idea

An aggregate accuracy is a comfortable lie: pool F4/F6 (recall 1.0) with F2 (0.33)
and you get a middling number that describes none of them. Q2 answers the Day-11
split hypothesis with real, held-out measurement — per class, with uncertainty —
and shows exactly which faults are missed and why.

## What's here

```
faultline_q2/
  q2.py         run all detectors over the Day-13 labelled set; per-class confusion
                + Wilson CIs (Day 14); deterministic vs semantic groups; no-hiding
                reconciliation (micro vs macro; every FP/FN accounted)
  investigate.py trace_sample + collect_failures: a Day-4 trace for every FP/FN
  tables.py     render the Q2 markdown tables with links to failing examples
scripts/ make_evidence.py
tests/   test_q2.py  (8 tests)
evidence/
  q2_results.json q2_failures.json Q2_FINDINGS.md traces/<id>.json
CHECKPOINT-15.md · LEARN-imbalanced-metrics.md · DECISIONS.md · REFLECTION.md
```

## Quickstart

```
python -m pytest tests/ -q       # 8 tests
python scripts/make_evidence.py  # regenerate Q2 tables, failures, traces (byte-reproducible)
```

Standard library only. Consumes Day 13 (dataset + predictions), Day 14 (intervals),
Day 11 (det/sem groups), Day 4 (traces). Detectors are fixed/untrained, so the
headline evaluates the full labelled set (n=44); the held-out test split is also
reported and agrees.

## Q2 result (dataset `de5068d574cae9fd`, full labelled set, n=44)

| Fault | TP | FP | FN | TN | recall | recall 95% CI |
|---|---|---|---|---|---|---|
| F1 | 4 | 0 | 2 | 3 | 0.667 | [0.30, 0.90] |
| F2 | 2 | 0 | 4 | 3 | 0.333 | [0.10, 0.70] |
| F3 | 2 | 0 | 2 | 3 | 0.500 | [0.15, 0.85] |
| F4 | 2 | 0 | 0 | 3 | 1.000 | [0.34, 1.00] |
| F5 | 2 | 0 | 2 | 3 | 0.500 | [0.15, 0.85] |
| F6 | 4 | 0 | 0 | 3 | 1.000 | [0.51, 1.00] |

- **Precision is 1.0 in every class — zero false positives.**
- **10 false negatives, of two kinds:** 4 **irreducible semantic escapes**
  (F3 `drift_value`, F5 `context_drift` — structurally identical to correct
  outputs) and 6 **threshold-reducible** (low-severity F1/F2 below the schema
  range / latency budget — caught by tightening the threshold).
- **micro recall 0.615 vs macro recall 0.667** — the gap is the fingerprint of the
  per-class imbalance the aggregate would hide.

## What the aggregate hides (the fail condition, refused)

`no_hiding` in `q2_results.json` reconciles the tables: total FP + FN across classes
equals the number of failing examples listed, so nothing is averaged away. Each of
those examples is in `q2_failures.json` with its `why` and a Day-4 trace under
`evidence/traces/` — a reviewer can open the exact run behind every miss.

## Mastery map

- **Explain** → [LEARN-imbalanced-metrics.md](LEARN-imbalanced-metrics.md)
- **Build** → `faultline_q2/` (per-class confusion, groups, intervals)
- **Debug** → `evidence/traces/*.json` (one trace per FP/FN) + `q2_failures.json`
- **Measure** → `evidence/q2_results.json` (per class, with Wilson CIs)
- **Defend** → [DECISIONS.md](DECISIONS.md), [CHECKPOINT-15.md](CHECKPOINT-15.md)
