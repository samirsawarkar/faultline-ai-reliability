"""The evaluation audit — independently re-derive contradictions and prove none is
ignored, the reversal detector works, and the discipline was applied.

This is the check that enforces the mission's fail condition: it recomputes the set
of contradicting subgroups from the analysis and asserts the report acknowledged
every one. If a report dropped a contradiction, the audit fails.
"""
from __future__ import annotations

from typing import Any, Dict

from .analysis import detection_analysis, hop_analysis
from .report import build_report, contradiction_keys
from .reversal import verify_reversal_detector


def run_audit(report: Dict[str, Any] = None) -> Dict[str, Any]:
    report = report if report is not None else build_report()

    # 1. independently recompute what SHOULD have been acknowledged
    detected = set(contradiction_keys(detection_analysis(), hop_analysis()))
    acknowledged = set(report.get("contradictions_acknowledged", []))
    ignored = sorted(detected - acknowledged)

    # 2. the reversal detector recovers a known Simpson's paradox
    rev = verify_reversal_detector()

    # 3. the discipline is present in the report
    gate = report["measurement_gate"]
    discipline = gate["min_sample_discipline"] and gate["multiple_comparison_discipline"]

    passed = (not ignored and rev["detector_recovers_known_paradox"] and discipline
              and gate["passed"])
    return {
        "no_contradiction_ignored": not ignored,
        "ignored_contradictions": ignored,
        "reversal_detector_verified": rev["detector_recovers_known_paradox"],
        "reversal_detector_detail": rev,
        "discipline_applied": discipline,
        "gate_passed": gate["passed"],
        "audit_passed": passed,
    }
