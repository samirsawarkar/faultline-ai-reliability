"""Availability, strict quality, and provenance metrics with explicit denominators."""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict, List

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT / "day14") not in sys.path:
    sys.path.insert(0, str(_ROOT / "day14"))

from faultline_stats import wilson_interval  # noqa: E402 (Day 14)

PROVENANCE_FIELDS = ("served_by", "is_fallback", "is_degraded", "answered")


def rate_block(successes: int, n: int) -> Dict[str, Any]:
    lo, hi = wilson_interval(successes, n)
    return {
        "count": successes,
        "n": n,
        "rate": round(successes / n, 4) if n else None,
        "wilson_ci95": [round(lo, 4), round(hi, 4)],
    }


def provenance_consistent(record: Dict[str, Any]) -> bool:
    p = record.get("provenance", {})
    if not all(field in p for field in PROVENANCE_FIELDS):
        return False
    expected = {
        "primary": (False, False, True),
        "secondary": (True, False, True),
        "degraded": (True, True, True),
        None: (False, False, False),
    }
    if p["served_by"] not in expected:
        return False
    return (
        p["is_fallback"],
        p["is_degraded"],
        p["answered"],
    ) == expected[p["served_by"]]


def summarize(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Summarize without hiding denominator changes.

    `strict_quality_given_answered` answers "how good were delivered answers?"
    `strict_quality_service_rate` treats an unanswered request as not useful and
    answers "how many requests received a strictly acceptable answer?"
    """
    n = len(records)
    answered = [record for record in records if record["answered"]]
    fallback = [
        record for record in records
        if record.get("provenance", {}).get("is_fallback") is True
    ]
    strict_answered = sum(record["strict_quality_acceptable"] for record in answered)
    oracle_answered = sum(record["oracle_passed"] for record in answered)
    complete = sum(
        all(field in record.get("provenance", {}) for field in PROVENANCE_FIELDS)
        for record in records
    )
    consistent = sum(provenance_consistent(record) for record in records)
    fallback_strict = sum(record["strict_quality_acceptable"] for record in fallback)
    silent = sum(
        (not record["strict_quality_acceptable"])
        and not record["provenance"]["is_degraded"]
        for record in fallback
    )
    flagged = sum(record["provenance"]["is_degraded"] for record in fallback)

    return {
        "requests": n,
        "availability": rate_block(len(answered), n),
        "oracle_correctness_given_answered": rate_block(oracle_answered, len(answered)),
        "oracle_service_pass_rate": rate_block(oracle_answered, n),
        "strict_quality_given_answered": rate_block(strict_answered, len(answered)),
        "strict_quality_service_rate": rate_block(strict_answered, n),
        "fallback_quality": {
            "fallback_answers": len(fallback),
            "strictly_acceptable": rate_block(fallback_strict, len(fallback)),
            "silently_degraded": rate_block(silent, len(fallback)),
            "flagged_degraded": rate_block(flagged, len(fallback)),
        },
        "provenance": {
            "complete": rate_block(complete, n),
            "consistent": rate_block(consistent, n),
            "fallback_rate": rate_block(len(fallback), n),
        },
    }
