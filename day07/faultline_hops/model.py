"""Product-model comparison + interval reporting (Build B).

Three curves over n = required hops:

  measured(n)   empirical end-to-end success, with a Wilson 95% CI.
  naive(n)      the compounding fallacy: assume every hop has the SAME
                reliability p1 (the measured single-hop rate) and that hops are
                independent, so success = p1**n. Its band is [lo1**n, hi1**n],
                propagating the single-hop CI.
  corrected(n)  product of the MEASURED per-hop rates, prod_k p_k. This tracks
                the measured curve and demonstrates the mechanism: the gap is
                explained by per-hop reliability declining with depth, not by a
                bug.

Divergence: the smallest n at which the naive band and the measured band are
disjoint — i.e. the data falsifies the constant-per-step assumption.
"""
from __future__ import annotations

from typing import Any, Dict, List

from .stats import rate, wilson_interval
from .sweep import SweepResult


def _round(x: float, places: int = 6) -> float:
    return round(x, places)


def build_curves(sweep: SweepResult) -> Dict[str, Any]:
    cfg = sweep.config

    # single-hop reliability p1 from pooled hop-1 accounting (every run reaches it)
    h1 = sweep.per_hop[1]
    p1 = rate(h1["success"], h1["reached"])
    p1_lo, p1_hi = wilson_interval(h1["success"], h1["reached"])

    # per-hop measured rates (for the corrected product + explanation)
    per_hop: List[Dict[str, Any]] = []
    for k in sorted(sweep.per_hop):
        b = sweep.per_hop[k]
        lo, hi = wilson_interval(b["success"], b["reached"])
        per_hop.append({
            "hop": k,
            "reached": b["reached"],
            "success": b["success"],
            "rate": _round(rate(b["success"], b["reached"])),
            "ci95": [_round(lo), _round(hi)],
        })
    rate_by_hop = {row["hop"]: row["rate"] for row in per_hop}

    points: List[Dict[str, Any]] = []
    first_divergence = None
    corrected_prod = 1.0
    for n in range(1, cfg.max_hops + 1):
        e = sweep.e2e[n]
        m = rate(e["successes"], e["total"])
        m_lo, m_hi = wilson_interval(e["successes"], e["total"])

        naive = p1 ** n
        naive_lo, naive_hi = p1_lo ** n, p1_hi ** n

        corrected_prod *= rate_by_hop.get(n, 0.0)

        # disjoint bands => naive falsified at this n
        disjoint = (naive_lo > m_hi) or (naive_hi < m_lo)
        if disjoint and first_divergence is None:
            first_divergence = n

        points.append({
            "hops": n,
            "measured": _round(m),
            "measured_ci95": [_round(m_lo), _round(m_hi)],
            "naive": _round(naive),
            "naive_ci95": [_round(naive_lo), _round(naive_hi)],
            "corrected": _round(corrected_prod),
            "measured_minus_naive": _round(m - naive),
            "naive_outside_measured_ci": disjoint,
        })

    return {
        "single_hop_reliability": {
            "p1": _round(p1),
            "ci95": [_round(p1_lo), _round(p1_hi)],
            "reached": h1["reached"],
        },
        "per_hop": per_hop,
        "points": points,
        "first_divergence_hop": first_divergence,
    }
