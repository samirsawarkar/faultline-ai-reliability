# FAULTLINE — Day 13: evaluation harness + versioned dataset

A **leakage-resistant, versioned, oracle-grounded** evaluation system over the
six-fault spectrum. The dataset is content-addressed, splits are deterministic and
disjoint, results are immutable and bound to the exact data + code they were
computed against, and two attacks — train/test contamination and stale-result
reuse — are shown to be caught.

> **Fail condition:** dataset versions, splits, or leakage controls are ambiguous.
> **Status: not triggered** — `dataset_version` is the content hash of the whole
> manifest; the split is a deterministic, stratified, disjoint partition; and every
> leakage control is enforced and audited (`leakage_report.json`). See
> [CHECKPOINT-13.md](CHECKPOINT-13.md).

## The one idea

Days 8–12 built and catalogued the faults and their detectors. To turn "these
detectors work" into a defensible claim you need an evaluation you cannot cheat:
labels grounded in truth (not the detector), a held-out test split with no
contamination, and results that are worthless the moment the data changes. This
day builds exactly that harness — and grounds every label in the injection oracle.

## What's here

```
faultline_eval/
  dataset.py   Sample + versioned Dataset: content-addressed version, stratified
               disjoint splits, oracle-grounded expected labels
  predict.py   run_and_predict: one unit through the owning day (9-11) + detector
  runner.py    evaluate -> frozen EvalResult bound to dataset_version + code_version
  leakage.py   split disjointness, label non-leakage, version binding + the attacks
  card.py      the dataset card (datasheet)
scripts/ eval.py (the reproducible command) · make_evidence.py
tests/   test_dataset.py test_eval_leakage.py  (14 tests)
evidence/
  manifest.json splits.json eval_result.json leakage_report.json DATASET_CARD.md
CHECKPOINT-13.md · LEARN-eval-infra.md · DECISIONS.md · REFLECTION.md
```

## Reproducible eval command

```
python day13/scripts/eval.py --split test      # or: make day13-eval
```

Deterministic: no wall clock, no RNG outside seeded fault injection — same command,
same `result_id` and numbers, on any machine. Standard library only.

## Build A — the versioned dataset

A **Sample** is `(modality F1-F6, is_fault, kind, severity=tier, seed)` with an
oracle-grounded `expected_label`. Identity, version and split are all
content-addressed and unambiguous:

- **sample_id** = sha256 of the sample's config.
- **dataset_version** = sha256 of the whole manifest (generator version + every
  sample). Change any seed/tier/config/label → the version changes.
- **split** = a deterministic, **stratified by (modality, kind)** partition (≈40%
  test), so every fault kind — including the semantic escapes `drift_value` and
  `context_drift` — appears in both train and test.
- **expected labels** come from the injection truth + oracle, never a detector.

## Build B — immutable results

`evaluate(dataset, split)` returns a **frozen** `EvalResult` carrying its
`dataset_version`, `code_version`, `split`, per-modality + overall confusion, and a
`result_id` derived from those versions. A result can always be checked for
freshness; it can never be silently reused against different data.

Test-split result (`dataset_version de5068d574cae9fd`): overall recall **0.727**,
precision **1.0** — F1/F4/F6 at 1.0, F2 0.5 (budget-gated), F3 0.5 and F5 0.5 (the
semantic escapes miss on held-out data, reproducing the Q2 split honestly).

## Attack — contamination and stale reuse

`evidence/leakage_report.json` (all pass):

- **train/test contamination** — copying a test sample into train is caught by the
  disjointness check (`detected_after: true`, the leaked id reported).
- **stale-result reuse** — a result computed on dataset v1, reused against a changed
  v2, is rejected as `stale` (`stale_reuse_blocked: true`).
- **label non-leakage** — the detector receives only injection config, never the
  expected label, so a prediction cannot depend on the answer key.
- **split disjoint** — train ∩ test = ∅.

## Mastery map

- **Explain** → [LEARN-eval-infra.md](LEARN-eval-infra.md)
- **Build** → `faultline_eval/` (dataset, runner, leakage)
- **Debug** → `evidence/splits.json` + `eval_result.json` (per-modality, per-split)
- **Measure** → `evidence/eval_result.json` (bound to `dataset_version`)
- **Defend** → [DECISIONS.md](DECISIONS.md), [CHECKPOINT-13.md](CHECKPOINT-13.md)
