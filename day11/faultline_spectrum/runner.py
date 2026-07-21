"""Run a BATCH of task runs with F5/F6 injected, labelled by the Day-8 truth log.

Each run is one sample (seq = run index). A spec fires on a run via the Day-8
`triggers.fires`, and the injection is recorded in a `GroundTruthLog` exactly as
in Days 8-10. The observation is the observable `RunResult`; correctness lives in
the oracle (task.is_correct), never on the observation.
"""
from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple

_DAY8 = Path(__file__).resolve().parents[2] / "day8"
if str(_DAY8) not in sys.path:
    sys.path.insert(0, str(_DAY8))

from faultline_inject import GroundTruthLog, TruthEntry  # noqa: E402
from faultline_inject.triggers import component_matches, fires  # noqa: E402

from .spec import SpectrumFaultSpec  # noqa: E402
from .task import RunResult, run_task  # noqa: E402


@dataclass(frozen=True)
class RunObservation:
    seq: int
    result: RunResult

    def to_dict(self) -> dict:
        return {"seq": self.seq, "result": self.result.to_dict()}


def _first_firing(specs: List[SpectrumFaultSpec], run_seed: int, seq: int, dig: str
                  ) -> Optional[SpectrumFaultSpec]:
    for spec in specs:
        if component_matches(spec, "task") and fires(spec, run_seed, seq, dig):
            return spec
    return None


def run_batch(specs: List[SpectrumFaultSpec], run_seed: int, n_runs: int = 8
              ) -> Tuple[List[RunObservation], GroundTruthLog]:
    specs = [s.validate() for s in specs]
    truth = GroundTruthLog(run_seed)
    obs: List[RunObservation] = []
    for seq in range(n_runs):
        dig = f"run-{seq}"
        spec = _first_firing(specs, run_seed, seq, dig)
        fired = spec is not None
        rr = run_task(spec.kind if fired else None, spec.severity if fired else 2)
        truth.record(TruthEntry(
            seq=seq, span_id=None, component="task", input_digest=dig,
            fired=fired, label=spec.label if fired else "clean",
            fault_id=spec.fault_id if fired else None,
            mode=spec.kind if fired else None,
            severity=spec.severity if fired else None,
            trigger=spec.trigger if fired else None))
        obs.append(RunObservation(seq=seq, result=rr))
    return obs, truth
