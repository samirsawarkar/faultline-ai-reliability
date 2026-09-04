"""Tests for SRE multiwindow multi-burn-rate arithmetic and TraceStore SLO evaluations."""
import pytest
from faultline_p2.slo.burn_rate import compute_burn_rate, evaluate_burn_rate_alert
from faultline_p2.slo.evaluator import (
    evaluate_grounded_pass_rate_sli,
    evaluate_agent_error_rate_sli,
    evaluate_step_latency_sli,
    evaluate_slos_from_trace,
)
from faultline_p2.trace.store import TraceStore


def test_hand_computed_burn_rate_arithmetic():
    """Verify SRE burn rate math against hand-computed values.
    
    Target: 0.95 (Budget: 0.05). Period: 720h (30d).
    Case 1: Error rate 0.10, window 1h -> burn rate 2.0x, consumed 0.2778%
    Case 2: Error rate 0.72, window 1h -> burn rate 14.4x, consumed 2.0%
    Case 3: Error rate 0.30, window 6h -> burn rate 6.0x, consumed 5.0%
    """
    # Case 1: Healthy minor drift
    b1 = compute_burn_rate(error_rate=0.10, error_budget=0.05, window_hours=1.0, compliance_period_hours=720.0)
    assert b1.burn_rate == 2.0
    # 2.0 * (1 / 720) * 100 = 0.2778%
    assert round(b1.budget_consumed_percent, 4) == 0.2778

    # Case 2: Catastrophic fast burn (fires Page)
    b2 = compute_burn_rate(error_rate=0.72, error_budget=0.05, window_hours=1.0, compliance_period_hours=720.0)
    assert b2.burn_rate == 14.4
    # 14.4 * (1 / 720) * 100 = 2.0%
    assert round(b2.budget_consumed_percent, 4) == 2.0

    # Case 3: Prolonged slow burn (fires Ticket)
    b3 = compute_burn_rate(error_rate=0.30, error_budget=0.05, window_hours=6.0, compliance_period_hours=720.0)
    assert b3.burn_rate == 6.0
    # 6.0 * (6 / 720) * 100 = 5.0%
    assert round(b3.budget_consumed_percent, 4) == 5.0


def test_alert_rule_evaluation():
    """Verify Page, Ticket, and OK alert decisions."""
    # Fast burn fires PAGE
    a_page = evaluate_burn_rate_alert(
        slo_id="grounded_pass_rate",
        error_rate=0.72,
        error_budget=0.05,
        fast_burn_threshold=14.4,
        slow_burn_threshold=6.0,
    )
    assert a_page.severity == "page"
    assert a_page.fast_burn_fired is True
    assert a_page.burn_rate == 14.4

    # Slow burn fires TICKET
    a_ticket = evaluate_burn_rate_alert(
        slo_id="grounded_pass_rate",
        error_rate=0.30,
        error_budget=0.05,
        fast_burn_threshold=14.4,
        slow_burn_threshold=6.0,
    )
    assert a_ticket.severity == "ticket"
    assert a_ticket.fast_burn_fired is False
    assert a_ticket.slow_burn_fired is True

    # Nominal traffic is OK
    a_ok = evaluate_burn_rate_alert(
        slo_id="grounded_pass_rate",
        error_rate=0.02,
        error_budget=0.05,
        fast_burn_threshold=14.4,
        slow_burn_threshold=6.0,
    )
    assert a_ok.severity == "ok"
    assert a_ok.fast_burn_fired is False
    assert a_ok.slow_burn_fired is False


def test_trace_store_eval_both_directions(tmp_path):
    """Test both directions: healthy traffic does NOT fire; degraded traffic DOES fire."""
    db_path = tmp_path / "slo_test.db"
    store = TraceStore(str(db_path))

    # --- 1. HEALTHY SWEEP ---
    healthy_run = store.start_run()
    for i in range(20):
        sc_id = f"healthy-{i}"
        store.log_span(
            run_id=healthy_run, scenario_id=sc_id, tier="T1", step_index=1,
            model_name="stub", provider="local", model_version="1.0",
            prompt_tokens=100, completion_tokens=20, latency_ms=15.0,
            termination_reason="ANSWERED", verdict=1
        )
        store.record_verdict(healthy_run, sc_id, True)
    store.end_run(healthy_run, "completed")

    # Evaluate Healthy Run:
    pass_sli = evaluate_grounded_pass_rate_sli(store.conn, healthy_run)
    assert pass_sli["pass_rate"] == 1.0
    assert pass_sli["error_rate"] == 0.0

    err_sli = evaluate_agent_error_rate_sli(store.conn, healthy_run)
    assert err_sli["error_rate"] == 0.0

    eval_healthy = evaluate_slos_from_trace(store.conn, run_id=healthy_run)
    assert eval_healthy["overall_status"] == "ok"
    assert eval_healthy["slos"]["grounded_pass_rate"]["fast_burn_fired"] is False
    assert eval_healthy["slos"]["grounded_pass_rate"]["slow_burn_fired"] is False

    # --- 2. DEGRADED SWEEP ---
    # 20 scenarios, 16 fail (80% error rate -> burn rate = 0.80 / 0.05 = 16.0x > 14.4x)
    degraded_run = store.start_run()
    for i in range(20):
        sc_id = f"degraded-{i}"
        passed = (i < 4)  # 4 pass, 16 fail
        term = "ANSWERED" if passed else "MODEL_FAILURE"
        store.log_span(
            run_id=degraded_run, scenario_id=sc_id, tier="T1", step_index=1,
            model_name="stub", provider="local", model_version="1.0",
            prompt_tokens=100, completion_tokens=20, latency_ms=25.0,
            termination_reason=term, verdict=1 if passed else 0
        )
        store.record_verdict(degraded_run, sc_id, passed)
    store.end_run(degraded_run, "completed")

    # Evaluate Degraded Run:
    pass_sli_deg = evaluate_grounded_pass_rate_sli(store.conn, degraded_run)
    assert pass_sli_deg["pass_rate"] == 0.20
    assert pass_sli_deg["error_rate"] == 0.80

    err_sli_deg = evaluate_agent_error_rate_sli(store.conn, degraded_run)
    assert err_sli_deg["error_rate"] == 0.80

    eval_degraded = evaluate_slos_from_trace(store.conn, run_id=degraded_run)
    # Must fire PAGE alert
    assert eval_degraded["overall_status"] == "page"
    assert eval_degraded["slos"]["grounded_pass_rate"]["fast_burn_fired"] is True
    assert eval_degraded["slos"]["grounded_pass_rate"]["burn_rate"] >= 14.4
    assert eval_degraded["slos"]["agent_error_rate"]["fast_burn_fired"] is True

    store.close()
