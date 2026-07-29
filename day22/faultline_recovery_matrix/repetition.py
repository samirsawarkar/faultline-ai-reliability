"""M6 — detect repeated non-progress and attempt one bounded replan.

Repetition is consecutive equality of a normalized action fingerprint. When the
allowed run length is exceeded, M6 switches once to a recovery plan. A second
repetition aborts cleanly. Step and cost ceilings wrap the entire composition.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional, Sequence


@dataclass(frozen=True)
class RepetitionPolicy:
    max_consecutive: int = 2
    max_replans: int = 1
    max_steps: int = 8
    cost_budget: int = 8
    latency_per_step: int = 10

    def validate(self) -> "RepetitionPolicy":
        if self.max_consecutive < 1:
            raise ValueError("max_consecutive must be positive")
        if self.max_replans < 0:
            raise ValueError("max_replans must be non-negative")
        for name in ("max_steps", "cost_budget", "latency_per_step"):
            if getattr(self, name) <= 0:
                raise ValueError(f"{name} must be positive")
        return self


@dataclass(frozen=True)
class RepetitionResult:
    status: str
    steps: int
    cost: int
    latency: int
    completed: bool
    repetitions_detected: int
    replans: int

    def to_dict(self) -> Dict[str, object]:
        return {
            "status": self.status,
            "steps": self.steps,
            "cost": self.cost,
            "latency": self.latency,
            "completed": self.completed,
            "repetitions_detected": self.repetitions_detected,
            "replans": self.replans,
        }


def run_repetition_recovery(
    actions: Sequence[str],
    recovery_actions: Optional[Sequence[str]] = None,
    policy: RepetitionPolicy = RepetitionPolicy(),
) -> RepetitionResult:
    policy.validate()
    current = list(actions)
    steps = cost = latency = detections = replans = 0
    previous = None
    consecutive = 0
    cursor = 0

    while cursor < len(current):
        if steps >= policy.max_steps:
            return RepetitionResult(
                "step_ceiling", steps, cost, latency, False, detections, replans
            )
        if cost + 1 > policy.cost_budget:
            return RepetitionResult(
                "cost_ceiling", steps, cost, latency, False, detections, replans
            )

        action = current[cursor]
        cursor += 1
        steps += 1
        cost += 1
        latency += policy.latency_per_step

        if action == previous:
            consecutive += 1
        else:
            previous = action
            consecutive = 1

        if consecutive > policy.max_consecutive:
            detections += 1
            if recovery_actions is not None and replans < policy.max_replans:
                replans += 1
                current = list(recovery_actions)
                cursor = 0
                previous = None
                consecutive = 0
                continue
            return RepetitionResult(
                "repetition_aborted", steps, cost, latency, False, detections, replans
            )

        if action == "complete":
            return RepetitionResult(
                "completed", steps, cost, latency, True, detections, replans
            )

    return RepetitionResult(
        "plan_exhausted", steps, cost, latency, False, detections, replans
    )
