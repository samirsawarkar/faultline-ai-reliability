"""Replay stability, graph evidence, narrative, and the mission gate."""
from __future__ import annotations

import faultline_cascade as fc


def test_repeated_and_cross_process_replay_are_stable():
    report = fc.replay_stability(repetitions=5, include_cross_process=True)
    assert report["in_process_stable"] is True
    assert report["cross_process_stable"] is True
    assert len(report["cross_process_runs"]) == 4
    assert len(report["unique_incident_digests"]) == 1
    assert len(report["unique_trace_digests"]) == 1
    assert report["reproducible_from_one_seed_and_config"] is True


def test_causal_graph_is_single_chain_and_trace_referenced():
    run = fc.run_cascade()
    graph = fc.build_causal_graph(run)
    assert len(graph["nodes"]) == 9
    assert len(graph["edges"]) == 8
    assert graph["root_cause"] == "E01"
    assert graph["terminal_event"] == "E09"
    assert graph["audit"]["all_nodes_observed"] is True
    assert graph["audit"]["all_nodes_trace_referenced"] is True
    assert graph["audit"]["single_chain"] is True


def test_graph_svg_is_deterministic_and_names_terminal_nodes():
    graph = fc.build_causal_graph(fc.run_cascade())
    first = fc.render_causal_graph_svg(graph)
    second = fc.render_causal_graph_svg(graph)
    assert first == second
    assert ">primary<" in first
    assert ">latency spike<" in first
    assert ">cost<" in first
    assert ">ceiling abort<" in first
    assert "trace:" in first


def test_narrative_contains_seed_digests_and_span_references():
    run = fc.run_cascade()
    stability = fc.replay_stability(
        repetitions=3, include_cross_process=False
    )
    narrative = fc.render_incident_narrative(run, stability)
    assert str(fc.CANONICAL_SEED) in narrative
    assert run["config_digest"] in narrative
    assert run["trace_digest"] in narrative
    assert run["events"][0]["span_refs"][0] in narrative
    assert "python day23/scripts/replay_once.py" in narrative


def test_report_passes_the_one_seed_config_fail_condition():
    report = fc.build_report()
    gate = report["fail_condition_guard"]
    assert all(value is True for key, value in gate.items() if key != "passed")
    assert gate["passed"] is True
    assert report["replay_stability"][
        "reproducible_from_one_seed_and_config"
    ] is True


def test_report_graph_and_skeleton_are_deterministic():
    first = fc.build_report()
    second = fc.build_report()
    assert first == second
    assert first["incident_skeleton"]["event_span_index"]
    assert first["causal_graph"]["graph_digest"] == second["causal_graph"]["graph_digest"]
