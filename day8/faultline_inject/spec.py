"""The common fault specification — exactly ten fields, and no eleventh.

A `FaultSpec` is the *single, uniform contract* every injected fault is written
in. Its discipline is the whole point of Build A: one shape for every fault kind,
so that a fault is data (declarable, serializable, diffable, replayable) rather
than a bespoke bit of test code. If two faults cannot be described by the same
ten fields, one of them is out of scope for this injector — that constraint is a
feature, not a limitation.

The ten fields, and why each earns its place:

    1. fault_id      stable identity of THIS fault, so its ground-truth label can
                     be joined back to a trace without guessing.
    2. component     which boundary the fault targets (matches Channel.call's
                     `component`, e.g. "tool.retrieve"). "*" matches any.
    3. mode          WHAT goes wrong — one of MODES. The fault's kind.
    4. severity      HOW MUCH — an integer 1..5. Maps deterministically to a
                     concrete magnitude per mode (see faults.py). Not free-form.
    5. trigger       WHEN it fires — one of TRIGGERS. The deterministic condition.
    6. trigger_value the trigger's parameter (kept as a string so every spec
                     serializes identically regardless of trigger kind).
    7. seed          the fault's own seed; combined with the run seed it makes
                     the `probabilistic` trigger reproducible rather than random.
    8. rate          target fire fraction for the `probabilistic` trigger (0..1);
                     ignored (must be 1.0) for the deterministic triggers.
    9. label         the ground-truth class written at injection time — the
                     INDEPENDENT truth, never derived from the produced output.
   10. spec_version  schema version, so a change of meaning is visible in a diff
                     and cannot silently invalidate old evidence.

Determinism is a gate here too: a spec carries no wall-clock, no object identity,
no free-form payload. Two specs with equal fields are equal, hash the same, and
serialize to the same bytes.
"""
from __future__ import annotations

import dataclasses
from dataclasses import dataclass
from typing import Any, Dict

SPEC_VERSION = "1.0.0"

# WHAT can go wrong. Each mode has a deterministic effect defined in faults.py.
#   error      -> raise a boundary exception instead of returning (hard failure)
#   corrupt    -> mutate a numeric field in the output deterministically
#   truncate   -> drop the tail of a list/str output
#   drop       -> return an empty result where content was expected
#   duplicate  -> repeat the leading element of a list output
#   stall      -> add cost/latency units; OUTPUT CONTENT IS UNCHANGED
MODES = ("error", "corrupt", "truncate", "drop", "duplicate", "stall")

# WHEN it fires. All are deterministic given (spec, run_seed, call_seq, digest).
#   call_index    -> fires on exactly the call whose 0-based seq == trigger_value
#   every_n       -> fires when (seq % N) == 0, N = int(trigger_value)
#   input_match   -> fires when the call's input digest starts with trigger_value
#   probabilistic -> fires when a seeded draw < rate (reproducible, NOT random)
TRIGGERS = ("call_index", "every_n", "input_match", "probabilistic")

SEVERITY_MIN, SEVERITY_MAX = 1, 5


@dataclass(frozen=True)
class FaultSpec:
    """The ten-field fault contract. Frozen so a spec cannot mutate mid-run."""
    fault_id: str
    component: str
    mode: str
    severity: int
    trigger: str
    trigger_value: str
    seed: int
    rate: float
    label: str
    spec_version: str = SPEC_VERSION

    # A guard so the "ten fields, no eleventh" rule is machine-checked, not a hope.
    FIELDS = (
        "fault_id", "component", "mode", "severity", "trigger",
        "trigger_value", "seed", "rate", "label", "spec_version",
    )

    def validate(self) -> "FaultSpec":
        """Structural validation. Raises ValueError on any violation; returns
        self so specs can be validated inline."""
        if len(dataclasses.fields(self)) != 10:
            raise ValueError("a FaultSpec must have exactly 10 fields")
        if not self.fault_id:
            raise ValueError("fault_id is required")
        if not self.component:
            raise ValueError("component is required (use '*' to match any)")
        if self.mode not in MODES:
            raise ValueError(f"mode {self.mode!r} not in {MODES}")
        if not isinstance(self.severity, int) or isinstance(self.severity, bool):
            raise ValueError("severity must be an int")
        if not (SEVERITY_MIN <= self.severity <= SEVERITY_MAX):
            raise ValueError(f"severity must be in [{SEVERITY_MIN}, {SEVERITY_MAX}]")
        if self.trigger not in TRIGGERS:
            raise ValueError(f"trigger {self.trigger!r} not in {TRIGGERS}")
        if not isinstance(self.trigger_value, str):
            raise ValueError("trigger_value must be a str (stable serialization)")
        if not isinstance(self.seed, int) or isinstance(self.seed, bool):
            raise ValueError("seed must be an int")
        if not isinstance(self.rate, (int, float)) or isinstance(self.rate, bool):
            raise ValueError("rate must be a number")
        if not (0.0 <= float(self.rate) <= 1.0):
            raise ValueError("rate must be in [0.0, 1.0]")
        if not self.label:
            raise ValueError("label is required (the independent ground truth)")
        if self.spec_version != SPEC_VERSION:
            raise ValueError(
                f"spec_version {self.spec_version!r} != supported {SPEC_VERSION!r}")

        # Trigger-specific parameter checks — a spec that cannot fire is a bug.
        if self.trigger in ("call_index", "every_n"):
            try:
                v = int(self.trigger_value)
            except ValueError:
                raise ValueError(f"{self.trigger} trigger_value must be an int string")
            if self.trigger == "every_n" and v < 1:
                raise ValueError("every_n requires trigger_value >= 1")
            if self.trigger == "call_index" and v < 0:
                raise ValueError("call_index requires trigger_value >= 0")
        if self.trigger == "input_match" and not self.trigger_value:
            raise ValueError("input_match requires a non-empty digest prefix")
        # Deterministic triggers must not hide behind a partial rate.
        if self.trigger != "probabilistic" and float(self.rate) != 1.0:
            raise ValueError(
                "only the probabilistic trigger may use rate != 1.0; deterministic "
                "triggers fire on a condition, not a fraction")
        return self

    def to_dict(self) -> Dict[str, Any]:
        return dataclasses.asdict(self)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "FaultSpec":
        extra = set(d) - set(cls.FIELDS)
        if extra:
            raise ValueError(f"unknown fault-spec fields: {sorted(extra)}")
        return cls(**d).validate()
