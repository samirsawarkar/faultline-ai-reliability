# CHECKPOINT-8 — reproducible fault injection with independent ground truth

**Mission.** Inject reproducible component faults with ground-truth labels
written at injection time.

**Fail condition.** Injected faults lack deterministic triggers or independent
truth labels. — **Not triggered.**

## What was built

A fault is now **data**: a frozen ten-field `FaultSpec` (Build A), fired by a
deterministic trigger (`triggers.py`) with a severity-scaled deterministic effect
(`faults.py`), injected at a generic call boundary (`InjectingChannel`, Build B),
and labelled — at injection time, out of band — in a `GroundTruthLog`
(`truth.py`). 45 tests gate it; three evidence artifacts prove it.

## The two required properties, proven

### 1. Deterministic / identical triggers

Every trigger is a pure function of `(spec, run_seed, seq, input_digest)` — no
wall clock, no default RNG. Across seeds `[20260718, 1, 42, 777, 100000]`
(`integrity_report.json`):

| property | value |
|---|---|
| `all_seeds_reproducible` | **true** — a seed re-run gives byte-identical outputs, truth, cost |
| `deterministic_triggers_seed_independent` | **true** — `call_index`/`every_n`/`input_match` fire on the same calls for every seed |
| `probabilistic_trigger_varies_across_seeds` | **true** — seeded trigger varies per seed, reproducible within each |

Even the `probabilistic` trigger is seeded: variation without randomness.

### 2. Independent truth labels / no leakage

Labels are written from the injection *decision*, before output exists, into a
log the system under test never sees; the trace span carries only public
component/output and joins to the label by `span_id`.

| property | value |
|---|---|
| `no_label_leakage` | **true** |
| `label_leaks_total` | **0** (across all 5 seeds; outputs and spans scanned) |
| `stall` output vs clean output | **byte-identical** — content cannot reveal the label |

The scanner is non-vacuous: planting a label in the output is caught
(`test_leakage_scan_would_catch_a_planted_leak`).

## The reproducible fault trace (Debug artifact)

`evidence/fault_trace.json` — one run (seed 20260718, 12 calls) with all four
non-clean content/behaviour modes exercised (`corrupt`, `truncate`, `error`,
`stall`), faults fired at seqs `[0, 2, 3, 4, 6, 7, 8]`, `cost_units = 120`, and
`no_label_leakage = true`. The trace and the ground-truth log are joined by
`span_id`, so the run is fully labelled without a single label living in a span.

## Mastery gate — all five

- **Explain** — `LEARN-chaos.md`: why measurement needs deterministic triggers,
  independent labels, and a bounded fault space that chaos can skip.
- **Build** — `faultline_inject/`: the 10-field spec, four triggers, six modes,
  the boundary wrapper, and the out-of-band truth log.
- **Debug** — `evidence/fault_trace.json`: reconstruct a labelled run by joining
  the truth log to the trace on `span_id`.
- **Measure** — `evidence/integrity_report.json`: reproducibility and leakage as
  counts, across five seeds.
- **Defend** — `DECISIONS.md` (D8-001…D8-008): every non-obvious choice with its
  why and reversal cost.
