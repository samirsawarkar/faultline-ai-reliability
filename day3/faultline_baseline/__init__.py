"""FAULTLINE Day 3 — the reproducible baseline (zero point) across tiers."""
from .accounting import account_outcome
from .figure import render_success_vs_hops
from .records import (
    Baseline,
    BaselineConfig,
    CostModel,
    HopPoint,
    LatencyModel,
    RunRecord,
    RunStatus,
    Tier,
    TierAggregate,
    TierSpec,
)
from .runner import (
    aggregate_tier,
    build_baseline,
    canonical_json,
    run_one,
    run_tier,
    success_vs_hops,
)
from .stats import mean, median, percentile, wilson_interval
from .tiers import Sampler, actual_tier_for_hops, task_seed

__all__ = [
    "account_outcome",
    "render_success_vs_hops",
    "Baseline",
    "BaselineConfig",
    "CostModel",
    "HopPoint",
    "LatencyModel",
    "RunRecord",
    "RunStatus",
    "Tier",
    "TierAggregate",
    "TierSpec",
    "aggregate_tier",
    "build_baseline",
    "canonical_json",
    "run_one",
    "run_tier",
    "success_vs_hops",
    "mean",
    "median",
    "percentile",
    "wilson_interval",
    "Sampler",
    "actual_tier_for_hops",
    "task_seed",
]
