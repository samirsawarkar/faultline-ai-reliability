"""Unit tests for Project P6 pass^k and concentration statistical analysis."""
from __future__ import annotations

import json
import math
import random
import sqlite3
from pathlib import Path
import pytest

from projects.p06_passk.analysis import (
    adjust_holm_family,
    classify_terminal_states,
    compute_attempts_summary,
    compute_beta_binomial_extrapolation,
    compute_concentration_counts,
    compute_independence_test,
    compute_intra_scenario_correlation,
    compute_pass_at_1,
    compute_pass_k,
    compute_tarone_z_test,
    detect_infra_dead_trials,
    load_scenario_trial_matrix,
    run_analysis,
)


def test_synthetic_matrix_metrics():
    """Verify known analytical values on a synthetic 4-scenario x 3-trial matrix."""
    # Symmetrical 4-scenario matrix:
    # Scenario 0: [1, 1, 1] (3 passes)
    # Scenario 1: [1, 1, 0] (2 passes)
    # Scenario 2: [1, 0, 0] (1 pass)
    # Scenario 3: [0, 0, 0] (0 passes)
    matrix = [
        [True, True, True],
        [True, True, False],
        [True, False, False],
        [False, False, False],
    ]

    # 1. pass@1: 6 / 12 = 0.5
    p1 = compute_pass_at_1(matrix, n_resamples=500)
    assert p1["score"] == 0.5
    assert p1["passing_trials"] == 6
    assert p1["total_trials"] == 12

    # 2. pass_k for k=2:
    # First 2 trials: [1, 1], [1, 1], [1, 0], [0, 0] -> 2 / 4 = 0.5
    # naive_2: 0.5^2 = 0.25
    # C_2: 0.5 / 0.25 = 2.0
    # pass_2_all_pairs: (3/3 + 1/3 + 0/3 + 0/3) / 4 = (4/3) / 4 = 1/3
    pk2 = compute_pass_k(matrix, 2, n_resamples=500)
    assert pk2["pass_hat_k"] == 0.5
    assert pk2["naive_k"] == 0.25
    assert pk2["concentration_ratio_C_k"] == 2.0
    assert abs(pk2["pass_2_all_pairs"] - (1.0 / 3.0)) < 1e-5

    # 3. pass_k for k=3:
    # All 3 trials: [1, 1, 1] -> 1 / 4 = 0.25
    # naive_3: 0.5^3 = 0.125
    # C_3: 0.25 / 0.125 = 2.0
    pk3 = compute_pass_k(matrix, 3, n_resamples=500)
    assert pk3["pass_hat_k"] == 0.25
    assert pk3["naive_k"] == 0.125
    assert pk3["concentration_ratio_C_k"] == 2.0
    assert "deviation_delta" in pk3
    assert pk3["deviation_delta"] == 0.125

    # 4. Histogram: exactly 1 scenario per success count in {0, 1, 2, 3}
    ind = compute_independence_test(matrix, n_mc_draws=500)
    assert ind["observed_histogram"] == {0: 1, 1: 1, 2: 1, 3: 1}
    assert ind["chi2_df"] == 2

    # 5. ICC(1, 1): analytically exactly 7 / 16 = 0.4375
    corr = compute_intra_scenario_correlation(matrix, n_resamples=500)
    assert abs(corr["icc"] - 0.4375) < 1e-5

    # 6. Concentration counts:
    conc = compute_concentration_counts(matrix)
    assert conc["always_pass"] == 1
    assert conc["always_fail"] == 1
    assert conc["mixed"] == 2
    assert conc["total_scenarios"] == 4


def test_r6_infra_invalid():
    """Verify that R6 yields status 'infra_invalid' with evidence and zero reliability statistics."""
    trace_db_path = Path("projects/p06_passk/trace.db")
    matrix_dict, spans, runs, max_verdicts = load_scenario_trial_matrix(trace_db_path, "p06_r6_7e0a1b79")
    assert spans == 900
    assert runs == 450
    assert max_verdicts == 0

    results = run_analysis(
        trace_db_path=trace_db_path,
        ledger_path=Path("projects/p06_passk/ledger.jsonl"),
        output_path=None,
        n_resamples=100,
    )
    r6 = results["rungs"]["R6"]
    assert r6["status"] == "infra_invalid"
    assert r6["evidence"]["spans_count"] == 900
    assert r6["evidence"]["runs_count"] == 450
    assert r6["evidence"]["verdicts_count"] == 0

    for forbidden_stat in [
        "pass_at_1",
        "pass_k",
        "independence_test",
        "intra_scenario_correlation",
        "concentration_counts",
        "cost_per_grounded_pass",
    ]:
        assert forbidden_stat not in r6, f"Forbidden statistic '{forbidden_stat}' found in R6"


def test_analysis_json_deterministic_reproducibility(tmp_path: Path):
    """Verify that analysis.json regenerates byte-identical on successive runs."""
    out1 = tmp_path / "analysis_run1.json"
    out2 = tmp_path / "analysis_run2.json"

    run_analysis(
        trace_db_path=Path("projects/p06_passk/trace.db"),
        ledger_path=Path("projects/p06_passk/ledger.jsonl"),
        output_path=out1,
        seed=42,
        n_resamples=200,
    )

    run_analysis(
        trace_db_path=Path("projects/p06_passk/trace.db"),
        ledger_path=Path("projects/p06_passk/ledger.jsonl"),
        output_path=out2,
        seed=42,
        n_resamples=200,
    )

    assert out1.read_bytes() == out2.read_bytes(), "analysis.json output is not byte-identical across runs"


def test_paired_comparison_structure():
    """Verify paired comparison computes all-3-pass and trial-1 pass tables and McNemar tests."""
    results = run_analysis(
        trace_db_path=Path("projects/p06_passk/trace.db"),
        ledger_path=Path("projects/p06_passk/ledger.jsonl"),
        output_path=None,
        n_resamples=100,
    )
    paired = results["paired_comparisons"]["R2_vs_R4"]
    assert "as_run" in paired
    assert "infra_excluded" in paired
    assert "infra_excluded_strict" in paired

    as_run = paired["as_run"]
    assert "all_3_pass" in as_run
    assert "trial_1_pass" in as_run

    # All-3-pass counts
    all3_table = as_run["all_3_pass"]["table"]
    assert all3_table["both_correct"] == 0
    assert all3_table["a_only"] == 34
    assert all3_table["b_only"] == 3
    assert all3_table["both_wrong"] == 113
    assert as_run["all_3_pass"]["ties"] == 113
    assert abs(as_run["all_3_pass"]["paired_d_z"] - 0.456) < 0.01
    assert as_run["all_3_pass"]["mcnemar"]["exact_p_value"] < 1e-4

    # Trial-1 pass counts
    t1_table = as_run["trial_1_pass"]["table"]
    assert t1_table["both_correct"] == 13
    assert t1_table["a_only"] == 77
    assert t1_table["b_only"] == 10
    assert t1_table["both_wrong"] == 50
    assert as_run["trial_1_pass"]["ties"] == 63
    assert abs(as_run["trial_1_pass"]["paired_d_z"] - 0.722) < 0.01
    assert as_run["trial_1_pass"]["mcnemar"]["exact_p_value"] < 1e-6


def test_infra_contamination_sensitivity():
    """Verify infrastructure-contamination sensitivity analysis for R4 and R2."""
    trace_db_path = Path("projects/p06_passk/trace.db")

    # a) R4 infra_dead count == 95, touched scenarios == 33, all3 == 31
    r4_dead_info = detect_infra_dead_trials(trace_db_path, "p06_r4_7e0a1b79")
    assert r4_dead_info["infra_dead_trials"] == 95
    assert r4_dead_info["infra_dead_scenarios"] == 33
    assert r4_dead_info["infra_dead_scenarios_all3"] == 31

    # b) R2 infra_dead count == 0
    r2_dead_info = detect_infra_dead_trials(trace_db_path, "p06_r2_7e0a1b79")
    assert r2_dead_info["infra_dead_trials"] == 0
    assert r2_dead_info["infra_dead_scenarios"] == 0
    assert r2_dead_info["infra_dead_scenarios_all3"] == 0

    results = run_analysis(
        trace_db_path=trace_db_path,
        ledger_path=Path("projects/p06_passk/ledger.jsonl"),
        output_path=None,
        n_resamples=200,
    )

    assert "as_run" in results["rungs"]["R2"]
    assert "infra_excluded" in results["rungs"]["R2"]
    assert "infra_excluded_strict" in results["rungs"]["R2"]
    assert "as_run" in results["rungs"]["R4"]
    assert "infra_excluded" in results["rungs"]["R4"]
    assert "infra_excluded_strict" in results["rungs"]["R4"]

    r4_infra = results["rungs"]["R4"]["infra_excluded"]
    assert r4_infra["concentration_counts"]["total_scenarios"] == 117
    assert r4_infra["pass_at_1"]["total_trials"] == 117 * 3

    p1 = r4_infra["pass_at_1"]["score"]
    assert 0.185 <= p1 <= 0.195

    c3 = r4_infra["pass_k"]["k3"]["concentration_ratio_C_k"]
    assert 3.0 <= c3 <= 4.5


def test_parametric_bootstrap_uniform_null_and_df2():
    """Verify that parametric bootstrap GoF uses df=2 and recovers p roughly uniform under H0."""
    # Under H0 with true p=0.5, 60 scenarios x 3 iid trials
    rng = random.Random(123)
    p_values = []
    for _ in range(15):
        sim_mat = [[rng.random() < 0.5 for _ in range(3)] for _ in range(60)]
        gof = compute_independence_test(sim_mat, seed=42, n_mc_draws=400)
        assert gof["chi2_df"] == 2
        p_values.append(gof["parametric_bootstrap_p_value"])
    
    # Loose check: mean p-value under null should be well away from extremes (e.g. between 0.20 and 0.80)
    mean_p = sum(p_values) / len(p_values)
    assert 0.20 <= mean_p <= 0.80, f"Expected roughly uniform mean p-value under null, got {mean_p}"


def test_holm_never_emits_zero():
    """Verify Holm-Bonferroni correction never stores 0.0, handling tiny p-values gracefully."""
    raw_tests = [
        {"test": "test_underflow", "description": "tiny p", "raw_p_source": "src1", "raw_p_value": 1e-16},
        {"test": "test_small", "description": "mcnemar exact", "raw_p_source": "src2", "raw_p_value": 5.92e-14},
        {"test": "test_mid", "description": "gof r4", "raw_p_source": "src3", "raw_p_value": 0.005},
        {"test": "test_large", "description": "gof r2", "raw_p_source": "src4", "raw_p_value": 0.38},
    ]
    adjusted = adjust_holm_family(raw_tests)
    for t in adjusted:
        adj = t["holm_adjusted_p_value"]
        assert adj != 0.0, f"Adjusted p-value is 0.0 for {t['test']}"
        assert adj != "0.0", f"Adjusted p-value string is '0.0' for {t['test']}"
        if isinstance(adj, (float, int)):
            assert adj > 0.0


def test_terminal_state_classifier_synthetic_fixture(tmp_path: Path):
    """Verify terminal-state classification on a synthetic 3-run fixture covering key categories."""
    db_file = tmp_path / "test_synth.db"
    conn = sqlite3.connect(db_file)
    conn.execute(
        """
        CREATE TABLE spans (
            span_id TEXT, run_id TEXT, scenario_id TEXT, tier TEXT, step_index INT,
            tool_name TEXT, model_name TEXT, provider TEXT, model_version TEXT,
            quantization TEXT, prompt_tokens INT, completion_tokens INT, latency_ms REAL,
            termination_reason TEXT, timestamp TEXT, verdict INT
        )
        """
    )
    # Run 1: answered_pass
    conn.execute(
        "INSERT INTO spans VALUES ('s1', 'r1', 'scen1_k1', 't3', 1, 'answer', 'm', 'p', 'v', 'q', 100, 50, 500.0, 'answered', '2026-09-16T12:00:00Z', 1)"
    )
    # Run 2: dead_at_start (<1ms latency)
    conn.execute(
        "INSERT INTO spans VALUES ('s2', 'r1', 'scen2_k1', 't3', 0, NULL, 'm', 'p', 'v', 'q', 100, 0, 0.4, 'client_timeout', '2026-09-16T12:01:00Z', 0)"
    )
    # Run 3: midrun_no_completion (>60s latency on terminal step 2)
    conn.execute(
        "INSERT INTO spans VALUES ('s3a', 'r1', 'scen3_k1', 't3', 1, 'search', 'm', 'p', 'v', 'q', 100, 60, 400.0, 'tool_use', '2026-09-16T12:02:00Z', 0)"
    )
    conn.execute(
        "INSERT INTO spans VALUES ('s3b', 'r1', 'scen3_k1', 't3', 2, NULL, 'm', 'p', 'v', 'q', 150, 0, 65000.0, 'model_failure', '2026-09-16T12:03:00Z', 0)"
    )
    conn.commit()
    conn.close()

    res = classify_terminal_states(db_file, "r1")
    cats = res["categories"]
    assert cats["answered_pass"]["total"] == 1
    assert cats["dead_at_start"]["total"] == 1
    assert cats["dead_at_start"]["latency_signature"]["<1ms"] == 1
    assert cats["midrun_no_completion"]["total"] == 1
    assert cats["midrun_no_completion"]["latency_signature"][">60s"] == 1
    assert "scen2" in res["strict_dropped_scenarios"]
    assert "scen3" in res["strict_dropped_scenarios"]


def test_strict_variant_and_retained_ids():
    """Verify strict variant drops the right scenarios and retained_scenario_ids are stored."""
    results = run_analysis(
        trace_db_path=Path("projects/p06_passk/trace.db"),
        ledger_path=Path("projects/p06_passk/ledger.jsonl"),
        output_path=None,
        n_resamples=100,
    )

    r2 = results["rungs"]["R2"]
    r4 = results["rungs"]["R4"]

    # Pass 2 attempt segmentation: R2 strict n=49, R4 strict n=24
    assert r2["infra_excluded_strict"]["n_scenarios"] == 49
    assert r4["infra_excluded_strict"]["n_scenarios"] == 24

    # Check retained_scenario_ids present and non-empty in all variants
    for var in ["as_run", "infra_excluded", "infra_excluded_strict"]:
        assert "retained_scenario_ids" in r2[var]
        assert "retained_scenario_ids" in r4[var]
        assert len(r2[var]["retained_scenario_ids"]) == r2[var]["n_scenarios"]
        assert len(r4[var]["retained_scenario_ids"]) == r4[var]["n_scenarios"]
        assert "order_effects" in r2[var]
        assert "order_effects" in r4[var]

    # Check paired comparisons also have retained_scenario_ids
    paired = results["paired_comparisons"]["R2_vs_R4"]
    for var in ["as_run", "infra_excluded", "infra_excluded_strict"]:
        assert "retained_scenario_ids" in paired[var]
        assert len(paired[var]["retained_scenario_ids"]) == paired[var]["n_scenarios"]

    # Verify that a dropped scenario (e.g. r-0305 or r-0320) is not in R4 strict
    assert "r-0305" not in r4["infra_excluded_strict"]["retained_scenario_ids"]
    assert "r-0320" not in r4["infra_excluded_strict"]["retained_scenario_ids"]


def test_d010_attempt_segmentation():
    """Verify D-010 attempt segmentation: Pass 1 cap 12 discarded spend vs Pass 2 cap 24 final spend."""
    trace_db_path = Path("projects/p06_passk/trace.db")
    ledger_path = Path("projects/p06_passk/ledger.jsonl")
    
    attempts = compute_attempts_summary(trace_db_path, ledger_path)
    assert "pass_1" in attempts
    assert "pass_2" in attempts
    assert "total" in attempts

    p1 = attempts["pass_1"]
    p2 = attempts["pass_2"]
    tot = attempts["total"]

    assert p1["cap"] == 12
    assert p2["cap"] == 24

    # Discarded tokens (~18.9M) and final tokens (~35.4M)
    assert p1["total_discarded_tokens"] == 18917495
    assert p2["total_final_tokens"] == 35401507
    assert tot["grand_total_tokens"] == 54319002
    assert abs(tot["discarded_token_percentage"] - 34.83) < 0.1

    # Discarded spend ($0.3974) and final spend ($23.0719)
    assert abs(p1["total_discarded_spend_usd"] - 0.3974) < 1e-3
    assert abs(p2["total_final_spend_usd"] - 23.0719) < 1e-3
    assert abs(tot["grand_total_spend_usd"] - 23.4693) < 1e-3

    # Pass 2 terminal states have zero step_cap_sub24 (since Pass 2 was run at cap 24)
    r2_term = classify_terminal_states(trace_db_path, "p06_r2_7e0a1b79")
    r4_term = classify_terminal_states(trace_db_path, "p06_r4_7e0a1b79")
    assert r2_term["categories"]["step_cap_sub24"]["total"] == 0
    assert r4_term["categories"]["step_cap_sub24"]["total"] == 0


def test_tarone_z_score_test():
    """Verify Tarone (1979) C(alpha) score test detects overdispersion structure correctly."""
    rng = random.Random(42)
    mat_homo = [[rng.random() < 0.5 for _ in range(3)] for _ in range(100)]
    t_homo = compute_tarone_z_test(mat_homo)
    assert t_homo["method"] == "tarone_1979_c_alpha_score_test"
    assert t_homo["n_clusters"] == 100
    assert t_homo["trials_per_cluster"] == 3
    assert t_homo["p_value"] > 0.05

    mat_over = [[True, True, True] for _ in range(50)] + [[False, False, False] for _ in range(50)]
    t_over = compute_tarone_z_test(mat_over)
    assert t_over["z_statistic"] > 5.0
    assert t_over["p_value"] < 1e-5


def test_beta_binomial_compounding_extrapolation():
    """Verify closed-form beta-binomial moment compounding table against Reviewer #2 analytical values."""
    table = compute_beta_binomial_extrapolation(
        [[True, True, True]] * 63 + [[False, False, False]] * 37,
        icc=-0.0287,
        icc_ci=[-0.1156, 0.0668],
        n_resamples=100,
    )
    assert "k1" in table
    assert "k8" in table
    assert "k10" in table
    assert table["k1"]["concentration_ratio_C_k"] == 1.0

    results = run_analysis(
        trace_db_path=Path("projects/p06_passk/trace.db"),
        ledger_path=Path("projects/p06_passk/ledger.jsonl"),
        output_path=None,
        n_resamples=100,
    )
    r2_extrap = results["rungs"]["R2"]["as_run"]["intra_scenario_correlation"]["extrapolation_table_beta_binomial"]
    assert "k8" in r2_extrap
    assert r2_extrap["k8"]["concentration_ratio_C_k"] == 1.0
    assert 1.5 <= r2_extrap["k8"]["concentration_ratio_at_icc_ci_upper"] <= 2.5
