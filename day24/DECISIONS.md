# DECISIONS.md — Day 24 (Q5 cascade policy) decision log

Append-only. Date · id · decision · why · reversal cost.

---

### 2026-08-03 · D24-001 · Correct visible answer is the success numerator
**Decision.** Availability, containment, rejection, and wrong visible answers do
not count as successful recovery.
**Why.** Optimizing “response returned” would reproduce the silent-degradation
failure measured on Day 21.
**Reversal cost.** None; alternate outcomes remain separately measurable.

### 2026-08-03 · D24-002 · Every policy sees the same 400 seeds
**Decision.** Generate one immutable trial population and evaluate P0–P4 at the
same seed indices.
**Why.** Cascade severity and fallback quality vary by seed. Pairing removes this
variation from policy contrasts.
**Reversal cost.** Low; larger samples can preserve the seed-prefix contract.

### 2026-08-03 · D24-003 · Constraints precede efficiency optimization
**Decision.** Reject policies on confidence-bound success, wrong-answer, cost, and
p95-latency limits before comparing efficiency ratios.
**Why.** A policy must not win by failing fast, abandoning expensive cases, or
showing wrong answers.
**Reversal cost.** Medium; changed product limits can update the four declared
thresholds and regenerate Q5.

### 2026-08-03 · D24-004 · Do not collapse cost and latency into one utility
**Decision.** Require one eligible policy to lead both success/cost and
success/latency.
**Why.** No evidence-backed exchange rate between spend and user waiting was
provided. A weighted score would manufacture that preference.
**Reversal cost.** Low if stakeholders later provide stable, reviewable weights.

### 2026-08-03 · D24-005 · Point leadership is insufficient
**Decision.** Both paired bootstrap efficiency-difference intervals versus every
other eligible policy must have lower bounds above zero.
**Why.** Selecting from noisy ratios without uncertainty would trigger the mission
fail condition.
**Reversal cost.** Low; a larger population can narrow the intervals.

### 2026-08-03 · D24-006 · p95 uses the nearest-rank definition
**Decision.** Sort observed latencies and select rank `ceil(0.95 × n)`.
**Why.** The definition is deterministic, auditable, and valid for discrete
latency tiers.
**Reversal cost.** Low, but historical evidence would need a named metric-version
migration.

### 2026-08-03 · D24-007 · Attack the selected policy under two envelope shifts
**Decision.** Increase fault persistence/correlation and separately tighten
per-request cost/latency budgets.
**Why.** A base-distribution winner is not a policy invariant. The attacks expose
both quality-supply and recovery-budget boundaries.
**Reversal cost.** None; additional scenarios are additive.

### 2026-08-03 · D24-008 · Withdraw Q5 when attack bounds fail
**Decision.** Recommend P4 only for the base envelope; do not claim it survives
either stress attack.
**Why.** Under worse severity its success lower bound and cost upper bound fail;
under tight budgets 170 recoveries are suppressed.
**Reversal cost.** None; this is the claim-integrity rule.

### 2026-08-03 · D24-009 · Label P4 as a simulator reference upper bound
**Decision.** Serialize its perfect retryability signal and strict-oracle fallback
guard, and carry both caveats into the Q5 artifact.
**Why.** Day 16 showed that the narrow judge has a token-order blind spot. Reusing
the word “guarded” without naming the stronger oracle would silently overstate
deployment readiness.
**Reversal cost.** Medium; a deployable P4 needs paired classifier/guard errors,
cost, and latency added to the policy model.
