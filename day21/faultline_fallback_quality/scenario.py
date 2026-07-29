"""The paired Day-21 primary/fallback experiment.

Both configurations see the same 120 request seeds and the same deterministic
primary outage (every third request). The primary-only configuration leaves those
40 requests unanswered. The fallback-enabled configuration serves them from the
Day-20 secondary route, but cycles through four quality slices:

  clear_accept       exact fallback
  clear_reject       wrong value
  borderline_tokens  correct value, corrupted token context
  borderline_extra   correct value/tokens, fabricated field

This creates the failure we need to measure: availability is perfect, provenance
truthfully says "secondary", but `is_degraded` remains false because Day 20's flag
describes the route tier—not the semantic quality of its answer.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict, List

_ROOT = Path(__file__).resolve().parents[2]
for _day in ("day01", "day16", "day20"):
    _path = str(_ROOT / _day)
    if _path not in sys.path:
        sys.path.insert(0, _path)

from faultline import oracle_check  # noqa: E402 (Day 1)
from faultline_breaker import Served, route_fallback  # noqa: E402 (Day 20)
from faultline_judge import gold_acceptable, gold_quality  # noqa: E402 (Day 16)

N = 120
SEED_BASE = 2026073100
FALLBACK_VARIANTS = (
    "clear_accept",
    "clear_reject",
    "borderline_tokens",
    "borderline_extra",
)


def _reference(index: int) -> Dict[str, Any]:
    value = (index + 1) * 10
    return {"value": value, "tokens": [index, index + 1, index + 2, index + 3]}


def _candidate(reference: Dict[str, Any], variant: str) -> Dict[str, Any]:
    if variant == "clear_accept":
        return {"value": reference["value"], "tokens": list(reference["tokens"])}
    if variant == "clear_reject":
        return {"value": reference["value"] + 37, "tokens": [9, 9, 9, 9]}
    if variant == "borderline_tokens":
        return {
            "value": reference["value"],
            "tokens": [token + 2 for token in reference["tokens"]],
        }
    if variant == "borderline_extra":
        return {
            "value": reference["value"],
            "tokens": list(reference["tokens"]),
            "note": "synthesized",
        }
    raise ValueError(f"unknown fallback variant: {variant}")


def _primary_is_up(index: int) -> bool:
    return index % 3 != 0


def _evaluate(
    index: int,
    served: Served,
    candidate: Dict[str, Any] = None,
    fallback_variant: str = None,
) -> Dict[str, Any]:
    reference = _reference(index)
    source = f"doc-{index:03d}"
    if served.answered:
        assert candidate is not None
        oracle = oracle_check(
            {"id": f"q-{index:03d}", "answer": str(reference["value"]),
             "required_source": source},
            {"answer": str(candidate.get("value", "")), "cited_sources": [source]},
        )
        strict_quality = gold_acceptable(reference, candidate)
        quality_score = gold_quality(reference, candidate)
    else:
        oracle = {
            "question_id": f"q-{index:03d}",
            "correct": False,
            "cited_required": False,
            "passed": False,
        }
        strict_quality = False
        quality_score = 0

    return {
        "request_index": index,
        "seed": SEED_BASE + index,
        "primary_would_be_up": _primary_is_up(index),
        "route": (
            "fallback" if served.is_fallback
            else ("primary" if served.served_by == "primary" else "unanswered")
        ),
        "answered": served.answered,
        "provenance": served.to_dict(),
        "reference": reference,
        "candidate": candidate,
        "fallback_variant": fallback_variant,
        "oracle": oracle,
        "oracle_passed": bool(oracle["passed"]),
        "strict_quality_score": quality_score,
        "strict_quality_acceptable": strict_quality,
    }


def primary_only_record(index: int) -> Dict[str, Any]:
    """One request through the primary-only configuration."""
    if _primary_is_up(index):
        reference = _reference(index)
        return _evaluate(
            index,
            Served("primary", is_fallback=False, is_degraded=False, answered=True),
            _candidate(reference, "clear_accept"),
        )
    return _evaluate(index, Served(None, False, False, False))


def fallback_enabled_record(index: int) -> Dict[str, Any]:
    """The same request with Day-20 fallback enabled."""
    reference = _reference(index)
    if _primary_is_up(index):
        return _evaluate(
            index,
            Served("primary", is_fallback=False, is_degraded=False, answered=True),
            _candidate(reference, "clear_accept"),
        )

    fallback_rank = index // 3
    variant = FALLBACK_VARIANTS[fallback_rank % len(FALLBACK_VARIANTS)]
    served = route_fallback(secondary_up=True)
    return _evaluate(index, served, _candidate(reference, variant), variant)


def build_paired_records(n: int = N) -> Dict[str, List[Dict[str, Any]]]:
    """Aligned configurations: element i in each list is the same request seed."""
    if n <= 0:
        raise ValueError("n must be positive")
    return {
        "primary_only": [primary_only_record(i) for i in range(n)],
        "fallback_enabled": [fallback_enabled_record(i) for i in range(n)],
    }
