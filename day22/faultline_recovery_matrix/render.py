"""Render the six-mechanism matrix and aggregate trade-offs as Markdown."""
from __future__ import annotations

from typing import Any, Dict, List


def _short(mechanism: str) -> str:
    return mechanism.split("_", 1)[0]


def render_matrix(report: Dict[str, Any]) -> str:
    matrix = report["matrix"]
    cells = {
        (cell["mechanism"], cell["fault"]): cell for cell in matrix["cells"]
    }
    lines: List[str] = [
        "# Day 22 — Six-mechanism recovery matrix",
        "",
        "Every cell is paired against no recovery on the same 24 seeds "
        "(18 injected faults + 6 clean controls). `S` is correct-success rate; "
        "`ΔC` and `ΔL` are paired mean cost and latency changes; `H` is measured "
        "recovery-induced harm events.",
        "",
        "| mechanism | F1 | F2 | F3 | F4 | F5 | F6 |",
        "|---|---|---|---|---|---|---|",
    ]
    for mechanism in matrix["design"]["mechanisms"]:
        row = [f"| {_short(mechanism)} |"]
        for fault in matrix["design"]["faults"]:
            cell = cells[(mechanism, fault)]
            row.append(
                " S={s}; ΔC={c:+}; ΔL={l:+}; H={h} |".format(
                    s=cell["with_mechanism"]["success"]["rate"],
                    c=cell["paired"]["cost_delta"]["mean"],
                    l=cell["paired"]["latency_delta"]["mean"],
                    h=cell["recovery_induced_harms"]["count"],
                )
            )
        lines.append("".join(row))

    lines.extend([
        "",
        "## Aggregate outcome, cost, and latency (144 paired requests per mechanism)",
        "",
        "| mechanism | correct success | availability | contained | answered wrong | "
        "mean cost | p95 latency | recoveries | regressions | measured harms |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ])
    baseline = matrix["mechanism_summaries"][
        matrix["design"]["mechanisms"][0]
    ]["baseline"]
    lines.append(
        f"| no recovery | {baseline['success']['rate']} | "
        f"{baseline['availability']['rate']} | {baseline['contained']['rate']} | "
        f"{baseline['answered_wrong']['rate']} | {baseline['mean_cost']} | "
        f"{baseline['p95_latency']} | — | — | — |"
    )
    for mechanism in matrix["design"]["mechanisms"]:
        summary = matrix["mechanism_summaries"][mechanism]
        after = summary["with_mechanism"]
        paired = summary["paired"]
        lines.append(
            f"| {_short(mechanism)} | {after['success']['rate']} | "
            f"{after['availability']['rate']} | {after['contained']['rate']} | "
            f"{after['answered_wrong']['rate']} | {after['mean_cost']} | "
            f"{after['p95_latency']} | {paired['outcome_recoveries']} | "
            f"{paired['outcome_regressions']} | "
            f"{summary['recovery_induced_harms']['count']} |"
        )

    lines.extend([
        "",
        "## Recovery-induced harms (none hidden)",
        "",
    ])
    for mechanism in matrix["design"]["mechanisms"]:
        audit = matrix["recovery_induced_harm_audit"]["by_mechanism"][mechanism]
        lines.append(
            f"- **{_short(mechanism)}:** {audit['count']} — {audit['by_type']}"
        )

    lines.extend([
        "",
        "M1/M2 spend retry budgets on persistent faults; M3 false-opens on healthy "
        "controls after clustered provider failures; M4 can turn an unavailable "
        "failure into an answered-but-wrong fallback; M5 cuts off legitimate long "
        "plans; M6 mistakes legitimate pagination for non-progress. These are "
        "measured effects, not footnotes.",
        "",
        "## Composition conclusion",
        "",
        report["composition_policy"]["rule"],
        "",
        report["composition_policy"]["do_not_compose_blindly"],
        "",
        f"Checkpoint 22 passed: **{report['checkpoint_22']['passed']}**. "
        f"Matrix fail-condition guard passed: "
        f"**{matrix['fail_condition_guard']['passed']}**.",
        "",
    ])
    return "\n".join(lines)
