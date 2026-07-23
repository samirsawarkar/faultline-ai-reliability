"""The measured-vs-naive finding and its explanation."""
from __future__ import annotations

from faultline_hops import SweepConfig, build_curves, build_q1, run_sweep


def test_measured_decays_faster_than_naive():
    q1 = build_q1()
    pts = q1["curve"]
    # by the last hop, measured is well below naive
    assert pts[-1]["measured"] < pts[-1]["naive"]
    assert pts[-1]["measured_minus_naive"] < -0.1


def test_naive_is_falsified_at_a_finite_hop():
    q1 = build_q1()
    div = q1["first_divergence_hop"]
    assert div is not None and 2 <= div <= q1["config"]["max_hops"]
    # at the divergence hop the naive band is above the measured band
    pt = next(p for p in q1["curve"] if p["hops"] == div)
    assert pt["naive_ci95"][0] > pt["measured_ci95"][1]


def test_corrected_product_tracks_measured():
    """Product of measured per-hop rates explains the measured curve (mechanism),
    so the divergence is per-hop degradation, not a bug."""
    sweep = run_sweep(SweepConfig())
    curves = build_curves(sweep)
    for p in curves["points"]:
        assert abs(p["corrected"] - p["measured"]) < 0.05


def test_per_hop_reliability_declines_with_depth():
    q1 = build_q1()
    rates = [h["rate"] for h in q1["per_hop_reliability"]]
    # generally declining: hop1 is the most reliable, deep hops less so
    assert rates[0] > rates[3] > rates[5] - 0.05
    assert q1["single_hop_reliability"]["p1"] == rates[0]


def test_finding_text_is_populated():
    q1 = build_q1()
    assert "decays faster" in q1["finding"]
    assert str(q1["first_divergence_hop"]) in q1["finding"]
