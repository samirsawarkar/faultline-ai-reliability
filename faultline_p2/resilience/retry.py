"""Bounded retries with exponential backoff and seeded jitter."""
from __future__ import annotations
import random
import time
from dataclasses import dataclass
from typing import Callable, Optional


@dataclass
class RetryPolicy:
    max_retries: int = 3
    initial_backoff_s: float = 0.1
    backoff_multiplier: float = 2.0
    max_backoff_s: float = 2.0
    seed: Optional[int] = 42
    sleep_fn: Optional[Callable[[float], None]] = None

    def __post_init__(self):
        self._rng = random.Random(self.seed if self.seed is not None else 42)
        if self.sleep_fn is None:
            self.sleep_fn = time.sleep

    def compute_backoff(self, attempt: int) -> float:
        """Compute exponential backoff with deterministic seeded jitter."""
        base_backoff = min(
            self.max_backoff_s,
            self.initial_backoff_s * (self.backoff_multiplier ** attempt)
        )
        # Seeded uniform jitter [0, base_backoff]
        jitter = self._rng.uniform(0.0, base_backoff)
        return base_backoff + jitter

    def wait(self, attempt: int) -> float:
        """Sleep for backoff duration and return actual wait duration."""
        duration = self.compute_backoff(attempt)
        if self.sleep_fn:
            self.sleep_fn(duration)
        return duration
