"""M1–M6 adapters over the shared Day-22 trial contract."""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Dict, List

_ROOT = Path(__file__).resolve().parents[2]
for _day in ("day18", "day20"):
    _path = str(_ROOT / _day)
    if _path not in sys.path:
        sys.path.insert(0, _path)

from faultline_breaker import BreakerConfig, CircuitBreaker, route_fallback  # noqa: E402
from faultline_recovery import RetryPolicy, run_bounded_retry  # noqa: E402

from .ceilings import CeilingPolicy, run_with_ceilings
from .repetition import RepetitionPolicy, run_repetition_recovery
from .scenario import Outcome, Trial, baseline_outcome, clean_plan

MECHANISMS = (
    "M1_repair_retry",
    "M2_timeout_backoff",
    "M3_circuit_breaker",
    "M4_provider_fallback",
    "M5_step_cost_ceilings",
    "M6_repetition_recovery",
)

M1_POLICY = RetryPolicy(
    max_attempts=4,
    base_delay=2,
    max_delay=8,
    total_latency_budget=100,
    cost_per_attempt=1,
    cost_budget=4,
    jitter=False,
    seed=20260801,
)
M2_POLICY = RetryPolicy(
    max_attempts=4,
    base_delay=5,
    max_delay=20,
    total_latency_budget=200,
    cost_per_attempt=1,
    cost_budget=4,
    jitter=False,
    seed=20260801,
)
M5_POLICY = CeilingPolicy(max_steps=6, cost_budget=6, cost_per_step=1, latency_per_step=10)
M6_POLICY = RepetitionPolicy(
    max_consecutive=2,
    max_replans=1,
    max_steps=8,
    cost_budget=8,
    latency_per_step=10,
)


def _retry(trial: Trial, mechanism: str) -> Outcome:
    if mechanism == "M1_repair_retry" and trial.fault == "F1" and trial.injected:
        policy, attempt_latency = M1_POLICY, 10
    elif mechanism == "M2_timeout_backoff" and trial.fault == "F2" and trial.injected:
        policy, attempt_latency = M2_POLICY, 30
    else:
        return baseline_outcome(trial)

    clears_after = 99 if trial.variant == "persistent" else int(trial.variant[-1])

    def attempt(index: int):
        return index >= clears_after, attempt_latency, {"attempt": index}

    result = run_bounded_retry(attempt, policy)
    if result.recovered:
        return Outcome(
            "recovered", True, True, False, result.total_cost, result.total_latency
        )
    harm = (
        "wasted_repair_budget"
        if mechanism == "M1_repair_retry"
        else "wasted_timeout_retry_budget"
    )
    return Outcome(
        result.status,
        False,
        False,
        True,
        result.total_cost,
        result.total_latency,
        (harm,),
    )


def _m4(trial: Trial) -> Outcome:
    if trial.fault != "F4" or not trial.injected:
        return baseline_outcome(trial)
    served = route_fallback(secondary_up=True)
    assert served.answered and served.served_by == "secondary"
    quality_ok = trial.fault_rank % 3 != 2
    if quality_ok:
        return Outcome("fallback_recovered", True, True, False, 2, 20)
    return Outcome(
        "fallback_wrong_answer",
        True,
        False,
        False,
        2,
        20,
        ("silent_fallback_degradation",),
    )


def _m5(trial: Trial) -> Outcome:
    if not trial.injected:
        result = run_with_ceilings(clean_plan(trial), M5_POLICY)
        if result.completed:
            return Outcome("success", True, True, False, result.cost, result.latency)
        harms = (
            ("premature_step_ceiling",)
            if trial.variant == "long_legitimate"
            else ()
        )
        return Outcome(
            result.status,
            False,
            False,
            True,
            result.cost,
            result.latency,
            harms,
        )
    if trial.fault != "F6":
        return baseline_outcome(trial)
    actions = (
        ["repeat"] * 20
        if trial.variant == "persistent"
        else [f"work_{i}" for i in range(20)]
    )
    result = run_with_ceilings(actions, M5_POLICY)
    return Outcome(
        result.status, False, False, True, result.cost, result.latency
    )


def _m6(trial: Trial) -> Outcome:
    if not trial.injected:
        plan = clean_plan(trial)
        result = run_repetition_recovery(plan, None, M6_POLICY)
        if result.completed:
            return Outcome("success", True, True, False, result.cost, result.latency)
        harms = (
            ("false_repetition_positive",)
            if trial.variant == "legitimate_repeat"
            else ()
        )
        return Outcome(
            result.status,
            False,
            False,
            True,
            result.cost,
            result.latency,
            harms,
        )
    if trial.fault != "F6":
        return baseline_outcome(trial)

    initial = ["search", "search", "search", "search", "complete"]
    recovery = (
        ["search", "search", "search", "complete"]
        if trial.variant == "persistent"
        else ["refresh_context", "search", "complete"]
    )
    result = run_repetition_recovery(initial, recovery, M6_POLICY)
    if result.completed:
        return Outcome("replanned_recovery", True, True, False, result.cost, result.latency)
    return Outcome(
        result.status, False, False, True, result.cost, result.latency
    )


def _m3_batch(trials: List[Trial]) -> List[Outcome]:
    breaker = CircuitBreaker(BreakerConfig(3, 5, 4, 1))
    outcomes: List[Outcome] = []
    for tick, trial in enumerate(trials):
        allowed, _ = breaker.allow(tick)
        transport_fails = trial.fault == "F4" and trial.injected
        if not allowed:
            if not trial.injected:
                outcomes.append(
                    Outcome(
                        "false_open",
                        False,
                        False,
                        True,
                        0,
                        1,
                        ("false_open_blocked_healthy",),
                    )
                )
            else:
                outcomes.append(Outcome("short_circuited", False, False, True, 0, 1))
            continue

        breaker.record(not transport_fails, tick)
        outcomes.append(baseline_outcome(trial))
    return outcomes


def run_mechanism(mechanism: str, trials: List[Trial]) -> List[Outcome]:
    if mechanism not in MECHANISMS:
        raise ValueError(f"unknown mechanism: {mechanism}")
    if mechanism == "M3_circuit_breaker":
        return _m3_batch(trials)
    if mechanism == "M4_provider_fallback":
        return [_m4(trial) for trial in trials]
    if mechanism == "M5_step_cost_ceilings":
        return [_m5(trial) for trial in trials]
    if mechanism == "M6_repetition_recovery":
        return [_m6(trial) for trial in trials]
    return [_retry(trial, mechanism) for trial in trials]
