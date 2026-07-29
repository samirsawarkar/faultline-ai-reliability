"""Render a trace-referenced incident narrative from the canonical run."""
from __future__ import annotations

from typing import Any, Dict, List


def render_incident_narrative(
    run: Dict[str, Any],
    stability: Dict[str, Any],
) -> str:
    lines: List[str] = [
        "# INCIDENT — retry/fallback/repetition cascade",
        "",
        "## Summary",
        "",
        f"Incident `{run['incident_id']}` is reproduced from seed "
        f"**{run['seed']}** and configuration digest "
        f"`{run['config_digest']}`. The trace digest is "
        f"`{run['trace_digest']}`.",
        "",
        "A seeded primary latency spike caused a retry, opened the breaker, routed "
        "to a stale fallback that the narrow judge accepted, repeated downstream "
        "verification, and sent repetition recovery back to the same secondary. "
        "The global cost ceiling then stopped final synthesis before it could "
        "return the wrong answer.",
        "",
        "## Causal chain with trace references",
        "",
        "| event | component | observation | supporting span(s) |",
        "|---|---|---|---|",
    ]
    for event in run["events"]:
        refs = ", ".join(f"`{ref}`" for ref in event["span_refs"])
        lines.append(
            f"| {event['event_id']} `{event['label']}` | "
            f"{event['component']} | {event['detail']} | {refs} |"
        )

    lines.extend([
        "",
        "## Why this is a cascade, not a list of faults",
        "",
    ])
    for edge in run["causal_edges"]:
        lines.append(
            f"- **{edge['cause']} → {edge['effect']}**: {edge['relation']}."
        )

    metrics = run["metrics"]
    lines.extend([
        "",
        "The initiating F2 fault alone did not consume the envelope. Recovery "
        "composition propagated it: M2 added a primary call; M3 redirected traffic; "
        "M4 exposed a correlated semantic fault; the quality gate missed it; M6 "
        "re-entered the degraded route. M5 contained the final blast radius.",
        "",
        "## Outcome and blast radius",
        "",
        f"- primary calls: **{metrics['primary_calls']}** "
        f"({metrics['retry_calls_added']} added by retry)",
        f"- fallback calls: **{metrics['fallback_calls']}**",
        f"- repeated verifications: **{metrics['verification_repeats']}**",
        f"- cost: **{metrics['cost']}/{metrics['cost_ceiling']}**; "
        f"steps: **{metrics['steps']}/{metrics['step_ceiling']}**",
        f"- virtual latency: **{metrics['latency']}**",
        "- terminal state: **contained_cost_ceiling**",
        "- user-visible wrong answer: **suppressed**, not counted as success",
        "",
        "## Trace completeness",
        "",
        f"The trace contains **{run['audit']['span_count']}** closed spans, including "
        f"**{run['audit']['error_span_count']}** complete error spans. Parent links, "
        "event-to-span references, and causal-edge endpoints all resolve. "
        f"Trace audit passed: **{run['audit']['passed']}**.",
        "",
        "## Reproduction proof",
        "",
        f"The incident was replayed **{stability['repetitions']}** times in-process "
        "and under four different Python hash seeds. Unique incident digests: "
        f"`{stability['unique_incident_digests']}`; unique trace digests: "
        f"`{stability['unique_trace_digests']}`. Cross-process stable: "
        f"**{stability['cross_process_stable']}**.",
        "",
        "From the repository root:",
        "",
        "```bash",
        "python day23/scripts/replay_once.py --scenario day23/evidence/cascade_scenario.json",
        "```",
        "",
        f"Expected incident digest: `{stability['unique_incident_digests'][0]}`.",
        "",
        "## Causal-analysis caveat",
        "",
        "The graph is intervention-informed within this deterministic simulator: "
        "the seed/config fixes the initiating fault and each edge is backed by an "
        "observed transition. It is not a claim that temporal order alone proves "
        "causality in production; external confounders would require additional "
        "counterfactual or intervention evidence.",
        "",
    ])
    return "\n".join(lines)
