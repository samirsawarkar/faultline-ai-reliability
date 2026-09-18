"""Tests for P10: Calibrated Cascade simulation module and runner."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

import pytest

from faultline_p2.cascade.simulate import (
    evaluate,
    fit,
    pareto_frontier,
    split_scenarios,
)
from projects.p10_cascade.run import simulate_cascade


def test_split_scenarios_deterministic_and_disjoint() -> None:
    scenario_ids = [f"r-{i:04d}" for i in range(1, 11)]

    train_1, test_1 = split_scenarios(scenario_ids, train_frac=0.7)
    train_2, test_2 = split_scenarios(scenario_ids, train_frac=0.7)

    # Deterministic
    assert train_1 == train_2
    assert test_1 == test_2

    # Disjoint and complete
    assert set(train_1).isdisjoint(set(test_1))
    assert set(train_1) | set(test_1) == set(scenario_ids)

    # 70% of 10 is 7 train, 3 test
    assert len(train_1) == 7
    assert len(test_1) == 3


def test_evaluate_hand_computed_metrics() -> None:
    # 6 hand-crafted scenario pairs
    pairs: List[Dict[str, Any]] = [
        # Pair 0: R2 pass, R4 pass
        {
            "scenario_id": "s0",
            "r2": {"status": "answered", "grounded": True, "steps_used": 5, "cited_sources": ["d1"], "cost_usd": 0.01},
            "r4": {"status": "answered", "grounded": True, "steps_used": 3, "cost_usd": 0.05},
        },
        # Pair 1: R2 step_cap fail, R4 pass
        {
            "scenario_id": "s1",
            "r2": {"status": "step_cap", "grounded": False, "steps_used": 24, "cited_sources": [], "cost_usd": 0.01},
            "r4": {"status": "answered", "grounded": True, "steps_used": 4, "cost_usd": 0.05},
        },
        # Pair 2: R2 answered fail, R4 fail
        {
            "scenario_id": "s2",
            "r2": {"status": "answered", "grounded": False, "steps_used": 10, "cited_sources": ["d2"], "cost_usd": 0.01},
            "r4": {"status": "answered", "grounded": False, "steps_used": 6, "cost_usd": 0.05},
        },
        # Pair 3: R2 pass but no citation, R4 pass
        {
            "scenario_id": "s3",
            "r2": {"status": "answered", "grounded": True, "steps_used": 8, "cited_sources": [], "cost_usd": 0.01},
            "r4": {"status": "answered", "grounded": True, "steps_used": 2, "cost_usd": 0.05},
        },
        # Pair 4: R2 malformed fail, R4 pass
        {
            "scenario_id": "s4",
            "r2": {"status": "malformed", "grounded": False, "steps_used": 3, "cited_sources": [], "cost_usd": 0.01},
            "r4": {"status": "answered", "grounded": True, "steps_used": 5, "cost_usd": 0.05},
        },
        # Pair 5: R2 pass, R4 fail
        {
            "scenario_id": "s5",
            "r2": {"status": "answered", "grounded": True, "steps_used": 15, "cited_sources": ["d3"], "cost_usd": 0.01},
            "r4": {"status": "answered", "grounded": False, "steps_used": 4, "cost_usd": 0.05},
        },
    ]

    # 1. r2_only: no escalation
    # R2 passes on s0, s3, s5 -> 3/6 = 0.5
    # Total cost = 6 * 0.01 = 0.06 -> mean 0.01
    r2_res = evaluate("r2_only", pairs)
    assert r2_res["n"] == 6
    assert r2_res["escalations"] == 0
    assert r2_res["escalation_rate"] == 0.0
    assert r2_res["passed"] == 3
    assert pytest.approx(r2_res["pass_rate"], 1e-6) == 0.5
    assert pytest.approx(r2_res["mean_cost"], 1e-6) == 0.01

    # 2. r4_only: all escalate
    # R4 passes on s0, s1, s3, s4 -> 4/6 = 2/3
    # Total cost = 6 * (0.01 + 0.05) = 0.36 -> mean 0.06
    r4_res = evaluate("r4_only", pairs)
    assert r4_res["n"] == 6
    assert r4_res["escalations"] == 6
    assert r4_res["escalation_rate"] == 1.0
    assert r4_res["passed"] == 4
    assert pytest.approx(r4_res["pass_rate"], 1e-6) == 4 / 6
    assert pytest.approx(r4_res["mean_cost"], 1e-6) == 0.06

    # 3. escalate_if_not_answered:
    # Escalates on s1 (step_cap) and s4 (malformed) -> 2 escalations.
    # Out of s1, s4: both R4 pass.
    # Out of non-escalated: s0 (pass), s2 (fail), s3 (pass), s5 (pass) -> 3 pass.
    # Total pass = 2 + 3 = 5 / 6.
    # Total cost = 4 * 0.01 + 2 * (0.01 + 0.05) = 0.04 + 0.12 = 0.16 -> mean 0.16/6 = 0.026666...
    not_ans_res = evaluate("escalate_if_not_answered", pairs)
    assert not_ans_res["n"] == 6
    assert not_ans_res["escalations"] == 2
    assert pytest.approx(not_ans_res["escalation_rate"], 1e-6) == 2 / 6
    assert not_ans_res["passed"] == 5
    assert pytest.approx(not_ans_res["pass_rate"], 1e-6) == 5 / 6
    assert pytest.approx(not_ans_res["mean_cost"], 1e-6) == 0.16 / 6


def test_pareto_frontier_drops_dominated_point() -> None:
    points = [
        {"name": "p_cheap_low", "mean_cost": 0.01, "pass_rate": 0.60},
        {"name": "p_dominated_1", "mean_cost": 0.01, "pass_rate": 0.50},  # same cost, lower pass -> dominated by p_cheap_low
        {"name": "p_mid", "mean_cost": 0.02, "pass_rate": 0.75},          # non-dominated
        {"name": "p_dominated_2", "mean_cost": 0.025, "pass_rate": 0.70}, # higher cost than p_mid, lower pass -> dominated
        {"name": "p_frontier_high", "mean_cost": 0.04, "pass_rate": 0.90}, # non-dominated
    ]

    frontier = pareto_frontier(points)
    names = [p["name"] for p in frontier]
    assert names == ["p_cheap_low", "p_mid", "p_frontier_high"]
    # Check that dominated points were eliminated
    assert "p_dominated_1" not in names
    assert "p_dominated_2" not in names


def test_fit_picks_expected_t() -> None:
    # Create a training set where steps >= 12 should escalate to R4
    # For steps < 12, R2 is correct (True) and R4 is wrong (False).
    # For steps >= 12, R2 is wrong (False) and R4 is correct (True).
    pairs_train = []
    for step in range(2, 25):
        if step < 12:
            r2_pass = True
            r4_pass = False
        else:
            r2_pass = False
            r4_pass = True

        pairs_train.append({
            "scenario_id": f"s-{step}",
            "r2": {"status": "answered", "grounded": r2_pass, "steps_used": step, "cost_usd": 0.01},
            "r4": {"status": "answered", "grounded": r4_pass, "steps_used": 4, "cost_usd": 0.05},
        })

    fitted = fit(pairs_train)
    # The optimal threshold for steps >= t must be exactly 12 to achieve 100% accuracy
    assert fitted["chosen_thresholds"]["escalate_if_steps_ge_t"] == 12
    assert fitted["escalate_if_steps_ge_t"] == 12


def test_run_simulate_writes_results(tmp_path: Path) -> None:
    # Create two tiny sweep files
    r2_data = [
        {"scenario_id": "r-001", "status": "answered", "grounded": True, "steps_used": 5, "cost_usd": 0.005, "cited_sources": ["s1"]},
        {"scenario_id": "r-002", "status": "step_cap", "grounded": False, "steps_used": 24, "cost_usd": 0.009, "cited_sources": []},
        {"scenario_id": "r-003", "status": "answered", "grounded": False, "steps_used": 12, "cost_usd": 0.006, "cited_sources": ["s2"]},
        {"scenario_id": "r-004", "status": "answered", "grounded": True, "steps_used": 7, "cost_usd": 0.005, "cited_sources": ["s3"]},
    ]
    r4_data = [
        {"scenario_id": "r-001", "status": "answered", "grounded": True, "steps_used": 3, "cost_usd": 0.03, "cited_sources": ["s1"]},
        {"scenario_id": "r-002", "status": "answered", "grounded": True, "steps_used": 4, "cost_usd": 0.035, "cited_sources": ["s2"]},
        {"scenario_id": "r-003", "status": "answered", "grounded": False, "steps_used": 6, "cost_usd": 0.032, "cited_sources": ["s2"]},
        {"scenario_id": "r-004", "status": "answered", "grounded": True, "steps_used": 2, "cost_usd": 0.028, "cited_sources": ["s3"]},
    ]

    r2_file = tmp_path / "sweep_r2.json"
    r4_file = tmp_path / "sweep_r4.json"
    r2_file.write_text(json.dumps(r2_data), encoding="utf-8")
    r4_file.write_text(json.dumps(r4_data), encoding="utf-8")

    out_dir = tmp_path / "out"
    dummy_db = tmp_path / "nonexistent.db"

    results = simulate_cascade(
        r2_file=r2_file,
        r4_file=r4_file,
        p6_db=dummy_db,
        output_dir=out_dir,
    )

    results_file = out_dir / "results.json"
    assert results_file.exists()

    saved_data = json.loads(results_file.read_text(encoding="utf-8"))
    assert saved_data["n_pairs"] == 4
    assert "split_ids_sha256" in saved_data
    assert "chosen_thresholds" in saved_data
    assert "frontier_points" in saved_data
    assert "baselines" in saved_data
    assert "r2_only" in saved_data["baselines"]
    assert "r4_only" in saved_data["baselines"]
