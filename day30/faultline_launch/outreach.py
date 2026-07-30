from __future__ import annotations

from typing import Any

from .evidence import DAY30, EVIDENCE, ROOT, load_json, resolve_pointer, words, write_json


def _audit_target(target: dict[str, Any]) -> dict[str, Any]:
    binding = target["evidence"]
    actual = resolve_pointer(load_json(ROOT / binding["artifact"]), binding["pointer"])
    message = target["message"]
    lowered = message.casefold()
    checks = {
        "public_target_named": target["target"].casefold() in lowered,
        "tailored_hook_present": all(
            term.casefold() in lowered for term in target["tailored_terms"]
        ),
        "specific_ask_present": "?" in message and target["ask"].casefold() in lowered,
        "evidence_number_verified": actual == binding["expected"]
        and str(binding["display"]) in message,
        "evidence_link_present": "https://github.com/samirsawarkar/faultline-ai-reliability/" in message,
        "limitation_present": any(
            term in lowered for term in ("simulator", "synthetic", "not production", "upper bound")
        ),
        "concise": 70 <= len(words(message)) <= 190,
        "not_claimed_sent": target["status"] in {"draft", "sent"},
    }
    return {
        "id": target["id"],
        "target": target["target"],
        "channel": target["channel"],
        "status": target["status"],
        "word_count": len(words(message)),
        "evidence_actual": actual,
        "checks": checks,
        "passed": all(checks.values()),
    }


def render_outreach(targets: list[dict[str, Any]]) -> str:
    lines = [
        "# Eight evidence-led outreach messages",
        "",
        "These are tailored drafts for public maintainer channels. A message is marked",
        "`sent` only after a durable public URL is recorded; prepared text is not",
        "misrepresented as outreach.",
        "",
    ]
    for target in targets:
        lines.extend(
            [
                f"## {target['id']} · {target['target']}",
                "",
                f"- Channel: {target['channel']}",
                f"- Target: {target['target_url']}",
                f"- Status: `{target['status']}`",
                f"- Intended ask: {target['ask']}",
                "",
                target["message"],
                "",
            ]
        )
    return "\n".join(lines)


def build_outreach_report() -> dict[str, Any]:
    source = load_json(DAY30 / "outreach_targets.json")
    targets = source["targets"]
    audits = [_audit_target(target) for target in targets]
    rendered = render_outreach(targets)
    (DAY30 / "OUTREACH.md").write_text(rendered, encoding="utf-8")
    report = {
        "schema_version": "1.0.0",
        "target_count": len(targets),
        "message_count": len(targets),
        "all_tailored": all(item["passed"] for item in audits),
        "sent_count": sum(item["status"] == "sent" for item in audits),
        "durable_sent_urls": [
            target["sent_url"]
            for target in targets
            if target["status"] == "sent" and target.get("sent_url")
        ],
        "audits": audits,
        "passed": len(targets) == 8 and all(item["passed"] for item in audits),
        "external_delivery_complete": sum(
            item["status"] == "sent" for item in audits
        ) >= source["minimum_selective_sends"],
    }
    write_json(EVIDENCE / "outreach_audit.json", report)
    return report
