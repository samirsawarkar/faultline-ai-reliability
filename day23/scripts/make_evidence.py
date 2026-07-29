"""Regenerate the complete deterministic Day-23 incident evidence."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for rel in ("", "../day04", "../day14", "../day16", "../day20", "../day21"):
    sys.path.insert(0, str((ROOT / rel).resolve()))

from faultline_cascade import (  # noqa: E402
    build_report,
    render_causal_graph_svg,
    render_incident_narrative,
)

EVIDENCE = ROOT / "evidence"


def _dump(path: Path, obj) -> None:
    path.write_text(
        json.dumps(obj, sort_keys=True, ensure_ascii=True, indent=2) + "\n",
        encoding="utf-8",
    )


def main() -> None:
    EVIDENCE.mkdir(exist_ok=True)
    report = build_report()
    run = report["run"]
    stability = report["replay_stability"]
    scenario = {
        "scenario_version": run["config"]["scenario_version"],
        "seed": run["seed"],
        "config": run["config"],
        "config_digest": run["config_digest"],
        "incident_digest": stability["unique_incident_digests"][0],
        "trace_digest": run["trace_digest"],
        "initiating_fault": run["trigger_truth"]["initiating_fault"],
        "expected_chain": [event["label"] for event in run["events"]],
        "trigger_truth": run["trigger_truth"],
        "replay_command": (
            "python day23/scripts/replay_once.py "
            "--scenario day23/evidence/cascade_scenario.json"
        ),
        "fail_condition_guard": report["fail_condition_guard"],
    }
    _dump(EVIDENCE / "cascade_scenario.json", scenario)
    _dump(
        EVIDENCE / "cascade_trace.json",
        {
            "incident_id": run["incident_id"],
            "seed": run["seed"],
            "config_digest": run["config_digest"],
            "trace_digest": run["trace_digest"],
            "events": run["events"],
            "causal_edges": run["causal_edges"],
            "terminal": run["terminal"],
            "metrics": run["metrics"],
            "audit": run["audit"],
            "trace": run["trace"],
        },
    )
    _dump(EVIDENCE / "replay_stability.json", stability)
    _dump(EVIDENCE / "causal_graph.json", report["causal_graph"])
    _dump(EVIDENCE / "incident_skeleton.json", report["incident_skeleton"])
    (EVIDENCE / "causal_graph.svg").write_text(
        render_causal_graph_svg(report["causal_graph"]), encoding="utf-8"
    )
    (EVIDENCE / "INCIDENT_NARRATIVE.md").write_text(
        render_incident_narrative(run, stability), encoding="utf-8"
    )

    print("Day 23 evidence written:")
    print(
        f"  seed/config: {run['seed']} / {run['config_digest'][:12]}"
    )
    print(
        f"  chain: {' -> '.join(event['label'] for event in run['events'])}"
    )
    print(
        f"  replay: {stability['repetitions']} runs, "
        f"cross-process={stability['cross_process_stable']}"
    )
    print(
        f"  trace: {run['audit']['span_count']} complete spans; "
        f"gate={report['fail_condition_guard']['passed']}"
    )


if __name__ == "__main__":
    main()
