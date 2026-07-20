"""The severity sweep and specificity checks are deterministic and coherent."""
from __future__ import annotations

from faultline_detect import build_report, specificity, sweep_f1, sweep_f2


def test_report_is_deterministic():
    assert build_report() == build_report()


def test_f1_recall_rises_with_severity_precision_stays_perfect():
    rows = sweep_f1()
    assert rows[0]["recall"] < 1.0            # small corruption slips past schema
    assert all(r["recall"] == 1.0 for r in rows[1:])  # larger corruption always caught
    assert all(r["precision"] == 1.0 for r in rows)   # never flags a clean call


def test_f2_detection_is_budget_gated():
    rows = sweep_f2()                         # default budget 45
    detected = [r["severity"] for r in rows if r["recall"] == 1.0]
    missed = [r["severity"] for r in rows if r["recall"] == 0.0]
    assert detected == [4, 5] and missed == [1, 2, 3]


def test_specificity_each_detector_blind_to_other_family():
    s = specificity()
    assert s["each_detector_blind_to_other_family"] is True
    assert s["schema_detector_vs_latency_truth"]["recall"] == 0.0
    assert s["duration_detector_vs_corruption_truth"]["recall"] == 0.0


def test_every_sweep_row_is_scored_over_all_twelve_calls():
    for r in sweep_f1() + sweep_f2():
        assert r["n"] == 12                   # scored against the full labelling
