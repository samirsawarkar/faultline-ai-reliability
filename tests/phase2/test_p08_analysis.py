"""Regression and verification test for Project P8 analysis layer."""
from __future__ import annotations

import json
from pathlib import Path

from projects.p08_mcptox.analysis import run_analysis


def test_p08_analysis() -> None:
    """Verify analysis against real P8 files: 6 rungs, Success counts, paradigm sums, contract_blocked."""
    base_dir = Path("projects/p08_mcptox")
    results_path = base_dir / "results.json"
    with open(results_path, "r", encoding="utf-8") as f:
        results_data = json.load(f)

    analysis_data = run_analysis(base_dir=base_dir)

    rungs = ["R1", "R2", "R3", "R4", "R5", "R6"]

    # 1. Six rungs
    assert list(analysis_data["rungs"].keys()) == rungs

    # 2. Per-rung arm A/B Success equals results.json n_by_category Success
    for r in rungs:
        res_a = results_data["rungs"][r]["arm_a"]["n_by_category"]["Success"]
        res_b = results_data["rungs"][r]["arm_b"]["n_by_category"]["Success"]
        ana_a = analysis_data["rungs"][r]["arm_a"]["success"]
        ana_b = analysis_data["rungs"][r]["arm_b"]["success"]
        assert ana_a == res_a, f"{r} Arm A success mismatch: {ana_a} != {res_a}"
        assert ana_b == res_b, f"{r} Arm B success mismatch: {ana_b} != {res_b}"

    # 3. Paradigm n per rung sums to 300
    for r in rungs:
        a_paradigm_n = sum(p["n"] for p in analysis_data["rungs"][r]["arm_a"]["by_paradigm"].values())
        b_paradigm_n = sum(p["n"] for p in analysis_data["rungs"][r]["arm_b"]["by_paradigm"].values())
        assert a_paradigm_n == 300, f"{r} Arm A paradigm n sum != 300 (got {a_paradigm_n})"
        assert b_paradigm_n == 300, f"{r} Arm B paradigm n sum != 300 (got {b_paradigm_n})"

    # 4. Step-2 rejected-call sums equal contract_blocked
    total_rej = 0
    total_blocked = 0
    for r in rungs:
        rej = analysis_data["rungs"][r]["retry_mechanics"]["step2_rejected_call"]
        blocked = results_data["rungs"][r]["arm_b"]["contract_blocked"]
        assert rej == blocked, f"{r} step-2 rejected call mismatch: {rej} != {blocked}"
        total_rej += rej
        total_blocked += blocked

    assert total_rej == total_blocked
    assert analysis_data["pooled"]["retry_mechanics"]["step2_rejected_call"] == total_rej
