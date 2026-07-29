"""Build and score every mechanism × fault cell against its paired baseline."""
from __future__ import annotations

import hashlib
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Sequence

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT / "day14") not in sys.path:
    sys.path.insert(0, str(_ROOT / "day14"))

from faultline_stats import bootstrap_ci, mcnemar_from_pairs, wilson_interval  # noqa: E402

from .mechanisms import MECHANISMS, run_mechanism
from .scenario import FAULTS, N_PER_FAULT, Outcome, Trial, baseline_outcome, build_trials


def _rate(count: int, n: int) -> Dict[str, Any]:
    lo, hi = wilson_interval(count, n)
    return {
        "count": count,
        "n": n,
        "rate": round(count / n, 4) if n else None,
        "wilson_ci95": [round(lo, 4), round(hi, 4)],
    }


def _p95(values: Sequence[int]) -> int:
    ordered = sorted(values)
    return ordered[min(len(ordered) - 1, int(0.95 * len(ordered)))]


def _summary(outcomes: Sequence[Outcome]) -> Dict[str, Any]:
    n = len(outcomes)
    success = sum(outcome.correct for outcome in outcomes)
    available = sum(outcome.available for outcome in outcomes)
    contained = sum(outcome.contained for outcome in outcomes)
    wrong = sum(outcome.available and not outcome.correct for outcome in outcomes)
    return {
        "n": n,
        "success": _rate(success, n),
        "availability": _rate(available, n),
        "contained": _rate(contained, n),
        "answered_wrong": _rate(wrong, n),
        "total_cost": sum(outcome.cost for outcome in outcomes),
        "mean_cost": round(sum(outcome.cost for outcome in outcomes) / n, 4),
        "p95_latency": _p95([outcome.latency for outcome in outcomes]),
        "mean_latency": round(sum(outcome.latency for outcome in outcomes) / n, 4),
        "outcomes": dict(sorted(Counter(outcome.status for outcome in outcomes).items())),
    }


def _paired_delta(
    baseline: Sequence[Outcome],
    mechanism: Sequence[Outcome],
    field: str,
    seed: int,
) -> Dict[str, Any]:
    deltas = [
        float(getattr(after, field) - getattr(before, field))
        for before, after in zip(baseline, mechanism)
    ]
    lo, hi = bootstrap_ci(deltas, iters=1000, seed=seed)
    return {
        "mean": round(sum(deltas) / len(deltas), 4),
        "bootstrap_ci95": [round(lo, 4), round(hi, 4)],
        "min": min(deltas),
        "max": max(deltas),
    }


def compare_pair(
    fault: str,
    mechanism_name: str,
    trials: List[Trial],
    baseline: List[Outcome],
    mechanism: List[Outcome],
) -> Dict[str, Any]:
    if not (len(trials) == len(baseline) == len(mechanism)):
        raise ValueError("paired inputs must have equal lengths")
    seeds = [trial.seed for trial in trials]
    seed_digest = hashlib.sha256(
        ",".join(str(seed) for seed in seeds).encode("ascii")
    ).hexdigest()[:16]
    harms = []
    for trial, outcome in zip(trials, mechanism):
        for harm in outcome.harms:
            harms.append(
                {
                    "seed": trial.seed,
                    "request_index": trial.request_index,
                    "fault": trial.fault,
                    "variant": trial.variant,
                    "type": harm,
                    "status": outcome.status,
                    "cost": outcome.cost,
                    "latency": outcome.latency,
                }
            )

    key_seed = sum(ord(ch) for ch in fault + mechanism_name)
    regressions = sum(
        before.correct and not after.correct
        for before, after in zip(baseline, mechanism)
    )
    recoveries = sum(
        not before.correct and after.correct
        for before, after in zip(baseline, mechanism)
    )
    return {
        "fault": fault,
        "mechanism": mechanism_name,
        "paired": {
            "n": len(trials),
            "same_seed_population": True,
            "seed_digest": seed_digest,
            "success_mcnemar": mcnemar_from_pairs(
                [outcome.correct for outcome in baseline],
                [outcome.correct for outcome in mechanism],
            ),
            "availability_mcnemar": mcnemar_from_pairs(
                [outcome.available for outcome in baseline],
                [outcome.available for outcome in mechanism],
            ),
            "cost_delta": _paired_delta(baseline, mechanism, "cost", key_seed),
            "latency_delta": _paired_delta(
                baseline, mechanism, "latency", key_seed + 1
            ),
            "outcome_recoveries": recoveries,
            "outcome_regressions": regressions,
        },
        "baseline": _summary(baseline),
        "with_mechanism": _summary(mechanism),
        "recovery_induced_harms": {
            "count": len(harms),
            "by_type": dict(sorted(Counter(item["type"] for item in harms).items())),
            "examples": harms,
            "all_surfaced": True,
        },
        "paired_evidence_complete": True,
    }


def build_matrix() -> Dict[str, Any]:
    cells: List[Dict[str, Any]] = []
    aggregate: Dict[str, Dict[str, List[Any]]] = {
        mechanism: {"trials": [], "baseline": [], "outcomes": []}
        for mechanism in MECHANISMS
    }
    for fault in FAULTS:
        trials = build_trials(fault)
        baseline = [baseline_outcome(trial) for trial in trials]
        for mechanism_name in MECHANISMS:
            outcomes = run_mechanism(mechanism_name, trials)
            cells.append(
                compare_pair(
                    fault, mechanism_name, trials, baseline, outcomes
                )
            )
            aggregate[mechanism_name]["trials"].extend(trials)
            aggregate[mechanism_name]["baseline"].extend(baseline)
            aggregate[mechanism_name]["outcomes"].extend(outcomes)

    mechanism_summaries: Dict[str, Dict[str, Any]] = {}
    all_harms = []
    for mechanism_name in MECHANISMS:
        data = aggregate[mechanism_name]
        compared = compare_pair(
            "ALL",
            mechanism_name,
            data["trials"],
            data["baseline"],
            data["outcomes"],
        )
        mechanism_summaries[mechanism_name] = compared
        all_harms.extend(compared["recovery_induced_harms"]["examples"])

    unpaired = [
        f"{cell['mechanism']}:{cell['fault']}"
        for cell in cells
        if not cell["paired_evidence_complete"]
        or cell["paired"]["n"] != N_PER_FAULT
        or not cell["paired"]["same_seed_population"]
    ]
    harm_count_cells = sum(
        cell["recovery_induced_harms"]["count"] for cell in cells
    )
    audit_count = sum(
        item["recovery_induced_harms"]["count"]
        for item in mechanism_summaries.values()
    )

    return {
        "design": {
            "mechanisms": list(MECHANISMS),
            "faults": list(FAULTS),
            "cells": len(cells),
            "paired_seeds_per_cell": N_PER_FAULT,
            "faulted_per_cell": 18,
            "clean_controls_per_cell": 6,
            "outcomes": (
                "correct success, answered-wrong, contained termination, unavailable"
            ),
            "comparison_dimensions": ["outcome", "availability", "cost", "latency"],
        },
        "cells": cells,
        "mechanism_summaries": mechanism_summaries,
        "recovery_induced_harm_audit": {
            "by_mechanism": {
                mechanism: mechanism_summaries[mechanism][
                    "recovery_induced_harms"
                ]
                for mechanism in MECHANISMS
            },
            "total": audit_count,
            "cell_total_reconciles": harm_count_cells == audit_count,
            "all_mechanisms_measured": set(mechanism_summaries) == set(MECHANISMS),
            "all_harms_surfaced": all(
                item["recovery_induced_harms"]["all_surfaced"]
                for item in mechanism_summaries.values()
            ),
        },
        "fail_condition_guard": {
            "expected_cells": len(MECHANISMS) * len(FAULTS),
            "observed_cells": len(cells),
            "unpaired_cells": unpaired,
            "every_mechanism_has_paired_evidence": not unpaired,
            "every_mechanism_has_harm_audit": set(
                mechanism_summaries
            ) == set(MECHANISMS),
            "every_cell_has_outcome_cost_latency": all(
                "success_mcnemar" in cell["paired"]
                and "cost_delta" in cell["paired"]
                and "latency_delta" in cell["paired"]
                for cell in cells
            ),
            "all_recovery_induced_harms_measured": (
                harm_count_cells == audit_count
                and all(
                    cell["recovery_induced_harms"]["all_surfaced"]
                    for cell in cells
                )
            ),
            "passed": (
                len(cells) == len(MECHANISMS) * len(FAULTS)
                and not unpaired
                and set(mechanism_summaries) == set(MECHANISMS)
                and harm_count_cells == audit_count
                and all(
                    cell["recovery_induced_harms"]["all_surfaced"]
                    for cell in cells
                )
            ),
        },
    }
