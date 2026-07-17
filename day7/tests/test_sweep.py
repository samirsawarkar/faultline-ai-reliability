"""Sweep determinism + per-step accounting correctness."""
from __future__ import annotations

from faultline_hops import SweepConfig, run_sweep
from faultline_hops.simulator import hop_probability, run_once


def test_sweep_is_deterministic():
    a = run_sweep(SweepConfig())
    b = run_sweep(SweepConfig())
    assert a.e2e == b.e2e
    assert a.per_hop == b.per_hop


def test_run_once_is_pure_function_of_seed():
    r1 = run_once(20260717, 5, 42)
    r2 = run_once(20260717, 5, 42)
    assert r1 == r2


def test_run_stops_at_first_failure():
    # a run that fails mid-chain reaches fewer than n hops, last hop is the failure
    cfg = SweepConfig()
    for trial in range(cfg.trials):
        r = run_once(cfg.master_seed, 8, trial)
        if not r.success:
            assert r.hops_reached <= 8
            assert r.hop_success[-1] is False
            assert all(r.hop_success[:-1])  # everything before the failure succeeded
            break


def test_per_hop_reached_is_non_increasing_with_depth():
    sweep = run_sweep(SweepConfig())
    reached = [sweep.per_hop[k]["reached"] for k in sorted(sweep.per_hop)]
    assert reached == sorted(reached, reverse=True)


def test_measured_per_hop_rate_tracks_model():
    sweep = run_sweep(SweepConfig())
    for k in (1, 2, 3, 4):
        b = sweep.per_hop[k]
        emp = b["success"] / b["reached"]
        assert abs(emp - hop_probability(k)) < 0.03  # within sampling noise
