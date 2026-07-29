"""FAULTLINE Day 21: Q4 — silent fallback degradation.

Measure availability and answer quality on the same seeded requests, then score a
provenance-aware degradation detector that uses Day 16's narrow semantic judge only
inside its documented scope. The judge is advisory and never contributes to the
core oracle or strict-quality ground truth.
"""
from .detector import NarrowJudgeIntegration, score_detector
from .findings import render_findings
from .metrics import provenance_consistent, rate_block, summarize
from .report import build_report
from .scenario import (
    N,
    SEED_BASE,
    build_paired_records,
    fallback_enabled_record,
    primary_only_record,
)

__all__ = [
    "N",
    "SEED_BASE",
    "build_paired_records",
    "primary_only_record",
    "fallback_enabled_record",
    "rate_block",
    "provenance_consistent",
    "summarize",
    "NarrowJudgeIntegration",
    "score_detector",
    "build_report",
    "render_findings",
]
