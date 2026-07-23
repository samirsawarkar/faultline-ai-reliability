"""The oracle — the ONE true answer for a call, used only as truth.

Day 9's schema detector answers "is this well-formed?"; this mission is about the
gap between well-formed and *correct*. To talk about that gap honestly we need a
correctness oracle: for a given request, exactly one output is right, and the
oracle is a pure function of the request (never of the produced output). It is the
same stance as Day 1's required-source oracle — correctness is computed, not
judged.

The clean boundary (`DemoChannel`) IS the oracle's reference implementation: the
correct output for a call is what the clean channel would have returned. So a
fault is "semantically wrong" iff its output differs from `expected_output`, no
matter how well-formed it looks.

Crucially, NO detector imports this module. Only the truth/scoring layer does —
because a detector that consulted the oracle would be the oracle, and the whole
point is to measure what cheap deterministic detectors miss relative to it.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict, Optional

_DAY8 = Path(__file__).resolve().parents[2] / "day08"
if str(_DAY8) not in sys.path:
    sys.path.insert(0, str(_DAY8))

from faultline_inject import DemoChannel  # noqa: E402

_CLEAN = DemoChannel()


def expected_output(component: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    """The single correct output for this request (the clean channel's answer)."""
    return _CLEAN.call(component, payload)


def is_correct(component: str, payload: Dict[str, Any], out: Any) -> bool:
    """True iff `out` is exactly the correct answer for the request."""
    return out == expected_output(component, payload)


def diff(component: str, payload: Dict[str, Any], out: Any) -> Optional[Dict[str, Any]]:
    """Field-level expected-vs-got for a wrong output; None if correct.
    Used only to make a missed detection concrete in the evidence."""
    exp = expected_output(component, payload)
    if out == exp:
        return None
    if not isinstance(out, dict):
        return {"expected": exp, "got": out}
    fields: Dict[str, Any] = {}
    for k in exp:
        if not isinstance(out, dict) or out.get(k) != exp[k]:
            fields[k] = {"expected": exp[k], "got": out.get(k) if isinstance(out, dict) else out}
    return fields
