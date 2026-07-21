"""A bounded multi-step task — the substrate for F5 (context) and F6 (loop) faults.

The task runs a short deterministic loop: at step k it produces a value and
appends it to a running CONTEXT, and after M steps it completes and reports a
FINAL that is the sum of the context. Two things can now go wrong in ways the
earlier per-call faults could not express:

  F5 — context corruption: a plausible WRONG value enters the context and flows
       into the final. The output stays well-formed; catching it needs reasoning
       about the *values*, not their shape (semantic detection).
  F6 — loop faults: the loop repeats a step, or never terminates and burns its
       STEP BUDGET. Catching it needs only counting/equality (deterministic).

Everything is a pure function of (kind, severity); there is no wall clock and no
RNG, so a run is byte-reproducible.
"""
from __future__ import annotations

import copy
from dataclasses import dataclass
from typing import List, Optional

M_STEPS = 4              # a clean task completes in exactly this many steps
STEP_BUDGET = 6          # the loop aborts if it exceeds this many steps


def step_value(k: int) -> int:
    """The correct value produced at step k (a round ten)."""
    return (k + 1) * 10


EXPECTED_CONTEXT: List[int] = [step_value(k) for k in range(M_STEPS)]  # [10,20,30,40]
EXPECTED_FINAL = sum(EXPECTED_CONTEXT)                                 # 100
_MULTIPLES = list(range(10, 210, 10))


@dataclass(frozen=True)
class RunResult:
    context: List[int]           # per-step values accumulated
    final: Optional[int]         # reported result (sum of context when complete)
    steps_used: int
    completed: bool
    step_signatures: List[str]   # identity of each executed step, in order

    def to_dict(self) -> dict:
        return {"context": list(self.context), "final": self.final,
                "steps_used": self.steps_used, "completed": self.completed,
                "step_signatures": list(self.step_signatures)}


def _clean() -> RunResult:
    return RunResult(
        context=list(EXPECTED_CONTEXT), final=EXPECTED_FINAL, steps_used=M_STEPS,
        completed=True, step_signatures=[f"step:{k}" for k in range(M_STEPS)])


def _drifted_value(base: int, severity: int) -> int:
    """A different, plausible round ten (coherent wrong value)."""
    others = [m for m in _MULTIPLES if m != base]
    return others[(base // 10 + severity) % len(others)]


def run_task(kind: Optional[str], severity: int = 2) -> RunResult:
    """Execute the task under an optional F5/F6 fault kind. `None` = clean."""
    if kind is None:
        return _clean()

    if kind == "context_drift":
        # Corrupt one context value to a plausible different value AND keep the
        # final consistent (final == sum(context)). Internally coherent, yet
        # wrong: only the oracle knows step 1 should have been 20.
        ctx = list(EXPECTED_CONTEXT)
        ctx[1] = _drifted_value(ctx[1], severity)
        return RunResult(context=ctx, final=sum(ctx), steps_used=M_STEPS,
                         completed=True,
                         step_signatures=[f"step:{k}" for k in range(M_STEPS)])

    if kind == "context_inconsistent":
        # Corrupt one context value but leave the final unchanged -> the internal
        # consistency invariant (final == sum(context)) now breaks.
        ctx = list(EXPECTED_CONTEXT)
        ctx[1] = _drifted_value(ctx[1], severity)
        return RunResult(context=ctx, final=EXPECTED_FINAL, steps_used=M_STEPS,
                         completed=True,
                         step_signatures=[f"step:{k}" for k in range(M_STEPS)])

    if kind == "repetition":
        # The loop gets stuck repeating one step and never progresses, burning
        # the whole budget. Same step signature appears many times.
        sigs = ["step:0"] + ["step:1"] * (STEP_BUDGET - 1)
        return RunResult(context=[step_value(0)], final=None,
                         steps_used=STEP_BUDGET, completed=False,
                         step_signatures=sigs)

    if kind == "budget_exhaustion":
        # The loop makes (distinct) progress too slowly and hits the step budget
        # without ever completing. No repeated step signature.
        sigs = [f"step:{k}" for k in range(STEP_BUDGET)]
        return RunResult(context=[step_value(k) for k in range(STEP_BUDGET)],
                         final=None, steps_used=STEP_BUDGET, completed=False,
                         step_signatures=sigs)

    raise ValueError(f"unknown task fault kind {kind!r}")


def is_correct(rr: RunResult) -> bool:
    """The oracle: a run is correct iff it completed in M steps with the exact
    expected context and final, and never repeated a step."""
    return (rr.completed and rr.steps_used == M_STEPS
            and rr.context == EXPECTED_CONTEXT and rr.final == EXPECTED_FINAL
            and len(set(rr.step_signatures)) == len(rr.step_signatures))
