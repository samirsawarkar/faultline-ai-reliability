"""Seeded batch runner: config in, baseline out.

`build_baseline(config)` is the reproducibility unit. Same config -> same records
-> same aggregates -> same content_hash. Nothing here reads a clock, samples
entropy outside the derived per-task seeds, or iterates hash-ordered containers.
"""
from __future__ import annotations

import hashlib
import json
from typing import Any, Dict, List, Optional, Tuple

from ._bridge import Agent, OutcomeStatus, verdict
from .accounting import account_outcome
from .records import (
    Baseline,
    BaselineConfig,
    HopPoint,
    RunRecord,
    RunStatus,
    Tier,
    TierAggregate,
    TierSpec,
)
from .stats import histogram, mean, median, percentile, round6, wilson_interval
from .tiers import Sampler, actual_tier_for_hops

_STATUS_MAP = {
    OutcomeStatus.SOLVED: RunStatus.SOLVED,
    OutcomeStatus.INCOMPLETE: RunStatus.INCOMPLETE,
    OutcomeStatus.INVALID: RunStatus.INVALID,
}


def canonical_json(obj: Any) -> bytes:
    return (json.dumps(obj, sort_keys=True, ensure_ascii=True, separators=(",", ":"))
            + "\n").encode("utf-8")


def run_one(
    sampler: Sampler,
    spec: TierSpec,
    i: int,
    config: BaselineConfig,
    declared_tier: Optional[Tier] = None,
) -> RunRecord:
    task, env, env_seed, seed, hops = sampler.sample(spec, i)
    outcome = Agent(env, step_cap=config.step_cap).run(task.model_dump())
    v = verdict(env, task, outcome)
    success = outcome.status is OutcomeStatus.SOLVED and v["passed"]
    tokens, cost, latency = account_outcome(outcome, config.cost, config.latency)

    actual = actual_tier_for_hops(hops, config.tiers)
    declared = declared_tier if declared_tier is not None else spec.tier
    return RunRecord(
        task_id=task.task_id,
        declared_tier=declared,
        actual_tier=actual,
        mislabeled=(actual is None or declared != actual),
        env_seed=env_seed,
        task_seed=seed,
        hops=hops,
        step_cap=config.step_cap,
        status=_STATUS_MAP[outcome.status],
        success=success,
        steps_used=outcome.steps_used,
        tokens_total=tokens,
        cost_usd=round6(cost),
        latency_ms=round6(latency),
    )


def run_tier(sampler: Sampler, spec: TierSpec, config: BaselineConfig) -> List[RunRecord]:
    return [run_one(sampler, spec, i, config) for i in range(config.n_per_tier)]


def aggregate_tier(tier: Tier, records: List[RunRecord], z: float) -> TierAggregate:
    n = len(records)
    successes = sum(1 for r in records if r.success)
    low, high = wilson_interval(successes, n, z)
    return TierAggregate(
        tier=tier,
        n=n,
        successes=successes,
        success_rate=round6(successes / n if n else 0.0),
        wilson_low=round6(low),
        wilson_high=round6(high),
        steps_mean=round6(mean([r.steps_used for r in records])),
        steps_median=round6(median([r.steps_used for r in records])),
        tokens_mean=round6(mean([r.tokens_total for r in records])),
        cost_usd_mean=round6(mean([r.cost_usd for r in records])),
        latency_ms_mean=round6(mean([r.latency_ms for r in records])),
        latency_ms_p95=round6(percentile([r.latency_ms for r in records], 95)),
        hop_histogram=histogram([r.hops for r in records]),
    )


def success_vs_hops(records: List[RunRecord], z: float) -> List[HopPoint]:
    by_hop: Dict[int, List[RunRecord]] = {}
    for r in records:
        by_hop.setdefault(r.hops, []).append(r)
    points: List[HopPoint] = []
    for hops in sorted(by_hop):
        rs = by_hop[hops]
        k = sum(1 for r in rs if r.success)
        low, high = wilson_interval(k, len(rs), z)
        points.append(HopPoint(
            hops=hops, n=len(rs), successes=k,
            success_rate=round6(k / len(rs)),
            wilson_low=round6(low), wilson_high=round6(high),
        ))
    return points


def build_baseline(config: BaselineConfig) -> Tuple[Baseline, List[RunRecord]]:
    sampler = Sampler(config.master_seed)
    all_records: List[RunRecord] = []
    tier_aggs: List[TierAggregate] = []
    for spec in config.tiers:
        recs = run_tier(sampler, spec, config)
        all_records.extend(recs)
        tier_aggs.append(aggregate_tier(spec.tier, recs, config.wilson_z))
    hop_points = success_vs_hops(all_records, config.wilson_z)

    body = {
        "config": config.model_dump(mode="json"),
        "tiers": [t.model_dump(mode="json") for t in tier_aggs],
        "success_vs_hops": [p.model_dump(mode="json") for p in hop_points],
    }
    content_hash = hashlib.sha256(canonical_json(body)).hexdigest()

    baseline = Baseline(
        spec_version=config.spec_version,
        config=config,
        content_hash=content_hash,
        tiers=tier_aggs,
        success_vs_hops=hop_points,
    )
    return baseline, all_records
