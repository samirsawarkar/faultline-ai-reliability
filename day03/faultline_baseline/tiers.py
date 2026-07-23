"""Difficulty tiers and deterministic per-task sampling.

A tier is a set of hop counts (records.TierSpec). To sample task #i of a tier we
derive a dedicated integer seed from (master_seed, tier, i) — no global RNG, no
hashing surprises — and use it to pick a hop count and a set of entities. The
same (config, tier, i) always yields the same task, on any machine.
"""
from __future__ import annotations

import random
from typing import Dict, List

from ._bridge import ArchiveSumTask, entity_names, load_env
from .records import Tier, TierSpec

# Stable integer offsets so each tier occupies a disjoint seed lane.
_TIER_LANE = {Tier.EASY: 1, Tier.MEDIUM: 2, Tier.HARD: 3}


def task_seed(master_seed: int, tier: Tier, i: int) -> int:
    """Deterministic per-task seed. Pure arithmetic; reproducible everywhere."""
    return (master_seed * 1_000_003) + (_TIER_LANE[tier] * 1_000_000) + i


def actual_tier_for_hops(hops: int, specs: List[TierSpec]) -> Tier | None:
    """Which tier a hop count actually belongs to (first spec that lists it).

    Used by the mislabel attack to recompute the honest tier from the task
    itself rather than trusting a possibly-wrong declared label.
    """
    for spec in specs:
        if hops in spec.hops:
            return spec.tier
    return None


class Sampler:
    """Builds deterministic tasks and caches per-seed environments."""

    def __init__(self, master_seed: int) -> None:
        self._master = master_seed
        self._env_cache: Dict[int, dict] = {}

    def _env(self, seed: int) -> dict:
        if seed not in self._env_cache:
            self._env_cache[seed] = load_env(seed)
        return self._env_cache[seed]

    def sample(self, spec: TierSpec, i: int):
        """Return (task, env, env_seed, task_seed, hops) for task #i of a tier."""
        seed = task_seed(self._master, spec.tier, i)
        rng = random.Random(seed)
        hops = rng.choice(spec.hops)
        # Use the same derived seed as the corpus seed so answer values (hence
        # token counts) vary across tasks while staying fully reproducible.
        env_seed = seed % 100_000
        env = self._env(env_seed)
        names = entity_names(env)
        # If a tier asks for more hops than the corpus has entities, clamp — the
        # corpus size is a fixed property, not a source of nondeterminism.
        k = min(hops, len(names))
        chosen = rng.sample(names, k)
        task = ArchiveSumTask(task_id=f"{spec.tier.value}-{i:04d}", entities=chosen)
        return task, env, env_seed, seed, k
