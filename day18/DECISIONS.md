# DECISIONS.md — Day 18 (bounded recovery: M1 repair-retry, M2 timeout) decision log

Append-only. Date · id · decision · why · reversal cost.

---

### 2026-07-28 · D18-001 · The bound is a first-class object, checked every attempt
**Decision.** `RetryPolicy` holds `max_attempts`, `cost_budget`, and
`total_latency_budget`; the engine checks them on every attempt and there is a hard
`MAX_ATTEMPTS_CAP` (10) a caller cannot exceed.
**Why.** The fail condition is unbounded/unbudgeted recovery. Making the limits a
validated data object — not a hope encoded in a loop — means recovery is terminal
by construction. The cost check is a strict pre-check, so cost never exceeds budget.
**Reversal cost.** None; policies are data.

### 2026-07-28 · D18-002 · Cost ceiling is strict; latency ceiling is bounded-overshoot
**Decision.** Cost is checked BEFORE spending an attempt (never exceeds). Latency is
accumulated as attempts run and aborts once exceeded, so it can overshoot by at most
one attempt/timeout.
**Why.** You cannot know a tool's latency before calling it, so a strict-before
latency ceiling is impossible without a per-attempt timeout — which M2 supplies
(overshoot ≤ one timeout). Cost, being per-attempt-fixed, IS knowable in advance, so
it is enforced strictly. Being honest about the difference is better than pretending
both are strict.
**Reversal cost.** Tighten latency by lowering the per-attempt timeout.

### 2026-07-28 · D18-003 · Backoff + jitter are deterministic (seeded), capped at max_delay
**Decision.** `delay_for(attempt)` = `min(max_delay, base·2^attempt)`, full-jittered
by `Random(seed, attempt)`.
**Why.** Exponential backoff spreads load and avoids hammering a struggling
dependency; jitter de-synchronises retriers (the thundering-herd fix). Seeding it
keeps the whole recovery byte-reproducible — wall-clock jitter would break the
determinism gate every prior day relies on.
**Reversal cost.** None; a real clock can replace the virtual units later.

### 2026-07-28 · D18-004 · Idempotency ledger makes retry SAFE TO REPEAT
**Decision.** A recovered result is committed through an `IdempotencyLedger` keyed by
request id; repeats replay the cached result without re-applying the side effect. A
`NaiveNoLedger` is kept only as the unsafe contrast.
**Why.** A bounded retry that re-applies a side effect on each try (or on re-delivery)
is still a fault — it just happens a bounded number of times. Idempotency is the
difference between "bounded" and "correct." The Learn block is exactly this.
**Reversal cost.** None; it is the safety guarantee.

### 2026-07-28 · D18-005 · Recover only transient faults; let persistent faults exhaust cleanly
**Decision.** The model separates transient faults (clear after k attempts / slow
spell subsides) from persistent ones (never clear). Recovery rescues the former and
exhausts the latter within budget — it never pretends to fix the unfixable.
**Why.** Retrying a persistent fault is pure waste; the honest behaviour is to spend
the budget once and stop with a terminal status. This is what the new-failure
analysis quantifies (cost spent, benefit none).
**Reversal cost.** None; a circuit breaker (Mission 20) will cut persistent faults off sooner.

### 2026-07-28 · D18-006 · Prove recovery helps with a paired, adequately-powered McNemar
**Decision.** Compare no-recovery vs recovery on identical seeded scenarios (Day 14
paired design), sized so the discordant count (6) clears the significance threshold.
**Why.** "Recovery helps" must be measured, not asserted, and paired against the same
faults so the comparison is fair. Sizing to ≥6 discordant pairs is the Day-14 lesson
applied — 5 would have been a real effect the test could not certify (p=0.0625).
**Reversal cost.** None; the scenarios are config.

### 2026-07-28 · D18-007 · Commit the new-failure analysis, not just the wins
**Decision.** The evidence reports what recovery COSTS (wasted budget on persistent
faults) and the failure it would introduce without idempotency (doubled side effects).
**Why.** A recovery layer that only advertises its success rate is dishonest — it
hides the latency/cost it adds and the correctness hazard it creates. Committing the
downside is what makes the win defensible.
**Reversal cost.** None; additive honesty.
