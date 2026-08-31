"""Checkpoint 29 assembly."""
from __future__ import annotations

from typing import Any, Dict, List


def build_checkpoint(audit: Dict[str, Any]) -> Dict[str, Any]:
    groups = {
        "under_five_minute_demo": all(
            audit["checks"][key]
            for key in (
                "demo_sequence_complete",
                "demo_under_five_minutes",
                "recording_duration_matches",
                "live_before_red",
                "live_after_green",
                "live_traces_complete",
                "replay_verified",
            )
        ),
        "one_page_four_layer_case_study": all(
            audit["checks"][key]
            for key in (
                "case_study_exactly_four_layers",
                "case_study_one_page_word_budget",
                "case_study_exactly_five_verified_numbers",
            )
        ),
        "cold_viewer_comprehension": audit["checks"][
            "cold_viewer_can_state_proof"
        ],
        "dead_weight_removed": audit["checks"][
            "dead_weight_attack_red_to_green"
        ],
        "coordinated_publication_bundle": audit["checks"][
            "publication_bundle_complete"
        ],
        "claim_boundary_honest": audit["checks"][
            "human_test_caveat_explicit"
        ],
    }
    return {
        "checkpoint": 29,
        "mission": "Help a busy staff engineer understand the evidence in under three minutes.",
        "required_evidence": [
            "under-five-minute demo",
            "one-page case study",
            "Checkpoint 29",
        ],
        "gates": groups,
        "demo_duration_seconds": audit["demo"]["planned_duration_seconds"],
        "case_study_words": audit["case_study"]["word_count"],
        "verified_number_count": audit["case_study"]["five_numbers"][
            "declared_count"
        ],
        "fail_condition_triggered": not audit["checks"][
            "cold_viewer_can_state_proof"
        ],
        "passed": all(groups.values()) and audit["passed"],
    }


def render_checkpoint(checkpoint: Dict[str, Any]) -> str:
    lines: List[str] = [
        "# CHECKPOINT 29 — three-minute staff-engineer evidence path",
        "",
        f"Mission: {checkpoint['mission']}",
        "",
        "| gate | passed |",
        "|---|---|",
    ]
    for name, passed in checkpoint["gates"].items():
        lines.append(f"| {name} | {passed} |")
    lines += [
        "",
        f"Recorded demo: **{checkpoint['demo_duration_seconds']} seconds**.",
        f"Case study: **{checkpoint['case_study_words']} words**.",
        f"Verified numbers: **{checkpoint['verified_number_count']}**.",
        f"Fail condition triggered: **{checkpoint['fail_condition_triggered']}**.",
        f"Checkpoint passed: **{checkpoint['passed']}**.",
        "",
    ]
    return "\n".join(lines)
