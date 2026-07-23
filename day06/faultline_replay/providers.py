"""Providers and the record/replay channel.

A *provider* answers a call. Two providers model the two sides of the
reproducibility boundary:

  SimulatorProvider  output is a pure function of the call inputs -> re-executing
                     gives the same bytes forever. This is our deterministic
                     simulator.
  FlakyProvider      output depends on entropy that is NOT in the captured state
                     (a process-global nonce standing in for sampling temperature
                     / hardware RNG / model-version drift). Re-executing gives
                     DIFFERENT bytes. This is our stand-in for a real provider;
                     we do not call a real API.

A *channel* is how the program talks to a provider:

  LiveChannel    computes via the provider and RECORDS each call.
  ReplayChannel  serves recorded outputs from a bundle and never computes. If the
                 program asks for a call the recording didn't see (or with a
                 different input), it raises ReplayDivergence instead of guessing.
"""
from __future__ import annotations

import itertools
from typing import Any, Dict, List

from .bundle import digest

# Process-global "uncaptured entropy": monotonic, so two live runs in one process
# reliably differ. Stands in for real-provider nondeterminism (NOT a real API).
_UNCAPTURED_ENTROPY = itertools.count(1)


class SimulatorProvider:
    name = "simulator"

    def compute(self, component: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        idx = int(payload.get("index", 0))
        return {"step": payload.get("step"), "value": (idx + 1) * 10, "by": "simulator"}


class FlakyProvider:
    """Real-provider stand-in: output carries a nonce absent from captured state."""
    name = "flaky"

    def compute(self, component: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        idx = int(payload.get("index", 0))
        return {"step": payload.get("step"), "value": (idx + 1) * 10,
                "by": "real-provider", "nonce": next(_UNCAPTURED_ENTROPY)}


def make_provider(name: str):
    if name == "simulator":
        return SimulatorProvider()
    if name == "flaky":
        return FlakyProvider()
    raise ValueError(f"unknown provider {name!r}")


class ReplayDivergence(RuntimeError):
    """The program asked for something the recording cannot answer."""


class LiveChannel:
    """Compute via a provider and record every call."""

    def __init__(self, provider):
        self.provider = provider
        self.records: List[Dict[str, Any]] = []
        self._seq = itertools.count(0)

    def call(self, component: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        out = self.provider.compute(component, payload)
        self.records.append({
            "seq": next(self._seq),
            "component": component,
            "input_digest": digest(payload),
            "output": out,
        })
        return out


class ReplayChannel:
    """Serve recorded outputs in order; never compute. Diverge loudly."""

    def __init__(self, recorded_calls: List[Dict[str, Any]]):
        self._records = sorted(recorded_calls, key=lambda r: r["seq"])
        self._i = 0
        self.consumed = 0

    def call(self, component: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        if self._i >= len(self._records):
            raise ReplayDivergence(
                f"program requested call #{self._i} ({component}) but the "
                f"recording has only {len(self._records)} calls")
        rec = self._records[self._i]
        if rec["component"] != component:
            raise ReplayDivergence(
                f"call #{self._i}: recording is {rec['component']!r}, "
                f"program asked {component!r}")
        if rec["input_digest"] != digest(payload):
            raise ReplayDivergence(
                f"call #{self._i} ({component}): input digest mismatch — the "
                f"program is not on the recorded path")
        self._i += 1
        self.consumed += 1
        return rec["output"]
