"""Build two complete postmortems and the executable Checkpoint-25 gate."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

from .catalog import INCIDENTS
from .config import canonical_config
from .replay import verify_red_green
from .runner import run_incident

_ROOT = Path(__file__).resolve().parents[2]


def _source_evidence() -> Dict[str, Any]:
    day23 = json.loads(
        (_ROOT / "day23/evidence/incident_skeleton.json").read_text(
            encoding="utf-8"
        )
    )
    day24 = json.loads(
        (_ROOT / "day24/evidence/winner_attack.json").read_text(
            encoding="utf-8"
        )
    )
    tight = day24["attacks"]["tight_budgets"]
    return {
        "INC-25-001": {
            "artifact": "day23/evidence/incident_skeleton.json",
            "source_incident_id": day23["incident_id"],
            "seed": day23["seed"],
            "terminal_event": day23["terminal_event"],
            "trace_digest": day23["trace_digest"],
            "matched": (
                day23["seed"] == INCIDENTS[0].seed
                and day23["terminal_event"] == "E09"
            ),
        },
        "INC-25-002": {
            "artifact": "day24/evidence/winner_attack.json",
            "seed": INCIDENTS[1].seed,
            "attack": "tight_budgets",
            "latency_budget_abort_count": tight["metrics"]["statuses"][
                "latency_budget_abort"
            ],
            "latency_budget": tight["config"]["per_request_latency_budget"],
            "matched": (
                tight["metrics"]["statuses"]["latency_budget_abort"] == 105
                and tight["config"]["seed_base"] <= INCIDENTS[1].seed
                < tight["config"]["seed_base"] + tight["config"]["n"]
            ),
        },
    }


def build_report(
    repetitions: int = 20,
    include_cross_process: bool = True,
) -> Dict[str, Any]:
    config = canonical_config()
    sources = _source_evidence()
    incident_reports: Dict[str, Any] = {}
    replays: Dict[str, Any] = {}
    runs: Dict[str, Any] = {}
    for spec in INCIDENTS:
        before = run_incident(spec.incident_id, "legacy", config)
        after = run_incident(spec.incident_id, "fixed", config)
        replay = verify_red_green(
            spec.incident_id,
            config,
            repetitions=repetitions,
            include_cross_process=include_cross_process,
        )
        incident_reports[spec.incident_id] = {
            **spec.to_dict(),
            "source_evidence": sources[spec.incident_id],
            "timeline": before["timeline"],
            "fixed_timeline": after["timeline"],
            "before_outcome": {
                "terminal": before["terminal"],
                "metrics": before["metrics"],
                "regression": before["regression"],
                "trace_digest": before["trace_digest"],
            },
            "after_outcome": {
                "terminal": after["terminal"],
                "metrics": after["metrics"],
                "regression": after["regression"],
                "trace_digest": after["trace_digest"],
            },
            "replay_summary": {
                "repetitions_per_version": repetitions,
                "before_stable": replay["before"]["stability"]["stable"],
                "after_stable": replay["after"]["stability"]["stable"],
                "cross_process_stable": (
                    all(
                        item["stable"]
                        for item in replay["cross_process"].values()
                    )
                    if include_cross_process
                    else None
                ),
                "replay_verified_fix": replay["replay_verified_fix"],
            },
            "trace_artifacts": {
                "before": f"{spec.slug}-before-trace.json",
                "after": f"{spec.slug}-after-trace.json",
            },
        }
        replays[spec.incident_id] = replay
        runs[spec.incident_id] = {"before": before, "after": after}

    required_sections = (
        "timeline",
        "impact",
        "detection",
        "root_cause",
        "contributing_factors",
        "corrective_actions",
    )
    gate = {
        "two_or_three_incident_reports": 2 <= len(incident_reports) <= 3,
        "all_required_sections_present": all(
            all(report.get(section) for section in required_sections)
            for report in incident_reports.values()
        ),
        "all_source_evidence_matched": all(
            item["matched"] for item in sources.values()
        ),
        "all_before_tests_red": all(
            not report["before_outcome"]["regression"]["passed"]
            and report["before_outcome"]["regression"]["color"] == "red"
            for report in incident_reports.values()
        ),
        "all_after_tests_green": all(
            report["after_outcome"]["regression"]["passed"]
            and report["after_outcome"]["regression"]["color"] == "green"
            for report in incident_reports.values()
        ),
        "same_tests_flip_red_to_green": all(
            replay["flip_checks"]["same_regression_test"]
            and replay["flip_checks"]["before_is_red"]
            and replay["flip_checks"]["after_is_green"]
            for replay in replays.values()
        ),
        "all_fixes_replay_verified": all(
            replay["replay_verified_fix"] for replay in replays.values()
        ),
        "all_after_traces_complete": all(
            pair["after"]["trace_audit"]["passed"]
            for pair in runs.values()
        ),
        "all_regressions_trace_linked": all(
            pair["before"]["regression"]["trace_refs"]
            and pair["after"]["regression"]["trace_refs"]
            for pair in runs.values()
        ),
    }
    gate["passed"] = all(gate.values())
    checkpoint = {
        "checkpoint": 25,
        "mission": (
            "Turn failures into replay-verified postmortems whose fixes stay fixed."
        ),
        "incident_count": len(incident_reports),
        "red_to_green": {
            incident_id: (
                replay["before"]["regression"]["color"]
                + "->"
                + replay["after"]["regression"]["color"]
            )
            for incident_id, replay in replays.items()
        },
        "repetitions_per_version": repetitions,
        "fail_condition_triggered": not gate["passed"],
        "gate": gate,
    }
    return {
        "config": config.to_dict(),
        "source_evidence": sources,
        "incident_reports": incident_reports,
        "red_green_replay": replays,
        "checkpoint_25": checkpoint,
        "_runs": runs,
    }
