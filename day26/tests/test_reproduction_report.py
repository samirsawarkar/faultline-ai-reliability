"""Eval, experiment, test-profile, aggregate checkpoint, and renderer gates."""
import json
from pathlib import Path

from faultline_repro import build_report, render_checkpoint

ROOT = Path(__file__).resolve().parents[2]


def _evidence(name):
    return json.loads(
        (ROOT / "day26/evidence" / name).read_text(encoding="utf-8")
    )


def test_frozen_eval_verification_is_green():
    report = _evidence("eval_verification.json")
    assert report["passed"]
    assert report["result_id"] == "66ac42d8d4433e5c"


def test_fast_experiment_subset_is_byte_identical():
    report = _evidence("fast_experiment_report.json")
    assert report["passed"]
    assert {item["name"] for item in report["experiments"]} == {
        "tool_hops",
        "fallback_quality",
        "postmortem_replay",
    }
    assert all(item["byte_identical"] for item in report["experiments"])


def test_fast_profile_includes_tests_eval_and_recent_incidents():
    source = (ROOT / "day26/scripts/run_test_gate.py").read_text()
    assert "FAST_DAYS = (1, 4, 13, 21, 25, 26)" in source


def test_aggregate_report_passes_before_outer_container_attestation():
    report = build_report(require_container=False)
    assert report["checkpoint_26"]["passed"]
    assert report["checkpoint_26"]["checks"]["make_full_tests_green"]
    assert report["checkpoint_26"]["checks"]["frozen_eval_green"]
    assert report["checkpoint_26"]["checks"]["fast_experiment_subset_green"]


def test_checkpoint_renderer_is_results_first_and_explicit():
    report = build_report(require_container=False)
    rendered = render_checkpoint(report)
    assert "v0.26.0-rc1" in rendered
    assert "results_first_readme_traceable" in rendered
    assert "clean_container_reproduction_green" in rendered
    assert "Checkpoint passed: **True**" in rendered
