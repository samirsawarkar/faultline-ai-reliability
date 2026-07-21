# FAULTLINE — Day 11: F5/F6 — completing the six-fault spectrum

Add the last two fault families and close the spectrum from **semantic corruption**
to **deterministic budget exhaustion**: F5 (context corruption) needs semantic
evaluation to catch; F6 (loop exhaustion) is caught by counting. The capstone is
a **deterministic-vs-semantic map** across all six faults and the **Q2 split
hypothesis** it implies.

> **Fail condition:** you cannot separate deterministic from semantic detection.
> **Status: not triggered** — `deterministic_vs_semantic_map.json` classifies
> every fault F1–F6 by detection nature and backs it with observed recall; F6 is
> closed by deterministic detectors (recall 1.0, zero escape) while F5's coherent
> `context_drift` escapes every deterministic/consistency check and is isolated as
> requiring the oracle. The separation is asserted in tests. See [CHECKPOINT-11.md](CHECKPOINT-11.md).

## The one idea

Across F1–F6 there is a clean fault line: some faults announce themselves in
*structure or counts* (a malformed shape, a blown latency budget, an explicit
error, a repeated step, an exhausted budget) — these are caught **deterministically**,
no notion of "correct" required. Others hide inside *well-formed, plausible
values* (a schema-valid wrong number, a coherently-corrupted context) — these can
only be caught by **semantic evaluation** against a model of correctness. Naming
which faults fall on which side is the point of the day, and the precondition for
Q2 (detection accuracy, Mission 15).

## What's here

```
faultline_spectrum/
  task.py        a bounded multi-step loop (context + final + step budget)
  spec.py        SpectrumFaultSpec + F5/F6 kinds + DETECTION_NATURE
  detectors.py   repetition + budget (deterministic); context-integrity (semantic)
  runner.py      run_batch: a batch of runs, labelled by the Day-8 truth log
  score.py       F5/F6 confusion vs truth + semantic_escapes (oracle evidence)
  spectrum_map.py the F1-F6 deterministic-vs-semantic map (pulls Day 9/10 recalls)
  experiment.py  build_report + the Q2 split hypothesis
  cards.py       F5/F6 fault cards
scripts/ make_evidence.py
tests/   test_task_detectors.py test_score_map.py  (12 tests)
evidence/
  fault_cards.json spectrum_report.json deterministic_vs_semantic_map.json
  q2_split_hypothesis.json escape_examples.json trace_f5_context.json trace_f6_loop.json
CHECKPOINT-11.md · LEARN-context-termination.md · DECISIONS.md · REFLECTION.md
```

## Quickstart

```
python -m pytest tests/ -q       # 12 tests
python scripts/make_evidence.py  # regenerate evidence (byte-reproducible)
```

Standard library only. Builds on Day 8 (truth), Day 9 (F1/F2 + scoring), Day 10
(F3/F4 + oracle), Day 4 (traces).

## F5 — context corruption (Build A, semantic)

A plausible wrong value enters the task's running context. Two kinds:
`context_inconsistent` breaks the consistency invariant `final == sum(context)`
and is caught; `context_drift` recomputes the final to stay consistent — coherent,
well-formed, and **wrong**, so it passes every deterministic/consistency check and
only the oracle catches it (recall of the consistency detector: **0.5**).

## F6 — loop exhaustion (Build B, deterministic)

The agent loop `repetition` (repeats a step, never progresses) or
`budget_exhaustion` (hits the step budget without completing). Both are caught by
counting and equality — **recall 1.0, zero escape**, no correctness model needed.

## The deterministic-vs-semantic map (the required artifact)

`evidence/deterministic_vs_semantic_map.json`, backed by observed recalls:

| fault | primary detector | nature | closed by deterministic detection? |
|---|---|---|---|
| F1 structured-output corruption | schema | deterministic | mostly (small in-range drift residual) |
| F2 latency | duration vs budget | deterministic | **yes** (recall 1.0) |
| F3 schema drift | schema + invariant | mixed | no — `drift_value`/`offbase_tokens` escape |
| F4 provider error | explicit flag | deterministic | **yes** (recall 1.0) |
| F5 context corruption | consistency invariant | semantic | no — `context_drift` escapes |
| F6 loop exhaustion | repetition + budget | deterministic | **yes** (recall 1.0) |

**Fully deterministic (recall 1.0, no escape): F2, F4, F6.**
**Require semantic evaluation: F1 (residual), F3, F5.**

## Q2 split hypothesis (committed)

`evidence/q2_split_hypothesis.json`: detection accuracy bifurcates by *detection
nature*, not severity. Deterministic faults are caught at recall 1.0 by cheap
detectors with no residual; semantic faults leave an irreducible escape set under
any deterministic detector and require an oracle or validated judge. Falsifiable
by any deterministic detector that closes `context_drift` or `drift_value` without
a correctness model — none exists, because those corruptions are structurally
identical to correct outputs. Q2 (Mission 15) will measure the split with intervals.

## Mastery map

- **Explain** → [LEARN-context-termination.md](LEARN-context-termination.md)
- **Build** → `faultline_spectrum/` (task, F5/F6 injectors, detectors)
- **Debug** → `evidence/trace_f5_context.json` (per-run verdict vs oracle, traced)
- **Measure** → `evidence/spectrum_report.json` + `deterministic_vs_semantic_map.json`
- **Defend** → [DECISIONS.md](DECISIONS.md), [CHECKPOINT-11.md](CHECKPOINT-11.md)
