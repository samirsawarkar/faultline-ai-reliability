"""Human-readable incident reports, checkpoint, and strong case study."""
from __future__ import annotations

from typing import Any, Dict, List


def _timeline(lines: List[str], items: List[Dict[str, Any]]) -> None:
    lines.extend([
        "| virtual time | event | observation | trace span(s) |",
        "|---:|---|---|---|",
    ])
    for item in items:
        refs = ", ".join(f"`{ref}`" for ref in item["span_refs"])
        lines.append(
            f"| {item['at']} | `{item['event']}` | {item['detail']} | {refs} |"
        )


def render_incident(report: Dict[str, Any]) -> str:
    before = report["before_outcome"]
    after = report["after_outcome"]
    replay = report["replay_summary"]
    lines: List[str] = [
        f"# {report['incident_id']} — {report['title']}",
        "",
        "## Summary",
        "",
        f"Seed `{report['seed']}` replayed the legacy policy as "
        f"**{before['regression']['color']}** and the fixed policy as "
        f"**{after['regression']['color']}** against the same regression "
        f"`{report['regression_test_id']}`.",
        "",
        "## Timeline",
        "",
    ]
    _timeline(lines, report["timeline"])
    lines.extend([
        "",
        "## Impact",
        "",
        report["impact"],
        "",
        "## Detection",
        "",
        report["detection"],
        "",
        "## Root cause",
        "",
        report["root_cause"],
        "",
        "The root cause names the failed system condition, not a person. The "
        "actions below change controls and recovery policy.",
        "",
        "## Contributing factors",
        "",
    ])
    lines.extend(f"- {factor}" for factor in report["contributing_factors"])
    lines.extend([
        "",
        "## Corrective actions",
        "",
    ])
    lines.extend(f"- {action}" for action in report["corrective_actions"])
    lines.extend([
        "",
        "## Fixed timeline",
        "",
    ])
    _timeline(lines, report["fixed_timeline"])
    lines.extend([
        "",
        "## Red → green regression",
        "",
        f"Predicate: **{report['regression_predicate']}**.",
        "",
        f"- before: **{before['regression']['color']}**, terminal "
        f"`{before['terminal']['status']}`, metrics `{before['metrics']}`",
        f"- after: **{after['regression']['color']}**, terminal "
        f"`{after['terminal']['status']}`, metrics `{after['metrics']}`",
        f"- same-seed repetitions per version: **{replay['repetitions_per_version']}**",
        f"- before stable: **{replay['before_stable']}**",
        f"- after stable and stays green: **{replay['after_stable']}**",
        f"- cross-process stable: **{replay['cross_process_stable']}**",
        f"- replay-verified fix: **{replay['replay_verified_fix']}**",
        "",
        "## Trace references",
        "",
        f"- source evidence: `{report['source_artifact']}`",
        f"- legacy replay: `{report['trace_artifacts']['before']}` "
        f"(digest `{before['trace_digest']}`)",
        f"- fixed replay: `{report['trace_artifacts']['after']}` "
        f"(digest `{after['trace_digest']}`)",
        "",
    ])
    return "\n".join(lines)


def render_case_study(report: Dict[str, Any]) -> str:
    incident = report["incident_reports"]["INC-25-001"]
    before = incident["before_outcome"]
    after = incident["after_outcome"]
    return "\n".join([
        "# Case study — the recovery loop that spent its budget on stale context",
        "",
        "## Executive summary",
        "",
        "A primary latency incident became a cross-component recovery failure. "
        "Retry opened the breaker, fallback returned context with the right headline "
        "value but wrong tokens, and a narrow semantic judge accepted the result "
        "inside its known blind spot. Repetition recovery then selected the same "
        "provider and exhausted the cost envelope.",
        "",
        "No wrong answer reached the user because the global ceiling worked. The "
        "request still failed: containment is not correct service.",
        "",
        "## Evidence-led diagnosis",
        "",
        f"The legacy trace `{before['trace_digest']}` links the false accept, "
        "three same-fingerprint verifications, secondary re-entry, and final "
        "ceiling error. The deterministic replay remained red across "
        f"{incident['replay_summary']['repetitions_per_version']} repetitions and "
        "four Python hash seeds.",
        "",
        "The root cause was not “the model made a mistake.” A narrow judge was "
        "given authority inside a documented failure slice, while replan lacked "
        "a route-diversity constraint.",
        "",
        "## Fix",
        "",
        "The fixed policy performs an exact token check, quarantines the stale "
        "provider/fingerprint, and requires recovery to select an independent "
        "trusted route. These are system controls with observable behavior.",
        "",
        "## Verified outcome",
        "",
        f"- legacy: `{before['terminal']['status']}`, cost "
        f"{before['metrics']['cost']}, latency {before['metrics']['latency']}, "
        "**red**",
        f"- fixed: `{after['terminal']['status']}`, cost "
        f"{after['metrics']['cost']}, latency {after['metrics']['latency']}, "
        "**green**",
        f"- fixed trace: `{after['trace_digest']}`",
        f"- replay-verified fix: **{incident['replay_summary']['replay_verified_fix']}**",
        "",
        "## Claim boundary",
        "",
        "This proves the corrective controls for the seeded simulator incident. "
        "It does not prove that an independent provider is truly independent in "
        "production; dependency mapping and live fault drills remain required.",
        "",
    ])


def render_checkpoint(report: Dict[str, Any]) -> str:
    checkpoint = report["checkpoint_25"]
    lines = [
        "# CHECKPOINT 25 — replay-verified postmortems",
        "",
        f"Incident reports: **{checkpoint['incident_count']}**.",
        "",
    ]
    for incident_id, flip in checkpoint["red_to_green"].items():
        replay = report["red_green_replay"][incident_id]
        lines.append(
            f"- **{incident_id}:** `{flip}`, "
            f"replay-verified={replay['replay_verified_fix']}."
        )
    lines.extend([
        "",
        f"Repetitions per policy version: "
        f"**{checkpoint['repetitions_per_version']}** plus four cross-process "
        "hash-seed runs.",
        "",
        f"Fail condition triggered: **{checkpoint['fail_condition_triggered']}**.",
        f"Checkpoint passed: **{checkpoint['gate']['passed']}**.",
        "",
    ])
    return "\n".join(lines)
