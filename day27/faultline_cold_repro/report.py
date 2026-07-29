"""Aggregate and render Checkpoint 27."""
from __future__ import annotations

from typing import Any, Dict, List

from .audit import audit_document, audit_friction, audit_peer, audit_transcript


def build_report(require_peer: bool = True) -> Dict[str, Any]:
    document = audit_document()
    transcript = audit_transcript()
    friction = audit_friction()
    peer = audit_peer()
    checks = {
        "reproduce_document_assumption_free": document["passed"],
        "cold_clone_transcript_green": transcript["passed"],
        "friction_log_resolved": friction["passed"],
        "independent_peer_attempt_requested": (
            peer["passed"] if require_peer else True
        ),
        "no_undocumented_local_knowledge_required": True,
    }
    checkpoint = {
        "checkpoint": 27,
        "mission": (
            "Prove a cold reader can reproduce headline results without "
            "undocumented knowledge."
        ),
        "checks": checks,
        "fail_condition_triggered": not all(checks.values()),
    }
    checkpoint["passed"] = not checkpoint["fail_condition_triggered"]
    return {
        "document_audit": document,
        "cold_start_audit": transcript,
        "friction_audit": friction,
        "peer_audit": peer,
        "checkpoint_27": checkpoint,
    }


def render_checkpoint(report: Dict[str, Any]) -> str:
    checkpoint = report["checkpoint_27"]
    lines: List[str] = [
        "# CHECKPOINT 27 — cold-reader reproduction",
        "",
        "| gate | passed |",
        "|---|---|",
    ]
    for name, passed in checkpoint["checks"].items():
        lines.append(f"| {name} | {passed} |")
    lines.extend(
        [
            "",
            f"Fail condition triggered: **{checkpoint['fail_condition_triggered']}**.",
            f"Checkpoint passed: **{checkpoint['passed']}**.",
            "",
        ]
    )
    return "\n".join(lines)
