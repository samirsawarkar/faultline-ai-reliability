# CHECKPOINT-13 — evaluation harness + versioned dataset

**Mission.** Create a leakage-resistant, versioned evaluation system grounded in
the oracle.

**Fail condition.** Dataset versions, splits, or leakage controls are ambiguous. —
**Not triggered.**

## What was built

A complete evaluation system over the six-fault spectrum:

- **Versioned dataset** — content-addressed `dataset_version`; samples carry seeds,
  tiers, fault configs, and oracle-grounded labels.
- **Deterministic disjoint splits** — stratified by (modality, kind), so every
  fault kind (including the semantic escapes) is in both train and test.
- **Evaluation runner** — a frozen `EvalResult` bound to `dataset_version` +
  `code_version` + `split`, with a derived `result_id`.
- **Leakage checks** — split disjointness, label non-leakage, version binding.
- **Reproducible command** — `python day13/scripts/eval.py --split test`.

14 tests gate it; five evidence artifacts prove it.

## Unambiguous by construction

| control | mechanism | evidence |
|---|---|---|
| dataset version | sha256 of the full manifest | `manifest.json` (`de5068d574cae9fd`) |
| splits | deterministic, stratified by (modality, kind), disjoint | `splits.json` |
| labels | grounded in injection oracle, never a detector | `manifest.json` samples |
| result freshness | bound to dataset + code version | `eval_result.json` |

## The measurement (test split, dataset `de5068d574cae9fd`)

Overall recall **0.727**, precision **1.0** over 17 held-out samples. Per modality:
F1 1.0, F2 0.5 (budget-gated), F3 0.5, F4 1.0, F5 0.5, F6 1.0. The F3/F5 misses are
the semantic escapes (`drift_value`, `context_drift`) on held-out data —
reproducing the Q2 split honestly, not hiding it.

## Attack — PASSED (`leakage_report.json`)

- **train/test contamination** — copying a test sample into train is caught
  (`detected_after: true`, leaked id reported); the clean baseline is clean.
- **stale-result reuse** — a result computed on dataset v1, reused against a changed
  v2 (`versions_differ: true`), is rejected as `stale` (`stale_reuse_blocked: true`);
  the same result is `fresh` against v1.
- **label non-leakage** — the detector receives only injection config; the expected
  label is never an input.
- **split disjoint** — train ∩ test = ∅.

## Mastery gate — all five

- **Explain** — `LEARN-eval-infra.md`: trust is a property of the plumbing (held-out
  splits, content versioning, dataset cards, immutable provenance, independent labels).
- **Build** — `faultline_eval/`: dataset, splits, runner, leakage controls, card.
- **Debug** — `evidence/splits.json` + `eval_result.json`: per-modality, per-split.
- **Measure** — `evidence/eval_result.json`: recall/precision bound to a
  `dataset_version`.
- **Defend** — `DECISIONS.md` (D13-001…D13-007); versions content-addressed, splits
  deterministic, leakage attacks caught and committed.
