"""Unit tests for Project P7: Provider Variance & Multi-Endpoint Grounding Calibration."""
from __future__ import annotations

import json
from pathlib import Path
import pytest

from faultline_p2.stats.intervals import wilson_interval
from faultline_p2.stats.paired import mcnemar_from_pairs
from projects.p07_variance.run import (
    ENDPOINTS,
    ensure_manifest,
    generate_figure,
    run_variance_experiment,
)


def test_p07_manifest_attestation(tmp_path):
    manifest1 = ensure_manifest(tmp_path)
    manifest2 = ensure_manifest(tmp_path)

    assert manifest1["spec_version"] == "2.0.0"
    assert manifest1["experiment"] == "p07_provider_variance"
    assert manifest1["scenario_count"] == 150

    from faultline_p2.env.corpus import build_corpus
    import random
    corpus = build_corpus()
    std_scenarios = [s for s in corpus.scenarios if s.pool == "standard"]
    rng = random.Random(42)
    sampled = rng.sample(std_scenarios, min(150, len(std_scenarios)))
    expected_tier_counts = {
        "T1": len([s for s in sampled if s.tier == "T1"]),
        "T2": len([s for s in sampled if s.tier == "T2"]),
        "T3": len([s for s in sampled if s.tier == "T3"]),
    }

    assert manifest1["tier_counts"] == expected_tier_counts
    assert manifest1["tier_counts"]["T1"] == 47
    assert manifest1["tier_counts"]["T2"] == 53
    assert manifest1["tier_counts"]["T3"] == 50
    assert len(manifest1["scenario_ids"]) == 150
    assert manifest1["manifest_sha256"] == manifest2["manifest_sha256"]
    assert "aicredits" in manifest1["endpoints"]
    assert "agy" in manifest1["endpoints"]
    assert len(manifest1["endpoints"]) == 2


def test_p07_ci_disjoint_logic():
    # Identical pass rates -> overlapping CIs
    ci_e1 = wilson_interval(28, 30, confidence=0.95)
    ci_e2 = wilson_interval(28, 30, confidence=0.95)
    # Check overlap
    is_disjoint = ci_e1[1] < ci_e2[0] or ci_e2[1] < ci_e1[0]
    assert not is_disjoint

    # Disjoint case (e.g. 0/30 vs 28/30)
    ci_zero = wilson_interval(0, 30, confidence=0.95)
    is_disjoint_zero = ci_zero[1] < ci_e1[0] or ci_e1[1] < ci_zero[0]
    assert is_disjoint_zero


def test_p07_mcnemar_invariance():
    # When all outcomes match across endpoints
    e1_bools = [True] * 28 + [False] * 2
    e2_bools = [True] * 28 + [False] * 2

    res = mcnemar_from_pairs(e1_bools, e2_bools)
    assert res["table"]["both_correct"] == 28
    assert res["table"]["both_wrong"] == 2
    assert res["table"]["a_only"] == 0
    assert res["table"]["b_only"] == 0
    assert res["p_value"] == 1.0


def test_p07_dry_run_execution(tmp_path):
    # Run stub/dry-run mode
    results = run_variance_experiment(
        scenario_count=6,
        step_cap=10,
        concurrency=1,
        real=False,
        confirm=False,
        output_dir=tmp_path,
    )
    assert "dry_run_est_cost_usd" in results
    assert results["dry_run_est_cost_usd"] < 5.0
    assert results["manifest"]["scenario_count"] == 6
    assert (tmp_path / "manifest.json").exists()

    # Verify the real results writer output schema
    shipped_path = Path("projects/p07_variance/results.json")
    assert shipped_path.exists()
    with open(shipped_path, "r", encoding="utf-8") as f:
        shipped = json.load(f)

    assert "endpoints" in shipped
    assert "aicredits" in shipped["endpoints"]
    assert "agy" in shipped["endpoints"]
    assert shipped["endpoints"]["aicredits"]["n"] == 150
    assert shipped["endpoints"]["aicredits"]["passed"] == 144
    assert shipped["endpoints"]["agy"]["n"] == 150
    assert shipped["endpoints"]["agy"]["passed"] == 134

    assert "contingency" in shipped
    assert shipped["contingency"]["both_pass"] == 130
    assert shipped["contingency"]["aicredits_only"] == 14
    assert shipped["contingency"]["agy_only"] == 4
    assert shipped["contingency"]["neither"] == 2

    assert "mcnemar" in shipped
    assert shipped["mcnemar"]["b"] == 14
    assert shipped["mcnemar"]["c"] == 4
    assert shipped["mcnemar"]["n_discordant"] == 18
    assert shipped["mcnemar"]["significant_at_0.05"] is True


def test_p07_figure_generation(tmp_path):
    mock_results = {
        "spec_version": "2.0.0",
        "experiment": "p07_provider_variance",
        "n_scenarios": 30,
        "total_sweep_cost_usd": 0.12,
        "hypothesis_h6": {
            "statement": "Same model, 2+ endpoints, grounded rates with disjoint CIs",
            "verdict": "FALSIFIED (Wilson CIs overlap across all endpoint pairs)",
        },
        "endpoints": {
            "E1": {
                "endpoint_id": "E1",
                "name": "AICredits Primary Route",
                "pass_rate": 0.9333,
                "wilson_ci": [0.7868, 0.9815],
                "latency_p50_ms": 2100.0,
                "latency_p90_ms": 3500.0,
                "latency_mean_ms": 2300.0,
                "cost_per_1k_queries": 0.38,
            },
            "E2": {
                "endpoint_id": "E2",
                "name": "AICredits Failover Route",
                "pass_rate": 0.9333,
                "wilson_ci": [0.7868, 0.9815],
                "latency_p50_ms": 2200.0,
                "latency_p90_ms": 3600.0,
                "latency_mean_ms": 2400.0,
                "cost_per_1k_queries": 0.38,
            },
            "E3": {
                "endpoint_id": "E3",
                "name": "AICredits Gateway Route",
                "pass_rate": 0.9333,
                "wilson_ci": [0.7868, 0.9815],
                "latency_p50_ms": 2150.0,
                "latency_p90_ms": 3550.0,
                "latency_mean_ms": 2350.0,
                "cost_per_1k_queries": 0.38,
            },
        },
        "mcnemar_tests": {
            "E1_vs_E2": {"p_value": 1.0, "n_discordant": 0},
        },
    }

    fig_path = tmp_path / "figure.svg"
    generate_figure(mock_results, fig_path)
    assert fig_path.exists()
    content = fig_path.read_text(encoding="utf-8")
    assert "<svg" in content
    assert "Figure 7: Provider Variance" in content
    assert "Primary Route" in content
