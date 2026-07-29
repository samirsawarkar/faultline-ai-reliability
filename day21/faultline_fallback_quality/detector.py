"""A provenance-aware degradation detector using the Day-16 narrow judge.

The integration is deliberately conservative:

* it checks that the Day-16 validation report and prohibitions are present;
* it uses pointwise judgments only (no position-biased pairwise comparison);
* it runs only on fallback outputs;
* it never writes or replaces `oracle_passed` or strict-quality ground truth.

The simulated judge is known to miss token-order drift. That miss is retained and
measured rather than patched out, because Q4 must state the detector's real limits.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict, List

_ROOT = Path(__file__).resolve().parents[2]
for _day in ("day14", "day16"):
    _path = str(_ROOT / _day)
    if _path not in sys.path:
        sys.path.insert(0, _path)

from faultline_judge import SimulatedJudge, build_report as judge_validation_report  # noqa: E402

from .metrics import PROVENANCE_FIELDS, provenance_consistent, rate_block


class NarrowJudgeIntegration:
    """Validation-gated, pointwise-only adapter for fallback-quality alerts."""

    def __init__(self, judge=None, validation: Dict[str, Any] = None):
        self.judge = judge or SimulatedJudge()
        self.validation = validation or judge_validation_report()
        verdict = self.validation.get("verdict", {})
        scope = self.validation.get("rubric_scope", "")
        if not scope.startswith("narrow fallback-quality"):
            raise ValueError("judge validation scope is not narrow fallback quality")
        if verdict.get("forbidden_from_core_success_scoring") is not True:
            raise ValueError("judge validation must preserve the core-scoring prohibition")
        if not self.validation.get("validation_set_size"):
            raise ValueError("judge must be validated against human-labelled examples")

    def policy(self) -> Dict[str, Any]:
        report = self.validation
        verdict = report["verdict"]
        return {
            "scope": report["rubric_scope"],
            "validation_set_size": report["validation_set_size"],
            "judge_vs_human_kappa": report["judge_vs_human"]["cohen_kappa"],
            "human_ceiling_kappa": report["human_ceiling_inter_rater"]["cohen_kappa"],
            "known_failure_slices": list(report["failure_slices"]),
            "validated_for_standalone_use": verdict["validated_for_standalone_use"],
            "forbidden_from_core_success_scoring": True,
            "mode": "pointwise_only",
            "judge_contributes_to_core_success": False,
        }

    def inspect(self, record: Dict[str, Any]) -> Dict[str, Any]:
        p = record.get("provenance", {})
        missing = [field for field in PROVENANCE_FIELDS if field not in p]
        reasons: List[str] = []
        if missing:
            reasons.append("provenance_incomplete")
        elif not provenance_consistent(record):
            reasons.append("provenance_inconsistent")

        routed_as_fallback = (
            p.get("is_fallback") is True
            or p.get("served_by") in ("secondary", "degraded")
        )
        judge_label = "not_run"
        if routed_as_fallback and record.get("answered") and record.get("candidate") is not None:
            judge_label = self.judge.accept(record["reference"], record["candidate"])
            if judge_label == "reject":
                reasons.append("narrow_judge_reject")
        if p.get("is_degraded") is True:
            reasons.append("route_declared_degraded")

        return {
            "request_index": record.get("request_index"),
            "seed": record.get("seed"),
            "alert": bool(reasons),
            "reasons": reasons,
            "judge_label": judge_label,
            "core_oracle_untouched": True,
        }


def score_detector(
    records: List[Dict[str, Any]],
    integration: NarrowJudgeIntegration = None,
) -> Dict[str, Any]:
    """Score only the fallback slice against strict human-rubric ground truth."""
    adapter = integration or NarrowJudgeIntegration()
    fallback = [record for record in records if record["route"] == "fallback"]
    inspected = [adapter.inspect(record) for record in fallback]

    tp = fp = fn = tn = 0
    false_negatives: List[Dict[str, Any]] = []
    judge_accepts = 0
    for record, result in zip(fallback, inspected):
        truth = not record["strict_quality_acceptable"]
        predicted = result["alert"]
        judge_accepts += int(result["judge_label"] == "accept")
        if predicted and truth:
            tp += 1
        elif predicted and not truth:
            fp += 1
        elif not predicted and truth:
            fn += 1
            false_negatives.append({
                "request_index": record["request_index"],
                "seed": record["seed"],
                "variant": record["fallback_variant"],
                "judge_label": result["judge_label"],
                "strict_quality_score": record["strict_quality_score"],
            })
        else:
            tn += 1

    by_variant: Dict[str, Dict[str, int]] = {}
    for record, result in zip(fallback, inspected):
        variant = record["fallback_variant"]
        cell = by_variant.setdefault(variant, {"n": 0, "bad": 0, "alerts": 0, "misses": 0})
        truth = not record["strict_quality_acceptable"]
        cell["n"] += 1
        cell["bad"] += int(truth)
        cell["alerts"] += int(result["alert"])
        cell["misses"] += int(truth and not result["alert"])

    return {
        "population": "fallback answers only",
        "n": len(fallback),
        "ground_truth": "Day-16 strict human rubric (not the judge)",
        "confusion": {"tp": tp, "fp": fp, "fn": fn, "tn": tn},
        "recall": rate_block(tp, tp + fn),
        "precision": rate_block(tp, tp + fp),
        "judge_acceptance": rate_block(judge_accepts, len(fallback)),
        "by_variant": by_variant,
        "false_negatives": false_negatives,
        "all_false_negatives_surfaced": len(false_negatives) == fn,
        "policy": adapter.policy(),
    }
