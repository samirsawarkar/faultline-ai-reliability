"""Deterministic detectors — turn an observable into a signal, never truth.

A detector sees ONLY what the system under test sees: the returned output (for
the schema detector) or the measured duration (for the duration detector). It
never reads the ground-truth log. Its output is a *signal* the recovery layer
will act on in later missions:

  SchemaDetector  -> repair_signal   (the output is malformed; attempt repair)
  DurationDetector -> timeout_signal  (the call breached its latency budget)

Both are pure functions, so a run's signals are byte-reproducible. Scoring these
signals against the injection truth happens in score.py — kept separate on
purpose, so a detector can never be graded on anything it emitted.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, List

from .latency import DEFAULT_BUDGET, breaches_budget
from .schema import validate_output


@dataclass(frozen=True)
class SchemaSignal:
    seq: int
    valid: bool
    violation_codes: List[str] = field(default_factory=list)
    repair_signal: bool = False

    def to_dict(self) -> dict:
        return {"seq": self.seq, "valid": self.valid,
                "violation_codes": list(self.violation_codes),
                "repair_signal": self.repair_signal}


@dataclass(frozen=True)
class DurationSignal:
    seq: int
    duration: int
    budget: int
    timeout_signal: bool

    def to_dict(self) -> dict:
        return {"seq": self.seq, "duration": self.duration,
                "budget": self.budget, "timeout_signal": self.timeout_signal}


def schema_detect(seq: int, output: Any) -> SchemaSignal:
    """Flag a structurally malformed output and raise a repair signal for it."""
    violations = validate_output(output)
    codes = [v.code for v in violations]
    return SchemaSignal(seq=seq, valid=not violations,
                        violation_codes=codes, repair_signal=bool(violations))


def duration_detect(seq: int, dur: int, budget: int = DEFAULT_BUDGET) -> DurationSignal:
    """Flag a call whose duration breached the latency budget."""
    return DurationSignal(seq=seq, duration=dur, budget=budget,
                          timeout_signal=breaches_budget(dur, budget))
