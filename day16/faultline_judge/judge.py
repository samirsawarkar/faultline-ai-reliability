"""The judge adapter — a real LLM judge plugs in here; a simulated one stands in.

`Judge` is the interface the validation harness talks to. Two implementations:

  SimulatedJudge   deterministic, dependency-free, with a KNOWN blind spot
                   (token-order drift) and a configurable, KNOWN positional bias.
                   It exists so the validation harness can be built and verified
                   reproducibly — and so the bias detector can be checked against a
                   judge whose bias we already know (the Day-14 verification stance).
  RealJudgeAdapter the boundary for an actual LLM judge. It refuses to run without
                   a configured client, and — per the mission — a real judge must be
                   validated against these human labels before any use.

No network, no API key, nothing non-reproducible is imported here.
"""
from __future__ import annotations

import json
from typing import Any, Dict, Optional

from .rubric import RUBRIC_TEXT, judge_estimate, rubric_criteria


def _canon(d: Dict[str, Any]) -> str:
    return json.dumps(d, sort_keys=True, ensure_ascii=True)


class SimulatedJudge:
    """A deterministic stand-in for an LLM judge with known, documented flaws."""
    name = "simulated"

    def __init__(self, positional: bool = True, first_preference: float = 1.0):
        # positional=True + first_preference=1.0 models a judge that, when it cannot
        # tell two candidates apart, always prefers whichever is presented FIRST.
        self.positional = positional
        self.first_preference = first_preference

    def accept(self, reference: Dict[str, Any], candidate: Dict[str, Any]) -> str:
        """Pointwise verdict. Accept iff the judge's estimate meets every criterion
        it can check (value, token length, no fabrication) — note it does NOT verify
        exact token order, its known blind spot."""
        return "accept" if judge_estimate(reference, candidate) == len(rubric_criteria()) else "reject"

    def compare_positions(self, reference: Dict[str, Any], first: Dict[str, Any],
                          second: Dict[str, Any]) -> str:
        """Pairwise verdict returning which POSITION wins ('first'/'second').
        Presenting the same two candidates in both orders reveals positional bias."""
        ef, es = judge_estimate(reference, first), judge_estimate(reference, second)
        if ef != es:
            return "first" if ef > es else "second"
        # a genuine tie the judge cannot resolve on quality:
        if self.positional:
            # positional bias: prefer the first-presented (worst case at pref=1.0)
            if self.first_preference >= 1.0:
                return "first"
            # a partial bias, still order-DEPENDENT (seeded by ordered content)
            import random
            r = random.Random(hash(_canon(first) + "|" + _canon(second)) & 0x7FFFFFFF)
            return "first" if r.random() < self.first_preference else "second"
        # fair tie-break: decided by content, so it is order-INVARIANT
        cf, cs = _canon(first), _canon(second)
        return "first" if min(cf, cs) == cf else "second"


class RealJudgeAdapter:
    """Boundary for a real LLM judge. Not callable without a configured client, and
    forbidden from use until validated against the human labels (see JUDGE_CARD.md)."""
    name = "real"

    def __init__(self, client: Optional[Any] = None):
        self.client = client

    def _prompt(self, reference: Dict[str, Any], candidate: Dict[str, Any]) -> str:
        return (RUBRIC_TEXT + "\n\nReference:\n" + _canon(reference)
                + "\n\nCandidate:\n" + _canon(candidate)
                + "\n\nAnswer strictly 'accept' or 'reject'.")

    def accept(self, reference: Dict[str, Any], candidate: Dict[str, Any]) -> str:
        if self.client is None:
            raise NotImplementedError(
                "RealJudgeAdapter needs a configured LLM client AND a passing "
                "validation run (agreement + bias) against the human labels before "
                "use. See JUDGE_CARD.md; the judge is forbidden from core scoring.")
        raise NotImplementedError(
            "Wire self.client to an LLM here, send _prompt(), parse accept/reject — "
            "then re-run the Day-16 validation harness before trusting it.")
