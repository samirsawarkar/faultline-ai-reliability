from __future__ import annotations

from typing import Any

from .audit import audit_day30
from .evidence import DAY30, EVIDENCE, write_json


def _render(checkpoint: dict[str, Any]) -> str:
    audit = checkpoint["audit"]
    lines = [
        "# CHECKPOINT 30 — defend, contribute, and launch",
        "",
        "Mission: Defend every core decision aloud and put the evidence in front of relevant experts.",
        "",
        "| gate | passed |",
        "|---|---|",
    ]
    lines.extend(
        f"| {name} | {passed} |" for name, passed in audit["checks"].items()
    )
    lines.extend(
        [
            "",
            f"Defense questions: **{audit['defense']['questions']}**.",
            f"Tailored messages: **{audit['outreach']['targets']}**.",
            f"Messages with durable send receipts: **{audit['outreach']['sent']}**.",
            f"OSS contributions opened or merged: **{audit['oss']['opened_or_merged']}**.",
            f"Fail condition triggered: **{checkpoint['fail_condition_triggered']}**.",
            f"Checkpoint passed: **{checkpoint['passed']}**.",
            "",
        ]
    )
    if audit["external_actions_pending"]:
        lines.extend(
            [
                "## Pending external evidence",
                "",
                *[f"- {item}" for item in audit["external_actions_pending"]],
                "",
                "Prepared drafts and contribution packets do not count as sent or opened.",
                "",
            ]
        )
    return "\n".join(lines)


def build_checkpoint() -> dict[str, Any]:
    audit = audit_day30()
    checkpoint = {
        "schema_version": "1.0.0",
        "mission": "Defend every core decision aloud and put the evidence in front of relevant experts.",
        "fail_condition": "A core decision or limitation cannot be defended without reading code.",
        "fail_condition_triggered": bool(
            audit["defense"]["recording"]["valid"] is False
            or audit["checks"]["every_core_decision_defended"] is False
        ),
        "audit": audit,
        "passed": audit["passed"],
    }
    write_json(EVIDENCE / "checkpoint_30.json", checkpoint)
    rendered = _render(checkpoint)
    (DAY30 / "CHECKPOINT-30.md").write_text(rendered, encoding="utf-8")
    (EVIDENCE / "CHECKPOINT-30.md").write_text(rendered, encoding="utf-8")
    return checkpoint
