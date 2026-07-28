"""M4 — a provider fallback chain that records PROVENANCE on every response.

When the primary is short-circuited (breaker OPEN) or its call fails, the request
is routed down a chain: primary -> secondary -> degraded (a last-resort canned/cached
answer). Graceful degradation means a request is (almost) always answered, but never
by hiding the failure: every response carries where it came from and whether it is a
fallback or a degraded answer. The degraded tier is the honesty valve — it keeps
availability up while flagging that the answer is second-best.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict, Optional


@dataclass(frozen=True)
class Served:
    served_by: Optional[str]     # "primary" | "secondary" | "degraded" | None (unanswered)
    is_fallback: bool
    is_degraded: bool
    answered: bool

    def to_dict(self) -> Dict[str, object]:
        return {"served_by": self.served_by, "is_fallback": self.is_fallback,
                "is_degraded": self.is_degraded, "answered": self.answered}


UNANSWERED = Served(None, False, False, False)


def route_fallback(secondary_up: bool, degraded_available: bool = True) -> Served:
    """Route a request that could not be served by the primary."""
    if secondary_up:
        return Served("secondary", is_fallback=True, is_degraded=False, answered=True)
    if degraded_available:
        return Served("degraded", is_fallback=True, is_degraded=True, answered=True)
    return UNANSWERED           # everything down and no degraded tier: honest failure
