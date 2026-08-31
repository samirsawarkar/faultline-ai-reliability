from __future__ import annotations

from typing import Any

from .defense import build_defense_report
from .evidence import DAY30, EVIDENCE, ROOT, load_json, resolve_pointer, write_json
from .outreach import build_outreach_report


def _audit_oss() -> dict[str, Any]:
    source = load_json(DAY30 / "oss_contributions.json")
    entries = []
    for item in source["contributions"]:
        issue_url = item["upstream_issue"]
        files_exist = all((ROOT / path).exists() for path in item["packet_files"])
        checks = {
            "upstream_issue_named": issue_url.startswith("https://github.com/"),
            "scope_is_bounded": item["lines_changed"] <= 10,
            "issue_request_matches_patch": item["issue_match"] is True,
            "validation_named": bool(item["validation"]),
            "packet_complete": files_exist,
            "status_valid": item["status"] in {"prepared", "opened", "merged"},
            "opened_has_url": item["status"] == "prepared"
            or str(item.get("contribution_url", "")).startswith("https://github.com/"),
        }
        entries.append(
            {
                "id": item["id"],
                "repository": item["repository"],
                "status": item["status"],
                "contribution_url": item.get("contribution_url"),
                "checks": checks,
                "passed": all(checks.values()),
            }
        )
    opened = [entry for entry in entries if entry["status"] in {"opened", "merged"}]
    report = {
        "schema_version": "1.0.0",
        "contribution_count": len(entries),
        "prepared_count": sum(entry["status"] == "prepared" for entry in entries),
        "opened_or_merged_count": len(opened),
        "entries": entries,
        "packets_passed": 1 <= len(entries) <= 2 and all(entry["passed"] for entry in entries),
        "external_contribution_complete": 1 <= len(opened) <= 2,
    }
    write_json(EVIDENCE / "oss_audit.json", report)
    return report


def _audit_launch_plan() -> dict[str, Any]:
    plan = load_json(DAY30 / "first_72_hours.json")
    windows = plan["windows"]
    checks = {
        "three_windows": [window["hours"] for window in windows]
        == ["0-24", "24-48", "48-72"],
        "owners_named": all(window["owner"] for window in windows),
        "gates_named": all(window["exit_gate"] for window in windows),
        "rollback_named": all(window["rollback"] for window in windows),
        "metrics_cover_outcome_cost_latency": {
            metric
            for window in windows
            for metric in window["metrics"]
        }
        >= {"correct_service_success", "mean_cost", "p95_latency"},
    }
    return {"checks": checks, "passed": all(checks.values())}


def audit_day30() -> dict[str, Any]:
    defense = build_defense_report()
    outreach = build_outreach_report()
    oss = _audit_oss()
    launch = _audit_launch_plan()
    checkpoint_ready = bool(
        defense["passed"]
        and outreach["passed"]
        and outreach["external_delivery_complete"]
        and oss["packets_passed"]
        and oss["external_contribution_complete"]
        and launch["passed"]
    )
    checks = {
        "recorded_mock_defense": defense["passed"],
        "every_core_decision_defended": not defense["final_failed_questions"],
        "weak_answers_repaired": defense["red_to_green"],
        "eight_tailored_messages": outreach["passed"],
        "selective_outreach_has_receipts": outreach["external_delivery_complete"],
        "one_or_two_oss_contributions": oss["external_contribution_complete"],
        "oss_has_no_unmeasured_scope": oss["packets_passed"],
        "first_72_hours_scheduled": launch["passed"],
        "human_proficiency_caveat": defense["recording"]["human_proficiency_claimed"] is False,
    }
    report = {
        "schema_version": "1.0.0",
        "checks": checks,
        "defense": {
            "questions": defense["question_count"],
            "weakest_answer": defense["weakest_answer"],
            "recording": defense["recording"],
        },
        "outreach": {
            "targets": outreach["target_count"],
            "sent": outreach["sent_count"],
            "minimum_selective_sends": load_json(DAY30 / "outreach_targets.json")[
                "minimum_selective_sends"
            ],
        },
        "oss": {
            "packets": oss["contribution_count"],
            "opened_or_merged": oss["opened_or_merged_count"],
        },
        "launch_plan": launch,
        "external_actions_pending": [
            name for name, passed in checks.items() if not passed
        ],
        "passed": checkpoint_ready and all(checks.values()),
    }
    write_json(EVIDENCE / "day30_audit.json", report)
    return report
