"""Circuit Breaker with CLOSED, OPEN, and HALF_OPEN states."""
from __future__ import annotations
import time
from enum import Enum
from typing import Callable, Optional


class BreakerState(str, Enum):
    CLOSED = "CLOSED"
    OPEN = "OPEN"
    HALF_OPEN = "HALF_OPEN"


class CircuitBreakerOpenError(RuntimeError):
    """Raised when a request is blocked by an OPEN circuit breaker."""
    pass


class CircuitBreaker:
    """Explicit circuit breaker protecting downstream models/endpoints."""

    def __init__(
        self,
        failure_threshold: int = 3,
        cooldown_seconds: float = 2.0,
        time_fn: Optional[Callable[[], float]] = None,
    ) -> None:
        self.failure_threshold = failure_threshold
        self.cooldown_seconds = cooldown_seconds
        self.time_fn = time_fn or time.time

        self.state: BreakerState = BreakerState.CLOSED
        self.failure_count: int = 0
        self.success_count: int = 0
        self.opened_at: Optional[float] = None
        self.total_trips: int = 0
        self.fast_fails: int = 0

    def allow_request(self) -> bool:
        """Determine if a request is permitted to proceed to downstream endpoint."""
        now = self.time_fn()
        if self.state == BreakerState.CLOSED:
            return True

        if self.state == BreakerState.OPEN:
            if self.opened_at is not None and (now - self.opened_at) >= self.cooldown_seconds:
                self.state = BreakerState.HALF_OPEN
                return True
            self.fast_fails += 1
            return False

        if self.state == BreakerState.HALF_OPEN:
            # Allow trial probe call
            return True

        return True

    def on_success(self) -> None:
        """Record a successful downstream call."""
        if self.state == BreakerState.HALF_OPEN:
            self.state = BreakerState.CLOSED
            self.failure_count = 0
            self.opened_at = None
        elif self.state == BreakerState.CLOSED:
            self.failure_count = 0
        self.success_count += 1

    def on_failure(self) -> None:
        """Record a downstream failure."""
        now = self.time_fn()
        if self.state == BreakerState.HALF_OPEN:
            # Probe failed; trip immediately back to OPEN
            self.state = BreakerState.OPEN
            self.opened_at = now
            self.total_trips += 1
        elif self.state == BreakerState.CLOSED:
            self.failure_count += 1
            if self.failure_count >= self.failure_threshold:
                self.state = BreakerState.OPEN
                self.opened_at = now
                self.total_trips += 1

    def reset(self) -> None:
        """Manually reset the breaker to CLOSED state."""
        self.state = BreakerState.CLOSED
        self.failure_count = 0
        self.opened_at = None
