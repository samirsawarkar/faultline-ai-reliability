"""Drive a request stream through the breaker + fallback chain, recording provenance.

Per request (one per virtual tick) we record: the breaker state, whether the primary
was allowed or short-circuited, who served the response, and the degraded flag. A
Day-4 trace mirrors this (one span per request, provenance in attributes) and the
breaker's transition log is returned alongside — so both breaker transitions AND
fallback provenance are traceable, which is the mission's fail condition.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT / "day04") not in sys.path:
    sys.path.insert(0, str(_ROOT / "day04"))

from .breaker import CircuitBreaker  # noqa: E402
from .fallback import Served, route_fallback  # noqa: E402


def run_stream(n: int, primary_fails: Callable[[int], bool], breaker: CircuitBreaker, *,
               use_fallback: bool = True, secondary_up: Callable[[int], bool] = None,
               tracer=None) -> Dict[str, Any]:
    """primary_fails(tick) -> True if the primary would fail at this tick.
    secondary_up(tick) -> True if the fallback provider is up (default: always)."""
    secondary_up = secondary_up or (lambda t: True)
    outcomes: List[Dict[str, Any]] = []

    for t in range(n):
        primary_up = not primary_fails(t)
        if breaker is None:
            allowed, note = True, "no_breaker"
        else:
            allowed, note = breaker.allow(t)
        short_circuited = not allowed
        served: Served

        if allowed:
            success = primary_up
            if breaker is not None:
                breaker.record(success, t)
            if success:
                served = Served("primary", is_fallback=False, is_degraded=False, answered=True)
            else:
                served = (route_fallback(secondary_up(t)) if use_fallback
                          else Served(None, False, False, False))
        else:
            # breaker OPEN: do NOT call the primary; go straight to fallback
            served = (route_fallback(secondary_up(t)) if use_fallback
                      else Served(None, False, False, False))

        outcomes.append({
            "tick": t, "state_at": (breaker.state if breaker is not None else "no_breaker"), "primary_up": primary_up,
            "allowed": allowed, "short_circuited": short_circuited,
            "note": note, **served.to_dict(),
            # a HEALTHY call we refused: primary was up but we short-circuited it
            "healthy_blocked": primary_up and short_circuited,
        })

    if tracer is not None:
        for o in outcomes:
            with tracer.span(f"req.{o['tick']}", "agent",
                             payload={"tick": o["tick"]}) as h:
                h.set_output({"state": o["state_at"], "served_by": o["served_by"],
                              "is_fallback": o["is_fallback"], "is_degraded": o["is_degraded"],
                              "short_circuited": o["short_circuited"]})

    n_ans = sum(1 for o in outcomes if o["answered"])
    metrics = {
        "n": n,
        "answered": n_ans,
        "availability": round(n_ans / n, 4),
        "served_primary": sum(1 for o in outcomes if o["served_by"] == "primary"),
        "served_secondary": sum(1 for o in outcomes if o["served_by"] == "secondary"),
        "served_degraded": sum(1 for o in outcomes if o["served_by"] == "degraded"),
        "unanswered": sum(1 for o in outcomes if not o["answered"]),
        "primary_calls": sum(1 for o in outcomes if o["allowed"]),
        "healthy_blocked": sum(1 for o in outcomes if o["healthy_blocked"]),
    }
    return {"outcomes": outcomes, "metrics": metrics,
            "transitions": list(breaker.transitions) if breaker is not None else [],
            "trace": tracer.to_dict() if tracer is not None else None}
