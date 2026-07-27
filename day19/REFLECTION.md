# REFLECTION.md — five-minute mission reflection (Day 19)

**Mission.** Find where retries stop helping success and begin amplifying latency
and cost.
**Fail condition.** Retries improve point success while cost or tail latency becomes
unacceptable. — *Not triggered:* the recommended budget is capped by an amplification
ceiling and a p99 budget, every breaching K is surfaced outside the recommendation,
and a test enforces it. See [CHECKPOINT-19.md](CHECKPOINT-19.md).

**Do we need an LLM API now? No.** Q3 is a cost/latency curve over a seeded retry
sweep — deterministic and reproducible. A real subject slots into the same request
model; the crossover analysis is unchanged.

**The sharpest decision.** Making the recommendation min(under-ceilings, crossover)
rather than "the K with the best success" (D19-002). That single choice is the fail
condition turned into arithmetic: you cannot recommend a ceiling-breaching K even if
its success is higher, because the ceiling caps the recommendation first. Recommended
K=3 (independent) is set by the amplification ceiling, not by the success plateau.

**The result I most wanted to show.** Correlated failure as pure amplification:
success flat at 0.45 while amplification hits 4x and p99 hits 257. It is the concrete
version of "retries DDoS your own recovering dependency," and it is why the honest
answer for correlated failures is a tiny K plus a circuit breaker — which Mission 20
builds.

**Mastery gate.**
- *Explain* — [LEARN-retry-amplification.md](LEARN-retry-amplification.md).
- *Build* — sweep, crossover, figure, report.
- *Debug* — [`evidence/retry_sweep.json`](evidence/retry_sweep.json) + the SVG curve.
- *Measure* — success (Wilson) + p99 (bootstrap) per K; crossover at K=4, recommended K=3.
- *Defend* — [`evidence/q3_conclusion.json`](evidence/q3_conclusion.json), [DECISIONS.md](DECISIONS.md).

**What I'd watch next.** Mission 20 (M3+M4): the circuit breaker + fallback that this
mission's correlated finding demands — so retries stop feeding the storm — then
Mission 21's silent-fallback-degradation (Q4) checks the fallback isn't quietly worse.
