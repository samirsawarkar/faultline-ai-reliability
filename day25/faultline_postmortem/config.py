"""One serializable environment shared by legacy and fixed policy replays."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Dict


@dataclass(frozen=True)
class PostmortemConfig:
    scenario_version: str = "1.0.0"
    cascade_cost_budget: int = 12
    cascade_step_budget: int = 9
    deadline_cost_budget: int = 2
    deadline_latency_budget: int = 45
    hedge_start_latency: int = 20
    hedge_completion_latency: int = 45
    trusted_tertiary_cost: int = 2
    trusted_tertiary_latency: int = 8

    def validate(self) -> "PostmortemConfig":
        if self.scenario_version != "1.0.0":
            raise ValueError("unsupported scenario_version")
        positive = (
            "cascade_cost_budget",
            "cascade_step_budget",
            "deadline_cost_budget",
            "deadline_latency_budget",
            "hedge_start_latency",
            "hedge_completion_latency",
            "trusted_tertiary_cost",
            "trusted_tertiary_latency",
        )
        for name in positive:
            if getattr(self, name) <= 0:
                raise ValueError(f"{name} must be positive")
        if self.hedge_start_latency >= self.deadline_latency_budget:
            raise ValueError("hedge must start before the deadline")
        if self.hedge_completion_latency > self.deadline_latency_budget:
            raise ValueError("hedge completion must fit the deadline")
        return self

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def canonical_config() -> PostmortemConfig:
    return PostmortemConfig().validate()
