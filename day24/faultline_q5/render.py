"""Render the measured Q5 comparison and conditional recommendation."""
from __future__ import annotations

from typing import Any, Dict, List


def render_q5(report: Dict[str, Any]) -> str:
    experiment = report["experiment"]
    recommendation = report["q5_recommendation"]
    selection = experiment["selection"]
    lines: List[str] = [
        "# Q5 — Cascade success per unit cost and latency",
        "",
        f"**Recommendation: `{recommendation['winner']}`.**",
        "",
        recommendation["statement"],
        "",
        "## Policy comparison (same 400 seeds)",
        "",
        "| policy | correct visible success (95% CI) | wrong visible (95% CI) | "
        "mean cost (95% boot CI) | p95 latency (95% boot CI) | "
        "success/cost (95% boot CI) | success/100 latency (95% boot CI) | eligible |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for policy, metrics in experiment["policy_metrics"].items():
        eligible = selection["eligibility"][policy]["eligible"]
        lines.append(
            f"| {policy} | {metrics['user_visible_correct_success']['rate']} "
            f"{metrics['user_visible_correct_success']['wilson_ci95']} | "
            f"{metrics['wrong_visible_answer']['rate']} "
            f"{metrics['wrong_visible_answer']['wilson_ci95']} | "
            f"{metrics['mean_cost']['value']} {metrics['mean_cost']['bootstrap_ci95']} | "
            f"{metrics['p95_latency']['value']} "
            f"{metrics['p95_latency']['bootstrap_ci95']} | "
            f"{metrics['success_per_cost']['value']} "
            f"{metrics['success_per_cost']['bootstrap_ci95']} | "
            f"{metrics['success_per_100_latency']['value']} "
            f"{metrics['success_per_100_latency']['bootstrap_ci95']} | "
            f"{eligible} |"
        )

    lines.extend([
        "",
        "## Selection rule",
        "",
        "A candidate must clear all confidence-bound thresholds for correct success, "
        "wrong-answer risk, mean cost, and p95 latency. The winner must then lead "
        "both efficiency measures, and its paired bootstrap difference intervals "
        "against every other eligible policy must stay above zero.",
        "",
        f"- eligible candidates: `{selection['eligible_candidates']}`",
        f"- success/cost point leader: `{selection['point_leader_success_per_cost']}`",
        f"- success/latency point leader: `{selection['point_leader_success_per_latency']}`",
        f"- uncertainty-backed dual dominance: **{selection['dominance_proven']}**",
        "",
        "## Paired success versus no recovery",
        "",
    ])
    for policy, paired in experiment["paired_vs_no_recovery"].items():
        mc = paired["success_mcnemar"]
        lines.append(
            f"- **{policy}:** Δsuccess={paired['success_rate_delta']:+}; "
            f"discordant={mc['n_discordant']}, p={mc['p_value']:.6g}, "
            f"significant={mc['significant_at_0.05']}."
        )

    lines.extend([
        "",
        "## Winner under attack",
        "",
    ])
    for name, attack in report["winner_attack"]["attacks"].items():
        metrics = attack["metrics"]
        lines.append(
            f"- **{name}:** success={metrics['user_visible_correct_success']['rate']} "
            f"{metrics['user_visible_correct_success']['wilson_ci95']}, "
            f"mean cost={metrics['mean_cost']['value']}, "
            f"p95 latency={metrics['p95_latency']['value']}, "
            f"recommendation survives={attack['recommendation_survives']}."
        )
    lines.extend([
        "",
        report["winner_attack"]["boundary_finding"],
        "",
        "## Tradeoff statement",
        "",
        recommendation["tradeoff"],
        "",
        "## Model caveats",
        "",
    ])
    lines.extend(f"- {caveat}" for caveat in recommendation["model_caveats"])
    lines.extend([
        "",
        f"Fail-condition guard passed: **{report['fail_condition_guard']['passed']}**. "
        "The winner is never reported without cost, latency, and uncertainty.",
        "",
    ])
    return "\n".join(lines)
