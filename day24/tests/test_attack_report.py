"""Q5 attack boundary, recommendation, renderer, and fail-condition gate."""
from faultline_q5 import render_q5


def test_winner_improves_paired_success_over_no_recovery(q5_report):
    paired = q5_report["q5_recommendation"]["paired_success_vs_no_recovery"]
    assert paired["table"]["b_only"] == 143
    assert paired["table"]["a_only"] == 0
    assert paired["significant_at_0.05"]


def test_worse_severity_breaks_the_success_and_cost_envelope(q5_report):
    attack = q5_report["winner_attack"]["attacks"]["worse_severity"]
    assert not attack["recommendation_survives"]
    assert not attack["threshold_checks"]["success_lower_bound"]
    assert not attack["threshold_checks"]["mean_cost_upper_bound"]
    assert (
        attack["paired_vs_base_operating_condition"]["success_rate_delta"]
        < 0
    )


def test_tight_budgets_surface_suppressed_recoveries(q5_report):
    attack = q5_report["winner_attack"]["attacks"]["tight_budgets"]
    metrics = attack["metrics"]
    assert not attack["recommendation_survives"]
    assert metrics["statuses"]["cost_budget_abort"] == 65
    assert metrics["statuses"]["latency_budget_abort"] == 105
    assert metrics["user_visible_correct_success"]["rate"] == 0.575
    assert metrics["mean_cost"]["value"] <= 2.0
    assert metrics["p95_latency"]["value"] <= 45.0


def test_fail_condition_guard_requires_all_three_decision_dimensions(q5_report):
    guard = q5_report["fail_condition_guard"]
    assert guard["winner_has_cost"]
    assert guard["winner_has_latency"]
    assert guard["winner_has_uncertainty"]
    assert guard["winner_model_caveats_present"]
    assert guard["passed"]


def test_q5_renderer_exposes_tradeoff_and_attack_boundary(q5_report):
    rendered = render_q5(q5_report)
    assert "P4_selective_guarded" in rendered
    assert "mean cost (95% boot CI)" in rendered
    assert "p95 latency (95% boot CI)" in rendered
    assert "paired bootstrap difference intervals" in rendered
    assert "worse_severity" in rendered
    assert "tight_budgets" in rendered
    assert "reference upper-bound policy" in rendered
    assert "strict simulator oracle" in rendered
    assert "Fail-condition guard passed: **True**" in rendered
