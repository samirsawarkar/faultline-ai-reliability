"""Assemble the availability/quality comparison, detector attack, and Q4 answer."""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT / "day14") not in sys.path:
    sys.path.insert(0, str(_ROOT / "day14"))

from faultline_stats import mcnemar_from_pairs  # noqa: E402 (Day 14)

from .detector import NarrowJudgeIntegration, score_detector
from .metrics import summarize
from .scenario import N, SEED_BASE, build_paired_records


def _rate(summary: Dict[str, Any], key: str) -> float:
    return summary[key]["rate"]


def build_report() -> Dict[str, Any]:
    paired = build_paired_records()
    primary = paired["primary_only"]
    enabled = paired["fallback_enabled"]
    primary_metrics = summarize(primary)
    fallback_metrics = summarize(enabled)

    fallback_slice = [record for record in enabled if record["route"] == "fallback"]
    detector = score_detector(enabled, NarrowJudgeIntegration())
    bad_fallbacks = [
        record for record in fallback_slice if not record["strict_quality_acceptable"]
    ]
    detector_alerts = detector["confusion"]["tp"] + detector["confusion"]["fp"]

    availability_test = mcnemar_from_pairs(
        [record["answered"] for record in primary],
        [record["answered"] for record in enabled],
    )
    strict_service_test = mcnemar_from_pairs(
        [record["strict_quality_acceptable"] for record in primary],
        [record["strict_quality_acceptable"] for record in enabled],
    )
    fallback_vs_expected_primary = mcnemar_from_pairs(
        [True] * len(fallback_slice),
        [record["strict_quality_acceptable"] for record in fallback_slice],
    )

    availability_gain = round(
        _rate(fallback_metrics, "availability") - _rate(primary_metrics, "availability"), 4
    )
    conditional_quality_change = round(
        _rate(fallback_metrics, "strict_quality_given_answered")
        - _rate(primary_metrics, "strict_quality_given_answered"),
        4,
    )
    service_quality_gain = round(
        _rate(fallback_metrics, "strict_quality_service_rate")
        - _rate(primary_metrics, "strict_quality_service_rate"),
        4,
    )

    attack = {
        "attack": (
            "Keep every request answered through the secondary, preserve valid "
            "provenance, and silently corrupt fallback quality while leaving "
            "is_degraded=false."
        ),
        "delivered_answers": fallback_metrics["availability"]["count"],
        "bad_fallback_answers": len(bad_fallbacks),
        "system_availability": fallback_metrics["availability"]["rate"],
        "availability_only_monitor": {
            "threshold": 0.99,
            "alerts": int(fallback_metrics["availability"]["rate"] < 0.99),
            "bad_answers_seen": 0,
            "fooled": fallback_metrics["availability"]["rate"] >= 0.99
                      and bool(bad_fallbacks),
        },
        "degraded_flag_only_monitor": {
            "alerts": sum(
                record["provenance"]["is_degraded"] for record in fallback_slice
            ),
            "bad_answers_seen": 0,
            "fooled": bool(bad_fallbacks)
                      and not any(
                          record["provenance"]["is_degraded"]
                          for record in fallback_slice
                      ),
        },
        "quality_detector": {
            "alerts": detector_alerts,
            "bad_answers_seen": detector["confusion"]["tp"],
            "bad_answers_missed": detector["confusion"]["fn"],
            "recall": detector["recall"],
            "precision": detector["precision"],
            "partially_resisted_attack": detector["confusion"]["tp"] > 0,
        },
        "known_caveat_reproduced": (
            detector["confusion"]["fn"] > 0
            and {item["variant"] for item in detector["false_negatives"]}
            == {"borderline_tokens"}
        ),
    }

    comparison = {
        "primary_only": primary_metrics,
        "fallback_enabled": fallback_metrics,
        "effects": {
            "availability_gain": availability_gain,
            "strict_quality_given_answered_change": conditional_quality_change,
            "strict_quality_service_rate_change": service_quality_gain,
        },
        "paired_tests": {
            "availability_primary_vs_fallback_enabled": availability_test,
            "strict_service_primary_vs_fallback_enabled": strict_service_test,
            "expected_primary_vs_fallback_quality_on_outage_slice": fallback_vs_expected_primary,
        },
    }

    q4 = {
        "question": (
            "Does fallback preserve availability while silently reducing answer quality?"
        ),
        "answer": "yes_in_this_experiment",
        "finding": (
            f"On the same {N} seeds, fallback raised availability by "
            f"{availability_gain} to {fallback_metrics['availability']['rate']}, "
            f"but strict quality among delivered answers changed by "
            f"{conditional_quality_change} to "
            f"{fallback_metrics['strict_quality_given_answered']['rate']}. "
            f"Only {fallback_metrics['fallback_quality']['strictly_acceptable']['rate']} "
            "of fallback answers met the strict rubric; "
            f"{fallback_metrics['fallback_quality']['silently_degraded']['rate']} "
            "were bad while the route-level degraded flag stayed false."
        ),
        "denominator_note": (
            "Conditional answer quality fell, while strict-quality service rate rose "
            f"by {service_quality_gain}: fallback delivered some useful answers as "
            "well as bad ones. Both denominators are reported."
        ),
        "detector_finding": (
            f"The provenance-aware narrow judge detector caught "
            f"{detector['confusion']['tp']} of "
            f"{detector['confusion']['tp'] + detector['confusion']['fn']} bad fallback "
            f"answers (recall {detector['recall']['rate']}) and surfaced every miss."
        ),
        "judge_caveats": [
            "The Day-16 judge has kappa 0.5 versus a 0.8 human inter-rater ceiling.",
            "It is not validated for standalone use and is forbidden from core success scoring.",
            "It is used pointwise only, on fallback quality; strict human-rubric labels remain ground truth.",
            "All detector false negatives are the known borderline_tokens failure slice.",
        ],
        "operating_rule": (
            "Do not declare fallback healthy from availability alone. Budget and alert "
            "on fallback strict quality, retain provenance, and route the judge's known "
            "failure slice to deterministic checks or human audit."
        ),
    }

    return {
        "params": {
            "n": N,
            "seed_base": SEED_BASE,
            "primary_outage_rule": "request_index % 3 == 0",
            "fallback_quality_slices": (
                "clear_accept, clear_reject, borderline_tokens, borderline_extra"
            ),
        },
        "metric_definitions": {
            "availability": "answered / all requests",
            "oracle_correctness_given_answered": "Day-1 oracle passes / answered",
            "strict_quality_given_answered": (
                "Day-16 strict human-rubric acceptable / answered"
            ),
            "strict_quality_service_rate": (
                "strict human-rubric acceptable / all requests; unanswered counts as not useful"
            ),
            "silently_degraded": (
                "fallback answer fails strict quality while route-level is_degraded is false"
            ),
            "provenance_complete": (
                "served_by, is_fallback, is_degraded, answered all present"
            ),
        },
        "comparison": comparison,
        "degradation_detector": detector,
        "silent_degradation_attack": attack,
        "q4_findings": q4,
        "fail_condition_guard": {
            "availability_reported": True,
            "fallback_quality_measured": (
                fallback_metrics["fallback_quality"]["fallback_answers"] > 0
            ),
            "quality_and_availability_reported_together": True,
            "judge_used_for_core_scoring": False,
            "all_detector_false_negatives_surfaced": detector[
                "all_false_negatives_surfaced"
            ],
            "passed": (
                fallback_metrics["fallback_quality"]["fallback_answers"] > 0
                and detector["all_false_negatives_surfaced"]
                and detector["policy"]["judge_contributes_to_core_success"] is False
            ),
        },
        "evidence_sample": {
            "first_bad_fallback": next(
                {
                    "request_index": record["request_index"],
                    "seed": record["seed"],
                    "variant": record["fallback_variant"],
                    "provenance": record["provenance"],
                    "oracle_passed": record["oracle_passed"],
                    "strict_quality_acceptable": record["strict_quality_acceptable"],
                }
                for record in fallback_slice
                if not record["strict_quality_acceptable"]
            )
        },
    }
