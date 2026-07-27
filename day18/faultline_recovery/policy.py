"""RetryPolicy — the bound. Recovery is only allowed inside this envelope.

The mission's fail condition is unbounded / unbudgeted / unsafe recovery. This
policy makes "bounded" structural: a finite `max_attempts`, a total latency budget,
a total cost budget, and a backoff schedule capped at `max_delay`. Nothing in the
recovery engine can loop forever or spend without a ceiling, because every limit is
a field here and is checked on every attempt.

Backoff + jitter are DETERMINISTIC: the delay for an attempt is a pure function of
(seed, attempt), so a recovery run is byte-reproducible — jitter that varied per
wall-clock would break the project's determinism gate.
"""
from __future__ import annotations

import random
from dataclasses import dataclass

MAX_ATTEMPTS_CAP = 10          # a hard ceiling even a caller cannot exceed


@dataclass(frozen=True)
class RetryPolicy:
    max_attempts: int          # total attempts, INCLUDING the first (>= 1)
    base_delay: int = 10       # backoff base (virtual latency units)
    max_delay: int = 80        # cap on any single backoff delay
    total_latency_budget: int = 1000
    cost_per_attempt: int = 1
    cost_budget: int = 100
    jitter: bool = True
    seed: int = 0

    def validate(self) -> "RetryPolicy":
        if not (1 <= self.max_attempts <= MAX_ATTEMPTS_CAP):
            raise ValueError(f"max_attempts must be in [1, {MAX_ATTEMPTS_CAP}]")
        if self.base_delay < 0 or self.max_delay < self.base_delay:
            raise ValueError("require 0 <= base_delay <= max_delay")
        for name in ("total_latency_budget", "cost_per_attempt", "cost_budget"):
            if getattr(self, name) <= 0:
                raise ValueError(f"{name} must be positive")
        return self

    def delay_for(self, attempt: int) -> int:
        """Backoff delay AFTER 0-based `attempt`, capped at max_delay, optionally
        full-jittered with a seeded RNG. Deterministic in (seed, attempt)."""
        base = min(self.max_delay, self.base_delay * (2 ** attempt))
        if not self.jitter:
            return base
        rng = random.Random(self.seed * 100003 + attempt)
        return int(rng.random() * base)          # full jitter in [0, base]

    def to_dict(self) -> dict:
        return {
            "max_attempts": self.max_attempts, "base_delay": self.base_delay,
            "max_delay": self.max_delay, "total_latency_budget": self.total_latency_budget,
            "cost_per_attempt": self.cost_per_attempt, "cost_budget": self.cost_budget,
            "jitter": self.jitter, "seed": self.seed,
        }
