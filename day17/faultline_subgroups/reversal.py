"""Reversal / Simpson's-paradox detection.

Two things to catch, both instances of "a subgroup contradicts the headline":

  * ORDERING REVERSAL (Simpson) — an aggregate says group A beats group B, yet
    within one or more slices B beats A. This happens when the slice mix differs
    between groups (a confound). `detect_ordering_reversal` finds every such slice.
  * HEADLINE CONTRADICTION — a subgroup whose interval excludes the headline value
    (from gate.py). Collected and classified by significance + sample adequacy so
    none can be quietly dropped.

A known Simpson example is included so the detector can be verified against a
paradox we already know is there (the Day-14 verify-against-a-known-answer stance).
"""
from __future__ import annotations

from typing import Any, Dict, List, Sequence

from .subgroups import overall_rate


def detect_ordering_reversal(rows: List[Dict[str, Any]], group_key: str,
                             group_a: str, group_b: str, slice_key: str,
                             outcome: str = "correct") -> Dict[str, Any]:
    """Aggregate A-vs-B ordering vs the per-slice ordering. Flags slices where the
    within-slice ordering reverses the aggregate one."""
    a_rows = [r for r in rows if r[group_key] == group_a]
    b_rows = [r for r in rows if r[group_key] == group_b]
    agg_a, agg_b = overall_rate(a_rows, outcome), overall_rate(b_rows, outcome)
    agg_order = "a>=b" if agg_a >= agg_b else "b>a"

    reversals: List[Dict[str, Any]] = []
    slices = sorted({r[slice_key] for r in rows}, key=str)
    per_slice = []
    for sv in slices:
        a = [r for r in a_rows if r[slice_key] == sv]
        b = [r for r in b_rows if r[slice_key] == sv]
        if not a or not b:
            continue                       # ordering undefined if a group is absent
        ra, rb = overall_rate(a, outcome), overall_rate(b, outcome)
        order = "a>=b" if ra >= rb else "b>a"
        entry = {"slice": {slice_key: sv}, "a_rate": ra, "b_rate": rb,
                 "a_n": len(a), "b_n": len(b), "order": order,
                 "reverses_aggregate": order != agg_order}
        per_slice.append(entry)
        if entry["reverses_aggregate"]:
            reversals.append(entry)

    return {
        "group_a": group_a, "group_b": group_b, "slice_key": slice_key,
        "aggregate": {"a_rate": agg_a, "b_rate": agg_b, "a_n": len(a_rows),
                      "b_n": len(b_rows), "order": agg_order},
        "per_slice": per_slice,
        "reversal_slices": reversals,
        "has_reversal": bool(reversals),
    }


def headline_contradictions(gated_subgroups: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Every subgroup whose 95% interval EXCLUDES the headline value — the honest
    definition of "this subgroup's data is inconsistent with the headline." Mere
    point-estimate variation (rate != headline) is NOT a contradiction; only an
    interval that excludes the headline counts. Each is surfaced with its
    significance + sample-adequacy status, so none is dropped."""
    out = []
    for s in gated_subgroups:
        if s.get("ci_excludes_headline"):
            out.append({
                "dims": s.get("dims"), "rate": s["rate"], "n": s["n"],
                "wilson_ci95": s["wilson_ci95"], "headline_rate": s["headline_rate"],
                "ci_excludes_headline": s.get("ci_excludes_headline", False),
                "significant_holm": s.get("significant_holm", False),
                "reportable": s["reportable"],
                "status": ("significant" if s.get("significant_holm")
                           else "not significant (underpowered)" if not s["reportable"]
                           else "not significant"),
            })
    return out


# --- a known Simpson's paradox, for verifying the detector -----------------
# Classic kidney-stone-style shape: treatment A beats B overall, but B beats A in
# BOTH severity subgroups, because A took the easy cases and B the hard ones.
def simpson_example_rows() -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []

    def add(group, sev, n, correct):
        for i in range(n):
            rows.append({"group": group, "severity": sev, "correct": i < correct})

    # small stones (easy): A 81/87, B 234/270  -> B better within slice (0.867 > 0.931? )
    add("A", "small", 87, 81)     # 0.931
    add("B", "small", 270, 234)   # 0.867
    # large stones (hard): A 192/263, B 55/80  -> B better within slice
    add("A", "large", 263, 192)   # 0.730
    add("B", "large", 80, 55)     # 0.688
    return rows
    # aggregate: A 273/350 = 0.780 ; B 289/350 = 0.826 -> B better overall,
    # yet A is better in BOTH slices -> Simpson's reversal.


def verify_reversal_detector() -> Dict[str, Any]:
    rows = simpson_example_rows()
    res = detect_ordering_reversal(rows, "group", "A", "B", "severity")
    # aggregate: B >= A is false in our labelling? A=0.780, B=0.826 -> agg order 'b>a'
    # within each slice A > B -> 'a>=b' -> reverses aggregate in BOTH slices.
    return {"aggregate_order": res["aggregate"]["order"],
            "reversal_slices": [r["slice"] for r in res["reversal_slices"]],
            "detector_recovers_known_paradox": len(res["reversal_slices"]) == 2}
