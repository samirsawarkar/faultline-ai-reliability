"""The boundary wrapper — inject at the seam, label as you inject.

`InjectingChannel` wraps any *clean* call boundary (an object with
`call(component, payload) -> dict`, exactly Day 6's channel shape) and turns it
into a fault surface. For each call it:

  1. computes the input digest and decides — deterministically — which spec, if
     any, fires (first matching, firing spec wins; one fault per call);
  2. writes the GROUND TRUTH for the call immediately, from that decision, into
     the out-of-band GroundTruthLog (clean or the fault's label);
  3. produces the output: clean passthrough, a deterministic content mutation, a
     side-channel cost bump (`stall`), or a raised InjectedFaultError (`error`);
  4. records a trace span (if a Day-4 tracer is given) carrying ONLY the public
     component/output — never the label.

The asymmetry in steps 2 and 4 is the whole point: truth is written from the
decision (independent), the observable record is written from the output (what a
detector gets). A fault is deterministic in *when* (triggers.py) and *what*
(faults.py), and its truth is independent of its observation (truth.py).
"""
from __future__ import annotations

import hashlib
import json
from typing import Any, Dict, List, Optional

from . import triggers
from .faults import apply_fault
from .spec import FaultSpec
from .truth import CLEAN_LABEL, GroundTruthLog, TruthEntry


def digest(payload: Any) -> str:
    """Stable content hash of a payload (canonical JSON -> sha256 hex)."""
    canon = json.dumps(payload, sort_keys=True, ensure_ascii=True,
                       separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(canon).hexdigest()


class DemoChannel:
    """A clean, deterministic inner boundary for tests and evidence.

    Output is a pure function of the call's index, with a numeric field and a
    list field so every fault mode has something to act on.
    """
    name = "demo"

    def call(self, component: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        idx = int(payload.get("index", 0))
        return {
            "step": payload.get("step"),
            "value": (idx + 1) * 10,
            "tokens": list(range(idx, idx + 4)),
        }


class InjectingChannel:
    """Wrap a clean channel; inject faults and label them at injection time."""

    def __init__(self, inner, specs: List[FaultSpec], run_seed: int,
                 truth: Optional[GroundTruthLog] = None, tracer=None):
        self.inner = inner
        self.specs = [s.validate() for s in specs]
        self.run_seed = run_seed
        self.truth = truth if truth is not None else GroundTruthLog(run_seed)
        self.tracer = tracer
        self._seq = 0
        self.cost_units = 0

    def _first_firing(self, component: str, seq: int, dig: str) -> Optional[FaultSpec]:
        """The first spec (in declaration order) that targets and fires on this
        call. Declaration order is the tie-break, so the choice is deterministic."""
        for spec in self.specs:
            if triggers.component_matches(spec, component) and \
                    triggers.fires(spec, self.run_seed, seq, dig):
                return spec
        return None

    def call(self, component: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        seq = self._seq
        self._seq += 1
        dig = digest(payload)
        spec = self._first_firing(component, seq, dig)

        if self.tracer is not None:
            # The span carries only public info; the ground-truth label is never
            # an attribute or payload here — it goes to the truth log instead.
            with self.tracer.span(f"call.{component}", "tool",
                                  payload={"component": component, "seq": seq}) as h:
                return self._produce(component, payload, seq, dig, spec, h.span_id, h)
        return self._produce(component, payload, seq, dig, spec, None, None)

    def _produce(self, component, payload, seq, dig, spec, span_id, handle):
        fired = spec is not None
        # (2) Truth first, from the decision — before any output exists.
        self.truth.record(TruthEntry(
            seq=seq, span_id=span_id, component=component, input_digest=dig,
            fired=fired,
            label=spec.label if fired else CLEAN_LABEL,
            fault_id=spec.fault_id if fired else None,
            mode=spec.mode if fired else None,
            severity=spec.severity if fired else None,
            trigger=spec.trigger if fired else None,
        ))

        if not fired:
            out = self.inner.call(component, payload)
            if handle is not None:
                handle.set_output(out)
            return out

        if spec.mode == "error":
            # Hard failure: never completes. apply_fault raises; the Day-4 span
            # closes as a complete error span in its `finally`.
            apply_fault(spec.mode, spec.severity, {})

        clean = self.inner.call(component, payload)
        faulted, cost = apply_fault(spec.mode, spec.severity, clean)
        self.cost_units += cost
        if handle is not None:
            handle.set_output(faulted)
        return faulted
