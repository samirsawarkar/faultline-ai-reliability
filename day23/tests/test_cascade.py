"""The initiating fault, propagation labels, trace completeness, and containment."""
from __future__ import annotations

import faultline_cascade as fc


def test_canonical_seed_triggers_the_exact_labelled_chain():
    run = fc.run_cascade()
    assert run["trigger_truth"]["triggered"] is True
    assert run["trigger_truth"]["initiating_fault"] == "F2:primary_latency_spike"
    assert tuple(event["label"] for event in run["events"]) == fc.EXPECTED_CHAIN
    assert [event["event_id"] for event in run["events"]] == [
        f"E{i:02d}" for i in range(1, 10)
    ]


def test_recovery_propagates_then_outer_ceiling_contains():
    run = fc.run_cascade()
    metrics = run["metrics"]
    assert metrics["primary_calls"] == 2
    assert metrics["retry_calls_added"] == 1
    assert metrics["fallback_calls"] == 2
    assert metrics["verification_repeats"] == 3
    assert metrics["replans"] == 1
    assert metrics["cost"] == 11 <= metrics["cost_ceiling"]
    assert metrics["steps"] == 8 <= metrics["step_ceiling"]
    assert run["terminal"]["status"] == "contained_cost_ceiling"
    assert run["terminal"]["correct_answer_returned"] is False


def test_fallback_is_strictly_bad_and_judge_false_accepts():
    truth = fc.run_cascade()["trigger_truth"]
    assert truth["fallback_variant"] == "borderline_tokens"
    assert truth["strict_fallback_quality"] is False
    assert truth["judge_false_accept"] is True


def test_complete_trace_and_error_spans_survive_the_cascade():
    run = fc.run_cascade()
    audit = run["audit"]
    assert audit["span_count"] == 16
    assert audit["root_count"] == 1
    assert audit["error_span_count"] == 3
    assert audit["all_spans_complete"] is True
    assert audit["all_error_spans_complete"] is True
    assert audit["unresolved_parent_links"] == []
    assert audit["passed"] is True


def test_every_causal_event_has_resolving_trace_references():
    run = fc.run_cascade()
    span_ids = {span["span_id"] for span in run["trace"]["spans"]}
    assert all(event["span_refs"] for event in run["events"])
    assert all(
        ref in span_ids
        for event in run["events"]
        for ref in event["span_refs"]
    )
    assert run["audit"]["unresolved_event_span_refs"] == []


def test_same_seed_and_config_are_byte_equivalent():
    config = fc.canonical_config()
    first = fc.run_cascade(fc.CANONICAL_SEED, config)
    second = fc.run_cascade(fc.CANONICAL_SEED, config)
    assert first == second
    assert first["incident_digest"] == second["incident_digest"]
    assert first["trace_digest"] == second["trace_digest"]
