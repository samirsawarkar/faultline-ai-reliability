"""Paired statistics and uncertainty-aware multi-objective selection."""
from dataclasses import replace

import pytest

from faultline_q5 import BASE_CONFIG, SelectionThresholds, build_trials
from faultline_q5.metrics import compare_paired
from faultline_q5.policies import evaluate_policy
from faultline_q5.selection import select_policy


def test_all_policy_rows_report_cost_latency_and_uncertainty(q5_report):
    for metrics in q5_report["experiment"]["policy_metrics"].values():
        assert "wilson_ci95" in metrics["user_visible_correct_success"]
        assert "wilson_ci95" in metrics["wrong_visible_answer"]
        assert "bootstrap_ci95" in metrics["mean_cost"]
        assert "bootstrap_ci95" in metrics["p95_latency"]
        assert "bootstrap_ci95" in metrics["success_per_cost"]
        assert "bootstrap_ci95" in metrics["success_per_100_latency"]


def test_all_candidates_have_paired_evidence_against_no_recovery(q5_report):
    paired = q5_report["experiment"]["paired_vs_no_recovery"]
    assert set(paired) == {
        "P1_bounded_retry",
        "P2_unchecked_fallback",
        "P3_full_cascade",
        "P4_selective_guarded",
    }
    assert all(item["same_seed_population"] for item in paired.values())
    assert all(item["n"] == 400 for item in paired.values())


def test_paired_comparison_refuses_misaligned_seeds():
    trials = build_trials()
    baseline = [
        evaluate_policy(trial, "P0_no_recovery", BASE_CONFIG)
        for trial in trials
    ]
    candidate = [
        evaluate_policy(trial, "P1_bounded_retry", BASE_CONFIG)
        for trial in trials[1:]
    ]
    with pytest.raises(ValueError, match="equal populations"):
        compare_paired(baseline, candidate, bootstrap_iters=20)

    shifted = [
        evaluate_policy(trial, "P1_bounded_retry", BASE_CONFIG)
        for trial in trials[1:] + trials[:1]
    ]
    with pytest.raises(ValueError, match="not aligned"):
        compare_paired(baseline, shifted, bootstrap_iters=20)


def test_guarded_policy_is_the_uncertainty_backed_dual_winner(q5_report):
    selection = q5_report["experiment"]["selection"]
    assert selection["eligible_candidates"] == [
        "P1_bounded_retry",
        "P4_selective_guarded",
    ]
    assert selection["winner"] == "P4_selective_guarded"
    assert selection["dominance_proven"]

    vs_retry = selection["paired_dominance_vs_other_eligible"][
        "P1_bounded_retry"
    ]
    assert vs_retry["success_per_cost_delta"]["paired_bootstrap_ci95"][0] > 0
    assert (
        vs_retry["success_per_100_latency_delta"][
            "paired_bootstrap_ci95"
        ][0]
        > 0
    )


def test_ineligible_policies_fail_an_explicit_constraint(q5_report):
    eligibility = q5_report["experiment"]["selection"]["eligibility"]
    assert not eligibility["P0_no_recovery"]["checks"]["success_lower_bound"]
    assert not eligibility["P2_unchecked_fallback"]["checks"][
        "wrong_answer_upper_bound"
    ]
    assert not eligibility["P3_full_cascade"]["checks"][
        "mean_cost_upper_bound"
    ]
    assert not eligibility["P3_full_cascade"]["checks"][
        "p95_latency_upper_bound"
    ]


def test_no_winner_is_reported_when_thresholds_cannot_be_cleared(q5_report):
    experiment = q5_report["experiment"]
    impossible = SelectionThresholds(min_success_ci_lower=0.99)
    # Rebuild outcomes cheaply from the same committed trials; the measured
    # summaries come from the report fixture.
    trials = build_trials()
    outcomes = {
        policy: [
            evaluate_policy(trial, policy, BASE_CONFIG) for trial in trials
        ]
        for policy in experiment["policy_definitions"]
    }
    result = select_policy(experiment["policy_metrics"], outcomes, impossible)
    assert result["winner"] is None
    assert not result["dominance_proven"]
