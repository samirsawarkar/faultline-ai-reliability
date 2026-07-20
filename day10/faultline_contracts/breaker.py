"""A circuit-breaker signal driven by provider errors (F4).

Explicit provider errors are the one fault family cheap to detect *and* cheap to
act on. The classic action is a circuit breaker: when errors pile up, stop
calling the provider for a while instead of hammering a failing dependency. Day
10 only needs the SIGNAL (the policy itself is Mission 20); this is a
deterministic, wall-clock-free breaker over the observed error stream.

Policy: sliding window of `window` calls; the breaker trips OPEN on the call at
which the error count within the window first reaches `threshold`, and stays open
(a half-open/reset policy is deferred to the recovery missions). Pure function of
the error flags, so the signal is byte-reproducible.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional


@dataclass(frozen=True)
class BreakerTrace:
    states: List[str]            # "closed" / "open" per call seq
    opened_at: Optional[int]     # seq where it first tripped, or None
    window: int
    threshold: int

    def to_dict(self) -> dict:
        return {"states": list(self.states), "opened_at": self.opened_at,
                "window": self.window, "threshold": self.threshold}


def run_breaker(error_flags: List[bool], window: int = 3, threshold: int = 2
                ) -> BreakerTrace:
    """Feed per-call error flags; return the breaker state trace."""
    states: List[str] = []
    opened_at: Optional[int] = None
    for i in range(len(error_flags)):
        if opened_at is not None:
            states.append("open")
            continue
        lo = max(0, i - window + 1)
        errors_in_window = sum(1 for f in error_flags[lo:i + 1] if f)
        if errors_in_window >= threshold:
            opened_at = i
            states.append("open")
        else:
            states.append("closed")
    return BreakerTrace(states=states, opened_at=opened_at,
                        window=window, threshold=threshold)
