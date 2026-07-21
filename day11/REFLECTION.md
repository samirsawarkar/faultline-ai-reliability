# REFLECTION.md — five-minute mission reflection (Day 11)

**Mission.** Complete the six-fault spectrum from semantic corruption to
deterministic budget exhaustion.
**Fail condition.** You cannot separate deterministic from semantic detection. —
*Not triggered:* `deterministic_vs_semantic_map.json` classifies all six faults by
an explicit criterion and backs each with observed recall; F6 is closed
deterministically (recall 1.0, zero escape), F5's `context_drift` escapes every
deterministic/consistency check and is isolated as needing the oracle. See
[CHECKPOINT-11.md](CHECKPOINT-11.md).

**Do we need an LLM API now? No.** The six-fault spectrum, its detectors, and the
map are all deterministic and cheap. The point of the map is precisely to show
*which* faults will eventually need a semantic judge (Mission 16) — F3 drift and
F5 context corruption — so the judge is introduced only where deterministic
detection provably cannot reach.

**The sharpest decision.** Defining "deterministic vs semantic" explicitly
(D11-001) before classifying anything. Without a stated criterion, the separation
is just vibes; with one, every fault gets the same test and the map is defensible.
The definition — "needs a model of correctness or not" — is what makes F6
(counting) obviously deterministic and F5 (`context_drift`) obviously semantic.

**The result that ties the arc together.** Consistency is not correctness (F5).
An internal check `final == sum(context)` feels like it should catch a corrupted
context, and it does — unless the corruption is coherent, in which case the lie is
self-consistent and only ground truth exposes it. That is the same lesson as Day
10's schema-valid drift, now at the level of propagating state, and it is why the
quiet faults dominate reliability work.

**Mastery gate.**
- *Explain* — [LEARN-context-termination.md](LEARN-context-termination.md).
- *Build* — the bounded task, F5/F6 injectors, deterministic + semantic detectors.
- *Debug* — [`trace_f5_context.json`](evidence/trace_f5_context.json): per-run
  verdict vs oracle.
- *Measure* — [`spectrum_report.json`](evidence/spectrum_report.json) +
  [`deterministic_vs_semantic_map.json`](evidence/deterministic_vs_semantic_map.json).
- *Defend* — [DECISIONS.md](DECISIONS.md), D11-001…D11-007.

**What I'd watch next.** Mission 12 (fault catalog + gallery) turns F1–F6 into one
browsable catalog; Mission 13 builds the evaluation harness + versioned dataset;
and Mission 15 (Q2) measures the detection-accuracy split this map predicts, per
family and with Wilson intervals.
