"""Day-22 attacks, matrix conclusions, and the recovery checkpoint guard."""
from __future__ import annotations

from typing import Any, Dict

from .ceilings import CeilingPolicy, run_with_ceilings
from .matrix import build_matrix
from .repetition import RepetitionPolicy, run_repetition_recovery


def _ceiling_attack() -> Dict[str, Any]:
    step_policy = CeilingPolicy(max_steps=6, cost_budget=20)
    cost_policy = CeilingPolicy(max_steps=20, cost_budget=5)
    step = run_with_ceilings(["work"] * 100, step_policy)
    cost = run_with_ceilings(["work"] * 100, cost_policy)
    checks = {
        "step_status": step.status,
        "step_count_le_ceiling": step.steps <= step_policy.max_steps,
        "step_cost_le_budget": step.cost <= step_policy.cost_budget,
        "cost_status": cost.status,
        "cost_count_le_ceiling": cost.steps <= cost_policy.max_steps,
        "cost_cost_le_budget": cost.cost <= cost_policy.cost_budget,
    }
    return {
        "attack": "100-action non-terminating plan",
        "step_ceiling": step.to_dict(),
        "cost_ceiling": cost.to_dict(),
        "checks": checks,
        "all_bounds_hold": all(
            value
            for key, value in checks.items()
            if key.endswith(("_ceiling", "_budget"))
        ),
    }


def _repetition_attack() -> Dict[str, Any]:
    policy = RepetitionPolicy()
    transient = run_repetition_recovery(
        ["search"] * 4 + ["complete"],
        ["refresh_context", "search", "complete"],
        policy,
    )
    persistent = run_repetition_recovery(
        ["search"] * 4 + ["complete"],
        ["search"] * 4 + ["complete"],
        policy,
    )
    legitimate = run_repetition_recovery(
        ["paginate", "paginate", "paginate", "complete"], None, policy
    )
    return {
        "transient_repetition": transient.to_dict(),
        "persistent_repetition": persistent.to_dict(),
        "legitimate_repeat_control": legitimate.to_dict(),
        "transient_recovers": transient.completed,
        "persistent_terminates_bounded": (
            not persistent.completed and persistent.status == "repetition_aborted"
        ),
        "false_positive_surfaced": (
            not legitimate.completed and legitimate.status == "repetition_aborted"
        ),
    }


def build_report() -> Dict[str, Any]:
    matrix = build_matrix()
    summaries = matrix["mechanism_summaries"]
    best_by_fault: Dict[str, Dict[str, Any]] = {}
    for fault in matrix["design"]["faults"]:
        candidates = [cell for cell in matrix["cells"] if cell["fault"] == fault]
        ranked = sorted(
            candidates,
            key=lambda cell: (
                -cell["with_mechanism"]["success"]["rate"],
                cell["with_mechanism"]["mean_cost"],
                cell["with_mechanism"]["p95_latency"],
            ),
        )
        winner = ranked[0]
        improves_success = (
            winner["with_mechanism"]["success"]["rate"]
            > winner["baseline"]["success"]["rate"]
        )
        if improves_success:
            best_by_fault[fault] = {
                "mechanism": winner["mechanism"],
                "success_rate": winner["with_mechanism"]["success"]["rate"],
                "mean_cost": winner["with_mechanism"]["mean_cost"],
                "p95_latency": winner["with_mechanism"]["p95_latency"],
                "note": (
                    "Ranked by correct success, then mean cost, then p95 latency; "
                    "containment-only mechanisms may be safer without winning success."
                ),
            }
        else:
            best_by_fault[fault] = {
                "mechanism": "none_of_M1_M6",
                "success_rate": winner["with_mechanism"]["success"]["rate"],
                "mean_cost": None,
                "p95_latency": None,
                "note": (
                    "No mechanism improves correct success over the paired baseline; "
                    "semantic rejection/re-grounding is still required."
                ),
            }

    composition = {
        "rule": (
            "Detect first, then select the narrowest mechanism: M1 for F1, M2 for F2, "
            "M3+M4 for F4, M5 as an outer envelope, and M6 inside that envelope for "
            "F6. F3/F5 require semantic rejection/re-grounding; none of M1–M6 proves "
            "those answers correct."
        ),
        "order": [
            "outer M5 step/cost ceiling",
            "fault-specific detector",
            "narrow recovery (M1/M2/M3+M4/M6)",
            "oracle or narrow semantic quality check",
            "terminal success, contained failure, or escalation",
        ],
        "do_not_compose_blindly": (
            "Applying every mechanism to every request compounds false opens, "
            "premature ceilings, latency, cost, and repetition false positives."
        ),
    }

    gate = matrix["fail_condition_guard"]
    checkpoint = {
        "six_mechanism_matrix_complete": (
            matrix["design"]["cells"] == 36
            and len(summaries) == 6
        ),
        "paired_evidence_complete": gate["every_mechanism_has_paired_evidence"],
        "new_failures_measured": gate["all_recovery_induced_harms_measured"],
        "ceilings_hold": _ceiling_attack()["all_bounds_hold"],
    }
    checkpoint["passed"] = all(checkpoint.values())

    return {
        "matrix": matrix,
        "attacks": {
            "ceilings": _ceiling_attack(),
            "repetition": _repetition_attack(),
            "recovery_induced_harms": matrix["recovery_induced_harm_audit"],
        },
        "best_by_fault": best_by_fault,
        "composition_policy": composition,
        "checkpoint_22": checkpoint,
    }
