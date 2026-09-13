"""Unit tests for Project P6: Pass^k Decay & Failure Concentration."""
from __future__ import annotations

import json
from pathlib import Path
import pytest

from faultline_p2.stats.intervals import wilson_interval
from faultline_p2.stats.paired import mcnemar_from_pairs
from faultline_p2.stats.passk import naive_p_k, pass_hat_k
from projects.p06_passk.run import (
    DEFAULT_RUNGS,
    ensure_hard_pool_manifest,
    generate_figure,
    simulate_mock_trial_outcome,
)


def test_p06_manifest_attestation(tmp_path):
    manifest_path1 = tmp_path / "manifest1.json"
    manifest_path2 = tmp_path / "manifest2.json"

    m1 = ensure_hard_pool_manifest(manifest_path1)
    m2 = ensure_hard_pool_manifest(manifest_path2)

    assert m1["scenario_count"] == 150
    assert m1["trials_per_scenario_k"] == 3
    assert m1["total_runs_per_model"] == 450
    assert m1["manifest_sha256"] == m2["manifest_sha256"]
    assert len(m1["scenario_ids"]) == 150
    assert m1["scenario_ids"][0] == "r-0201"
    assert m1["scenario_ids"][-1] == "r-0350"


def test_p06_passk_decay_calculations():
    # 5 scenarios, k=3 trials
    trials = [
        [True, True, True],
        [True, True, True],
        [True, False, True],
        [False, False, False],
        [False, False, False],
    ]
    # pass@1 = (3 + 3 + 2 + 0 + 0) / 15 = 8 / 15 = 0.5333
    all_trials = [t for sc in trials for t in sc]
    p1 = sum(all_trials) / len(all_trials)
    assert p1 == pytest.approx(8 / 15)

    # naive p^3 = (8/15)^3 = 0.1517
    p3_naive = naive_p_k(p1, 3)
    assert p3_naive == pytest.approx((8 / 15) ** 3)

    # measured pass^3 = 2 / 5 = 0.4000
    p3_hat = pass_hat_k(trials, 3)
    assert p3_hat == 0.40

    # Measured pass^3 strictly exceeds naive p^3 (concentration)
    assert p3_hat > p3_naive


def test_p06_mcnemar_paired():
    model_a_pass3 = [True, True, False, False, True, True]
    model_b_pass3 = [True, False, False, False, True, False]

    res = mcnemar_from_pairs(model_a_pass3, model_b_pass3)
    assert "table" in res
    assert res["table"]["both_correct"] == 2
    assert res["table"]["a_only"] == 2
    assert res["table"]["b_only"] == 0
    assert res["table"]["both_wrong"] == 2


def test_p06_mock_trial_determinism():
    res1 = simulate_mock_trial_outcome("r-0201", 1, "R2")
    res2 = simulate_mock_trial_outcome("r-0201", 1, "R2")
    assert res1 == res2


def test_p06_figure_generation(tmp_path):
    results_mock = {
        "metadata": {"project": "P6"},
        "rungs": {
            "R2": {
                "model": "z-ai/glm-5.3-flash",
                "role": "Cheap Workhorse",
                "pass@1": {"score": 0.40},
                "naive_p3": {"score": 0.064},
                "measured_pass3": {"score": 0.35, "wilson_ci": [0.28, 0.43]},
                "disjoint_from_naive": True,
            },
            "R4": {
                "model": "openai/gpt-5.6-luna",
                "role": "OpenAI Frontier",
                "pass@1": {"score": 0.65},
                "naive_p3": {"score": 0.274},
                "measured_pass3": {"score": 0.58, "wilson_ci": [0.50, 0.66]},
                "disjoint_from_naive": True,
            },
            "R6": {
                "model": "deepseek/deepseek-v4-pro",
                "role": "Frontier Anchor",
                "pass@1": {"score": 0.75},
                "naive_p3": {"score": 0.421},
                "measured_pass3": {"score": 0.70, "wilson_ci": [0.62, 0.77]},
                "disjoint_from_naive": True,
            },
        },
    }
    fig_path = tmp_path / "figure.svg"
    generate_figure(results_mock, fig_path)
    assert fig_path.is_file()
    content = fig_path.read_text(encoding="utf-8")
    assert "<svg" in content
    assert "Project P6" in content
    assert "glm-5.3-flash" in content
