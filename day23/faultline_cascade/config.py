"""The single, serializable configuration that defines the canonical incident."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Dict


@dataclass(frozen=True)
class CascadeConfig:
    scenario_version: str = "1.0.0"
    initiating_fault: str = "F2:primary_latency_spike"
    trigger_rate: float = 0.25
    primary_timeout: int = 30
    primary_fault_latency: int = 80
    primary_attempt_cost: int = 2
    max_retry_attempts: int = 3
    retry_backoff: int = 5
    breaker_failure_threshold: int = 2
    breaker_window: int = 2
    breaker_open_ticks: int = 5
    fallback_call_cost: int = 2
    fallback_latency: int = 12
    judge_cost: int = 1
    judge_latency: int = 4
    repetition_threshold: int = 2
    verification_cost: int = 1
    verification_latency: int = 3
    reentry_fallback_cost: int = 1
    reentry_fallback_latency: int = 8
    synthesis_cost: int = 2
    synthesis_latency: int = 5
    max_steps: int = 9
    total_cost_budget: int = 12

    def validate(self) -> "CascadeConfig":
        if self.scenario_version != "1.0.0":
            raise ValueError("unsupported scenario_version")
        if self.initiating_fault != "F2:primary_latency_spike":
            raise ValueError("canonical cascade requires the F2 initiating fault")
        if not (0.0 < self.trigger_rate <= 1.0):
            raise ValueError("trigger_rate must be in (0, 1]")
        positive = (
            "primary_timeout",
            "primary_fault_latency",
            "primary_attempt_cost",
            "max_retry_attempts",
            "breaker_failure_threshold",
            "breaker_window",
            "breaker_open_ticks",
            "fallback_call_cost",
            "fallback_latency",
            "judge_cost",
            "judge_latency",
            "repetition_threshold",
            "verification_cost",
            "verification_latency",
            "reentry_fallback_cost",
            "reentry_fallback_latency",
            "synthesis_cost",
            "synthesis_latency",
            "max_steps",
            "total_cost_budget",
        )
        for name in positive:
            if getattr(self, name) <= 0:
                raise ValueError(f"{name} must be positive")
        if self.retry_backoff < 0:
            raise ValueError("retry_backoff must be non-negative")
        if self.breaker_failure_threshold > self.breaker_window:
            raise ValueError("breaker threshold cannot exceed its window")
        return self

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def canonical_config() -> CascadeConfig:
    return CascadeConfig().validate()
