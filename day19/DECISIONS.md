# DECISIONS.md — Day 19 (Q3: retry crossover) decision log

Append-only. Date · id · decision · why · reversal cost.

---

### 2026-07-29 · D19-001 · Price every retry budget in cost AND tail latency, not just success
**Decision.** Each K reports success (Wilson CI), amplification (avg attempts), and
p95/p99 tail latency (bootstrap CI), plus success-per-attempt.
**Why.** Success alone always favours more retries; the whole mission is that the
cost and the tail rise without saturating. Reporting all three is what makes the
crossover visible and the recommendation honest.
**Reversal cost.** None; it is the deliverable.

### 2026-07-29 · D19-002 · The recommendation is capped by ceilings, never by success
**Decision.** Recommended K = min(last-K-under-both-ceilings, crossover-K). Ceilings:
amplification ≤ 2.0x, p99 ≤ 120.
**Why.** This is the fail condition encoded: a K that improves success but breaches a
ceiling can never be recommended, because the ceiling caps the recommendation before
the success gain is considered. A guard + test verify the recommended K is acceptable
and that breaching Ks are outside it.
**Reversal cost.** Ceilings are named constants; a different SLO changes the number, not the logic.

### 2026-07-29 · D19-003 · Model correlated failure + a retry storm, not just independent retries
**Decision.** A fraction of failures are a shared, retry-proof outage; total load adds
a queue-delay term to every request's latency as amplification rises.
**Why.** The independent-failure model flatters retry (each try is a fresh coin). Real
outages correlate, and retries then feed a storm. Without modelling that, the analysis
would recommend more retries than is safe.
**Reversal cost.** Low; the correlation fraction and storm coefficient are parameters.

### 2026-07-29 · D19-004 · Tail latency, not mean, is the latency metric
**Decision.** Report p95/p99, with a bootstrap CI on p99.
**Why.** Retries barely move the mean (most requests succeed on attempt 1) but move
the tail a lot (the retriers define p99). A mean would hide the exact harm the mission
is about.
**Reversal cost.** None; percentiles are cheap.

### 2026-07-29 · D19-005 · Pair the scenarios on the same seeded population
**Decision.** Independent and correlated sweeps run on the identical request
population; a McNemar at the recommended K quantifies the correlation effect.
**Why.** Paired comparison (Day 14) removes population variance, so "correlation costs
N successes" is a clean, significant statement rather than a difference of two noisy
runs.
**Reversal cost.** None.

### 2026-07-29 · D19-006 · Hand the correlated case to the circuit breaker, explicitly
**Decision.** The Q3 conclusion recommends K=2 for correlated failures AND states a
circuit breaker (Mission 20) is required.
**Why.** Bounding K is necessary but not sufficient under correlation — even K=2 feeds
the storm at scale. Naming the breaker as the real fix keeps the recommendation honest
about what retry alone can and cannot do.
**Reversal cost.** None; Mission 20 builds the breaker this points to.
