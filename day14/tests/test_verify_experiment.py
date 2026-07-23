"""Independent verification passes; the grounded paired experiment is sound."""
from __future__ import annotations

from faultline_stats import build_report, verify_all


def test_verification_all_passes():
    v = verify_all()
    assert v["all_passed"] is True
    for name, check in v["checks"].items():
        assert check["ok"], f"verification failed: {name}"


def test_wilson_verified_by_score_equation():
    v = verify_all()
    assert v["checks"]["wilson_score_equation"]["max_residual"] < 1e-9


def test_paired_experiment_is_deterministic():
    assert build_report() == build_report()


def test_experiment_shows_invariant_strictly_improves_detection():
    rep = build_report()
    # System B (schema+invariant) beats A (schema-only), significantly
    assert rep["system_b"]["accuracy"] > rep["system_a"]["accuracy"]
    mc = rep["mcnemar"]
    assert mc["c"] > 0 and mc["b"] == 0          # B-only wins, never A-only
    assert mc["significant_at_0.05"] is True


def test_experiment_reports_intervals_for_both_systems():
    rep = build_report()
    for sysd in (rep["system_a"], rep["system_b"]):
        lo, hi = sysd["wilson_ci95"]
        assert 0.0 <= lo <= sysd["accuracy"] <= hi <= 1.0
