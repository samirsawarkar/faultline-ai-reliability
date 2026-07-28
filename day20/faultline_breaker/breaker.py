"""M3 — a circuit breaker whose every state change is recorded and traceable.

Three states, the classic shape:

  CLOSED     calls pass through; failures accumulate in a rolling window; when the
             window holds >= failure_threshold failures the breaker trips OPEN.
  OPEN       calls are short-circuited (the failing dependency is NOT called), which
             is what stops a correlated outage from becoming a retry storm (Day 19).
             After open_ticks of cooldown the breaker moves to HALF_OPEN.
  HALF_OPEN  a few trial calls are allowed; success_threshold consecutive successes
             CLOSE it, any failure re-OPENs it (and restarts the cooldown).

The mission's fail condition is that a transition cannot be traced, so EVERY
transition is appended to `transitions` as {from, to, reason, tick}. Time is a
virtual tick supplied by the caller — no wall clock, so a run is byte-reproducible.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Tuple

CLOSED, OPEN, HALF_OPEN = "closed", "open", "half_open"


@dataclass(frozen=True)
class BreakerConfig:
    failure_threshold: int = 3      # failures within the window that trip OPEN
    window: int = 5                 # rolling window of recent CLOSED-state outcomes
    open_ticks: int = 10            # cooldown before a trial (HALF_OPEN)
    success_threshold: int = 2      # consecutive HALF_OPEN successes that CLOSE

    def validate(self) -> "BreakerConfig":
        if self.failure_threshold < 1 or self.failure_threshold > self.window:
            raise ValueError("require 1 <= failure_threshold <= window")
        if self.open_ticks < 1 or self.success_threshold < 1:
            raise ValueError("open_ticks and success_threshold must be >= 1")
        return self


@dataclass
class CircuitBreaker:
    cfg: BreakerConfig
    state: str = CLOSED
    opened_tick: int = -1
    _recent: List[bool] = field(default_factory=list)     # True = failure
    _ho_success: int = 0
    transitions: List[Dict[str, Any]] = field(default_factory=list)

    def __post_init__(self):
        self.cfg.validate()

    def _to(self, new: str, reason: str, tick: int) -> None:
        self.transitions.append({"from": self.state, "to": new, "reason": reason, "tick": tick})
        self.state = new
        self._recent = []
        self._ho_success = 0
        if new == OPEN:
            self.opened_tick = tick

    def allow(self, tick: int) -> Tuple[bool, str]:
        """Decide whether a request may call the primary at this tick."""
        if self.state == OPEN:
            if tick - self.opened_tick >= self.cfg.open_ticks:
                self._to(HALF_OPEN, "cooldown_elapsed", tick)
                return True, "half_open_trial"
            return False, "short_circuit_open"
        return True, ("closed_pass" if self.state == CLOSED else "half_open_trial")

    def record(self, success: bool, tick: int) -> None:
        """Feed back the outcome of a call that was allowed."""
        if self.state == CLOSED:
            self._recent.append(not success)
            self._recent = self._recent[-self.cfg.window:]
            if self._recent.count(True) >= self.cfg.failure_threshold:
                self._to(OPEN, "failure_threshold", tick)
        elif self.state == HALF_OPEN:
            if not success:
                self._to(OPEN, "half_open_failed", tick)
            else:
                self._ho_success += 1
                if self._ho_success >= self.cfg.success_threshold:
                    self._to(CLOSED, "recovered", tick)

    def to_dict(self) -> Dict[str, Any]:
        return {"state": self.state, "config": vars(self.cfg),
                "transitions": list(self.transitions),
                "transition_count": len(self.transitions)}
