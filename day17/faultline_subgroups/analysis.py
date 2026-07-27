"""Apply the subgroup machinery to the project's real evaluation data.

Detection results come from Day 15 (per-sample outcomes: fault, severity, outcome);
hop-count results come from Day 7's committed hop curve. Each axis is sliced,
gated, and searched for reversals against its headline claim.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, List

_ROOT = Path(__file__).resolve().parents[2]
for rel in ("day13", "day15"):
    p = _ROOT / rel
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from faultline_q2 import run_outcomes  # noqa: E402 (Day 15)
from faultline_q2.q2 import DETERMINISTIC_GROUP  # noqa: E402

from .gate import apply_gate
from .reversal import detect_ordering_reversal, headline_contradictions
from .subgroups import overall_rate, slice_by

_DAY07_Q1 = _ROOT / "day07" / "evidence" / "q1_results.json"


def detection_rows() -> List[Dict[str, Any]]:
    """One row per evaluation sample, with detection correctness + subgroup keys."""
    rows: List[Dict[str, Any]] = []
    for o in run_outcomes(split="all"):
        rows.append({
            "fault": o["modality"],
            "severity": o["severity"],
            "outcome": o["outcome"],
            "correct": o["outcome"] in ("TP", "TN"),
            "group": "deterministic" if o["modality"] in DETERMINISTIC_GROUP else "semantic",
        })
    return rows


def detection_analysis() -> Dict[str, Any]:
    rows = detection_rows()
    headline = overall_rate(rows)                # overall detection accuracy

    by_fault = apply_gate(slice_by(rows, ["fault"]), headline)
    by_severity = apply_gate(slice_by(rows, ["severity"]), headline)
    by_fault_sev = apply_gate(slice_by(rows, ["fault", "severity"]), headline)
    by_outcome = slice_by(rows, ["outcome"])     # distribution of outcome types

    reversal = detect_ordering_reversal(rows, "group", "deterministic", "semantic", "severity")

    contradictions = (headline_contradictions(by_fault)
                      + headline_contradictions(by_severity)
                      + headline_contradictions(by_fault_sev))
    return {
        "headline_claim": "overall detection accuracy",
        "headline_rate": headline,
        "n": len(rows),
        "by_fault": by_fault,
        "by_severity": by_severity,
        "by_fault_severity": by_fault_sev,
        "outcome_distribution": by_outcome,
        "deterministic_vs_semantic_reversal": reversal,
        "headline_contradictions": contradictions,
    }


def hop_analysis() -> Dict[str, Any]:
    """Slice Day 7's reliability-vs-hops curve; audit the 'naive p^n overpredicts'
    headline for the hops where it does NOT yet hold."""
    if not _DAY07_Q1.exists():
        return {"available": False}
    curve = json.loads(_DAY07_Q1.read_text())["curve"]
    per_hop = []
    contradictions = []
    for pt in curve:
        supports = bool(pt["naive_outside_measured_ci"])
        entry = {"hops": pt["hops"], "measured": pt["measured"],
                 "measured_ci95": pt["measured_ci95"], "naive": pt["naive"],
                 "naive_outside_measured_ci": supports}
        per_hop.append(entry)
        if not supports:
            contradictions.append({"hops": pt["hops"], "measured": pt["measured"],
                                   "naive": pt["naive"],
                                   "why": "naive prediction lies inside the measured "
                                          "CI here — the 'naive overpredicts' headline "
                                          "does NOT hold at this hop count"})
    return {
        "available": True,
        "headline_claim": "naive p^n overpredicts end-to-end reliability",
        "per_hop": per_hop,
        "first_divergence_hop": next((p["hops"] for p in per_hop
                                      if p["naive_outside_measured_ci"]), None),
        "headline_contradictions": contradictions,
    }
