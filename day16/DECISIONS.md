# DECISIONS.md — Day 16 (validate a narrow LLM judge) decision log

Append-only. Date · id · decision · why · reversal cost.

---

### 2026-07-26 · D16-001 · The judge is narrow by construction — one question, one place
**Decision.** The judge answers only "is this fallback candidate acceptable under
the rubric?" for the F3/F5 semantic escapes. It never scores overall success.
**Why.** A judge earns trust in inverse proportion to its scope. Restricting it to
the one question deterministic detection cannot answer (Q2) is what makes validation
tractable and keeps the oracle the sole arbiter of success.
**Reversal cost.** Widening scope requires re-validation on the wider task; the
narrow rubric would no longer certify it.

### 2026-07-26 · D16-002 · Validate against trusted human labels BEFORE any use
**Decision.** A blinded, hand-authored human-labelled set (24 items, 4 slices) is
the ground truth; the judge is scored against it (agreement, κ, bias, slices) before
it is trusted, and `RealJudgeAdapter` refuses to run without a client AND validation.
**Why.** This is the mission's fail condition verbatim. An unvalidated judge turns a
guess into an authoritative-looking number; validation-first is the only honest order.
**Reversal cost.** None; it is the deliverable.

### 2026-07-26 · D16-003 · Report Cohen's kappa against a human-vs-human ceiling, not against 1.0
**Decision.** Report chance-corrected κ, and also the inter-rater κ between two human
raters as the reliability ceiling the judge is compared to.
**Why.** Raw agreement flatters (two lenient raters agreeing by chance looks good);
κ corrects for chance. And humans do not agree perfectly either — judging the judge
against 1.0 is unfair and misleading. The ceiling is the honest bar.
**Reversal cost.** None; both numbers are reported.

### 2026-07-26 · D16-004 · Measure positional bias by presenting both orders; keep a fair control
**Decision.** Every pairwise item is judged in both orders; an order-dependent winner
is positional bias. A fair-tie-break control judge is run through the same detector.
**Why.** Positional bias is the best-known LLM-judge failure mode. Both-orders is the
standard way to expose it, and the fair control proves the detector reports 0 when
there is truly no bias (so a positive result is real, not an artifact) — the Day-14
verify-against-a-known-answer stance.
**Reversal cost.** None; additive.

### 2026-07-26 · D16-005 · A simulated judge with KNOWN flaws stands in for a real one
**Decision.** `SimulatedJudge` is deterministic, with a documented blind spot
(token-order drift) and a configurable known positional bias; `RealJudgeAdapter` is
the boundary for a real LLM, not callable here.
**Why.** No API is available and the repo is byte-reproducible. A stand-in with a
*known* bias lets the harness be built and verified now (does it recover the bias we
planted?), and a real judge plugs into the same adapter and re-runs the same harness.
Same pattern as the Day-3/6/7 simulators.
**Reversal cost.** Low; wire a client into `RealJudgeAdapter` and re-validate.

### 2026-07-26 · D16-006 · Forbid the judge from core success scoring, in code and in the card
**Decision.** The verdict sets `forbidden_from_core_success_scoring = True`
unconditionally; the judge card states the prohibition; the adapter refuses
unvalidated use.
**Why.** Core success is the oracle's job (Day 1). Even a well-validated judge is a
fallback-quality assistant, never the success arbiter — otherwise the honest,
reproducible metric the whole project rests on gets contaminated by a model's opinion.
**Reversal cost.** None; this boundary is load-bearing for the project's credibility.

### 2026-07-26 · D16-007 · A conservative validation bar: substantial kappa AND low bias AND no dead slice
**Decision.** `validated_for_standalone_use` requires κ ≥ 0.80, positional bias ≤
0.05, and no zero-agreement slice. The current judge fails all three, so the verdict
is "not standalone; assist only, never core."
**Why.** A judge that clears one metric but fails another is not trustworthy. Making
the bar conjunctive, and reporting exactly which conditions fail, prevents cherry-
picking a single flattering number.
**Reversal cost.** The thresholds are named constants; tightening/loosening them is a
one-line, auditable change.
