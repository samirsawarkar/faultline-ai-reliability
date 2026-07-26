"""The trusted human-labelled validation set (blinded) + a second human rater.

These labels are the GROUND TRUTH the judge is validated against. They are
hand-authored by applying the Day-16 rubric strictly to each (reference, candidate)
pair, WITHOUT reference to any judge output — the judge never sees them. A second
rater (`rater_b_label`) is included so inter-rater agreement (human vs human) can be
measured as the reliability ceiling the judge is compared to.

Four slices of six items each (24 total):
  clear_accept      candidate == reference                          -> accept
  clear_reject      wrong value + broken tokens                     -> reject
  borderline_tokens correct value, tokens reordered/shifted (wrong) -> reject
  borderline_extra  correct value+tokens, plus a fabricated field   -> reject
"""
from __future__ import annotations

from typing import Any, Dict, List

_N_PER_SLICE = 6


def _reference(i: int) -> Dict[str, Any]:
    return {"value": (i + 1) * 10, "tokens": [i, i + 1, i + 2, i + 3]}


def items() -> List[Dict[str, Any]]:
    """The 24-item validation set. `human_label` is the trusted label; the judge
    receives only `reference` and `candidate`."""
    out: List[Dict[str, Any]] = []
    for i in range(_N_PER_SLICE):
        ref = _reference(i)

        # clear accept: exact match
        out.append({"id": f"va-ca-{i}", "slice": "clear_accept", "request_index": i,
                    "reference": ref, "candidate": dict(ref),
                    "human_label": "accept", "rater_b_label": "accept"})

        # clear reject: wrong value (not a round ten) + broken tokens
        out.append({"id": f"va-cr-{i}", "slice": "clear_reject", "request_index": i,
                    "reference": ref,
                    "candidate": {"value": ref["value"] + 37, "tokens": [9, 9, 9, 9]},
                    "human_label": "reject", "rater_b_label": "reject"})

        # borderline tokens: correct value, tokens shifted (wrong order/values)
        out.append({"id": f"va-bt-{i}", "slice": "borderline_tokens", "request_index": i,
                    "reference": ref,
                    "candidate": {"value": ref["value"], "tokens": [t + 2 for t in ref["tokens"]]},
                    "human_label": "reject", "rater_b_label": "reject"})

        # borderline extra: correct value+tokens, plus a fabricated field.
        # Rater B tolerates a harmless "note" on 2 of the 6 -> human/human disagreement.
        rater_b = "accept" if i in (0, 3) else "reject"
        out.append({"id": f"va-be-{i}", "slice": "borderline_extra", "request_index": i,
                    "reference": ref,
                    "candidate": {"value": ref["value"], "tokens": list(ref["tokens"]),
                                  "note": "synthesized"},
                    "human_label": "reject", "rater_b_label": rater_b})
    return out


def pairs() -> List[Dict[str, Any]]:
    """Pairwise comparisons for the positional-bias test. In every pair `cand_a`
    is the TRULY better fallback (higher rubric quality). A fair judge picks `a`
    regardless of presentation order.

    - clear pairs: accept vs clear-reject (a cheap judge can tell them apart).
    - close pairs: accept vs borderline-tokens (a value-focused judge sees a tie,
      so its choice is decided by position — the bias we want to detect).
    """
    out: List[Dict[str, Any]] = []
    for i in range(_N_PER_SLICE):
        ref = _reference(i)
        accept = dict(ref)
        reject = {"value": ref["value"] + 37, "tokens": [9, 9, 9, 9]}
        bt = {"value": ref["value"], "tokens": [t + 2 for t in ref["tokens"]]}
        out.append({"pair_id": f"pr-clear-{i}", "kind": "clear", "request_index": i,
                    "reference": ref, "cand_a": accept, "cand_b": reject, "true_better": "a"})
        out.append({"pair_id": f"pr-close-{i}", "kind": "close", "request_index": i,
                    "reference": ref, "cand_a": accept, "cand_b": bt, "true_better": "a"})
    return out
