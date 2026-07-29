"""No-recovery and four candidate recovery policies over the same cascade trials."""
from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Dict, Tuple

from .scenario import CascadeTrial, ExperimentConfig

POLICIES: Tuple[str, ...] = (
    "P0_no_recovery",
    "P1_bounded_retry",
    "P2_unchecked_fallback",
    "P3_full_cascade",
    "P4_selective_guarded",
)

POLICY_DESCRIPTIONS = {
    "P0_no_recovery": "one primary call; timeout is user-visible failure",
    "P1_bounded_retry": "one retry for any timeout; persistent faults exhaust",
    "P2_unchecked_fallback": "secondary after timeout; no semantic quality gate",
    "P3_full_cascade": "retry + breaker + fallback + narrow judge + repetition + ceilings",
    "P4_selective_guarded": (
        "route by simulator retryability truth; persistent faults use one "
        "strict-oracle-gated fallback (reference upper-bound policy)"
    ),
}


@dataclass(frozen=True)
class PolicyOutcome:
    seed: int
    policy: str
    status: str
    visible_answer: bool
    correct_answer: bool
    wrong_visible_answer: bool
    contained: bool
    cost: float
    latency: float
    cascade_stage: str

    def to_dict(self) -> Dict[str, object]:
        return {
            "seed": self.seed,
            "policy": self.policy,
            "status": self.status,
            "visible_answer": self.visible_answer,
            "correct_answer": self.correct_answer,
            "wrong_visible_answer": self.wrong_visible_answer,
            "contained": self.contained,
            "cost": self.cost,
            "latency": self.latency,
            "cascade_stage": self.cascade_stage,
        }


def _outcome(
    trial: CascadeTrial,
    policy: str,
    status: str,
    visible: bool,
    correct: bool,
    contained: bool,
    cost: float,
    latency: float,
    stage: str,
) -> PolicyOutcome:
    return PolicyOutcome(
        seed=trial.seed,
        policy=policy,
        status=status,
        visible_answer=visible,
        correct_answer=correct,
        wrong_visible_answer=visible and not correct,
        contained=contained,
        cost=round(cost, 4),
        latency=round(latency, 4),
        cascade_stage=stage,
    )


def _apply_budget(
    outcome: PolicyOutcome,
    config: ExperimentConfig,
) -> PolicyOutcome:
    if outcome.cost > config.per_request_cost_budget:
        return replace(
            outcome,
            status="cost_budget_abort",
            visible_answer=False,
            correct_answer=False,
            wrong_visible_answer=False,
            contained=True,
            cost=config.per_request_cost_budget,
            latency=min(outcome.latency, config.per_request_latency_budget),
            cascade_stage="M5_cost_ceiling",
        )
    if outcome.latency > config.per_request_latency_budget:
        return replace(
            outcome,
            status="latency_budget_abort",
            visible_answer=False,
            correct_answer=False,
            wrong_visible_answer=False,
            contained=True,
            latency=config.per_request_latency_budget,
            cascade_stage="M5_latency_ceiling",
        )
    return outcome


def evaluate_policy(
    trial: CascadeTrial,
    policy: str,
    config: ExperimentConfig,
) -> PolicyOutcome:
    if policy not in POLICIES:
        raise ValueError(f"unknown policy: {policy}")
    scale = config.latency_scale
    if not trial.primary_fault:
        return _outcome(
            trial, policy, "primary_success", True, True, False,
            1.0, 10.0 * scale, "primary"
        )

    if policy == "P0_no_recovery":
        result = _outcome(
            trial, policy, "primary_timeout", False, False, False,
            1.0, 30.0 * scale, "F2_primary"
        )
    elif policy == "P1_bounded_retry":
        if trial.transient:
            result = _outcome(
                trial, policy, "retry_recovered", True, True, False,
                2.0, 50.0 * scale, "M2_retry"
            )
        else:
            result = _outcome(
                trial, policy, "retry_exhausted", False, False, True,
                2.0, 65.0 * scale, "M2_exhausted"
            )
    elif policy == "P2_unchecked_fallback":
        correct = trial.fallback_quality == "exact"
        result = _outcome(
            trial,
            policy,
            "fallback_correct" if correct else "fallback_wrong_visible",
            True,
            correct,
            False,
            2.0,
            42.0 * scale,
            "M4_fallback",
        )
    elif policy == "P3_full_cascade":
        if trial.transient:
            result = _outcome(
                trial, policy, "retry_recovered", True, True, False,
                2.0, 50.0 * scale, "M2_retry"
            )
        elif trial.fallback_quality == "exact":
            result = _outcome(
                trial, policy, "cascade_fallback_correct", True, True, False,
                3.25, 81.0 * scale, "M4_quality_pass"
            )
        elif trial.fallback_quality == "clear_wrong":
            result = _outcome(
                trial, policy, "judge_rejected", False, False, True,
                3.25, 81.0 * scale, "quality_reject"
            )
        else:
            result = _outcome(
                trial, policy, "cascade_ceiling_abort", False, False, True,
                4.5, 98.0 * scale, "M6_to_M5"
            )
    else:  # P4_selective_guarded
        if trial.transient:
            result = _outcome(
                trial, policy, "selective_retry_recovered", True, True, False,
                2.0, 50.0 * scale, "classified_M2"
            )
        else:
            correct = trial.fallback_quality == "exact"
            result = _outcome(
                trial,
                policy,
                (
                    "guarded_fallback_correct"
                    if correct else "guarded_fallback_rejected"
                ),
                correct,
                correct,
                not correct,
                2.25,
                46.0 * scale,
                "classified_M4_quality_gate",
            )
    return _apply_budget(result, config)
