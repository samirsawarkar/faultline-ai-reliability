# DECISIONS.md — Day 7 (Q1: reliability vs hops) decision log

Append-only. Date · id · decision · why · reversal cost.

---

### 2026-07-17 · D7-001 · Measure a curve, compare it to the naive product model
**Decision.** Report three curves over required hops: measured end-to-end (Wilson
CI), naive `p1^n` (with propagated CI), and `corrected = ∏ measured p_k`.
**Why.** The mission is the *gap* between real multi-hop reliability and the
compounding fallacy. Showing all three makes the finding falsifiable and shows
the mechanism (`corrected` ≈ measured proves degradation, not a bug).
**Reversal cost.** None; this is the deliverable.

### 2026-07-17 · D7-002 · One documented modeling assumption: per-hop degradation
**Decision.** `p_k = clamp(P0 − DECAY·(k−1), PMIN, 1)`; end-to-end = all hops
succeed; runs abort at first failure.
**Why.** A single, transparent assumption produces the effect we want to measure
(homogeneity broken → measured < `p1^n`) without hidden magic. It stands in for
real context/error accumulation. Stated up front so the finding can't be accused
of smuggling in its conclusion.
**Reversal cost.** Add correlated-failure or recovery terms later; bump
`MODEL_VERSION` (changes Q1 numbers).

### 2026-07-17 · D7-003 · No LLM; a seeded stochastic simulator
**Decision.** Per-hop outcomes come from a per-run seeded RNG; the whole sweep is
a pure function of the master seed.
**Why.** Confidence intervals need genuine trial-to-trial variation, and the
experiment must be byte-reproducible. A real model API would make "run controlled
seeds, investigate divergence" non-reproducible and conflate API flakiness with
the compounding effect under study. Consistent with Days 3–6.
**Reversal cost.** Swap the simulator for a real subject later; the harness
(sweep, accounting, intervals, gate) measures it unchanged.

### 2026-07-17 · D7-004 · Wilson intervals, reimplemented locally
**Decision.** Use the Wilson score interval; keep a local copy rather than
importing Day 3 (which needs pydantic), so Day 7 stays stdlib-only.
**Why.** The normal-approximation interval is zero-width at `p=1` and misleads.
Wilson is correct at the extremes and for small n (deep hops have few samples).
**Reversal cost.** Trivial; it's ~15 lines mirroring Day 3.

### 2026-07-17 · D7-005 · Observability gate precedes reporting
**Decision.** `build_q1` runs `check_gate` (every run backed by a complete,
gap-free record) before emitting any number; divergences are investigated with
concrete Day-4 traces.
**Why.** FAULTLINE's honesty thesis: a measurement is only as trustworthy as its
observability. No unbacked numbers; every divergence is shown to be real and
traceable, not an artifact.
**Reversal cost.** None; additive safety.

### 2026-07-17 · D7-006 · Falsification defined as disjoint CIs
**Decision.** "Naive is wrong at n" ⇔ the naive band and measured band are
disjoint. Report the first such n.
**Why.** Turns a qualitative "they diverge" into a precise, defensible threshold
that accounts for uncertainty on both curves.
**Reversal cost.** Could switch to a formal test (e.g. two-proportion z); the
disjoint-interval rule is stricter and simpler to defend.
