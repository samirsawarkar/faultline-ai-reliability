"""M5 — structural step and cost ceilings.

The controller checks both bounds BEFORE executing an action. It therefore cannot
overshoot either ceiling, even when the plan never terminates. Latency is virtual
and deterministic, so exhaustion is measurable without a real hang.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Sequence


@dataclass(frozen=True)
class CeilingPolicy:
    max_steps: int = 6
    cost_budget: int = 6
    cost_per_step: int = 1
    latency_per_step: int = 10

    def validate(self) -> "CeilingPolicy":
        for name in ("max_steps", "cost_budget", "cost_per_step", "latency_per_step"):
            if getattr(self, name) <= 0:
                raise ValueError(f"{name} must be positive")
        return self


@dataclass(frozen=True)
class CeilingResult:
    status: str
    steps: int
    cost: int
    latency: int
    completed: bool

    def to_dict(self) -> Dict[str, object]:
        return {
            "status": self.status,
            "steps": self.steps,
            "cost": self.cost,
            "latency": self.latency,
            "completed": self.completed,
        }


def run_with_ceilings(
    actions: Sequence[str],
    policy: CeilingPolicy = CeilingPolicy(),
) -> CeilingResult:
    """Execute until `complete` or stop before a step/cost ceiling is crossed."""
    policy.validate()
    steps = cost = latency = 0
    for action in actions:
        if steps >= policy.max_steps:
            return CeilingResult("step_ceiling", steps, cost, latency, False)
        if cost + policy.cost_per_step > policy.cost_budget:
            return CeilingResult("cost_ceiling", steps, cost, latency, False)
        steps += 1
        cost += policy.cost_per_step
        latency += policy.latency_per_step
        if action == "complete":
            return CeilingResult("completed", steps, cost, latency, True)
    return CeilingResult("plan_exhausted", steps, cost, latency, False)
