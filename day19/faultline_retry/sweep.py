"""Retry sweep — parameterize attempts/delay/jitter and measure what each K costs.

A seeded population of requests is run at each retry budget K = 1..KMAX. For every
K we record not just success but its PRICE: total attempts (cost), the amplification
factor (avg attempts/request), and the TAIL latency (p95/p99), because retries buy
mean success while paying in the tail. Two scenarios share the same population:

  independent — each attempt fails independently, so retries genuinely help.
  correlated  — a fraction of failures are a shared outage that ALL retries hit, so
                retrying does nothing for them but still multiplies cost, and a
                retry-storm term inflates every request's latency under the load.

Everything is a pure function of SEED (per-(request, attempt) Bernoulli draws +
seeded backoff), so the whole sweep is byte-reproducible.
"""
from __future__ import annotations

import random
import sys
from pathlib import Path
from typing import Any, Dict, List

_ROOT = Path(__file__).resolve().parents[2]
for rel in ("day14", "day18"):
    p = _ROOT / rel
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from faultline_recovery.policy import RetryPolicy  # noqa: E402 (Day 18 backoff)
from faultline_stats import bootstrap_ci, wilson_interval  # noqa: E402 (Day 14)

N = 200
KMAX = 6
ATTEMPT_LAT = 10
RHO_PERSISTENT = 0.15        # never succeed regardless of retries
P_FLAKY = 0.5                # per-attempt success prob for a flaky request
OUTAGE_FRAC = 0.40           # of flaky requests, the fraction that are retry-proof (correlated)
QUEUE_COEF = 40              # retry-storm: queue delay added to every request under load
SEED = 20260729

_POLICY = RetryPolicy(max_attempts=KMAX, base_delay=10, max_delay=80,
                      total_latency_budget=10 ** 9, cost_budget=10 ** 9,
                      jitter=True, seed=SEED)


def _bernoulli(p: float, r: int, i: int) -> bool:
    rng = random.Random(SEED * 1_000_003 + r * 1009 + i)
    return rng.random() < p


def _is_outage(r: int) -> bool:
    rng = random.Random(SEED * 7 + r * 31 + 5)
    return rng.random() < OUTAGE_FRAC


def _n_persistent() -> int:
    return int(RHO_PERSISTENT * N)


def _simulate(r: int, K: int, scenario: str):
    """Return (succeeded, attempts_used) for request r under budget K."""
    if r < _n_persistent():
        return False, K                       # persistent: never succeeds, uses all K
    if scenario == "correlated" and _is_outage(r):
        return False, K                       # shared outage: retry-proof
    for i in range(K):
        if _bernoulli(P_FLAKY, r, i):
            return True, i + 1
    return False, K


def _percentile(sorted_vals: List[float], q: float) -> float:
    if not sorted_vals:
        return 0.0
    idx = max(0, min(len(sorted_vals) - 1, int(round(q * (len(sorted_vals) - 1)))))
    return sorted_vals[idx]


def _p99(sample: List[float]) -> float:
    return _percentile(sorted(sample), 0.99)


def sweep_point(K: int, scenario: str) -> Dict[str, Any]:
    successes = 0
    total_attempts = 0
    per_request_attempts: List[int] = []
    for r in range(N):
        ok, used = _simulate(r, K, scenario)
        successes += int(ok)
        total_attempts += used
        per_request_attempts.append(used)

    amplification = total_attempts / N
    queue_delay = QUEUE_COEF * max(0.0, amplification - 1.0)   # the retry-storm term

    latencies: List[float] = []
    for used in per_request_attempts:
        backoff = sum(_POLICY.delay_for(i) for i in range(used - 1))
        latencies.append(used * ATTEMPT_LAT + backoff + queue_delay)

    lo, hi = wilson_interval(successes, N)
    slat = sorted(latencies)
    p99_lo, p99_hi = bootstrap_ci(latencies, statistic=_p99, iters=800, seed=SEED)
    return {
        "K": K, "scenario": scenario,
        "success_rate": round(successes / N, 4),
        "success_ci95": [round(lo, 4), round(hi, 4)],
        "successes": successes, "n": N,
        "total_attempts": total_attempts,
        "amplification": round(amplification, 4),
        "success_per_attempt": round(successes / total_attempts, 4),
        "p95_latency": round(_percentile(slat, 0.95), 2),
        "p99_latency": round(_percentile(slat, 0.99), 2),
        "p99_ci95": [round(p99_lo, 2), round(p99_hi, 2)],
        "queue_delay": round(queue_delay, 2),
    }


def sweep(scenario: str) -> List[Dict[str, Any]]:
    return [sweep_point(K, scenario) for K in range(1, KMAX + 1)]


def success_flags(K: int, scenario: str) -> List[bool]:
    """Per-request success at budget K — for a paired (same-population) comparison."""
    return [_simulate(r, K, scenario)[0] for r in range(N)]
