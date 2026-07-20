# DECISIONS.md — Day 10 (F3/F4 contracts + false-negative analysis) decision log

Append-only. Date · id · decision · why · reversal cost.

---

### 2026-07-20 · D10-001 · Three truth classes, not two: malformed / schema-valid-wrong / provider-error
**Decision.** F3 splits into malformed kinds (schema-catchable) and schema-valid
kinds (a validator accepts them); F4 is explicit provider errors. `F3_SCHEMA_VALID`
records which is which, machine-checked in tests.
**Why.** The mission is precisely about not conflating "wrong" with "malformed"
with "failed". Encoding the three classes up front makes the escape set a
first-class, testable category rather than an afterthought.
**Reversal cost.** None; it's the taxonomy.

### 2026-07-20 · D10-002 · A correctness oracle, used only by the truth/scoring layer
**Decision.** `oracle.expected_output` (the clean channel's answer) defines
correctness; `is_correct`/`diff` are imported by `score.py` and evidence only —
never by a detector.
**Why.** To call a schema-valid output "wrong" you need an independent notion of
right. Letting a detector see the oracle would collapse the very gap being
measured. Same separation as Day 8 (out-of-band truth) and Day 9 (detector never
reads truth).
**Reversal cost.** None; the oracle is the reference implementation of the clean
boundary.

### 2026-07-20 · D10-003 · One semantic invariant, deliberately partial
**Decision.** The only invariant beyond the schema is "value is a round ten." It
catches `nonmultiple`; it does not catch `drift_value` or `offbase_tokens`.
**Why.** An invariant strong enough to catch every semantic corruption would BE
the oracle. Keeping it partial is what produces an honest escape set and teaches
the real lesson: invariants raise the floor, they don't reach the ceiling.
**Reversal cost.** Add invariants freely; each narrows the escape set and changes
the recall number. The point is that a finite invariant set never closes it.

### 2026-07-20 · D10-004 · Escapes are counted as false negatives, with evidence
**Decision.** `classify` returns `OK` for schema-valid, invariant-respecting,
non-erroring output; the scorer counts such truth-wrong calls as FN;
`escaped_false_negatives` emits each with the oracle's expected-vs-got diff.
**Why.** This is the fail condition verbatim — schema-valid semantic corruption
must not be "treated as detected without evidence." The classifier honestly says
`OK` (a miss), and the miss is proven wrong by the oracle. A test asserts the
escapes land in FN, not TP.
**Reversal cost.** None; this is the deliverable's spine.

### 2026-07-20 · D10-005 · Score each family on its own run
**Decision.** F3 precision/recall come from an F3-only run, F4 from an F4-only
run; a combined run is used only to *illustrate* the classifier boundary per call.
**Why.** In a mixed run, a provider-error flag would count as an F3 false
positive (and vice versa), muddying the per-family numbers. Family-specific runs
keep each confusion matrix clean and interpretable (mirrors Day 9's specificity).
**Reversal cost.** Low; a per-class scorer could score a mixed run directly.

### 2026-07-20 · D10-006 · Severity scales magnitude, not detectability, for escapes
**Decision.** The schema-valid kinds scale their wrongness with severity but
remain schema- and invariant-valid at every severity; `severity_invariance`
asserts detection rate 0.0 across severities 1..5.
**Why.** It is the sharpest contrast with Day 9 (where recall rose with severity):
for semantic corruption that respects the contract, *bigger is not more
detectable*. A ten-fold-wrong value is as invisible as a rounding error.
**Reversal cost.** None; it falls out of the corruption design.

### 2026-07-20 · D10-007 · Provider errors drive a circuit-breaker signal
**Decision.** `run_breaker` emits a deterministic OPEN/closed trace over the error
stream (open after `threshold` errors in a sliding `window`).
**Why.** Explicit errors are the one family both cheap to detect and cheap to act
on; the circuit breaker is the canonical action, and Learn asks for the signal.
Kept to the signal only — the policy is Mission 20.
**Reversal cost.** None; additive, and the policy layer can consume this signal.
