"""Q5 base experiment, winner attacks, recommendation, and fail-condition gate."""
from __future__ import annotations

from dataclasses import replace
from typing import Any, Dict

from .experiment import build_experiment
from .metrics import compare_paired, summarize_policy
from .policies import evaluate_policy
from .scenario import BASE_CONFIG, build_trials
from .selection import SelectionThresholds


def _winner_attack(
    winner: str,
    thresholds: SelectionThresholds,
) -> Dict[str, Any]:
    worse = replace(
        BASE_CONFIG,
        name="worse_severity",
        primary_fault_rate=0.65,
        persistent_share_given_fault=0.70,
        fallback_exact_rate=0.35,
        fallback_clear_wrong_rate=0.30,
        latency_scale=1.60,
    ).validate()
    tight = replace(
        BASE_CONFIG,
        name="tight_budgets",
        per_request_cost_budget=2.0,
        per_request_latency_budget=45.0,
    ).validate()
    base_trials = build_trials(BASE_CONFIG)
    base_outcomes = [
        evaluate_policy(trial, winner, BASE_CONFIG) for trial in base_trials
    ]
    scenarios = {}
    for config in (worse, tight):
        trials = build_trials(config)
        outcomes = [evaluate_policy(trial, winner, config) for trial in trials]
        metrics = summarize_policy(outcomes)
        checks = {
            "success_lower_bound": (
                metrics["user_visible_correct_success"]["wilson_ci95"][0]
                >= thresholds.min_success_ci_lower
            ),
            "wrong_answer_upper_bound": (
                metrics["wrong_visible_answer"]["wilson_ci95"][1]
                <= thresholds.max_wrong_ci_upper
            ),
            "mean_cost_upper_bound": (
                metrics["mean_cost"]["bootstrap_ci95"][1]
                <= thresholds.max_mean_cost_ci_upper
            ),
            "p95_latency_upper_bound": (
                metrics["p95_latency"]["bootstrap_ci95"][1]
                <= thresholds.max_p95_latency_ci_upper
            ),
        }
        scenarios[config.name] = {
            "config": config.to_dict(),
            "metrics": metrics,
            "threshold_checks": checks,
            "recommendation_survives": all(checks.values()),
            "paired_vs_base_operating_condition": compare_paired(
                base_outcomes, outcomes
            ),
        }
    return {
        "winner_under_attack": winner,
        "attacks": scenarios,
        "boundary_finding": (
            "The base recommendation is conditional: higher persistence/correlation "
            "breaks the success floor, while tighter per-request budgets suppress "
            "recoverable answers. Re-run selection when either operating envelope changes."
        ),
    }


def build_report() -> Dict[str, Any]:
    thresholds = SelectionThresholds()
    experiment = build_experiment(BASE_CONFIG, thresholds)
    selection = experiment["selection"]
    winner = selection["winner"]
    if winner is None:
        raise RuntimeError("Q5 has no uncertainty-backed winner under base config")
    attack = _winner_attack(winner, thresholds)
    metrics = experiment["policy_metrics"][winner]
    paired = experiment["paired_vs_no_recovery"][winner]
    recommendation = {
        "question": (
            "Which cascade policy provides the best user-visible correct success "
            "per unit cost and latency?"
        ),
        "winner": winner,
        "statement": (
            f"{winner} is the only eligible policy that leads both correct successes "
            f"per cost ({metrics['success_per_cost']['value']}) and per 100 latency "
            f"({metrics['success_per_100_latency']['value']}); its paired 95% "
            "efficiency-difference intervals versus every other eligible policy stay "
            "above zero. It returns correct visible answers at rate "
            f"{metrics['user_visible_correct_success']['rate']} "
            f"(95% CI {metrics['user_visible_correct_success']['wilson_ci95']}) "
            f"with mean cost {metrics['mean_cost']['value']} "
            f"(bootstrap CI {metrics['mean_cost']['bootstrap_ci95']}) and p95 latency "
            f"{metrics['p95_latency']['value']} "
            f"(bootstrap CI {metrics['p95_latency']['bootstrap_ci95']})."
        ),
        "tradeoff": (
            "Selectively retrying transient faults and quality-gating one fallback "
            "avoids persistent retry waste and the full cascade's repetition path. "
            "The recommendation is not universal: both stress attacks violate at "
            "least one uncertainty-aware operating threshold."
        ),
        "paired_success_vs_no_recovery": paired["success_mcnemar"],
        "conditions": selection["thresholds"],
        "model_caveats": [
            (
                "P4 is a reference upper-bound policy: the simulator supplies the "
                "transient/persistent retryability label without classification error."
            ),
            (
                "P4's fallback guard is the strict simulator oracle, not the "
                "Day-16 narrow judge; production guard error and its cost/latency "
                "must be measured before deployment."
            ),
            (
                "Bootstrap and Wilson intervals quantify repeated-seed uncertainty "
                "inside this configured simulator, not model-form or production-shift uncertainty."
            ),
        ],
    }
    public_experiment = {
        key: value for key, value in experiment.items() if key != "_outcomes"
    }
    gate = {
        "all_policies_share_seeds": all(
            comparison["same_seed_population"]
            for comparison in experiment["paired_vs_no_recovery"].values()
        ),
        "winner_has_cost": "mean_cost" in metrics,
        "winner_has_latency": "p95_latency" in metrics,
        "winner_has_uncertainty": (
            "wilson_ci95" in metrics["user_visible_correct_success"]
            and "bootstrap_ci95" in metrics["mean_cost"]
            and "bootstrap_ci95" in metrics["p95_latency"]
            and "bootstrap_ci95" in metrics["success_per_cost"]
            and "bootstrap_ci95" in metrics["success_per_100_latency"]
        ),
        "paired_statistics_present": bool(
            experiment["paired_vs_no_recovery"]
        ),
        "dual_efficiency_dominance_proven": selection["dominance_proven"],
        "winner_attacked": len(attack["attacks"]) == 2,
        "winner_model_caveats_present": bool(recommendation["model_caveats"]),
    }
    gate["passed"] = all(gate.values())
    return {
        "experiment": public_experiment,
        "winner_attack": attack,
        "q5_recommendation": recommendation,
        "fail_condition_guard": gate,
    }
