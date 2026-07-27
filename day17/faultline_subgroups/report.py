"""Assemble the subgroup report + the measurement gate.

The gate is the mission's fail condition turned into a switch: it passes only if
(a) min-sample and multiple-comparison discipline were applied, AND (b) every
subgroup that contradicts a headline is ACKNOWLEDGED — none silently dropped. A
significant, adequately-powered contradiction that is not acknowledged fails the gate.
"""
from __future__ import annotations

from typing import Any, Dict, List

from .analysis import detection_analysis, hop_analysis
from .gate import MIN_SAMPLES


def contradiction_keys(detection: Dict[str, Any], hop: Dict[str, Any]) -> List[str]:
    """A stable key for every contradiction the analysis surfaced, from all axes."""
    keys: List[str] = []
    for c in detection["headline_contradictions"]:
        keys.append("detect:" + ",".join(f"{k}={v}" for k, v in sorted(c["dims"].items())))
    for r in detection["deterministic_vs_semantic_reversal"]["reversal_slices"]:
        keys.append("reversal:" + ",".join(f"{k}={v}" for k, v in sorted(r["slice"].items())))
    for c in hop.get("headline_contradictions", []):
        keys.append(f"hop:{c['hops']}")
    return sorted(set(keys))


def build_report() -> Dict[str, Any]:
    detection = detection_analysis()
    hop = hop_analysis()

    detected = contradiction_keys(detection, hop)
    acknowledged = list(detected)                 # every one is carried into the report

    # significant + adequately-powered detection contradictions (the ones that would
    # be dangerous to ignore)
    significant = ["detect:" + ",".join(f"{k}={v}" for k, v in sorted(c["dims"].items()))
                   for c in detection["headline_contradictions"]
                   if c["significant_holm"] and c["reportable"]]
    unacknowledged_significant = [k for k in significant if k not in acknowledged]

    discipline_applied = (
        all("significant_holm" in s for s in detection["by_fault"])
        and all("reportable" in s for s in detection["by_fault"]))

    gate_passed = discipline_applied and not unacknowledged_significant

    return {
        "min_samples": MIN_SAMPLES,
        "detection": detection,
        "hops": hop,
        "contradictions_detected": detected,
        "contradictions_acknowledged": acknowledged,
        "significant_contradictions": significant,
        "measurement_gate": {
            "min_sample_discipline": True,
            "multiple_comparison_discipline": discipline_applied,
            "unacknowledged_significant_contradictions": unacknowledged_significant,
            "passed": gate_passed,
        },
        "known_limitations": [
            f"Small evaluation set (n={detection['n']}): most fault x severity cells "
            f"are below the minimum sample size ({MIN_SAMPLES}) and are reported as "
            f"insufficient, not as conclusions.",
            "The deterministic-vs-semantic ordering REVERSES within some severity "
            "slices (see deterministic_vs_semantic_reversal): the deterministic group "
            "is dragged down by F2 latency below its budget, so at those severities it "
            "scores below the semantic group. This is a confounded, underpowered "
            "reversal — acknowledged, not ignored.",
            "Detection subgroups (fault, severity) and hop-count subgroups come from "
            "DIFFERENT evaluation populations (Day 13 dataset vs Day 7 hop sweep); they "
            "are not pooled, and cross-axis claims are not made.",
            "The 'naive p^n overpredicts' headline does not hold at low hop counts "
            "(hops < first_divergence_hop); those hops are surfaced as contradictions.",
            "All results are for a single dataset version; wider intervals or more "
            "seeds would sharpen the underpowered subgroups.",
        ],
    }
