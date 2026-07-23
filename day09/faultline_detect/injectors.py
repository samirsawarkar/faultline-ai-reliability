"""F1 / F2 injectors — thin, named builders over the Day-8 fault contract.

Day 8 already gives us the deterministic, labelled injection machinery (FaultSpec,
InjectingChannel, GroundTruthLog). Day 9 does not reinvent it; it names two fault
*families* as first-class, documented injectors:

  F1 — structured-output corruption: the boundary returns a well-typed-looking
       but schema-violating payload (a wrong value, a short/duplicated/empty
       token list). Built on the Day-8 content modes.
  F2 — virtual timeout / latency: the boundary returns the correct payload but
       takes too long (a cost/latency bump). Built on the Day-8 `stall` mode.

The label written into the ground-truth log uses an "F1:" / "F2:" prefix so the
scorer can partition truth by fault family without inspecting anything else.
"""
from __future__ import annotations

import sys
from pathlib import Path

_DAY8 = Path(__file__).resolve().parents[2] / "day08"
if str(_DAY8) not in sys.path:
    sys.path.insert(0, str(_DAY8))

from faultline_inject import FaultSpec, SPEC_VERSION  # noqa: E402

# Structured-output corruption modes (F1) and the latency mode (F2).
F1_MODES = ("corrupt", "drop", "truncate", "duplicate")
F2_MODE = "stall"

F1_LABEL_PREFIX = "F1:"
F2_LABEL = "F2:latency"


def f1_corruption_spec(component: str, severity: int, *, mode: str = "corrupt",
                       trigger: str = "every_n", trigger_value: str = "1",
                       seed: int = 1, rate: float = 1.0,
                       fault_id: str = "F1-corrupt") -> FaultSpec:
    """A structured-output corruption fault. Its label is the ground truth the
    schema detector is scored against."""
    if mode not in F1_MODES:
        raise ValueError(f"F1 mode {mode!r} not in {F1_MODES}")
    return FaultSpec(
        fault_id=fault_id, component=component, mode=mode, severity=severity,
        trigger=trigger, trigger_value=trigger_value, seed=seed, rate=rate,
        label=f"{F1_LABEL_PREFIX}{mode}", spec_version=SPEC_VERSION,
    ).validate()


def f2_latency_spec(component: str, severity: int, *,
                    trigger: str = "every_n", trigger_value: str = "1",
                    seed: int = 1, rate: float = 1.0,
                    fault_id: str = "F2-latency") -> FaultSpec:
    """A virtual latency/timeout fault. Content is unchanged; only duration moves,
    which is exactly why a schema detector must NOT flag it and a duration
    detector must."""
    return FaultSpec(
        fault_id=fault_id, component=component, mode=F2_MODE, severity=severity,
        trigger=trigger, trigger_value=trigger_value, seed=seed, rate=rate,
        label=F2_LABEL, spec_version=SPEC_VERSION,
    ).validate()


def is_f1(label: str) -> bool:
    return label.startswith(F1_LABEL_PREFIX)


def is_f2(label: str) -> bool:
    return label == F2_LABEL
