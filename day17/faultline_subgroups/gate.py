"""The measurement gate — minimum sample size + multiple-comparison discipline.

Subgroup analysis is where honest evaluations go to die: slice finely enough and
noise looks like a finding, and testing many subgroups against a headline inflates
false positives. Two disciplines defend against that:

  * MINIMUM SAMPLE — a subgroup with fewer than MIN_SAMPLES observations is marked
    `insufficient` and cannot support a conclusion (its Wilson interval is reported
    but no claim is drawn from it).
  * MULTIPLE COMPARISON — when many subgroups are each tested against the headline,
    Holm-Bonferroni controls the family-wise error rate, so a "contradiction" has
    to survive correction to count as significant.
"""
from __future__ import annotations

import math
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT / "day14") not in sys.path:
    sys.path.insert(0, str(_ROOT / "day14"))

from faultline_stats import wilson_interval  # noqa: E402 (Day 14)
from faultline_stats.mathfns import norm_cdf  # noqa: E402

MIN_SAMPLES = 5


def subgroup_rate(correct: int, n: int) -> Dict[str, Any]:
    lo, hi = wilson_interval(correct, n)
    return {"n": n, "correct": correct,
            "rate": round(correct / n, 4) if n else None,
            "wilson_ci95": [round(lo, 4), round(hi, 4)],
            "reportable": n >= MIN_SAMPLES,
            "insufficient": n < MIN_SAMPLES}


def one_proportion_p(correct: int, n: int, p0: float) -> float:
    """Two-sided z-test that a subgroup rate differs from the headline p0.
    Returns 1.0 when the test is undefined (n=0 or p0 at a boundary)."""
    if n == 0 or p0 <= 0.0 or p0 >= 1.0:
        return 1.0
    phat = correct / n
    se = math.sqrt(p0 * (1 - p0) / n)
    if se == 0:
        return 1.0
    z = (phat - p0) / se
    return round(2 * (1 - norm_cdf(abs(z))), 6)


def holm_bonferroni(pvalues: List[float], alpha: float = 0.05) -> List[bool]:
    """Holm step-down. Returns, in the ORIGINAL order, whether each hypothesis is
    rejected (significant) after controlling the family-wise error rate."""
    m = len(pvalues)
    if m == 0:
        return []
    order = sorted(range(m), key=lambda i: pvalues[i])
    reject = [False] * m
    for rank, idx in enumerate(order):
        threshold = alpha / (m - rank)
        if pvalues[idx] <= threshold:
            reject[idx] = True
        else:
            break            # Holm stops at the first non-rejection
    return reject


def apply_gate(subgroups: List[Dict[str, Any]], headline_rate: float,
               alpha: float = 0.05) -> List[Dict[str, Any]]:
    """Attach a raw p-value, a Holm-adjusted significance flag, and the min-sample
    verdict to each subgroup's test against the headline rate. Only REPORTABLE
    subgroups are entered into the multiple-comparison family."""
    reportable_idx = [i for i, s in enumerate(subgroups) if s["reportable"]]
    pvals = [one_proportion_p(subgroups[i]["correct"], subgroups[i]["n"], headline_rate)
             for i in reportable_idx]
    rejects = holm_bonferroni(pvals, alpha)
    reject_map = {reportable_idx[j]: rejects[j] for j in range(len(reportable_idx))}
    praw_map = {reportable_idx[j]: pvals[j] for j in range(len(reportable_idx))}

    out = []
    for i, s in enumerate(subgroups):
        row = dict(s)
        lo, hi = s["wilson_ci95"]
        row["headline_rate"] = headline_rate
        row["p_vs_headline"] = praw_map.get(i)          # None if insufficient
        row["significant_holm"] = reject_map.get(i, False)
        # pointwise contradiction: the subgroup's point estimate is on the far side
        # of the headline (a direction disagreement, regardless of significance).
        row["contradicts_pointwise"] = s["rate"] is not None and s["rate"] != headline_rate
        # CI contradiction: the subgroup's own 95% interval EXCLUDES the headline —
        # the subgroup's data is inconsistent with the headline value.
        row["ci_excludes_headline"] = (headline_rate < lo) or (headline_rate > hi)
        out.append(row)
    return out
