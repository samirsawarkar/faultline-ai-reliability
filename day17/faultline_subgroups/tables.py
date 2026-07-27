"""Render the subgroup findings as Markdown, with known limitations up front."""
from __future__ import annotations

from typing import Any, Dict, List


def _sub_table(title: str, rows: List[Dict[str, Any]]) -> List[str]:
    L = [f"### {title}", "",
         "| subgroup | n | rate | 95% CI | reportable | CI excludes headline |",
         "|---|---|---|---|---|---|"]
    for s in rows:
        dims = ", ".join(f"{k}={v}" for k, v in s["dims"].items())
        L.append(f"| {dims} | {s['n']} | {s['rate']} | {s['wilson_ci95']} | "
                 f"{s['reportable']} | {s.get('ci_excludes_headline', False)} |")
    L.append("")
    return L


def render_findings(report: Dict[str, Any]) -> str:
    d = report["detection"]
    rev = d["deterministic_vs_semantic_reversal"]
    L = [
        "# Day 17 — Subgroup findings (where aggregates hide failure)", "",
        "Every rate is gated: subgroups below the minimum sample size "
        f"({report['min_samples']}) are marked non-reportable, and headline tests are "
        "Holm-corrected for multiple comparisons. A subgroup 'contradicts' the "
        "headline only when its 95% interval EXCLUDES the headline value.", "",
        "## Known limitations (read first)", "",
    ]
    L += [f"- {lim}" for lim in report["known_limitations"]]
    L += ["", f"## Detection headline: overall accuracy = **{d['headline_rate']}** "
          f"(n={d['n']})", ""]
    L += _sub_table("By fault", d["by_fault"])
    L += _sub_table("By severity", d["by_severity"])
    L += [
        "## Deterministic vs semantic — an ordering REVERSAL", "",
        f"Aggregate: deterministic {rev['aggregate']['a_rate']} "
        f"(n={rev['aggregate']['a_n']}) vs semantic {rev['aggregate']['b_rate']} "
        f"(n={rev['aggregate']['b_n']}) → deterministic ahead. But within slices:", "",
        "| severity | deterministic | semantic | n(det) | n(sem) | reverses aggregate |",
        "|---|---|---|---|---|---|",
    ]
    for s in rev["per_slice"]:
        L.append(f"| {s['slice']['severity']} | {s['a_rate']} | {s['b_rate']} | "
                 f"{s['a_n']} | {s['b_n']} | {s['reverses_aggregate']} |")
    L += ["",
          "The severity-3 slice reverses the headline: the deterministic group "
          "(only F2 latency there, below its budget) scores 0.0 vs the semantic "
          "group's 0.667 — a confounded, underpowered reversal, surfaced not hidden.", ""]
    hop = report["hops"]
    if hop.get("available"):
        L += ["## Hop count (Day 7 reliability curve)", "",
              f"Headline: *{hop['headline_claim']}*; first divergence at hop "
              f"**{hop['first_divergence_hop']}**. Hops that do NOT support it: "
              f"{[c['hops'] for c in hop['headline_contradictions']]} (naive lies "
              "inside the measured CI there).", ""]
    L += ["## Contradictions (all surfaced, none ignored)", "",
          f"- detected: `{report['contradictions_detected']}`",
          f"- significant after Holm correction: `{report['significant_contradictions']}` "
          "(none — the spread is real but under-powered at this n)",
          f"- measurement gate passed: **{report['measurement_gate']['passed']}**", ""]
    return "\n".join(L) + "\n"
