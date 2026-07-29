"""Policy outcome, efficiency, uncertainty, and paired statistics."""
from __future__ import annotations

import hashlib
import math
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Sequence, Tuple

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT / "day14") not in sys.path:
    sys.path.insert(0, str(_ROOT / "day14"))

from faultline_stats import bootstrap_ci, mcnemar_from_pairs, wilson_interval  # noqa: E402

from .policies import PolicyOutcome


def _rate(count: int, n: int) -> Dict[str, Any]:
    lo, hi = wilson_interval(count, n)
    return {
        "count": count,
        "n": n,
        "rate": round(count / n, 4),
        "wilson_ci95": [round(lo, 4), round(hi, 4)],
    }


def _p95(values: Sequence[float]) -> float:
    ordered = sorted(values)
    # Nearest-rank p95: ceil(.95 * n), converted to a zero-based index.
    index = max(0, min(len(ordered) - 1, math.ceil(0.95 * len(ordered)) - 1))
    return round(ordered[index], 4)


def _bootstrap_seed(label: str) -> int:
    return int.from_bytes(hashlib.sha256(label.encode("utf-8")).digest()[:4], "big")


def _ratio(sample: Sequence[PolicyOutcome], denominator: str, scale: float) -> float:
    successes = sum(outcome.correct_answer for outcome in sample)
    total = sum(getattr(outcome, denominator) for outcome in sample)
    return scale * successes / total


def summarize_policy(
    outcomes: List[PolicyOutcome],
    bootstrap_iters: int = 1500,
) -> Dict[str, Any]:
    n = len(outcomes)
    policy = outcomes[0].policy
    success = sum(outcome.correct_answer for outcome in outcomes)
    visible = sum(outcome.visible_answer for outcome in outcomes)
    wrong = sum(outcome.wrong_visible_answer for outcome in outcomes)
    contained = sum(outcome.contained for outcome in outcomes)
    costs = [outcome.cost for outcome in outcomes]
    latencies = [outcome.latency for outcome in outcomes]
    mean_cost_lo, mean_cost_hi = bootstrap_ci(
        costs, iters=bootstrap_iters, seed=_bootstrap_seed(policy + ":cost")
    )
    p95_lo, p95_hi = bootstrap_ci(
        latencies,
        iters=bootstrap_iters,
        seed=_bootstrap_seed(policy + ":p95"),
        statistic=_p95,
    )
    spc = _ratio(outcomes, "cost", 1.0)
    spl = _ratio(outcomes, "latency", 100.0)
    spc_lo, spc_hi = bootstrap_ci(
        outcomes,
        iters=bootstrap_iters,
        seed=_bootstrap_seed(policy + ":spc"),
        statistic=lambda sample: _ratio(sample, "cost", 1.0),
    )
    spl_lo, spl_hi = bootstrap_ci(
        outcomes,
        iters=bootstrap_iters,
        seed=_bootstrap_seed(policy + ":spl"),
        statistic=lambda sample: _ratio(sample, "latency", 100.0),
    )
    return {
        "policy": policy,
        "n": n,
        "user_visible_correct_success": _rate(success, n),
        "visible_answer": _rate(visible, n),
        "wrong_visible_answer": _rate(wrong, n),
        "contained": _rate(contained, n),
        "mean_cost": {
            "value": round(sum(costs) / n, 4),
            "bootstrap_ci95": [round(mean_cost_lo, 4), round(mean_cost_hi, 4)],
        },
        "p95_latency": {
            "value": _p95(latencies),
            "bootstrap_ci95": [round(p95_lo, 4), round(p95_hi, 4)],
        },
        "mean_latency": round(sum(latencies) / n, 4),
        "success_per_cost": {
            "value": round(spc, 4),
            "bootstrap_ci95": [round(spc_lo, 4), round(spc_hi, 4)],
        },
        "success_per_100_latency": {
            "value": round(spl, 4),
            "bootstrap_ci95": [round(spl_lo, 4), round(spl_hi, 4)],
        },
        "statuses": dict(
            sorted(Counter(outcome.status for outcome in outcomes).items())
        ),
    }


def _paired_bootstrap(
    a: List[PolicyOutcome],
    b: List[PolicyOutcome],
    statistic,
    label: str,
    iters: int = 2000,
) -> Tuple[float, float]:
    pairs = list(zip(a, b))
    return bootstrap_ci(
        pairs,
        iters=iters,
        seed=_bootstrap_seed(label),
        statistic=statistic,
    )


def compare_paired(
    baseline: List[PolicyOutcome],
    candidate: List[PolicyOutcome],
    bootstrap_iters: int = 2000,
) -> Dict[str, Any]:
    if len(baseline) != len(candidate):
        raise ValueError("paired policies need equal populations")
    if [outcome.seed for outcome in baseline] != [
        outcome.seed for outcome in candidate
    ]:
        raise ValueError("paired policy seeds are not aligned")
    label = baseline[0].policy + "->" + candidate[0].policy
    pairs = list(zip(baseline, candidate))

    def mean_delta(sample, field):
        return sum(
            getattr(after, field) - getattr(before, field)
            for before, after in sample
        ) / len(sample)

    def efficiency_delta(sample, denominator, scale):
        before_success = sum(before.correct_answer for before, _ in sample)
        after_success = sum(after.correct_answer for _, after in sample)
        before_denom = sum(getattr(before, denominator) for before, _ in sample)
        after_denom = sum(getattr(after, denominator) for _, after in sample)
        return (
            scale * after_success / after_denom
            - scale * before_success / before_denom
        )

    cost_ci = _paired_bootstrap(
        baseline,
        candidate,
        lambda sample: mean_delta(sample, "cost"),
        label + ":cost",
        bootstrap_iters,
    )
    latency_ci = _paired_bootstrap(
        baseline,
        candidate,
        lambda sample: mean_delta(sample, "latency"),
        label + ":latency",
        bootstrap_iters,
    )
    spc_ci = _paired_bootstrap(
        baseline,
        candidate,
        lambda sample: efficiency_delta(sample, "cost", 1.0),
        label + ":spc",
        bootstrap_iters,
    )
    spl_ci = _paired_bootstrap(
        baseline,
        candidate,
        lambda sample: efficiency_delta(sample, "latency", 100.0),
        label + ":spl",
        bootstrap_iters,
    )
    base_success = sum(outcome.correct_answer for outcome in baseline)
    candidate_success = sum(outcome.correct_answer for outcome in candidate)
    return {
        "baseline": baseline[0].policy,
        "candidate": candidate[0].policy,
        "n": len(pairs),
        "same_seed_population": True,
        "success_mcnemar": mcnemar_from_pairs(
            [outcome.correct_answer for outcome in baseline],
            [outcome.correct_answer for outcome in candidate],
        ),
        "success_rate_delta": round(
            (candidate_success - base_success) / len(pairs), 4
        ),
        "mean_cost_delta": {
            "value": round(mean_delta(pairs, "cost"), 4),
            "paired_bootstrap_ci95": [round(cost_ci[0], 4), round(cost_ci[1], 4)],
        },
        "mean_latency_delta": {
            "value": round(mean_delta(pairs, "latency"), 4),
            "paired_bootstrap_ci95": [
                round(latency_ci[0], 4),
                round(latency_ci[1], 4),
            ],
        },
        "success_per_cost_delta": {
            "value": round(efficiency_delta(pairs, "cost", 1.0), 4),
            "paired_bootstrap_ci95": [round(spc_ci[0], 4), round(spc_ci[1], 4)],
        },
        "success_per_100_latency_delta": {
            "value": round(efficiency_delta(pairs, "latency", 100.0), 4),
            "paired_bootstrap_ci95": [round(spl_ci[0], 4), round(spl_ci[1], 4)],
        },
    }
