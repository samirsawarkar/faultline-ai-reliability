# CHECKPOINT-11 — F5/F6 and the deterministic-vs-semantic map

**Mission.** Complete the six-fault spectrum from semantic corruption to
deterministic budget exhaustion.

**Fail condition.** You cannot separate deterministic from semantic detection. —
**Not triggered.**

## What was built

The last two fault families and the cross-spectrum map:

| family | kinds | detector | nature | result |
|---|---|---|---|---|
| **F5** context corruption | `context_drift`, `context_inconsistent` | consistency invariant | semantic | recall **0.5** (drift escapes) |
| **F6** loop exhaustion | `repetition`, `budget_exhaustion` | repetition + step budget | deterministic | recall **1.0**, zero escape |

12 tests gate it; seven evidence artifacts prove it.

## The separation (the fail condition, met)

`deterministic_vs_semantic_map.json`, backed by observed recalls from Days 9–11:

- **Fully deterministic — recall 1.0, no escape: F2, F4, F6.**
- **Require semantic evaluation: F1 (small in-range drift residual), F3
  (`drift_value`/`offbase_tokens`), F5 (`context_drift`).**

A test asserts `separation_holds`: the fully-deterministic set is exactly
{F2, F4, F6} and both F3 and F5 are in the semantic set.

## F5 escapes — isolated with oracle evidence

`escape_examples.json`: the `context_drift` runs are internally consistent
(`final == sum(context)`), well-formed, and terminate normally — yet wrong. Example:
context `[10, 60, 30, 40]` with final `140` where the correct context was
`[10, 20, 30, 40]` with final `100`. The consistency detector passes it; only the
oracle catches it. Reported as **requiring semantic evaluation**, never as detected.

## F6 — deterministic, complete

Both loop faults are caught by counting and equality: `repetition` by a repeated
step signature, `budget_exhaustion` by `steps_used >= budget && not completed`.
Recall 1.0, precision 1.0, zero escape — no correctness model used.

## Q2 split hypothesis (committed)

`q2_split_hypothesis.json`: detection accuracy bifurcates by detection nature, not
severity. Deterministic faults → recall 1.0 with cheap detectors, no residual;
semantic faults → irreducible escape under any deterministic detector, closed only
by an oracle or validated judge. Falsifiable by a deterministic detector that
closes a semantic escape without a correctness model — impossible by construction,
since those corruptions are structurally identical to correct outputs. Q2
(Mission 15) will measure the split with intervals.

## Mastery gate — all five

- **Explain** — `LEARN-context-termination.md`: context integrity vs termination
  correctness, and why the split is structural.
- **Build** — `faultline_spectrum/`: the task/loop, F5/F6 injectors, the detectors.
- **Debug** — `trace_f5_context.json`: per-run verdict vs oracle, fully traced.
- **Measure** — `spectrum_report.json` + `deterministic_vs_semantic_map.json`.
- **Defend** — `DECISIONS.md` (D11-001…D11-007); the split has an explicit
  definition, observed backing, and a named refuter.
