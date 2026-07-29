"""Shared-seed population and candidate-policy behavior."""
from dataclasses import replace

import pytest

from faultline_q5 import BASE_CONFIG, POLICIES, ExperimentConfig, build_trials
from faultline_q5.policies import evaluate_policy


def test_config_rejects_invalid_rates_and_budgets():
    with pytest.raises(ValueError, match="rates"):
        replace(BASE_CONFIG, primary_fault_rate=1.1).validate()
    with pytest.raises(ValueError, match="slice"):
        replace(
            BASE_CONFIG,
            fallback_exact_rate=0.8,
            fallback_clear_wrong_rate=0.3,
        ).validate()
    with pytest.raises(ValueError, match="positive"):
        replace(BASE_CONFIG, per_request_cost_budget=0).validate()
    with pytest.raises(ValueError, match="retryability"):
        replace(BASE_CONFIG, retryability_signal="unmeasured_classifier").validate()
    with pytest.raises(ValueError, match="fallback_guard"):
        replace(BASE_CONFIG, fallback_guard="narrow_judge").validate()


def test_seeded_population_is_exactly_reproducible():
    first = build_trials()
    second = build_trials(ExperimentConfig())
    assert first == second
    assert len(first) == 400
    assert sum(not trial.primary_fault for trial in first) == 230
    assert sum(trial.transient for trial in first) == 105
    assert sum(trial.persistent for trial in first) == 65


def test_every_policy_uses_the_same_ordered_seed_population():
    trials = build_trials()
    expected = [trial.seed for trial in trials]
    for policy in POLICIES:
        outcomes = [evaluate_policy(trial, policy, BASE_CONFIG) for trial in trials]
        assert [outcome.seed for outcome in outcomes] == expected


def test_unchecked_fallback_can_create_visible_wrong_answers():
    trial = next(
        trial
        for trial in build_trials()
        if trial.primary_fault and trial.fallback_quality == "clear_wrong"
    )
    outcome = evaluate_policy(trial, "P2_unchecked_fallback", BASE_CONFIG)
    assert outcome.visible_answer
    assert outcome.wrong_visible_answer
    assert not outcome.correct_answer


def test_guarded_policy_rejects_the_same_wrong_fallback():
    trial = next(
        trial
        for trial in build_trials()
        if trial.persistent and trial.fallback_quality == "clear_wrong"
    )
    outcome = evaluate_policy(trial, "P4_selective_guarded", BASE_CONFIG)
    assert not outcome.visible_answer
    assert not outcome.wrong_visible_answer
    assert outcome.contained


def test_tight_budget_suppresses_recovery_before_reporting_success():
    config = replace(
        BASE_CONFIG,
        per_request_cost_budget=1.5,
        per_request_latency_budget=45.0,
    ).validate()
    trial = next(trial for trial in build_trials(config) if trial.transient)
    outcome = evaluate_policy(trial, "P4_selective_guarded", config)
    assert outcome.status == "cost_budget_abort"
    assert not outcome.visible_answer
    assert not outcome.correct_answer
    assert outcome.cost <= config.per_request_cost_budget
    assert outcome.latency <= config.per_request_latency_budget
