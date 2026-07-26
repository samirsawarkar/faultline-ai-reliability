"""Assemble the agreement + bias report and the validation verdict.

The verdict is deliberately conservative: the judge is FORBIDDEN from core success
scoring unconditionally (that is the oracle's job), and it is only "validated for
standalone narrow use" if it clears substantial agreement AND shows negligible
positional bias AND has no zero-agreement failure slice. Anything less means "use
only with a human check, and never for core scoring."
"""
from __future__ import annotations

from typing import Any, Dict, List

from .agreement import (
    agreement_block,
    cohen_kappa,
    kappa_label,
    per_slice_agreement,
    positional_bias,
    raw_agreement,
)
from .judge import SimulatedJudge
from .validation_set import items, pairs

KAPPA_VALIDATION_THRESHOLD = 0.80          # "substantial" (Landis & Koch)
BIAS_TOLERANCE = 0.05


def build_report() -> Dict[str, Any]:
    data = items()
    human = [it["human_label"] for it in data]
    rater_b = [it["rater_b_label"] for it in data]

    judge = SimulatedJudge(positional=True, first_preference=1.0)
    judge_labels = [judge.accept(it["reference"], it["candidate"]) for it in data]

    # inter-rater ceiling: two humans on the same items
    human_ceiling = {
        "raw_agreement": round(raw_agreement(human, rater_b), 4),
        "cohen_kappa": round(cohen_kappa(human, rater_b), 4),
        "kappa_label": kappa_label(cohen_kappa(human, rater_b)),
        "note": "human-vs-human agreement — the reliability ceiling the judge is "
                "measured against, not 1.0",
    }

    jvh = agreement_block(judge_labels, human)
    jvh["kappa_label"] = kappa_label(jvh["cohen_kappa"])
    slices = per_slice_agreement(data, judge_labels)
    failure_slices = sorted(s for s, c in slices.items() if c["agreement"] < 1.0)

    biased = positional_bias(pairs(), SimulatedJudge(positional=True, first_preference=1.0).compare_positions)
    fair = positional_bias(pairs(), SimulatedJudge(positional=False).compare_positions)

    kappa = jvh["cohen_kappa"]
    validated_standalone = (
        kappa >= KAPPA_VALIDATION_THRESHOLD
        and biased["positional_bias_rate"] <= BIAS_TOLERANCE
        and not failure_slices)

    return {
        "judge": judge.name,
        "rubric_scope": "narrow fallback-quality for F3 drift_value / F5 context_drift only",
        "validation_set_size": len(data),
        "human_ceiling_inter_rater": human_ceiling,
        "judge_vs_human": jvh,
        "per_slice_agreement": slices,
        "failure_slices": failure_slices,
        "positional_bias": {"judge_under_test": biased, "fair_control": fair,
                            "note": "each pair presented in both orders; an order-"
                                    "dependent winner is positional bias"},
        "verdict": {
            "validated_for_standalone_use": validated_standalone,
            "forbidden_from_core_success_scoring": True,
            "conditions": [
                "core success is scored ONLY by the Day-1 oracle; the judge never contributes to it",
                f"judge kappa {kappa} ({jvh['kappa_label']}) vs human ceiling "
                f"{human_ceiling['cohen_kappa']} ({human_ceiling['kappa_label']})",
                f"failure slice(s) where the judge must not be trusted alone: {failure_slices or 'none'}",
                f"positional bias rate {biased['positional_bias_rate']} on paired mode "
                f"(fair control {fair['positional_bias_rate']}) — prefer pointwise, or "
                f"average both orders",
            ],
            "rationale": "The judge agrees with humans on clear cases but is lenient "
                         "on token-order drift (a zero-agreement slice) and is fully "
                         "order-dependent on close pairwise calls. It is therefore NOT "
                         "validated for standalone use and is forbidden from core "
                         "scoring; it may assist ONLY on the narrow fallback-quality "
                         "question, outside its failure slice, with the bias mitigated.",
        },
    }
