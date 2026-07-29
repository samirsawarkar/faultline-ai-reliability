"""The shared paired population and baseline outcomes for the recovery matrix."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple

FAULTS: Tuple[str, ...] = ("F1", "F2", "F3", "F4", "F5", "F6")
N_PER_FAULT = 24
SEED_BASE = 2026080100


@dataclass(frozen=True)
class Trial:
    fault: str
    request_index: int
    seed: int
    injected: bool
    variant: str
    fault_rank: int

    def to_dict(self) -> Dict[str, object]:
        return {
            "fault": self.fault,
            "request_index": self.request_index,
            "seed": self.seed,
            "injected": self.injected,
            "variant": self.variant,
            "fault_rank": self.fault_rank,
        }


@dataclass(frozen=True)
class Outcome:
    status: str
    available: bool
    correct: bool
    contained: bool
    cost: int
    latency: int
    harms: Tuple[str, ...] = ()

    def to_dict(self) -> Dict[str, object]:
        return {
            "status": self.status,
            "available": self.available,
            "correct": self.correct,
            "contained": self.contained,
            "cost": self.cost,
            "latency": self.latency,
            "harms": list(self.harms),
        }


def build_trials(fault: str, n: int = N_PER_FAULT) -> List[Trial]:
    """18 faulted requests plus six clean controls, all deterministically stratified."""
    if fault not in FAULTS:
        raise ValueError(f"unknown fault: {fault}")
    if n != N_PER_FAULT:
        raise ValueError(f"the committed paired design requires n={N_PER_FAULT}")

    trials: List[Trial] = []
    fault_rank = 0
    control_rank = 0
    for index in range(n):
        injected = index % 4 != 0
        if injected:
            if fault in ("F1", "F2", "F6"):
                variant = (
                    "persistent" if fault_rank % 3 == 2
                    else f"transient_{1 + (fault_rank % 2)}"
                )
            else:
                variant = "injected"
            rank = fault_rank
            fault_rank += 1
        else:
            control_kinds = ("long_legitimate", "legitimate_repeat", "clean")
            variant = control_kinds[control_rank % len(control_kinds)]
            rank = control_rank
            control_rank += 1
        trials.append(
            Trial(
                fault=fault,
                request_index=index,
                seed=SEED_BASE + FAULTS.index(fault) * 100 + index,
                injected=injected,
                variant=variant,
                fault_rank=rank,
            )
        )
    return trials


def clean_plan(trial: Trial) -> List[str]:
    if trial.variant == "long_legitimate":
        return ["plan", "search", "read", "compare", "verify", "cite", "complete"]
    if trial.variant == "legitimate_repeat":
        return ["paginate", "paginate", "paginate", "complete"]
    return ["search", "read", "complete"]


def baseline_outcome(trial: Trial) -> Outcome:
    if not trial.injected:
        plan = clean_plan(trial)
        return Outcome("success", True, True, False, len(plan), len(plan) * 10)
    if trial.fault == "F1":
        return Outcome("malformed_answer", True, False, False, 1, 10)
    if trial.fault == "F2":
        return Outcome("timeout", False, False, False, 1, 50)
    if trial.fault == "F3":
        return Outcome("semantic_wrong_answer", True, False, False, 1, 12)
    if trial.fault == "F4":
        return Outcome("provider_error", False, False, False, 1, 8)
    if trial.fault == "F5":
        return Outcome("context_wrong_answer", True, False, False, 1, 15)
    # The benchmark guard stops the simulated loop at 12 steps; this is not a
    # recovery mechanism and is held constant so an actual test cannot hang.
    return Outcome("loop_exhaustion", False, False, False, 12, 120)
