# CHECKPOINT-19 — Q3: the retry crossover

**Mission.** Find where retries stop helping success and begin amplifying latency
and cost.

**Fail condition.** Retries improve point success while cost or tail latency becomes
unacceptable. — **Not triggered.**

## What was built

A parameterized retry sweep with the full price of each budget, a crossover
analysis, an independent-vs-correlated paired experiment with a retry storm, and a
recommended retry region capped by ceilings.

- **Sweep** (per K): success + Wilson CI, total cost, amplification, p95/p99 tail
  latency + bootstrap CI, success-per-attempt.
- **Crossover**: diminishing-returns knee + the largest budget under both ceilings.
- **Attack**: correlated failures (shared, retry-proof outage) + a retry-storm
  load→latency term.
- **Guard**: the recommendation is verified to be within ceilings; breaching regions
  are surfaced and lie outside it.

8 tests gate it; four evidence artifacts prove it.

## Q3 finding (N=200, seed 20260729)

- **Independent:** crossover at **K=4**; **recommended K=3** — the amplification
  ceiling (2.0x) binds first (K4 = 2.14x), and K≥5 breaches the p99 budget (120).
- **Correlated + storm:** success plateaus at **0.45** while amplification hits
  **4.07x** and p99 hits **257**; **recommended K=2** and a **circuit breaker
  (Mission 20) is required**.
- **Paired:** at K=3, correlation vs independence on the same 200 requests →
  McNemar b=0/c=69, **p ≈ 0 significant** (correlation costs 69 successes).

## The fail condition, refused

`crossover.json.fail_condition_guard`: the recommended K is within both ceilings for
both scenarios (`respected: true`), and every ceiling-breaching K (independent K4–6)
is `> recommended`. So the recommendation never trades a success bump for an
unacceptable cost/tail cost — a test enforces it.

## Mastery gate — all five

- **Explain** — `LEARN-retry-amplification.md`: why success is the wrong objective,
  and the retry-storm feedback loop.
- **Build** — `faultline_retry/`: sweep, crossover, figure, report.
- **Debug** — `retry_sweep.json` + `crossover_curve.svg`: per-K cost and tail.
- **Measure** — success (Wilson) + p99 (bootstrap) per K; the crossover.
- **Defend** — `q3_conclusion.json` + `DECISIONS.md` (D19-001…D19-006); the
  recommendation is capped by cost and tail ceilings, not by success.
