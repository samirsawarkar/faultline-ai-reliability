"""Attack + paired experiment: does bounded recovery help, and do the ceilings hold?

Three things, all deterministic:
  * PAIRED comparison (Day 14): the same seeded fault scenarios run with NO recovery
    (one attempt) vs WITH bounded recovery; McNemar on the paired success outcomes.
  * EXHAUSTION attack: force persistent faults and confirm every ceiling holds —
    attempts <= max, cost <= cost_budget (strict), latency bounded, and the outcome
    is a clean terminal status, never a hang.
  * NEW-FAILURE analysis: recovery is not free. It adds cost/latency on faults it
    cannot fix, and a naive (non-idempotent) retry would double side effects — the
    ledger prevents that. Both are quantified.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict, List

_DAY14 = Path(__file__).resolve().parents[2] / "day14"
if str(_DAY14) not in sys.path:
    sys.path.insert(0, str(_DAY14))

from faultline_stats import mcnemar_from_pairs  # noqa: E402 (Day 14)

from .idempotency import IdempotencyLedger, NaiveNoLedger
from .policy import RetryPolicy
from .repair import ATTEMPT_LATENCY, make_producer, schema_repair_retry
from .timeout import make_slow_tool, persistent_slow, timeout_retry, transient_slow
from .engine import run_bounded_retry

# --- committed paired experiment configs ----------------------------------
M1_POLICY = RetryPolicy(max_attempts=4, base_delay=5, max_delay=40,
                        total_latency_budget=200, cost_per_attempt=1, cost_budget=6,
                        jitter=True, seed=20260728)
M2_POLICY = RetryPolicy(max_attempts=5, base_delay=10, max_delay=80,
                        total_latency_budget=400, cost_per_attempt=1, cost_budget=8,
                        jitter=True, seed=20260728)
NO_RECOVERY = RetryPolicy(max_attempts=1, base_delay=0, max_delay=0,
                          total_latency_budget=1000, cost_per_attempt=1, cost_budget=1,
                          jitter=False, seed=20260728)

# fault scenarios: a mix of transient (clears at k) and persistent (never clears)
M1_SCENARIOS = [1, 2, 3, 1, 2, 3, 99, 99, 99]     # 6 transient + 3 persistent
M2_TIMEOUT = 30
M2_SCENARIOS = [("transient", 60, 20), ("transient", 50, 20), ("persistent", 90, 0),
                ("transient", 40, 20), ("persistent", 70, 0), ("transient", 55, 15),
                ("transient", 45, 20), ("transient", 35, 15), ("persistent", 80, 0)]


def _m1_success(clears_after: int, policy: RetryPolicy) -> bool:
    res, _ = schema_repair_retry(clears_after, policy)
    return res.recovered


def _m2_success(kind: str, a: int, b: int, policy: RetryPolicy) -> bool:
    fn = transient_slow(a, b) if kind == "transient" else persistent_slow(a)
    return timeout_retry(fn, M2_TIMEOUT, policy).recovered


def paired_m1() -> Dict[str, Any]:
    base = [_m1_success(c, NO_RECOVERY) for c in M1_SCENARIOS]
    recov = [_m1_success(c, M1_POLICY) for c in M1_SCENARIOS]
    mc = mcnemar_from_pairs(base, recov)
    return {"policy": M1_POLICY.to_dict(), "scenarios": M1_SCENARIOS,
            "no_recovery_success": sum(base), "recovery_success": sum(recov),
            "mcnemar": mc}


def paired_m2() -> Dict[str, Any]:
    base = [_m2_success(k, a, b, NO_RECOVERY) for (k, a, b) in M2_SCENARIOS]
    recov = [_m2_success(k, a, b, M2_POLICY) for (k, a, b) in M2_SCENARIOS]
    mc = mcnemar_from_pairs(base, recov)
    return {"policy": M2_POLICY.to_dict(), "timeout": M2_TIMEOUT,
            "scenarios": M2_SCENARIOS, "no_recovery_success": sum(base),
            "recovery_success": sum(recov), "mcnemar": mc}


def exhaustion_attack() -> Dict[str, Any]:
    """Force persistent faults; confirm ceilings hold and the status is terminal."""
    m1_res, _ = schema_repair_retry(99, M1_POLICY)          # never clears
    m2_res = timeout_retry(persistent_slow(90), M2_TIMEOUT, M2_POLICY)
    checks = {
        "m1_status": m1_res.status,
        "m1_attempts_le_max": m1_res.attempts <= M1_POLICY.max_attempts,
        "m1_cost_le_budget": m1_res.total_cost <= M1_POLICY.cost_budget,
        "m1_terminal": m1_res.status in ("exhausted_attempts", "aborted_latency_budget",
                                         "aborted_cost_budget"),
        "m2_status": m2_res.status,
        "m2_attempts_le_max": m2_res.attempts <= M2_POLICY.max_attempts,
        "m2_cost_le_budget": m2_res.total_cost <= M2_POLICY.cost_budget,
        "m2_latency_bounded": m2_res.total_latency <= M2_POLICY.total_latency_budget
                              + M2_TIMEOUT,     # <= budget + at most one timeout
        "m2_terminal": m2_res.status in ("exhausted_attempts", "aborted_latency_budget",
                                         "aborted_cost_budget"),
    }
    checks["all_ceilings_hold"] = all(v for k, v in checks.items()
                                      if k.endswith(("_le_max", "_le_budget",
                                                     "_bounded", "_terminal")))
    return {"m1": m1_res.to_dict(), "m2": m2_res.to_dict(), "checks": checks}


def new_failure_analysis() -> Dict[str, Any]:
    """Two new failures recovery can introduce, quantified."""
    # 1. wasted cost/latency on a persistent fault recovery cannot fix
    persistent, _ = schema_repair_retry(99, M1_POLICY)
    # 2. idempotency: repeat the whole recovery (at-least-once delivery). With the
    #    ledger the commit happens once; a naive retry would double it.
    led = IdempotencyLedger()
    naive = NaiveNoLedger()
    for _ in range(3):                                  # 3 duplicate deliveries
        schema_repair_retry(1, M1_POLICY, request_id="R", ledger=led)
        # simulate the naive path committing every delivery
        naive.execute("R", lambda: "commit")
    return {
        "wasted_recovery_on_persistent": {
            "status": persistent.status, "attempts": persistent.attempts,
            "wasted_cost": persistent.total_cost, "wasted_latency": persistent.total_latency,
            "benefit": "none (fault never clears) — recovery adds cost without success"},
        "idempotency": {
            "duplicate_deliveries": 3,
            "side_effects_with_ledger": led.side_effects,       # expect 1
            "side_effects_naive": naive.side_effects,           # expect 3
            "safe_to_repeat": led.side_effects == 1},
    }


def build_report() -> Dict[str, Any]:
    return {
        "configs": {"M1_repair": M1_POLICY.to_dict(), "M2_timeout": M2_POLICY.to_dict(),
                    "no_recovery": NO_RECOVERY.to_dict()},
        "paired_m1": paired_m1(),
        "paired_m2": paired_m2(),
        "exhaustion_attack": exhaustion_attack(),
        "new_failure_analysis": new_failure_analysis(),
    }
