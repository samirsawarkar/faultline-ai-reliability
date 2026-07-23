"""Per-modality run + detect — the reuse layer between the dataset and Days 9-11.

A dataset sample specifies a modality (F1-F6), whether a fault is injected, its
kind, severity and seed. `run_and_predict` runs exactly one unit through the
runner that OWNS that modality and applies that modality's detector, returning a
single boolean: did the detector flag this unit as faulty. It reads only the
sample's injection config — never its expected label — which is what keeps the
evaluation leakage-free by construction (see leakage.py).
"""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
for rel in ("day08", "day09", "day10", "day11"):
    p = _ROOT / rel
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

import faultline_contracts as fc  # noqa: E402 (day10)
import faultline_detect as fd  # noqa: E402 (day09)
import faultline_spectrum as fsp  # noqa: E402 (day11)
from faultline_contracts import ContractFaultSpec, classify, detected_faulty  # noqa: E402
from faultline_spectrum import SpectrumFaultSpec, context_integrity_detect, loop_detect  # noqa: E402

_ONE_CALL = [{"component": "tool.retrieve", "step": "retrieve", "index": 0}]


def run_and_predict(modality: str, is_fault: bool, kind: str, severity: int,
                    seed: int) -> bool:
    """Return predicted_faulty for one unit. Sees only the injection config."""
    if modality == "F1":
        specs = [fd.f1_corruption_spec("*", severity, mode=kind,
                                       trigger="call_index", trigger_value="0",
                                       seed=seed)] if is_fault else []
        obs, _, _ = fd.run(specs, seed, calls=_ONE_CALL)
        return fd.schema_detect(obs[0].seq, obs[0].output).repair_signal

    if modality == "F2":
        specs = [fd.f2_latency_spec("*", severity, trigger="call_index",
                                    trigger_value="0", seed=seed)] if is_fault else []
        obs, _, _ = fd.run(specs, seed, calls=_ONE_CALL)
        return fd.duration_detect(obs[0].seq, obs[0].duration).timeout_signal

    if modality in ("F3", "F4"):
        specs = [ContractFaultSpec("S", "*", kind, severity, "call_index", "0",
                                   seed=seed)] if is_fault else []
        obs, _, _ = fc.run_contracts(specs, seed, calls=_ONE_CALL)
        return detected_faulty(classify(obs[0].raised, obs[0].output))

    if modality == "F5":
        specs = [SpectrumFaultSpec("S", kind, severity, "call_index", "0",
                                   seed=seed)] if is_fault else []
        obs, _ = fsp.run_batch(specs, seed, n_runs=1)
        return context_integrity_detect(obs[0].result).fired

    if modality == "F6":
        specs = [SpectrumFaultSpec("S", kind, severity, "call_index", "0",
                                   seed=seed)] if is_fault else []
        obs, _ = fsp.run_batch(specs, seed, n_runs=1)
        return loop_detect(obs[0].result).fired

    raise ValueError(f"unknown modality {modality!r}")
