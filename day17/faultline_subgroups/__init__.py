"""FAULTLINE Day 17: subgroup analysis + measurement gate.

Slice the evaluation by fault, severity, hop count and outcome; apply minimum-sample
and multiple-comparison discipline; search for reversals (Simpson's paradox) and
unstable conclusions; and gate the headline so no contradicting subgroup is ignored.

Public surface:
    gate:      MIN_SAMPLES, subgroup_rate, one_proportion_p, holm_bonferroni, apply_gate
    subgroups: slice_by, overall_rate
    reversal:  detect_ordering_reversal, headline_contradictions, verify_reversal_detector,
               simpson_example_rows
    analysis:  detection_rows, detection_analysis, hop_analysis
    report:    build_report, contradiction_keys
    audit:     run_audit
"""
from . import analysis, audit, gate, report, reversal, subgroups, tables
from .analysis import detection_analysis, detection_rows, hop_analysis
from .audit import run_audit
from .tables import render_findings
from .gate import (
    MIN_SAMPLES,
    apply_gate,
    holm_bonferroni,
    one_proportion_p,
    subgroup_rate,
)
from .report import build_report, contradiction_keys
from .reversal import (
    detect_ordering_reversal,
    headline_contradictions,
    simpson_example_rows,
    verify_reversal_detector,
)
from .subgroups import overall_rate, slice_by

__all__ = [
    "MIN_SAMPLES", "subgroup_rate", "one_proportion_p", "holm_bonferroni", "apply_gate",
    "slice_by", "overall_rate",
    "detect_ordering_reversal", "headline_contradictions", "verify_reversal_detector",
    "simpson_example_rows",
    "detection_rows", "detection_analysis", "hop_analysis",
    "build_report", "contradiction_keys", "run_audit", "render_findings",
    "gate", "subgroups", "reversal", "analysis", "report", "audit", "tables",
]
