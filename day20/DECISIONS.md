# DECISIONS.md — Day 20 (circuit breaker + fallback) decision log

Append-only. Date · id · decision · why · reversal cost.

---

### 2026-07-30 · D20-001 · Every state transition is recorded, with reason and tick
**Decision.** `CircuitBreaker` appends `{from, to, reason, tick}` to a transition log on
every state change.
**Why.** The mission fails if a transition cannot be traced. An operator must be able to
answer "why did the breaker open at t22?" from the record alone. The log is the artifact
that makes recovery auditable.
**Reversal cost.** None; it is the deliverable's core.

### 2026-07-30 · D20-002 · Every response carries provenance, mirrored into the trace
**Decision.** Each request records `served_by` / `is_fallback` / `is_degraded` /
`short_circuited`, and the Day-4 span carries the same.
**Why.** Availability that is secretly all-degraded looks healthy on a dashboard and is
actually an incident. Provenance is what lets you tell a healthy system from one running
on its fallback — and it is the other half of the fail condition.
**Reversal cost.** None; additive metadata.

### 2026-07-30 · D20-003 · Rolling-window failure threshold, not consecutive failures
**Decision.** Trip OPEN when the last `window` calls contain `failure_threshold` failures.
**Why.** A consecutive-failure rule misses a dependency that fails intermittently (50%),
and a threshold-of-1 rule false-opens on isolated blips. "k in the last n" distinguishes a
blip from an outage — demonstrated by the false-open attack (25 healthy blocked at
threshold 1, 0 at 3-of-5).
**Reversal cost.** Low; the window/threshold are config.

### 2026-07-30 · D20-004 · Half-open probes with a success-threshold; failure re-opens
**Decision.** After cooldown, HALF_OPEN allows trials; `success_threshold` consecutive
successes CLOSE, any failure re-OPENs and restarts the cooldown.
**Why.** Probing is how you detect recovery without reopening the floodgates. Requiring
several successes (not one) and a real cooldown damps flapping — the flapping attack cuts
21 transitions to 7.
**Reversal cost.** Low; both are config.

### 2026-07-30 · D20-005 · A degraded tier keeps availability up but is always flagged
**Decision.** The fallback chain ends in a degraded (canned/cached) tier that is always
available; degraded responses are flagged `is_degraded=True`, never presented as fresh.
**Why.** "Restore availability without hiding failures": the degraded tier restores
availability, the flag prevents the hiding. Serving degraded silently is the Mission-21
hazard (silent fallback degradation), so we mark it from day one.
**Reversal cost.** None; the flag is load-bearing for honesty.

### 2026-07-30 · D20-006 · Measure breaker and fallback separately with a true no-breaker baseline
**Decision.** The paired study runs naive (no breaker, no fallback), breaker-only, and
breaker+fallback on the same outage.
**Why.** It would be easy to credit the fallback's availability win to the breaker. Running
breaker-only shows the honest truth: the breaker *protects the dependency* (18 fewer primary
calls) but slightly *lowers* availability on its own; the fallback is what restores it. Two
mechanisms, two measured effects.
**Reversal cost.** None; the baseline is `breaker=None`.
