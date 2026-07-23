"""SpectrumFaultSpec — F5/F6 fault kinds, fired per RUN by the Day-8 triggers.

F5 and F6 are run-level faults (a whole task run is corrupted or fails to
terminate), so the trigger fires on the run index (`seq`). Reuses the Day-8
`triggers.fires` for determinism, exactly like Day 10.

Detection nature is declared here and is the spine of the deterministic-vs-
semantic map: F5 needs semantic evaluation, F6 is deterministic.
"""
from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

_DAY8 = Path(__file__).resolve().parents[2] / "day08"
if str(_DAY8) not in sys.path:
    sys.path.insert(0, str(_DAY8))

from faultline_inject import TRIGGERS  # noqa: E402

# kind -> detection nature. This is the mission's required separation, declared
# and then PROVEN by scoring (deterministic detectors close F6, never F5).
F5_KINDS = ("context_drift", "context_inconsistent")   # semantic
F6_KINDS = ("repetition", "budget_exhaustion")          # deterministic
ALL_KINDS = F5_KINDS + F6_KINDS

DETECTION_NATURE = {
    "context_drift": "semantic",
    "context_inconsistent": "semantic",
    "repetition": "deterministic",
    "budget_exhaustion": "deterministic",
}

F5_LABEL_PREFIX = "F5:"
F6_LABEL_PREFIX = "F6:"


@dataclass(frozen=True)
class SpectrumFaultSpec:
    fault_id: str
    kind: str
    severity: int
    trigger: str
    trigger_value: str
    seed: int
    rate: float = 1.0
    component: str = "*"          # kept for triggers.fires duck-typing

    def validate(self) -> "SpectrumFaultSpec":
        if self.kind not in ALL_KINDS:
            raise ValueError(f"kind {self.kind!r} not in {ALL_KINDS}")
        if not (1 <= self.severity <= 5):
            raise ValueError("severity must be in [1, 5]")
        if self.trigger not in TRIGGERS:
            raise ValueError(f"trigger {self.trigger!r} not in {TRIGGERS}")
        if not (0.0 <= float(self.rate) <= 1.0):
            raise ValueError("rate must be in [0, 1]")
        return self

    @property
    def family(self) -> str:
        return "F5" if self.kind in F5_KINDS else "F6"

    @property
    def label(self) -> str:
        prefix = F5_LABEL_PREFIX if self.family == "F5" else F6_LABEL_PREFIX
        return f"{prefix}{self.kind}"
