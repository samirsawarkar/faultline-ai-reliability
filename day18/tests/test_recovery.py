"""Bounded recovery: budgets hold, retries are safe to repeat, and it helps."""
from __future__ import annotations

import pytest

import faultline_recovery as rec
from faultline_recovery import RetryPolicy
from faultline_recovery.policy import MAX_ATTEMPTS_CAP


def test_policy_rejects_unbounded_or_unbudgeted():
    with pytest.raises(ValueError):
        RetryPolicy(max_attempts=0).validate()
    with pytest.raises(ValueError):
        RetryPolicy(max_attempts=MAX_ATTEMPTS_CAP + 1).validate()
    with pytest.raises(ValueError):
        RetryPolicy(max_attempts=3, cost_budget=0).validate()


def test_engine_is_terminal_and_bounded_on_persistent_fault():
    pol = RetryPolicy(max_attempts=4, cost_per_attempt=1, cost_budget=6, seed=1)
    res, _ = rec.schema_repair_retry(99, pol)          # never clears
    assert res.status == "exhausted_attempts"
    assert res.attempts <= pol.max_attempts
    assert res.total_cost <= pol.cost_budget           # strict cost ceiling


def test_cost_budget_can_stop_before_max_attempts():
    # cost_budget=2 with cost_per_attempt=1 allows only 2 attempts even if max is 5
    pol = RetryPolicy(max_attempts=5, cost_per_attempt=1, cost_budget=2, seed=1)
    res, _ = rec.schema_repair_retry(99, pol)
    assert res.attempts == 2
    assert res.status == "aborted_cost_budget"


def test_m1_transient_recovers_and_commits_once():
    pol = rec.M1_POLICY
    res, committed = rec.schema_repair_retry(2, pol, request_id="R")
    assert res.recovered and res.attempts == 3      # invalid,invalid,valid
    assert committed["committed"] == "R"


def test_m2_transient_recovers_persistent_exhausts_within_latency_budget():
    pol = rec.M2_POLICY
    ok = rec.timeout_retry(rec.transient_slow(60, 20), 30, pol)
    bad = rec.timeout_retry(rec.persistent_slow(90), 30, pol)
    assert ok.recovered
    assert not bad.recovered
    assert bad.total_latency <= pol.total_latency_budget + 30   # bounded by +1 timeout


def test_backoff_is_deterministic_capped_and_jittered():
    pol = RetryPolicy(max_attempts=6, base_delay=10, max_delay=80, jitter=True, seed=7)
    a = [pol.delay_for(i) for i in range(6)]
    b = [pol.delay_for(i) for i in range(6)]
    assert a == b                                   # deterministic
    for i, d in enumerate(a):
        cap = min(80, 10 * (2 ** i))
        assert 0 <= d <= cap                        # full jitter within the cap


def test_idempotency_makes_retry_safe_to_repeat():
    nf = rec.new_failure_analysis()["idempotency"]
    assert nf["side_effects_with_ledger"] == 1
    assert nf["side_effects_naive"] == nf["duplicate_deliveries"]
    assert nf["safe_to_repeat"] is True


def test_exhaustion_attack_all_ceilings_hold():
    assert rec.exhaustion_attack()["checks"]["all_ceilings_hold"] is True


def test_recovery_significantly_improves_success():
    for m in (rec.paired_m1(), rec.paired_m2()):
        assert m["recovery_success"] > m["no_recovery_success"]
        assert m["mcnemar"]["b"] == 0               # recovery never regresses
        assert m["mcnemar"]["significant_at_0.05"] is True


def test_report_is_deterministic():
    assert rec.build_report() == rec.build_report()
