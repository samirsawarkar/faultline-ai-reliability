"""Agreement + bias metrics: raw agreement, Cohen's kappa, positional bias, slices.

All chance-corrected where it matters (Cohen's kappa, not just raw agreement),
with Wilson intervals (Day 14) on agreement rates, and every metric broken down by
slice so a single number cannot hide where the judge is unreliable.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Callable, Dict, List, Sequence, Tuple

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT / "day14") not in sys.path:
    sys.path.insert(0, str(_ROOT / "day14"))

from faultline_stats import wilson_interval  # noqa: E402 (Day 14)

_LABELS = ("accept", "reject")


def raw_agreement(a: Sequence[str], b: Sequence[str]) -> float:
    if len(a) != len(b) or not a:
        raise ValueError("need equal, non-empty label sequences")
    return sum(1 for x, y in zip(a, b) if x == y) / len(a)


def cohen_kappa(a: Sequence[str], b: Sequence[str]) -> float:
    """Chance-corrected agreement for two raters over a fixed label set.
    kappa = (po - pe) / (1 - pe); 1.0 perfect, 0.0 chance, <0 worse than chance."""
    n = len(a)
    if n == 0 or len(b) != n:
        raise ValueError("need equal, non-empty label sequences")
    po = raw_agreement(a, b)
    pe = 0.0
    for lab in _LABELS:
        pa = sum(1 for x in a if x == lab) / n
        pb = sum(1 for y in b if y == lab) / n
        pe += pa * pb
    if pe == 1.0:
        return 1.0                       # both raters constant and identical
    return (po - pe) / (1 - pe)


def confusion(judge: Sequence[str], human: Sequence[str]) -> Dict[str, int]:
    """Judge vs human, treating 'accept' as the positive class."""
    tp = fp = fn = tn = 0
    for j, h in zip(judge, human):
        if j == "accept" and h == "accept":
            tp += 1
        elif j == "accept" and h == "reject":
            fp += 1              # judge over-accepts (lenient)
        elif j == "reject" and h == "accept":
            fn += 1              # judge over-rejects (strict)
        else:
            tn += 1
    return {"tp": tp, "fp": fp, "fn": fn, "tn": tn}


def agreement_block(judge: Sequence[str], human: Sequence[str]) -> Dict[str, Any]:
    n = len(judge)
    agree = sum(1 for j, h in zip(judge, human) if j == h)
    lo, hi = wilson_interval(agree, n)
    return {
        "n": n,
        "raw_agreement": round(raw_agreement(judge, human), 4),
        "raw_agreement_ci95": [round(lo, 4), round(hi, 4)],
        "cohen_kappa": round(cohen_kappa(judge, human), 4),
        "confusion_judge_vs_human": confusion(judge, human),
    }


def per_slice_agreement(items: List[Dict[str, Any]], judge_labels: List[str]
                        ) -> Dict[str, Any]:
    by_slice: Dict[str, Dict[str, int]] = {}
    for it, jl in zip(items, judge_labels):
        s = by_slice.setdefault(it["slice"], {"agree": 0, "n": 0})
        s["n"] += 1
        s["agree"] += int(jl == it["human_label"])
    out = {}
    for s, c in by_slice.items():
        out[s] = {"n": c["n"], "agreement": round(c["agree"] / c["n"], 4),
                  "disagreements": c["n"] - c["agree"]}
    return out


def positional_bias(pairs: List[Dict[str, Any]],
                    compare_positions: Callable[[Dict, Dict, Dict], str]
                    ) -> Dict[str, Any]:
    """Present each pair in BOTH orders; a fair judge picks the same underlying
    candidate both times. An order-dependent decision is positional bias."""
    per_kind: Dict[str, Dict[str, int]] = {}
    order_dependent_total = 0
    for p in pairs:
        ref, a, b = p["reference"], p["cand_a"], p["cand_b"]
        # order 1: (a, b); order 2: (b, a). Map the winning POSITION back to a/b.
        w1 = "a" if compare_positions(ref, a, b) == "first" else "b"
        w2 = "b" if compare_positions(ref, b, a) == "first" else "a"
        order_dependent = w1 != w2                # the winner flipped with order
        k = per_kind.setdefault(p["kind"], {"n": 0, "order_dependent": 0})
        k["n"] += 1
        k["order_dependent"] += int(order_dependent)
        order_dependent_total += int(order_dependent)
    by_kind = {k: {"n": c["n"], "order_dependent": c["order_dependent"],
                   "bias_rate": round(c["order_dependent"] / c["n"], 4)}
               for k, c in per_kind.items()}
    n = len(pairs)
    return {"n_pairs": n, "order_dependent_total": order_dependent_total,
            "positional_bias_rate": round(order_dependent_total / n, 4),
            "by_kind": by_kind}


def kappa_label(kappa: float) -> str:
    """Landis & Koch bands, for plain-English reporting."""
    if kappa < 0.0:
        return "worse than chance"
    if kappa < 0.20:
        return "slight"
    if kappa < 0.40:
        return "fair"
    if kappa < 0.60:
        return "moderate"
    if kappa < 0.80:
        return "substantial"
    return "almost perfect"
