"""Uncertainty-aware eligibility and dual-efficiency winner selection."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Dict, List

from .metrics import compare_paired
from .policies import PolicyOutcome


@dataclass(frozen=True)
class SelectionThresholds:
    min_success_ci_lower: float = 0.78
    max_wrong_ci_upper: float = 0.02
    max_mean_cost_ci_upper: float = 1.75
    max_p95_latency_ci_upper: float = 80.0

    def to_dict(self) -> Dict[str, float]:
        return asdict(self)


def _eligibility(
    metrics: Dict[str, Any],
    thresholds: SelectionThresholds,
) -> Dict[str, Any]:
    checks = {
        "success_lower_bound": (
            metrics["user_visible_correct_success"]["wilson_ci95"][0]
            >= thresholds.min_success_ci_lower
        ),
        "wrong_answer_upper_bound": (
            metrics["wrong_visible_answer"]["wilson_ci95"][1]
            <= thresholds.max_wrong_ci_upper
        ),
        "mean_cost_upper_bound": (
            metrics["mean_cost"]["bootstrap_ci95"][1]
            <= thresholds.max_mean_cost_ci_upper
        ),
        "p95_latency_upper_bound": (
            metrics["p95_latency"]["bootstrap_ci95"][1]
            <= thresholds.max_p95_latency_ci_upper
        ),
    }
    return {"checks": checks, "eligible": all(checks.values())}


def select_policy(
    metrics_by_policy: Dict[str, Dict[str, Any]],
    outcomes_by_policy: Dict[str, List[PolicyOutcome]],
    thresholds: SelectionThresholds = SelectionThresholds(),
) -> Dict[str, Any]:
    eligibility = {
        policy: _eligibility(metrics, thresholds)
        for policy, metrics in metrics_by_policy.items()
    }
    candidates = [
        policy
        for policy, result in eligibility.items()
        if result["eligible"] and policy != "P0_no_recovery"
    ]
    if not candidates:
        return {
            "winner": None,
            "thresholds": thresholds.to_dict(),
            "eligibility": eligibility,
            "eligible_candidates": [],
            "reason": "no candidate clears all uncertainty-aware thresholds",
            "dominance_proven": False,
        }

    top_cost = max(
        candidates,
        key=lambda policy: metrics_by_policy[policy]["success_per_cost"]["value"],
    )
    top_latency = max(
        candidates,
        key=lambda policy: metrics_by_policy[policy][
            "success_per_100_latency"
        ]["value"],
    )
    winner = top_cost if top_cost == top_latency else None
    comparisons = {}
    dominance = winner is not None
    if winner is not None:
        for other in candidates:
            if other == winner:
                continue
            paired = compare_paired(
                outcomes_by_policy[other], outcomes_by_policy[winner]
            )
            comparisons[other] = paired
            dominance = dominance and (
                paired["success_per_cost_delta"]["paired_bootstrap_ci95"][0] > 0
                and paired["success_per_100_latency_delta"][
                    "paired_bootstrap_ci95"
                ][0] > 0
            )
    if not dominance:
        winner = None
    return {
        "winner": winner,
        "thresholds": thresholds.to_dict(),
        "eligibility": eligibility,
        "eligible_candidates": candidates,
        "point_leader_success_per_cost": top_cost,
        "point_leader_success_per_latency": top_latency,
        "paired_dominance_vs_other_eligible": comparisons,
        "dominance_proven": dominance,
        "reason": (
            "one eligible policy leads both efficiency metrics and both paired "
            "95% bootstrap difference intervals remain above zero"
            if winner else
            "no unique policy has uncertainty-backed dominance on both efficiencies"
        ),
    }
