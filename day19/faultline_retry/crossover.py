"""Crossover + the defensible recommended retry region.

Two ceilings make "unacceptable cost / tail latency" concrete: an amplification
ceiling (avg attempts per request) and a p99 latency budget. The crossover is where
extra retries stop buying meaningful success (marginal success gain < threshold).
The recommended budget is the largest K that is BOTH still improving AND under both
ceilings — so, by construction, the recommendation never trades a success bump for
an unacceptable cost/tail blow-up (the mission's fail condition).
"""
from __future__ import annotations

from typing import Any, Dict, List

COST_CEILING_AMP = 2.0        # max avg attempts per request
P99_BUDGET = 120              # max acceptable p99 latency
MIN_MARGINAL_SUCCESS = 0.05   # below this, extra retries are diminishing returns


def _acceptable(pt: Dict[str, Any]) -> bool:
    return pt["amplification"] <= COST_CEILING_AMP and pt["p99_latency"] <= P99_BUDGET


def crossover(points: List[Dict[str, Any]]) -> Dict[str, Any]:
    # first K whose marginal success gain over K-1 falls below the threshold
    crossover_k = points[-1]["K"]
    for i in range(1, len(points)):
        if points[i]["success_rate"] - points[i - 1]["success_rate"] < MIN_MARGINAL_SUCCESS:
            crossover_k = points[i]["K"]
            break

    # ceilings are monotone in K, so acceptable K form a prefix
    last_acceptable = 0
    for pt in points:
        if _acceptable(pt):
            last_acceptable = pt["K"]
        else:
            break

    recommended = max(1, min(last_acceptable, crossover_k))
    rec_pt = points[recommended - 1]
    return {
        "crossover_K": crossover_k,
        "last_acceptable_K": last_acceptable,
        "recommended_max_attempts": recommended,
        "recommended_point": rec_pt,
        "recommendation_within_ceilings": _acceptable(rec_pt),
        "marginal_success": [round(points[i]["success_rate"] - points[i - 1]["success_rate"], 4)
                             for i in range(1, len(points))],
    }


def fail_condition_check(points: List[Dict[str, Any]], recommended: int) -> Dict[str, Any]:
    """The mission fails if a recommended K improves success but breaches a ceiling.
    Confirm the recommendation is under both ceilings, and flag every K that DOES
    breach a ceiling (so it is visible, never silently recommended)."""
    breaching = [{"K": p["K"], "success_rate": p["success_rate"],
                  "amplification": p["amplification"], "p99_latency": p["p99_latency"],
                  "breaches": ([] + (["cost"] if p["amplification"] > COST_CEILING_AMP else [])
                               + (["tail_latency"] if p["p99_latency"] > P99_BUDGET else []))}
                 for p in points if not _acceptable(p)]
    rec_pt = points[recommended - 1]
    return {"recommended": recommended,
            "recommended_within_ceilings": _acceptable(rec_pt),
            "breaching_regions": breaching,
            "respected": _acceptable(rec_pt)}
