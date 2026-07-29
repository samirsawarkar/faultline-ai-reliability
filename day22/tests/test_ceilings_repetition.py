"""M5/M6 construction, bounds, recovery, and false-positive attacks."""
from __future__ import annotations

import pytest

import faultline_recovery_matrix as rm


def test_ceiling_policy_rejects_non_positive_bounds():
    with pytest.raises(ValueError):
        rm.CeilingPolicy(max_steps=0).validate()
    with pytest.raises(ValueError):
        rm.CeilingPolicy(cost_budget=0).validate()


def test_step_ceiling_never_overshoots():
    policy = rm.CeilingPolicy(max_steps=4, cost_budget=100)
    result = rm.run_with_ceilings(["work"] * 100, policy)
    assert result.status == "step_ceiling"
    assert result.steps == 4
    assert result.cost <= policy.cost_budget


def test_cost_ceiling_never_overshoots():
    policy = rm.CeilingPolicy(max_steps=100, cost_budget=3, cost_per_step=1)
    result = rm.run_with_ceilings(["work"] * 100, policy)
    assert result.status == "cost_ceiling"
    assert result.cost == 3
    assert result.steps <= policy.max_steps


def test_repetition_replan_recovers_transient_loop():
    result = rm.run_repetition_recovery(
        ["search"] * 4 + ["complete"],
        ["refresh", "search", "complete"],
    )
    assert result.completed is True
    assert result.repetitions_detected == 1
    assert result.replans == 1


def test_persistent_repetition_aborts_bounded():
    policy = rm.RepetitionPolicy(max_steps=8, cost_budget=8)
    result = rm.run_repetition_recovery(
        ["search"] * 5,
        ["search"] * 5,
        policy,
    )
    assert result.status == "repetition_aborted"
    assert result.steps <= policy.max_steps
    assert result.cost <= policy.cost_budget


def test_legitimate_repetition_false_positive_is_reproducible():
    result = rm.run_repetition_recovery(
        ["paginate", "paginate", "paginate", "complete"]
    )
    assert result.status == "repetition_aborted"
    assert result.completed is False
