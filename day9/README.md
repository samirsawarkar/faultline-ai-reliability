# FAULTLINE — Day 9: F1/F2 fault families with deterministic detectors + scoring

Implement two fault families — **structured-output corruption (F1)** and
**virtual timeout/latency (F2)** — each with a **deterministic detector**, and
score each detector's precision/recall **against the Day-8 injection truth**.

> **Fail condition:** detector scores are not computed against injection truth.
> **Status: not triggered** — every score in `evidence/detector_sweep.json` and
> `evidence/scored_runs.json` is a confusion matrix built by joining a detector's
> predicted-positive calls to the Day-8 `GroundTruthLog`, per `seq`. The scorer
> refuses to run on a misaligned or non-contiguous truth log, and tests prove the
> score follows the truth (scramble the labels → the confusion moves). See
> [CHECKPOINT-9.md](CHECKPOINT-9.md).

## The one idea

Day 8 proved faults can be injected reproducibly and labelled independently.
Day 9 asks the next question: **can a cheap, deterministic detector notice — and
how well?** "How well" is only meaningful if it's measured against the truth the
injector wrote, never against the detector's own output. So detection and scoring
are kept strictly separate: a detector sees only what the system under test sees
(the output, or the duration); the scorer alone touches the ground-truth log.

## What's here

```
faultline_detect/
  schema.py      OutputSchema + validate_output — structural rules (not an oracle)
  injectors.py   f1_corruption_spec / f2_latency_spec over the Day-8 FaultSpec
  latency.py     virtual duration = BASE + injected; a latency budget
  detectors.py   schema_detect -> repair_signal; duration_detect -> timeout_signal
  runner.py      run() drives the Day-8 injecting boundary, captures observables
  score.py       Confusion + score(): detector vs injection truth, joined by seq
  experiment.py  severity sweep, budget sensitivity, cross-family specificity
  cards.py       the F1/F2 fault cards
scripts/
  make_evidence.py   regenerate all evidence (deterministic)
tests/
  test_schema.py test_detectors.py test_score.py test_experiment.py  (22 tests)
evidence/
  fault_cards.json       F1/F2 datasheets
  detector_sweep.json    severity sweep + budget sensitivity + specificity
  scored_runs.json       two representative runs, per-call, scored vs truth
  trace_f1_corrupt.json  representative F1 run as a Day-4 trace + confusion
  trace_f2_latency.json  representative F2 run as a Day-4 trace + confusion
CHECKPOINT-9.md · LEARN-validation-latency.md · DECISIONS.md · REFLECTION.md
```

## Quickstart

```
python -m pytest tests/ -q      # 22 tests: schema, detectors, score, experiment
python scripts/make_evidence.py # regenerate evidence (byte-reproducible)
```

Standard library only. Builds on Day 8 (`faultline_inject`) and reuses Day 4's
tracer for representative traces.

## F1 — structured-output corruption + schema detector (Build A)

The boundary returns a schema-violating payload. The detector is a **schema
validator** (`value` in `[10, 150]`; `tokens` a list of exactly 4 strictly
consecutive ints; `step` a non-empty string). It emits a **repair_signal** on any
violation. Crucially it is *not an oracle*: it checks well-formedness, not
correctness — which is exactly why it **misses small, in-range corruption** and
catches gross corruption. That gap is the honest measurement.

## F2 — virtual latency/timeout + duration detector (Build B)

The boundary returns the correct payload but takes too long. Duration is virtual
(`BASE_LATENCY + severity*10`, no wall clock). The detector emits a
**timeout_signal** when `duration > budget`. Detection is **budget-gated**: the
same fault is caught under a tight budget and missed under a loose one.

## Attack — sweep severity, score against labels

`evidence/detector_sweep.json` (seed 20260719, 12 calls, fault on every 2nd call,
6 clean negatives):

| family | severity 1 | 2 | 3 | 4 | 5 |
|---|---|---|---|---|---|
| **F1 schema** recall | 0.667 | 1.0 | 1.0 | 1.0 | 1.0 |
| **F1 schema** precision | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 |
| **F2 latency** recall (budget 45) | 0.0 | 0.0 | 0.0 | 1.0 | 1.0 |

- **F1**: precision is a flat 1.0 (a clean output is never flagged); recall climbs
  from 0.667 because a severity-1 corruption stays inside the value range and
  looks well-formed.
- **F2**: recall is a step at severity 4, where `duration = 50` crosses the
  budget of 45. Budget sensitivity (`f2_budget_sensitivity`) shows the same
  severity-4 fault caught at budgets 30/45 and missed at 50/60.
- **Specificity**: the schema detector scored against latency truth, and the
  duration detector scored against corruption truth, both get **recall 0** — each
  detector is blind to the other family, which is why family-partitioned truth
  matters.

## Mastery map

- **Explain** → [LEARN-validation-latency.md](LEARN-validation-latency.md)
- **Build** → `faultline_detect/` (schema, latency, detectors, injectors)
- **Debug** → `evidence/trace_f1_corrupt.json` (a run where the detector *misses*
  two small corruptions — visible per call, joined to truth)
- **Measure** → `evidence/detector_sweep.json` (precision/recall vs injection truth)
- **Defend** → [DECISIONS.md](DECISIONS.md), [CHECKPOINT-9.md](CHECKPOINT-9.md)
