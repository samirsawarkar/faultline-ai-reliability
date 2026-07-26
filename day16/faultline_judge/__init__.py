"""FAULTLINE Day 16: validate a narrow LLM judge — and prove its limits.

A judge for the semantic escapes Q2 (Day 15) isolated, validated against trusted
human labels before any use, with agreement + positional-bias + failure-slice
analysis, and a judge card that FORBIDS it from core success scoring.

Public surface:
    rubric:         RUBRIC_TEXT, gold_quality, gold_acceptable, judge_estimate, criteria_report
    validation_set: items, pairs
    judge:          SimulatedJudge, RealJudgeAdapter
    agreement:      raw_agreement, cohen_kappa, confusion, agreement_block,
                    per_slice_agreement, positional_bias, kappa_label
    report:         build_report
    card:           judge_card
"""
from . import agreement, card, judge, report, rubric, validation_set
from .agreement import (
    agreement_block,
    cohen_kappa,
    confusion,
    kappa_label,
    per_slice_agreement,
    positional_bias,
    raw_agreement,
)
from .card import judge_card
from .judge import RealJudgeAdapter, SimulatedJudge
from .report import build_report
from .rubric import (
    RUBRIC_TEXT,
    criteria_report,
    gold_acceptable,
    gold_quality,
    judge_estimate,
)
from .validation_set import items, pairs

__all__ = [
    "RUBRIC_TEXT", "gold_quality", "gold_acceptable", "judge_estimate", "criteria_report",
    "items", "pairs",
    "SimulatedJudge", "RealJudgeAdapter",
    "raw_agreement", "cohen_kappa", "confusion", "agreement_block",
    "per_slice_agreement", "positional_bias", "kappa_label",
    "build_report", "judge_card",
    "rubric", "validation_set", "judge", "agreement", "report", "card",
]
