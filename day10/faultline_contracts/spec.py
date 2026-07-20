"""ContractFaultSpec — F3/F4 fault kinds, fired by the Day-8 deterministic triggers.

Day 10 introduces fault *kinds* that Day 8's six modes don't express (a
schema-valid-but-wrong value; an explicit provider error envelope), so it defines
its own small spec. It deliberately keeps the Day-8 trigger fields
(`trigger`, `trigger_value`, `seed`, `rate`) so the Day-8 `triggers.fires`
function decides WHEN, unchanged — determinism is inherited, not re-derived.

Kinds split into two families and two truth classes:

  F3 (wrong data)                         schema-valid?   caught by a contract?
    malformed_range   value out of range      NO           schema
    malformed_tokens  wrong-length tokens      NO           schema
    nonmultiple       value not a round ten    YES          semantic invariant
    drift_value       a DIFFERENT round ten    YES          nothing (escapes)
    offbase_tokens    shifted consecutive run  YES          nothing (escapes)

  F4 (provider error)
    provider_error    explicit error envelope   n/a          provider-error detector
"""
from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

_DAY8 = Path(__file__).resolve().parents[2] / "day8"
if str(_DAY8) not in sys.path:
    sys.path.insert(0, str(_DAY8))

from faultline_inject import TRIGGERS  # noqa: E402  (reuse the closed trigger set)

# F3 kinds and whether each produces a SCHEMA-VALID output (the crux of the day).
F3_SCHEMA_VALID = {
    "malformed_range": False,
    "malformed_tokens": False,
    "nonmultiple": True,
    "drift_value": True,
    "offbase_tokens": True,
}
F3_KINDS = tuple(F3_SCHEMA_VALID.keys())
F4_KINDS = ("provider_error",)
ALL_KINDS = F3_KINDS + F4_KINDS

F3_LABEL_PREFIX = "F3:"
F4_LABEL_PREFIX = "F4:"


@dataclass(frozen=True)
class ContractFaultSpec:
    fault_id: str
    component: str
    kind: str
    severity: int
    trigger: str
    trigger_value: str
    seed: int
    rate: float = 1.0

    def validate(self) -> "ContractFaultSpec":
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
        return "F4" if self.kind in F4_KINDS else "F3"

    @property
    def label(self) -> str:
        prefix = F4_LABEL_PREFIX if self.family == "F4" else F3_LABEL_PREFIX
        return f"{prefix}{self.kind}"
