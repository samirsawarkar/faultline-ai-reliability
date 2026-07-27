"""Bounded retry engine — terminal by construction.

`run_bounded_retry(attempt_fn, policy)` runs attempts until one succeeds or a bound
is hit: max_attempts, the total latency budget, or the cost budget. It cannot loop
forever and cannot overspend the cost budget (checked BEFORE each attempt), so an
exhaustion is a clean, explainable outcome — never a hang. The result records
exactly which bound stopped it.

    attempt_fn(i) -> (success: bool, latency: int, payload)  for 0-based attempt i
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, List, Tuple

from .policy import RetryPolicy

TERMINAL = ("recovered", "exhausted_attempts", "aborted_latency_budget", "aborted_cost_budget")


@dataclass
class RecoveryResult:
    status: str
    attempts: int
    total_latency: int
    total_cost: int
    delays: List[int]
    payload: Any = None

    @property
    def recovered(self) -> bool:
        return self.status == "recovered"

    def to_dict(self) -> dict:
        return {"status": self.status, "attempts": self.attempts,
                "total_latency": self.total_latency, "total_cost": self.total_cost,
                "delays": list(self.delays), "recovered": self.recovered}


def run_bounded_retry(attempt_fn: Callable[[int], Tuple[bool, int, Any]],
                      policy: RetryPolicy) -> RecoveryResult:
    policy.validate()
    attempts = total_latency = total_cost = 0
    delays: List[int] = []
    payload = None

    for i in range(policy.max_attempts):
        # cost ceiling is STRICT: never spend an attempt we cannot afford
        if total_cost + policy.cost_per_attempt > policy.cost_budget:
            return RecoveryResult("aborted_cost_budget", attempts, total_latency,
                                  total_cost, delays, payload)

        success, latency, payload = attempt_fn(i)
        attempts += 1
        total_cost += policy.cost_per_attempt
        total_latency += latency

        if total_latency > policy.total_latency_budget:
            return RecoveryResult("aborted_latency_budget", attempts, total_latency,
                                  total_cost, delays, payload)
        if success:
            return RecoveryResult("recovered", attempts, total_latency,
                                  total_cost, delays, payload)

        # backoff before the next attempt (if any); a delay that would breach the
        # latency budget aborts instead of being taken
        if i < policy.max_attempts - 1:
            d = policy.delay_for(i)
            if total_latency + d > policy.total_latency_budget:
                return RecoveryResult("aborted_latency_budget", attempts,
                                      total_latency + d, total_cost, delays + [d], payload)
            total_latency += d
            delays.append(d)

    return RecoveryResult("exhausted_attempts", attempts, total_latency,
                          total_cost, delays, payload)
