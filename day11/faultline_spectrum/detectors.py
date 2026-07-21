"""Detectors for F5 (semantic) and F6 (deterministic) — the separation, in code.

The three detectors are chosen to make the deterministic-vs-semantic split
concrete and defensible:

  repetition_detect  DETERMINISTIC — equality of step signatures. No notion of
                     "correct" is needed; a repeated step is a repeated step.
  budget_detect      DETERMINISTIC — a count vs a budget. Pure arithmetic on the
                     step counter and the completion flag.
  context_integrity  SEMANTIC — reasons about the MEANING of the values
                     (final == sum(context)). It needs a domain rule, not just a
                     shape or a count. It catches an *incoherent* corruption but
                     is blind to a *coherent* one (context_drift), which only the
                     oracle can catch.

Definition used throughout (see LEARN): a detector is DETERMINISTIC if its verdict
is a function of structure/counts/equality/explicit flags with no model of
correctness; it is SEMANTIC if it needs a correctness or meaning model (an
invariant over values, or the oracle).
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass

from .task import STEP_BUDGET, RunResult


@dataclass(frozen=True)
class Signal:
    fired: bool
    reason: str = ""

    def to_dict(self) -> dict:
        return {"fired": self.fired, "reason": self.reason}


def repetition_detect(rr: RunResult) -> Signal:
    """Deterministic: any step signature that occurs more than once."""
    counts = Counter(rr.step_signatures)
    repeated = [s for s, c in counts.items() if c > 1]
    return Signal(bool(repeated), f"repeated {repeated}" if repeated else "")


def budget_detect(rr: RunResult, budget: int = STEP_BUDGET) -> Signal:
    """Deterministic: the loop hit its step budget without completing."""
    fired = rr.steps_used >= budget and not rr.completed
    return Signal(fired, f"steps_used={rr.steps_used} budget={budget} not completed"
                  if fired else "")


def loop_detect(rr: RunResult, budget: int = STEP_BUDGET) -> Signal:
    """The F6 detector: repetition OR budget exhaustion."""
    rep = repetition_detect(rr)
    bud = budget_detect(rr, budget)
    if rep.fired or bud.fired:
        return Signal(True, "; ".join(s.reason for s in (rep, bud) if s.fired))
    return Signal(False)


def context_integrity_detect(rr: RunResult) -> Signal:
    """Semantic (consistency invariant): final must equal the sum of context.

    Catches an incoherent context corruption; blind to a coherent one where the
    final was recomputed to match the corrupted context."""
    if rr.final is None:
        return Signal(False, "no final to check")
    consistent = rr.final == sum(rr.context)
    return Signal(not consistent,
                  f"final {rr.final} != sum(context) {sum(rr.context)}"
                  if not consistent else "")
