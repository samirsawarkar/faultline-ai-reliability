"""Run all policies on aligned seeds and assemble comparison + paired evidence."""
from __future__ import annotations

import hashlib
from collections import Counter
from typing import Any, Dict, List

from .metrics import compare_paired, summarize_policy
from .policies import POLICIES, POLICY_DESCRIPTIONS, PolicyOutcome, evaluate_policy
from .scenario import BASE_CONFIG, CascadeTrial, ExperimentConfig, build_trials
from .selection import SelectionThresholds, select_policy


def _seed_digest(trials: List[CascadeTrial]) -> str:
    return hashlib.sha256(
        ",".join(str(trial.seed) for trial in trials).encode("ascii")
    ).hexdigest()[:16]


def build_experiment(
    config: ExperimentConfig = BASE_CONFIG,
    thresholds: SelectionThresholds = SelectionThresholds(),
) -> Dict[str, Any]:
    trials = build_trials(config)
    outcomes: Dict[str, List[PolicyOutcome]] = {
        policy: [evaluate_policy(trial, policy, config) for trial in trials]
        for policy in POLICIES
    }
    metrics = {
        policy: summarize_policy(policy_outcomes)
        for policy, policy_outcomes in outcomes.items()
    }
    baseline = outcomes["P0_no_recovery"]
    paired_vs_baseline = {
        policy: compare_paired(baseline, outcomes[policy])
        for policy in POLICIES
        if policy != "P0_no_recovery"
    }
    selection = select_policy(metrics, outcomes, thresholds)
    population = {
        "n": len(trials),
        "seed_digest": _seed_digest(trials),
        "clean": sum(not trial.primary_fault for trial in trials),
        "transient_fault": sum(trial.transient for trial in trials),
        "persistent_cascade": sum(trial.persistent for trial in trials),
        "fallback_quality": dict(
            sorted(Counter(trial.fallback_quality for trial in trials).items())
        ),
    }
    return {
        "config": config.to_dict(),
        "population": population,
        "policy_definitions": {
            policy: POLICY_DESCRIPTIONS[policy] for policy in POLICIES
        },
        "policy_metrics": metrics,
        "paired_vs_no_recovery": paired_vs_baseline,
        "selection": selection,
        "_outcomes": outcomes,
    }
