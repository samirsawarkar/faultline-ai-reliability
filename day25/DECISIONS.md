# DECISIONS.md — Day 25 (replay-verified postmortems)

Append-only. Date · id · decision · why · reversal cost.

---

### 2026-08-04 · D25-001 · Publish two incidents, not three
**Decision.** Cover one semantic/recovery cascade and one deadline-scheduling
failure.
**Why.** They exercise different controls and both have frozen provenance. A third
report would add volume without a new validation pattern.
**Reversal cost.** None; more incidents can join the same catalog.

### 2026-08-04 · D25-002 · The regression predicate is invariant
**Decision.** Keep test ID and predicate identical across legacy and fixed policy
versions.
**Why.** A fix cannot earn green by weakening the expected outcome.
**Reversal cost.** None; this is the red→green contract.

### 2026-08-04 · D25-003 · Seed and environment stay fixed
**Decision.** The policy version is the only before/after intervention.
**Why.** Changing the fault, budget, or deadline would not show that the corrective
action fixed the observed incident.
**Reversal cost.** None; new envelopes should be separate experiments.

### 2026-08-04 · D25-004 · A fix must restore correct service
**Decision.** Containment, rejection, and alarm suppression remain red unless a
correct visible answer is returned inside the original envelope.
**Why.** Day 23 demonstrated that correctly containing a bad answer can still be a
user-visible service failure.
**Reversal cost.** None; containment remains a separately reported outcome.

### 2026-08-04 · D25-005 · Every regression cites spans
**Decision.** Before and after assertions carry trace references that must resolve
to complete spans.
**Why.** A postmortem should be debuggable from evidence rather than trusted as
prose.
**Reversal cost.** None; more references are additive.

### 2026-08-04 · D25-006 · Route diversity is part of the semantic fix
**Decision.** Strict rejection quarantines the provider/fingerprint and recovery
must use an independent trusted route.
**Why.** Detection alone would turn a bad answer into an unanswered request. The
mission requires the incident to become green.
**Reversal cost.** Medium; production must validate that the route is genuinely
independent.

### 2026-08-04 · D25-007 · Hedge only a bounded idempotent read
**Decision.** Allow one overlapping retry at time 20, retain the two-call ceiling,
and cancel remaining work after the first valid answer.
**Why.** Overlap makes the 45-unit deadline feasible without increasing per-request
cost, while the idempotency and attempt constraints bound duplicate effects.
**Reversal cost.** Low; non-idempotent operations remain ineligible.

### 2026-08-04 · D25-008 · “Stays fixed” includes fresh processes
**Decision.** Verify each policy version across 20 in-process runs and four Python
hash seeds in fresh processes.
**Why.** Same-process determinism can inherit stable interpreter state. Cross-
process equality tests the full replay key.
**Reversal cost.** Low; CI can expand the process/platform matrix.

### 2026-08-04 · D25-009 · Root causes name controls, not people
**Decision.** Reports identify authority boundaries, route policy, scheduling, and
observability conditions.
**Why.** Those conditions are testable and changeable; blame neither predicts nor
prevents recurrence.
**Reversal cost.** None; accountability can coexist with system-level analysis.
