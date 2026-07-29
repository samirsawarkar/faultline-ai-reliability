"""The same trace-linked regressions must fail before and pass after."""
import pytest

from faultline_postmortem import INCIDENTS, run_incident, verify_red_green


@pytest.mark.parametrize("incident", INCIDENTS, ids=lambda item: item.incident_id)
def test_same_regression_flips_red_to_green(incident):
    before = run_incident(incident.incident_id, "legacy")
    after = run_incident(incident.incident_id, "fixed")
    assert before["seed"] == after["seed"] == incident.seed
    assert before["config_digest"] == after["config_digest"]
    assert before["regression"]["test_id"] == after["regression"]["test_id"]
    assert before["regression"]["color"] == "red"
    assert not before["regression"]["passed"]
    assert after["regression"]["color"] == "green"
    assert after["regression"]["passed"]


@pytest.mark.parametrize("incident", INCIDENTS, ids=lambda item: item.incident_id)
def test_before_and_after_regressions_resolve_to_complete_traces(incident):
    for version in ("legacy", "fixed"):
        result = run_incident(incident.incident_id, version)
        assert result["trace_audit"]["passed"]
        assert result["regression"]["trace_refs"]
        span_ids = {
            span["span_id"] for span in result["trace"]["spans"]
        }
        assert set(result["regression"]["trace_refs"]) <= span_ids


def test_stale_fallback_fix_returns_correct_within_original_envelope():
    before = run_incident("INC-25-001", "legacy")
    after = run_incident("INC-25-001", "fixed")
    assert before["metrics"] == {
        "cost": 11,
        "steps": 8,
        "latency": 98,
        "cost_budget": 12,
        "step_budget": 9,
    }
    assert after["terminal"]["status"] == "recovered_correct"
    assert after["metrics"]["cost"] == 11
    assert after["metrics"]["steps"] == 6
    assert after["metrics"]["latency"] == 94


def test_deadline_fix_stays_inside_the_same_cost_and_latency_limits():
    before = run_incident("INC-25-002", "legacy")
    after = run_incident("INC-25-002", "fixed")
    assert before["terminal"]["status"] == "latency_budget_abort"
    assert after["terminal"]["status"] == "recovered_correct"
    assert before["metrics"]["cost"] == after["metrics"]["cost"] == 2
    assert before["metrics"]["latency"] == after["metrics"]["latency"] == 45


def test_repeated_fixed_replays_stay_green():
    for incident in INCIDENTS:
        proof = verify_red_green(
            incident.incident_id,
            repetitions=5,
            include_cross_process=False,
        )
        assert proof["after"]["stability"]["stable"]
        assert proof["flip_checks"]["post_fix_stays_green"]
        assert proof["replay_verified_fix"]


def test_unknown_policy_version_is_refused():
    with pytest.raises(ValueError, match="version"):
        run_incident("INC-25-001", "experimental")
