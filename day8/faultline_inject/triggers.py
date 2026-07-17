"""Deterministic triggers — the WHEN, as a pure function.

`fires(spec, run_seed, seq, input_digest) -> bool` is the single decision point
for whether a fault activates on a given call. It is a pure function of its
arguments: no wall-clock, no global state, no `random` module default RNG. The
`probabilistic` trigger draws from a `random.Random` seeded *only* from
`(spec.seed, run_seed, seq)`, so "probabilistic" means "a fixed fraction fire,
and which ones is reproducible" — the opposite of chaos.

Two properties this module must guarantee (and Day 8's tests pin down):
  * Reproducible: same (spec, run_seed, seq, digest) => same bool, always.
  * Seed-independent where it claims to be: the deterministic triggers
    (call_index, every_n, input_match) do NOT consult run_seed, so they fire on
    identical calls no matter the seed. The probabilistic trigger DOES, so its
    fire pattern is stable per seed and genuinely varies across seeds.
"""
from __future__ import annotations

import random

from .spec import FaultSpec


def _draw_seed(spec_seed: int, run_seed: int, seq: int) -> int:
    """A collision-resistant, hash-randomization-free seed for one decision.

    Mirrors Day 7's mixing so the whole repo shares one determinism discipline.
    """
    s = (spec_seed & 0xFFFFFFFF) * 2654435761
    s = (s + (run_seed & 0xFFFFFFFF) * 40503 + seq * 2246822519) & 0x7FFFFFFFFFFFFFFF
    return s


def component_matches(spec: FaultSpec, component: str) -> bool:
    """A spec targets a call iff its component is '*' or an exact match."""
    return spec.component == "*" or spec.component == component


def fires(spec: FaultSpec, run_seed: int, seq: int, input_digest: str) -> bool:
    """Decide whether `spec` activates on call #`seq` (0-based) with the given
    input digest. Pure function; deterministic for all triggers."""
    if spec.trigger == "call_index":
        return seq == int(spec.trigger_value)
    if spec.trigger == "every_n":
        n = int(spec.trigger_value)
        return n >= 1 and seq % n == 0
    if spec.trigger == "input_match":
        return input_digest.startswith(spec.trigger_value)
    if spec.trigger == "probabilistic":
        rng = random.Random(_draw_seed(spec.seed, run_seed, seq))
        return rng.random() < float(spec.rate)
    raise ValueError(f"unknown trigger {spec.trigger!r}")
