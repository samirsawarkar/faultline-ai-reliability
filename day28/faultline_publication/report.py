"""Checkpoint 28 assembly and human-readable claim audit."""
from __future__ import annotations

from typing import Any, Dict, List


def build_checkpoint(audit: Dict[str, Any], figures: Dict[str, Any]) -> Dict[str, Any]:
    checks = {
        "publication_ready_article": audit["checks"]["claim_text_matches_article"],
        "all_substantive_prose_registered": audit["checks"][
            "all_substantive_prose_registered"
        ],
        "q1_to_q5_findings_first": audit["checks"]["findings_first"],
        "four_to_five_source_linked_figures": (
            audit["checks"]["four_to_five_figures"]
            and audit["checks"]["figures_source_linked"]
        ),
        "every_claim_traced_to_committed_result": (
            audit["checks"]["every_finding_has_source"]
            and audit["checks"]["source_results_committed"]
            and audit["checks"]["all_numeric_bindings_resolve"]
            and audit["checks"]["every_numeric_token_bound"]
        ),
        "every_finding_has_honest_limitation": audit["checks"][
            "every_finding_has_limitation"
        ],
        "standalone_captions": audit["checks"]["standalone_captions_present"],
        "figures_regenerated": figures["figure_count"] == audit["figure_count"],
        "fail_condition_not_triggered": audit["passed"],
    }
    return {
        "checkpoint": 28,
        "mission": "Convert Q1-Q5 into one rigorous, findings-first technical argument.",
        "required_evidence": [
            "publication-ready article",
            "4-5 figures",
            "claim-to-result audit",
        ],
        "checks": checks,
        "claim_count": audit["claim_count"],
        "limitation_count": audit["limitation_count"],
        "figure_count": audit["figure_count"],
        "fail_condition_triggered": not audit["passed"],
        "passed": all(checks.values()),
    }


def render_checkpoint(checkpoint: Dict[str, Any]) -> str:
    lines: List[str] = [
        "# CHECKPOINT 28 — findings-first, source-audited publication",
        "",
        f"Mission: {checkpoint['mission']}",
        "",
        "| gate | passed |",
        "|---|---|",
    ]
    for name, passed in checkpoint["checks"].items():
        lines.append(f"| {name} | {passed} |")
    lines += [
        "",
        f"Registered claims: **{checkpoint['claim_count']}**.",
        f"Explicit limitations: **{checkpoint['limitation_count']}**.",
        f"Source-linked figures: **{checkpoint['figure_count']}**.",
        f"Fail condition triggered: **{checkpoint['fail_condition_triggered']}**.",
        f"Checkpoint passed: **{checkpoint['passed']}**.",
        "",
    ]
    return "\n".join(lines)
