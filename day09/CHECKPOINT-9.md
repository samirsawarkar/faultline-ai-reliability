# CHECKPOINT-9 — F1/F2 fault families, detectors, and scoring against truth

**Mission.** Implement structured-output corruption and tool latency faults with
deterministic detectors, and score them.

**Fail condition.** Detector scores are not computed against injection truth. —
**Not triggered.**

## What was built

Two named fault families over the Day-8 injector, each with a deterministic
detector and a signal, plus a scorer whose only source of labels is the Day-8
`GroundTruthLog`:

| family | fault | detector | signal | truth label |
|---|---|---|---|---|
| **F1** | structured-output corruption (`corrupt`/`drop`/`truncate`/`duplicate`) | schema validator | `repair_signal` | `F1:*` |
| **F2** | virtual timeout/latency (`stall`) | duration vs budget | `timeout_signal` | `F2:latency` |

22 tests gate it; five evidence artifacts prove it.

## Scores are computed against injection truth

`score(predicted_positive, truth, truth_positive)` builds a confusion matrix by
joining a detector's flagged calls to the injection log per `seq`, and **refuses
to run** if the detector flags a seq absent from truth or if the truth log is not
a complete, contiguous labelling (D9-002). Tests prove the score *follows* the
truth:

- `test_scrambling_the_truth_changes_the_score` — flipping every `fired` flag
  turns 6 true positives into 6 false positives with the same detector output.
- `test_greedy_detector_loses_precision_against_truth` — a flag-everything
  detector drops to precision 0.5 (the 6 clean calls become FPs).
- alignment guards reject stray seqs and non-contiguous truth.

## The measurement (seed 20260719, 12 calls, fault on every 2nd call)

| family | sev 1 | 2 | 3 | 4 | 5 |
|---|---|---|---|---|---|
| F1 schema recall | **0.667** | 1.0 | 1.0 | 1.0 | 1.0 |
| F1 schema precision | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 |
| F2 latency recall (budget 45) | 0.0 | 0.0 | 0.0 | **1.0** | 1.0 |

- **F1** recall climbs from 0.667: a severity-1 corruption stays inside the value
  range and passes validation — a schema catches malformed, not wrong.
- **F2** recall is a step at severity 4, where `duration = 50` crosses the budget
  of 45; budget sensitivity confirms the same fault is caught at budgets 30/45 and
  missed at 50/60.
- **Specificity**: schema-detector-vs-latency-truth and
  duration-detector-vs-corruption-truth both score recall 0 — each detector is
  blind to the other family.

## Representative traces (Debug artifact)

`evidence/trace_f1_corrupt.json` — a severity-1 F1 run where the schema detector
**misses two of six** corruptions (confusion tp4/fp0/fn2/tn6), visible per call
and joined to truth. `evidence/trace_f2_latency.json` — a severity-4 F2 run where
every latency fault trips the timeout (tp6/fp0/fn0/tn6). Both carry a full Day-4
trace.

## Mastery gate — all five

- **Explain** — `LEARN-validation-latency.md`: validation catches malformed not
  wrong; latency is a budget not a property.
- **Build** — `faultline_detect/`: schema, latency, two detectors, two injectors.
- **Debug** — `trace_f1_corrupt.json`: the run where the detector misses small
  corruption, per call against truth.
- **Measure** — `detector_sweep.json`: precision/recall confusion matrices vs the
  injection log, across a severity sweep and a budget sweep.
- **Defend** — `DECISIONS.md` (D9-001…D9-007); detection and scoring are
  separated, and scoring is joined to truth by construction.
