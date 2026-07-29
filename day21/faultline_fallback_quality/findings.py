"""Render the committed Q4 findings from the measured report."""
from __future__ import annotations

from typing import Any, Dict, List


def _row(name: str, metrics: Dict[str, Any]) -> str:
    return (
        f"| {name} | {metrics['availability']['rate']} | "
        f"{metrics['oracle_correctness_given_answered']['rate']} | "
        f"{metrics['strict_quality_given_answered']['rate']} | "
        f"{metrics['strict_quality_service_rate']['rate']} |"
    )


def render_findings(report: Dict[str, Any]) -> str:
    comparison = report["comparison"]
    detector = report["degradation_detector"]
    attack = report["silent_degradation_attack"]
    q4 = report["q4_findings"]
    fallback = comparison["fallback_enabled"]["fallback_quality"]
    lines: List[str] = [
        "# Q4 — Availability versus silent fallback degradation",
        "",
        f"**Answer: yes.** {q4['finding']}",
        "",
        "## Availability and quality (same seeded requests)",
        "",
        "| configuration | availability | oracle correctness / answered | "
        "strict quality / answered | strict-quality service rate |",
        "|---|---:|---:|---:|---:|",
        _row("primary only", comparison["primary_only"]),
        _row("fallback enabled", comparison["fallback_enabled"]),
        "",
        f"- Availability change: **{comparison['effects']['availability_gain']:+}**.",
        "- Strict quality among answered change: "
        f"**{comparison['effects']['strict_quality_given_answered_change']:+}**.",
        "- Strict-quality service-rate change: "
        f"**{comparison['effects']['strict_quality_service_rate_change']:+}**.",
        f"- Fallback slice: {fallback['strictly_acceptable']['count']}/"
        f"{fallback['fallback_answers']} strictly acceptable; "
        f"{fallback['silently_degraded']['count']}/"
        f"{fallback['fallback_answers']} silently degraded.",
        "",
        q4["denominator_note"],
        "",
        "## Silent-degradation attack",
        "",
        f"The attack held availability at **{attack['system_availability']}** while "
        f"delivering **{attack['bad_fallback_answers']}** bad fallback answers. "
        "The availability-only monitor and the route-level degraded-flag monitor "
        "both raised zero alerts.",
        "",
        "The quality detector's fallback-only confusion matrix is "
        f"`{detector['confusion']}`: recall **{detector['recall']['rate']}** "
        f"(95% Wilson CI {detector['recall']['wilson_ci95']}), precision "
        f"**{detector['precision']['rate']}** "
        f"(95% Wilson CI {detector['precision']['wilson_ci95']}). Every false "
        "negative is committed in `degradation_detector.json`.",
        "",
        "## Judge caveats (load-bearing)",
        "",
    ]
    lines.extend(f"- {caveat}" for caveat in q4["judge_caveats"])
    lines.extend([
        "",
        "The detector therefore supplies an alert, not truth. Day-1 oracle results "
        "and the strict human rubric remain separate; the judge never contributes "
        "to core success.",
        "",
        "## Operating conclusion",
        "",
        q4["operating_rule"],
        "",
        f"Fail-condition guard passed: **{report['fail_condition_guard']['passed']}** "
        "(availability and fallback quality are reported together).",
        "",
    ])
    return "\n".join(lines)
