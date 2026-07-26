"""A NARROW fallback-quality rubric — the only thing the judge is allowed to score.

Q2 (Day 15) isolated the faults no deterministic detector can catch: the semantic
escapes F3 `drift_value` and F5 `context_drift`. When a future recovery layer
produces a *fallback* output for one of those, we need a semantic judgement of
whether that fallback is acceptable. That is the ONLY question this rubric asks —
not "is the system correct" (the Day-1 oracle owns that), just "is this one
fallback candidate acceptable quality."

The rubric is three explicit, checkable criteria applied to a candidate against a
known reference:

  C1  VALUE CORRECT   — the key field equals the reference value.
  C2  TOKENS EXACT    — the token list equals the reference exactly (order + values).
  C3  NO FABRICATION  — the candidate adds no field the reference did not have.

A candidate is ACCEPTABLE iff all three hold. `gold_quality` is what a human
applies (all three, strictly). `judge_estimate` is what a cheap judge is *likely*
to approximate — and the gap between them is exactly what Day 16 measures.
"""
from __future__ import annotations

from typing import Any, Dict, List

CRITERIA = ("value_correct", "tokens_exact", "no_fabrication")
_REFERENCE_FIELDS = ("value", "tokens")


def _checks(reference: Dict[str, Any], candidate: Dict[str, Any]) -> Dict[str, bool]:
    return {
        "value_correct": candidate.get("value") == reference.get("value"),
        "tokens_exact": candidate.get("tokens") == reference.get("tokens"),
        "no_fabrication": set(candidate.keys()) <= set(reference.keys()),
    }


def gold_quality(reference: Dict[str, Any], candidate: Dict[str, Any]) -> int:
    """The human rubric: number of criteria satisfied (0..3). Acceptable iff 3.
    This is the policy a trusted human annotator applies — the ground truth the
    judge is validated against, never derived from the judge."""
    return sum(_checks(reference, candidate).values())


def gold_acceptable(reference: Dict[str, Any], candidate: Dict[str, Any]) -> bool:
    return gold_quality(reference, candidate) == len(CRITERIA)


def judge_estimate(reference: Dict[str, Any], candidate: Dict[str, Any]) -> int:
    """What a cheap judge is *modelled* to approximate: it checks the value, the
    token LENGTH (not exact order), and fabrication — i.e. it has a known blind
    spot for token-order drift. This models a realistic LLM judge that keys on the
    headline value and gross structure but misses subtle ordering. It is NOT the
    rubric; the whole point of Day 16 is to measure how far it falls short."""
    value_ok = candidate.get("value") == reference.get("value")
    toks = candidate.get("tokens")
    ref_toks = reference.get("tokens")
    length_ok = isinstance(toks, list) and isinstance(ref_toks, list) and len(toks) == len(ref_toks)
    no_fab = set(candidate.keys()) <= set(reference.keys())
    return int(value_ok) + int(length_ok) + int(no_fab)


def criteria_report(reference: Dict[str, Any], candidate: Dict[str, Any]) -> Dict[str, Any]:
    checks = _checks(reference, candidate)
    return {"criteria": checks, "gold_quality": sum(checks.values()),
            "gold_acceptable": all(checks.values())}


RUBRIC_TEXT = """# FAULTLINE fallback-quality rubric (NARROW)

Scope: judge ONE fallback candidate for a semantic-escape fault (F3 drift_value,
F5 context_drift). This rubric does NOT decide overall system success — that is the
oracle's job (Day 1) and the judge is forbidden from it (see JUDGE_CARD.md).

A candidate is ACCEPTABLE iff all three criteria hold:

1. **Value correct** — the key value equals the reference value exactly.
2. **Tokens exact** — the token list equals the reference exactly (order and values).
3. **No fabrication** — the candidate introduces no field absent from the reference.

Any single failing criterion makes the candidate UNACCEPTABLE. Borderline cases
(e.g. correct value but reordered tokens, or an added "note" field) are
UNACCEPTABLE under this rubric even though they look plausible — that strictness is
deliberate, and it is where cheap judges are expected to disagree.
"""


def rubric_criteria() -> List[str]:
    return list(CRITERIA)
