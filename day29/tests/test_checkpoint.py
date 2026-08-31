"""Checkpoint 29 makes the mission fail condition executable."""
from copy import deepcopy

from faultline_brief import audit_day29, build_checkpoint, build_demo
from faultline_brief.evidence import DAY, EVIDENCE, load_json


def test_checkpoint_29_passes():
    checkpoint = build_checkpoint(audit_day29(build_demo()))
    assert checkpoint["checkpoint"] == 29
    assert checkpoint["demo_duration_seconds"] == 165
    assert checkpoint["verified_number_count"] == 5
    assert checkpoint["fail_condition_triggered"] is False
    assert checkpoint["passed"] is True


def test_checkpoint_fails_when_cold_viewer_cannot_state_proof():
    audit = deepcopy(audit_day29(build_demo()))
    audit["checks"]["cold_viewer_can_state_proof"] = False
    checkpoint = build_checkpoint(audit)
    assert checkpoint["fail_condition_triggered"] is True
    assert checkpoint["gates"]["cold_viewer_comprehension"] is False
    assert checkpoint["passed"] is False


def test_committed_checkpoint_matches_live_checkpoint():
    expected = build_checkpoint(audit_day29(build_demo()))
    assert load_json(EVIDENCE / "checkpoint_29.json") == expected


def test_mastery_gate_lists_all_five_capabilities():
    text = (DAY / "README.md").read_text(encoding="utf-8")
    for capability in (
        "Can explain",
        "Can build",
        "Can debug",
        "Can measure",
        "Can defend",
    ):
        assert capability in text
