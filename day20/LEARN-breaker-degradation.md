# LEARN — circuit-breaker tuning and graceful degradation

Day 19 ended with "correlated outages need a circuit breaker." Day 20 builds it, and
the lesson is that a breaker is a *tuning* problem wrapped around a state machine, and
that a breaker without a fallback trades one failure mode for another.

## The state machine, and why each state exists

- **CLOSED** — normal. Calls pass; failures accumulate in a rolling window. The window
  matters: counting *consecutive* failures misses a dependency that fails 50% of the
  time, while a "k failures in the last n" rule catches degradation without tripping on
  a single blip.
- **OPEN** — the dependency is presumed down; calls are short-circuited (not sent). This
  is the load protection: it stops the retry storm from Day 19 by simply not calling the
  failing service, giving it room to recover.
- **HALF_OPEN** — after a cooldown, let a few trial calls through. If they succeed, CLOSE;
  if any fails, re-OPEN and restart the cooldown. This is how the breaker *probes* for
  recovery without reopening the floodgates.

Every transition here is logged with its reason and tick, because an untraceable breaker
is an operator's nightmare — you cannot answer "why did availability drop at 09:14?" if
the state changes are invisible. Traceability is the mission's fail condition for exactly
this reason.

## Tuning is the whole game — two failure modes to avoid

A breaker has two ways to be wrong, and they pull in opposite directions:

- **False opens (too eager).** If the threshold is too low, a single transient blip trips
  the breaker, and now it is short-circuiting a *healthy* dependency — blocking good
  traffic. Day 20 shows a threshold-of-1 breaker blocking 25 healthy calls on isolated
  blips, versus 0 for a 3-of-5-window breaker. The window is what tells a blip from an
  outage.
- **Flapping (too eager to recover, or too eager to trip).** A marginally-up dependency
  makes the breaker oscillate OPEN↔HALF_OPEN — half-open trials keep failing, then a lucky
  success closes it, then it trips again. Damping it means a longer cooldown and requiring
  *several* consecutive successes to close (not one). Day 20 cuts 21 transitions to 7 by
  damping.

The tension is real: tighter thresholds catch outages faster but false-open more; longer
cooldowns damp flapping but keep you degraded longer. There is no universal setting — it is
an SLO-driven choice, which is why the breaker's parameters are explicit config and its
behaviour is measured, not assumed.

## Graceful degradation — restore availability without hiding failure

A breaker alone makes things *less* available in the short term: it refuses calls. The
availability comes back from the **fallback**: when the primary is short-circuited or
fails, route to a secondary provider, and if that is also down, to a **degraded** tier — a
cached/canned/best-effort answer. Two rules keep this honest:

1. **Never hide the failure.** A degraded answer is *flagged* degraded, all the way through
   the trace and the metrics. Silently serving a stale or best-effort answer as if it were
   fresh is how "graceful degradation" becomes "quiet wrongness" — the exact hazard Mission
   21 (silent fallback degradation) is about.
2. **Provenance on everything.** Every response records who served it and whether it was a
   fallback. Without that, you cannot tell a healthy system from one running entirely on
   its degraded tier — which looks fine on an availability dashboard and is actually an
   incident.

The Day-20 paired study makes the split concrete: the breaker cuts 18 calls to the failing
primary (protection) but dips availability on its own; the fallback restores it to 1.0. You
need both — the breaker for the dependency's sake, the (traced, flagged) fallback for the
user's.

## References worth reading next

- Nygard, *Release It!* — the Circuit Breaker and Bulkhead stability patterns.
- Fowler, *CircuitBreaker* (martinfowler.com) — the closed/open/half-open write-up.
- Google SRE Book — *Graceful degradation* and serving from a degraded mode under load.
- Netflix Hystrix docs (historical) — half-open probing and fallback provenance in practice.
