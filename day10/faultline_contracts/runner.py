"""Run an F3/F4-injected boundary and capture the observable stream + truth.

Reuses Day 8 wholesale for the parts that must not drift: `triggers.fires` for
deterministic WHEN, `GroundTruthLog`/`TruthEntry` for injection-time labels,
`DemoChannel` for the clean reference, `digest` for stable input hashing. Day 10
only supplies the new WHAT (F3 corruptions, F4 provider errors).

Each `Observation` is observable-only (what a downstream system sees): the
returned output or the fact that the call raised. Correctness is NOT stored on
the observation — it belongs to the oracle/truth layer, kept separate so a
detector can never reach it.
"""
from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

_DAY8 = Path(__file__).resolve().parents[2] / "day8"
if str(_DAY8) not in sys.path:
    sys.path.insert(0, str(_DAY8))

from faultline_inject import (  # noqa: E402
    DemoChannel,
    GroundTruthLog,
    TruthEntry,
    default_calls,
    digest,
)
from faultline_inject.triggers import component_matches, fires  # noqa: E402

from .corruption import ProviderError, apply_corruption  # noqa: E402
from .spec import ContractFaultSpec  # noqa: E402

_CLEAN = DemoChannel()


@dataclass(frozen=True)
class Observation:
    seq: int
    component: str
    payload: Dict[str, Any]
    output: Optional[Any]         # returned payload, or None if the call raised
    raised: bool
    error_code: Optional[str]

    def to_dict(self) -> dict:
        return {"seq": self.seq, "component": self.component,
                "payload": self.payload, "output": self.output,
                "raised": self.raised, "error_code": self.error_code}


def _first_firing(specs: List[ContractFaultSpec], component: str, run_seed: int,
                  seq: int, dig: str) -> Optional[ContractFaultSpec]:
    for spec in specs:
        if component_matches(spec, component) and fires(spec, run_seed, seq, dig):
            return spec
    return None


def run_contracts(specs: List[ContractFaultSpec], run_seed: int,
                  calls: Optional[List[dict]] = None, tracer=None
                  ) -> Tuple[List[Observation], GroundTruthLog, List[bool]]:
    """Drive `calls`; return (observations, truth_log, provider_error_flags)."""
    specs = [s.validate() for s in specs]
    calls = calls if calls is not None else default_calls()
    truth = GroundTruthLog(run_seed)
    obs: List[Observation] = []
    error_flags: List[bool] = []

    for c in calls:
        seq = len(obs)
        component = c["component"]
        payload = {k: v for k, v in c.items() if k != "component"}
        dig = digest(payload)
        spec = _first_firing(specs, component, run_seed, seq, dig)
        fired = spec is not None

        # Ground truth, written at injection time, out of band (Day-8 discipline).
        span_id = None
        raised = False
        error_code: Optional[str] = None
        output: Optional[Any] = None

        def _emit_truth(sid):
            truth.record(TruthEntry(
                seq=seq, span_id=sid, component=component, input_digest=dig,
                fired=fired, label=spec.label if fired else "clean",
                fault_id=spec.fault_id if fired else None,
                mode=spec.kind if fired else None,
                severity=spec.severity if fired else None,
                trigger=spec.trigger if fired else None))

        if tracer is not None:
            try:
                with tracer.span(f"call.{component}", "tool",
                                 payload={"component": component, "seq": seq}) as h:
                    span_id = h.span_id
                    _emit_truth(span_id)
                    output, raised, error_code = _produce(spec, component, payload)
                    if raised:
                        # raise so the span closes as a complete error span (Day 4);
                        # caught here so the run continues.
                        raise ProviderError(error_code or "provider_unavailable")
                    h.set_output(output)
            except ProviderError:
                pass
        else:
            _emit_truth(None)
            output, raised, error_code = _produce(spec, component, payload)

        error_flags.append(raised)
        obs.append(Observation(seq=seq, component=component, payload=payload,
                               output=output, raised=raised, error_code=error_code))
    return obs, truth, error_flags


def _produce(spec, component, payload):
    """Return (output, raised, error_code) for one call."""
    clean = _CLEAN.call(component, payload)
    if spec is None:
        return clean, False, None
    if spec.family == "F4":
        return None, True, "provider_unavailable"
    return apply_corruption(spec.kind, spec.severity, clean), False, None
