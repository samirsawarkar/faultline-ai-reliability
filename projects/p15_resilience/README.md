# P15: Agent Resilience and Failure-Handling Architecture

Evaluates the failure-handling layer for the FAULTLINE multi-step agent when operating against imperfect or degraded LLM endpoints.

## Problem Statement
Multi-step agents require 4 to 12 sequential model calls to complete a single task. In a 6-step task, even a modest 15% transient endpoint error rate reduces end-to-end task completion to $(1 - 0.15)^6 \approx 37.7\%$. Without client-side resilience, transient transport glitches become catastrophic task failures.

## Resilience Architecture
- `faultline_p2/resilience/`:
  - `CircuitBreaker`: Three-state (`CLOSED`, `OPEN`, `HALF_OPEN`) circuit breaker with explicit trip threshold (3 consecutive failures) and cool-down timer. Blocks outbound calls during outages, shedding load to protect upstream providers.
  - `RetryPolicy`: Bounded retries with exponential backoff and deterministic seeded jitter.
  - `FaultInjectingEndpoint`: Pluggable fake model endpoint producing timeouts, 5xx server errors, and 429 rate limits without external API keys ($0 budget).
  - `ResilientModel`: Wrapper integrating breaker, timeout, and backoff around `ModelInterface`.

## Key Findings & Reliability Gains
Across 200 standard multi-hop scenarios across varying endpoint error rates:
- **0% Faults**: 100.0% baseline [98.1%–100%] vs 100.0% resilient [98.1%–100%]. Zero extra calls.
- **15% Faults**: Baseline drops to **47.5%** [40.7%–54.4%]; Resilient maintains **100.0%** [98.1%–100%] (+52.5% gain, 650 extra retry calls).
- **30% Faults**: Baseline collapses to **20.5%** [15.5%–26.6%]; Resilient recovers to **96.5%** [93.0%–98.3%] (+76.0% gain, 1,138 extra retry calls).
- **45% Faults**: Baseline collapses to **13.0%** [9.0%–18.4%]; Resilient recovers to **81.0%** [75.0%–85.8%] (+68.0% gain, 1,391 extra retry calls).
- **Disjoint Wilson Intervals**: At all non-zero failure rates, the 95% Wilson confidence intervals are strictly disjoint (resilient lower bound exceeds baseline upper bound).
- **Circuit Breaker Load Shedding**: Under sustained outage, the circuit breaker tripped after 3 consecutive failures and shed **80.0%** of downstream calls (12 of 15 fast-failed), automatically recovering to `CLOSED` upon endpoint health restoration.

## Reproduction
```bash
make p15
# or directly:
.venv/bin/python projects/p15_resilience/run.py
```
