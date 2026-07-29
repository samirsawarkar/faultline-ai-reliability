"""Assemble canonical run, replay proof, graph, skeleton, and fail-condition gate."""
from __future__ import annotations

from typing import Any, Dict

from .cascade import CANONICAL_SEED, EXPECTED_CHAIN, run_cascade
from .config import canonical_config
from .graph import build_causal_graph
from .replay import replay_stability


def build_report() -> Dict[str, Any]:
    config = canonical_config()
    run = run_cascade(CANONICAL_SEED, config)
    stability = replay_stability(
        CANONICAL_SEED, config, repetitions=20, include_cross_process=True
    )
    graph = build_causal_graph(run)
    event_span_index = {
        event["event_id"]: list(event["span_refs"]) for event in run["events"]
    }
    skeleton = {
        "incident_id": run["incident_id"],
        "seed": run["seed"],
        "config_digest": run["config_digest"],
        "trace_digest": run["trace_digest"],
        "initiating_event": "E01",
        "terminal_event": "E09",
        "propagation_chain": [
            {"event_id": event["event_id"], "label": event["label"]}
            for event in run["events"]
        ],
        "event_span_index": event_span_index,
        "artifacts": {
            "trace": "cascade_trace.json",
            "narrative": "INCIDENT_NARRATIVE.md",
            "causal_graph_json": "causal_graph.json",
            "causal_graph_svg": "causal_graph.svg",
            "replay_proof": "replay_stability.json",
        },
    }
    gate = {
        "one_seed_present": isinstance(run["seed"], int),
        "one_config_present": bool(run["config"]),
        "config_digest_present": bool(run["config_digest"]),
        "initiating_fault_labelled": (
            run["events"][0]["label"] == EXPECTED_CHAIN[0]
        ),
        "propagation_chain_stable": stability["in_process_stable"],
        "cross_process_stable": stability["cross_process_stable"],
        "complete_trace": run["audit"]["passed"],
        "causal_graph_trace_referenced": (
            graph["audit"]["all_nodes_trace_referenced"]
            and graph["audit"]["single_chain"]
        ),
        "incident_skeleton_trace_referenced": all(event_span_index.values()),
    }
    gate["passed"] = all(gate.values())
    return {
        "run": run,
        "replay_stability": stability,
        "causal_graph": graph,
        "incident_skeleton": skeleton,
        "fail_condition_guard": gate,
    }
