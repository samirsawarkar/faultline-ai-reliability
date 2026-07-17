"""The generative model under measurement.

A task requires N tool hops; it succeeds end-to-end only if EVERY hop succeeds,
and a run stops at the first failed hop (later hops are never reached) — exactly
how a real agent chain aborts.

Per-hop success is NOT constant. Hop k (1-indexed) succeeds with probability

    p_k = clamp(P0 - DECAY * (k - 1),  PMIN, 1.0)

i.e. later hops are harder — a stand-in for accumulated context/error as a chain
grows. This single, documented assumption is what makes the measured end-to-end
curve decay FASTER than a naive "constant per-step" model predicts, which is the
whole point of Q1.

Everything is a pure function of (master_seed, n, trial): the per-run RNG is
seeded deterministically, so the entire sweep is byte-reproducible while
individual runs genuinely vary (needed for real confidence intervals).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List
import random

# Frozen model config. Changing any value changes Q1 and must bump this version.
MODEL_VERSION = "1.0.0"
P0 = 0.97      # base single-hop reliability
DECAY = 0.03   # reliability lost per additional hop of depth
PMIN = 0.50    # floor so deep hops never become impossible


def hop_probability(k: int) -> float:
    """Success probability of the k-th hop (k >= 1)."""
    if k < 1:
        raise ValueError("hop index is 1-based")
    return max(PMIN, min(1.0, P0 - DECAY * (k - 1)))


def _run_seed(master_seed: int, n: int, trial: int) -> int:
    """Deterministic, hash-randomization-free per-run seed."""
    s = (master_seed & 0xFFFFFFFF) * 2654435761
    s = (s + n * 40503 + trial * 2246822519) & 0x7FFFFFFFFFFFFFFF
    return s


@dataclass
class RunResult:
    n_hops: int
    trial: int
    hops_reached: int          # how many hops were attempted (<= n_hops)
    hop_success: List[bool]     # per attempted hop: did it succeed
    success: bool               # end-to-end success (all n hops succeeded)


def run_once(master_seed: int, n: int, trial: int) -> RunResult:
    """Simulate one n-hop task. Stops at the first failed hop."""
    rng = random.Random(_run_seed(master_seed, n, trial))
    hop_success: List[bool] = []
    for k in range(1, n + 1):
        ok = rng.random() < hop_probability(k)
        hop_success.append(ok)
        if not ok:
            break
    return RunResult(
        n_hops=n,
        trial=trial,
        hops_reached=len(hop_success),
        hop_success=hop_success,
        success=len(hop_success) == n and all(hop_success),
    )
