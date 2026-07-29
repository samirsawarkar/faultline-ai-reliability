"""One shared seeded cascade population for every candidate policy."""
from __future__ import annotations

import hashlib
from dataclasses import asdict, dataclass
from typing import Any, Dict, List

N = 400
SEED_BASE = 2026080300


def seeded_unit(seed: int, label: str) -> float:
    digest = hashlib.sha256(f"{seed}:{label}".encode("ascii")).digest()
    return int.from_bytes(digest[:8], "big") / float(2 ** 64)


@dataclass(frozen=True)
class ExperimentConfig:
    name: str = "base"
    n: int = N
    seed_base: int = SEED_BASE
    primary_fault_rate: float = 0.40
    persistent_share_given_fault: float = 0.40
    fallback_exact_rate: float = 0.55
    fallback_clear_wrong_rate: float = 0.25
    latency_scale: float = 1.0
    per_request_cost_budget: float = 5.0
    per_request_latency_budget: float = 120.0
    retryability_signal: str = "simulator_truth"
    fallback_guard: str = "strict_simulator_oracle"

    def validate(self) -> "ExperimentConfig":
        if self.n <= 0:
            raise ValueError("n must be positive")
        rates = (
            self.primary_fault_rate,
            self.persistent_share_given_fault,
            self.fallback_exact_rate,
            self.fallback_clear_wrong_rate,
        )
        if any(rate < 0.0 or rate > 1.0 for rate in rates):
            raise ValueError("rates must be in [0, 1]")
        if (
            self.fallback_exact_rate + self.fallback_clear_wrong_rate
            > 1.0
        ):
            raise ValueError("fallback quality slice rates exceed 1")
        for name in (
            "latency_scale",
            "per_request_cost_budget",
            "per_request_latency_budget",
        ):
            if getattr(self, name) <= 0:
                raise ValueError(f"{name} must be positive")
        if self.retryability_signal != "simulator_truth":
            raise ValueError("unsupported retryability_signal")
        if self.fallback_guard != "strict_simulator_oracle":
            raise ValueError("unsupported fallback_guard")
        return self

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


BASE_CONFIG = ExperimentConfig().validate()


@dataclass(frozen=True)
class CascadeTrial:
    index: int
    seed: int
    primary_fault: bool
    persistence: str
    severity: int
    fallback_quality: str

    @property
    def transient(self) -> bool:
        return self.primary_fault and self.persistence == "transient"

    @property
    def persistent(self) -> bool:
        return self.primary_fault and self.persistence == "persistent"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "index": self.index,
            "seed": self.seed,
            "primary_fault": self.primary_fault,
            "persistence": self.persistence,
            "severity": self.severity,
            "fallback_quality": self.fallback_quality,
        }


def build_trials(config: ExperimentConfig = BASE_CONFIG) -> List[CascadeTrial]:
    config.validate()
    trials: List[CascadeTrial] = []
    for index in range(config.n):
        seed = config.seed_base + index
        fault = seeded_unit(seed, "primary_fault") < config.primary_fault_rate
        persistent = (
            fault
            and seeded_unit(seed, "persistence")
            < config.persistent_share_given_fault
        )
        quality_roll = seeded_unit(seed, "fallback_quality")
        if quality_roll < config.fallback_exact_rate:
            quality = "exact"
        elif quality_roll < (
            config.fallback_exact_rate + config.fallback_clear_wrong_rate
        ):
            quality = "clear_wrong"
        else:
            quality = "borderline_tokens"
        trials.append(
            CascadeTrial(
                index=index,
                seed=seed,
                primary_fault=fault,
                persistence=(
                    "persistent" if persistent
                    else ("transient" if fault else "none")
                ),
                severity=1 + int(seeded_unit(seed, "severity") * 5),
                fallback_quality=quality,
            )
        )
    return trials
