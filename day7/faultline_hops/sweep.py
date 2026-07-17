"""Hop-count sweep + per-step success accounting (Build A).

For each n in 1..max_hops we run `trials` independent tasks and record:
  - end-to-end success at n            (for the measured curve)
  - per-hop reached/success, pooled    (for per-step reliability p_k)
  - a complete per-run record          (for the observability gate)

The per-run records ARE the observability substrate: every run leaves a
gap-free record of exactly which hops it reached and how each turned out, so no
number in the report is unbacked (cf. Day 4/5). `observability.py` gates on it.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

from .simulator import MODEL_VERSION, RunResult, run_once


@dataclass
class SweepConfig:
    master_seed: int = 20260717
    max_hops: int = 8
    trials: int = 500
    model_version: str = MODEL_VERSION

    def as_dict(self) -> Dict:
        return {
            "master_seed": self.master_seed,
            "max_hops": self.max_hops,
            "trials": self.trials,
            "model_version": self.model_version,
        }


@dataclass
class SweepResult:
    config: SweepConfig
    runs: List[RunResult]
    # end-to-end: n -> (successes, total)
    e2e: Dict[int, Dict[str, int]] = field(default_factory=dict)
    # per hop position k -> {reached, success} pooled across all runs
    per_hop: Dict[int, Dict[str, int]] = field(default_factory=dict)


def run_sweep(config: SweepConfig) -> SweepResult:
    runs: List[RunResult] = []
    e2e: Dict[int, Dict[str, int]] = {}
    per_hop: Dict[int, Dict[str, int]] = {}

    for n in range(1, config.max_hops + 1):
        succ = 0
        for trial in range(config.trials):
            r = run_once(config.master_seed, n, trial)
            runs.append(r)
            if r.success:
                succ += 1
            # pooled per-hop accounting: hop k was reached if attempted
            for k in range(1, r.hops_reached + 1):
                bucket = per_hop.setdefault(k, {"reached": 0, "success": 0})
                bucket["reached"] += 1
                if r.hop_success[k - 1]:
                    bucket["success"] += 1
        e2e[n] = {"successes": succ, "total": config.trials}

    return SweepResult(config=config, runs=runs, e2e=e2e, per_hop=per_hop)
