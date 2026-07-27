"""M2 — timeout + exponential backoff + jitter for slow tools (F2).

Each attempt calls a tool with some virtual duration. If the duration exceeds the
per-attempt timeout, the attempt fails (we "waited" only up to the timeout) and the
engine backs off — exponential, capped, jittered — before the next try. A transient
slow spell clears as durations fall under the timeout (recovered); a persistently
slow tool never does (exhausted, within the total latency budget).

Latency accounting is honest: a failed attempt costs exactly the timeout (we cut it
off), a successful one costs its actual duration. So the total-latency ceiling holds
to within one timeout — never unbounded.
"""
from __future__ import annotations

from typing import Callable, List, Tuple

from .engine import RecoveryResult, run_bounded_retry
from .policy import RetryPolicy


def transient_slow(start: int, step: int) -> Callable[[int], int]:
    """Duration decreases by `step` each attempt: a slow spell that recovers."""
    return lambda i: max(0, start - i * step)


def persistent_slow(duration: int) -> Callable[[int], int]:
    """Duration constant and high: a tool that never speeds up."""
    return lambda i: duration


def make_slow_tool(duration_fn: Callable[[int], int], per_attempt_timeout: int
                   ) -> Callable[[int], Tuple[bool, int, int]]:
    def attempt(i: int) -> Tuple[bool, int, int]:
        d = duration_fn(i)
        if d <= per_attempt_timeout:
            return True, d, d                       # completed under the deadline
        return False, per_attempt_timeout, d        # timed out: paid only the timeout
    return attempt


def timeout_retry(duration_fn: Callable[[int], int], per_attempt_timeout: int,
                  policy: RetryPolicy) -> RecoveryResult:
    return run_bounded_retry(make_slow_tool(duration_fn, per_attempt_timeout), policy)
