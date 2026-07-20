"""Run a fault-injected boundary and capture the observable stream.

This is the seam between Day 8 (inject + label) and Day 9 (detect + score). It
drives the Day-8 `InjectingChannel` over a clean `DemoChannel` and records, for
each call, exactly what a downstream system could see:

    seq, component, output (or None if the call raised), raised, duration

`duration = BASE_LATENCY + injected`, where `injected` is the per-call `stall`
cost delta read off the channel's own cost meter — an OBSERVABLE, computed from
the channel's behaviour, never from the truth log. The truth log is returned
alongside, untouched, for the scorer to use independently.
"""
from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, List, Optional, Tuple

_DAY8 = Path(__file__).resolve().parents[2] / "day8"
if str(_DAY8) not in sys.path:
    sys.path.insert(0, str(_DAY8))

from faultline_inject import (  # noqa: E402
    DemoChannel,
    GroundTruthLog,
    InjectedFaultError,
    InjectingChannel,
    default_calls,
)

from .latency import BASE_LATENCY, duration  # noqa: E402


@dataclass(frozen=True)
class Observation:
    seq: int
    component: str
    output: Optional[Any]     # the returned payload, or None if the call raised
    raised: bool
    duration: int

    def to_dict(self) -> dict:
        return {"seq": self.seq, "component": self.component,
                "output": self.output, "raised": self.raised,
                "duration": self.duration}


def run(specs, run_seed: int, calls: Optional[List[dict]] = None, tracer=None
        ) -> Tuple[List[Observation], GroundTruthLog, int]:
    """Drive `calls` through an injecting boundary; return (observations, truth,
    total_cost)."""
    calls = calls if calls is not None else default_calls()
    ch = InjectingChannel(DemoChannel(), specs, run_seed, tracer=tracer)
    obs: List[Observation] = []
    for c in calls:
        payload = {k: v for k, v in c.items() if k != "component"}
        cost_before = ch.cost_units
        raised = False
        output: Optional[Any] = None
        try:
            output = ch.call(c["component"], payload)
        except InjectedFaultError:
            raised = True
        injected = ch.cost_units - cost_before
        obs.append(Observation(
            seq=len(obs), component=c["component"], output=output,
            raised=raised, duration=duration(BASE_LATENCY, injected)))
    return obs, ch.truth, ch.cost_units
