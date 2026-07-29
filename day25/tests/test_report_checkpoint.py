"""Postmortem sections, replay proof, case study, and Checkpoint-25 gate."""
from faultline_postmortem import (
    render_case_study,
    render_checkpoint,
    render_incident,
)


def test_every_report_contains_required_postmortem_sections(postmortem_report):
    required = {
        "timeline",
        "impact",
        "detection",
        "root_cause",
        "contributing_factors",
        "corrective_actions",
    }
    for report in postmortem_report["incident_reports"].values():
        assert required <= report.keys()
        assert all(report[key] for key in required)


def test_cross_process_red_green_replay_is_stable(postmortem_report):
    for replay in postmortem_report["red_green_replay"].values():
        assert replay["cross_process"]["legacy"]["stable"]
        assert replay["cross_process"]["fixed"]["stable"]
        assert replay["replay_verified_fix"]


def test_checkpoint_25_passes_every_executable_guard(postmortem_report):
    checkpoint = postmortem_report["checkpoint_25"]
    assert checkpoint["red_to_green"] == {
        "INC-25-001": "red->green",
        "INC-25-002": "red->green",
    }
    assert not checkpoint["fail_condition_triggered"]
    assert all(checkpoint["gate"].values())


def test_incident_renderer_is_trace_linked_and_blameless(postmortem_report):
    for report in postmortem_report["incident_reports"].values():
        rendered = render_incident(report)
        assert "## Timeline" in rendered
        assert "## Impact" in rendered
        assert "## Detection" in rendered
        assert "## Root cause" in rendered
        assert "## Contributing factors" in rendered
        assert "## Red → green regression" in rendered
        assert "trace-" in rendered
        assert "not a person" in rendered


def test_case_study_states_outcome_and_claim_boundary(postmortem_report):
    rendered = render_case_study(postmortem_report)
    assert "containment is not correct service" in rendered
    assert "legacy: `contained_cost_ceiling`" in rendered
    assert "fixed: `recovered_correct`" in rendered
    assert "## Claim boundary" in rendered


def test_checkpoint_renderer_names_both_verified_fixes(postmortem_report):
    rendered = render_checkpoint(postmortem_report)
    assert "INC-25-001" in rendered
    assert "INC-25-002" in rendered
    assert rendered.count("replay-verified=True") == 2
    assert "Checkpoint passed: **True**" in rendered
