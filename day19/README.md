# FAULTLINE — Day 19: Q3 — the retry crossover

Find where retries stop buying success and start **amplifying** cost and tail
latency, and commit a retry budget that is defensible — capped by cost and p99
ceilings, not by point success.

> **Fail condition:** retries improve point success while cost or tail latency
> becomes unacceptable.
> **Status: not triggered** — the recommended budget is, by construction, the
> largest K that is BOTH still improving AND under both ceilings; every K that
> breaches a ceiling is surfaced and lies *outside* the recommendation. See
> [CHECKPOINT-19.md](CHECKPOINT-19.md).

## The one idea

Retry looks free when you only look at the success rate — it almost always goes up.
Q3 refuses to look at success alone: every retry budget K is priced in **cost**
(amplification: avg attempts/request) and **tail latency** (p95/p99), and the
recommendation is the knee where success has mostly plateaued and the ceilings are
about to break. Under *correlated* failures the picture is worse: retries buy almost
no success while cost and tail latency explode — pure amplification.

## What's here

```
faultline_retry/
  sweep.py      seeded request population; per-K success (Wilson CI), cost,
                amplification, p95/p99 tail latency (bootstrap CI), success-per-cost
  crossover.py  diminishing-returns crossover + recommended region (cost + p99 ceilings)
                + the fail-condition guard
  figure.py     deterministic SVG crossover curve
  report.py     both scenarios + crossover + paired correlation effect + Q3 conclusion
scripts/ make_evidence.py
tests/   test_retry.py  (8 tests)
evidence/ retry_sweep.json crossover.json crossover_curve.svg q3_conclusion.json
CHECKPOINT-19.md · LEARN-retry-amplification.md · DECISIONS.md · REFLECTION.md
```

## Quickstart

```
python -m pytest tests/ -q       # 8 tests
python scripts/make_evidence.py  # regenerate the sweep, crossover, SVG (byte-reproducible)
```

Standard library only. Builds on Day 18 (RetryPolicy backoff), Day 14 (Wilson +
bootstrap). Reuses the same seeded-simulator discipline as the rest of the project.

## Q3 result (N=200, seed 20260729)

**Independent failures** — retries help, with diminishing returns:

| K | success (95% CI) | amplification | p99 latency | success/attempt |
|---|---|---|---|---|
| 1 | 0.455 [0.39, 0.52] | 1.00x | 10 | 0.455 |
| 2 | 0.645 [0.58, 0.71] | 1.55x | 46 | 0.418 |
| **3** | **0.760 [0.70, 0.81]** | **1.90x** | **76** | **0.400** |
| 4 | 0.790 [0.73, 0.84] | 2.14x | 110 | 0.369 |
| 5 | 0.810 [0.75, 0.86] | 2.35x | 133 | 0.345 |
| 6 | 0.835 [0.78, 0.88] | 2.54x | 196 | 0.329 |

- **Crossover at K=4** (marginal success drops to +0.03).
- **Recommended budget K=3** — the amplification ceiling (2.0x) binds first; K≥4
  breaches cost, K≥5 breaches the p99 budget (120). Recommending beyond K=3 would be
  exactly the fail condition (more success, unacceptable cost/tail).

**Correlated failures + retry storm** — near-pure amplification:

- Success plateaus at **0.45** (a shared outage is retry-proof), while amplification
  reaches **4.07x** and p99 reaches **257**. Success-per-attempt collapses 0.27 → 0.11.
- Recommended budget **K=2**, and a **circuit breaker (Mission 20) is required** —
  retrying a correlated outage just amplifies the load.

**Paired check:** on the same 200 requests, correlation vs independence at K=3 gives
McNemar b=0 / c=69, **p ≈ 0 (significant)** — correlation costs 69 successes.

## Mastery map

- **Explain** → [LEARN-retry-amplification.md](LEARN-retry-amplification.md)
- **Build** → `faultline_retry/` (sweep, crossover, figure)
- **Debug** → `evidence/retry_sweep.json` (per-K cost + tail with CIs)
- **Measure** → the crossover curve + the fail-condition guard
- **Defend** → `evidence/q3_conclusion.json`, [DECISIONS.md](DECISIONS.md), [CHECKPOINT-19.md](CHECKPOINT-19.md)
