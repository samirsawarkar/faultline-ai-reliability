"""The retry crossover: sweep, ceilings, and the fail-condition guard."""
from __future__ import annotations

import faultline_retry as rt
from faultline_retry.crossover import COST_CEILING_AMP, P99_BUDGET, crossover, fail_condition_check


def test_report_is_deterministic():
    assert rt.build_report() == rt.build_report()


def test_success_rises_and_cost_climbs_with_retries():
    pts = rt.sweep("independent")
    succ = [p["success_rate"] for p in pts]
    amp = [p["amplification"] for p in pts]
    assert succ == sorted(succ)            # monotone non-decreasing success
    assert amp == sorted(amp)              # monotone non-decreasing cost
    assert amp[-1] > amp[0]


def test_efficiency_falls_as_retries_grow():
    spa = [p["success_per_attempt"] for p in rt.sweep("independent")]
    assert spa[0] > spa[-1]                # success-per-attempt decays


def test_correlated_plateaus_below_independent():
    corr = rt.sweep("correlated")
    indep = rt.sweep("independent")
    assert corr[-1]["success_rate"] == corr[-2]["success_rate"]     # plateau
    assert corr[-1]["success_rate"] < indep[-1]["success_rate"]


def test_recommendation_is_within_both_ceilings():
    pts = rt.sweep("independent")
    cx = crossover(pts)
    rec = pts[cx["recommended_max_attempts"] - 1]
    assert rec["amplification"] <= COST_CEILING_AMP
    assert rec["p99_latency"] <= P99_BUDGET
    assert cx["recommendation_within_ceilings"] is True


def test_fail_condition_recommended_never_breaches_a_ceiling():
    # The mission fails if a recommended K improves success while breaching cost or
    # tail latency. The recommendation must be acceptable, and every breaching K must
    # be OUTSIDE the recommendation.
    r = rt.build_report()
    for scen in ("independent", "correlated"):
        pts = r[f"sweep_{scen}"]
        rec = r[f"crossover_{scen}"]["recommended_max_attempts"]
        guard = fail_condition_check(pts, rec)
        assert guard["respected"] is True
        assert all(b["K"] > rec for b in guard["breaching_regions"])
    assert r["q3_conclusion"]["fail_condition_respected"] is True


def test_correlation_significantly_reduces_success_paired():
    mc = rt.build_report()["paired_correlation_effect_at_recommended_K"]["mcnemar"]
    assert mc["significant_at_0.05"] is True    # correlation hurts, on the same requests


def test_crossover_marks_diminishing_returns():
    from faultline_retry.sweep import KMAX
    cx = crossover(rt.sweep("independent"))
    assert 1 <= cx["crossover_K"] <= KMAX
    assert cx["crossover_K"] >= cx["recommended_max_attempts"]   # cross at/after the rec
