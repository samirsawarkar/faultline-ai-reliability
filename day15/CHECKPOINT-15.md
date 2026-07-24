# CHECKPOINT-15 — Q2: detection accuracy per fault

**Mission.** Measure per-fault precision, recall and confusion against injection
truth.

**Fail condition.** False positives or false negatives are hidden by aggregate
metrics. — **Not triggered.**

## What was built

A per-class measurement of the F1–F6 detectors over the Day-13 labelled set:

- **Per-class confusion matrices** with 95% Wilson intervals on recall and precision.
- **Deterministic {F2, F4, F6} vs semantic {F1, F3, F5} groups** with interval bands.
- **A no-hiding reconciliation**: total FP + FN across classes equals the failure
  list length; every miss is enumerated and traced.
- **An FN taxonomy**: irreducible semantic escapes vs threshold-reducible misses.

8 tests gate it; four evidence artifacts (plus 10 per-failure traces) prove it.

## Q2 result (dataset `de5068d574cae9fd`, full labelled set, n=44)

| Fault | TP | FP | FN | TN | recall | 95% CI |
|---|---|---|---|---|---|---|
| F1 | 4 | 0 | 2 | 3 | 0.667 | [0.30, 0.90] |
| F2 | 2 | 0 | 4 | 3 | 0.333 | [0.10, 0.70] |
| F3 | 2 | 0 | 2 | 3 | 0.500 | [0.15, 0.85] |
| F4 | 2 | 0 | 0 | 3 | 1.000 | [0.34, 1.00] |
| F5 | 2 | 0 | 2 | 3 | 0.500 | [0.15, 0.85] |
| F6 | 4 | 0 | 0 | 3 | 1.000 | [0.51, 1.00] |

- **Precision 1.0 in every class — zero false positives.**
- **10 false negatives = 4 irreducible semantic escapes (F3 `drift_value`,
  F5 `context_drift`) + 6 threshold-reducible (low-severity F1/F2).**
- **micro 0.615 vs macro 0.667** — the gap flags the per-class imbalance a single
  number would bury.

## Nothing hidden (`q2_results.json.no_hiding`)

`reconciled: true` — 0 FP + 10 FN = 10 failing examples listed. Each is in
`q2_failures.json` with its `why` and a Day-4 trace under `evidence/traces/`, so a
reviewer can open the exact run behind every miss. The held-out test split (n=17) is
reported alongside and agrees directionally.

## Q2 finding

Detection accuracy is **bimodal and must be read per class**. Deterministic faults
are caught with no false positives (F4/F6 at recall 1.0; F1/F2 misses are a
threshold dial). Semantic faults leave an **irreducible false-negative set** —
`drift_value` and `context_drift` are structurally identical to correct outputs and
no deterministic detector closes them. This confirms Day 11's split hypothesis on
labelled data; at n=44 the group interval bands are wide (directional), but the
undetectability of the escapes is structural, not sample-size-limited.

## Mastery gate — all five

- **Explain** — `LEARN-imbalanced-metrics.md`: why aggregates lie, micro vs macro,
  precision/recall separation, the FN taxonomy.
- **Build** — `faultline_q2/`: per-class confusion, groups, intervals, investigation.
- **Debug** — `evidence/traces/*.json`: one Day-4 trace per FP/FN, joined to `why`.
- **Measure** — `evidence/q2_results.json`: per-class confusion + Wilson CIs.
- **Defend** — `DECISIONS.md` (D15-001…D15-006); per-class first, every FP/FN
  reconciled and traced.
