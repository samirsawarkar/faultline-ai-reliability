"""Confidence intervals — Wilson (closed form) and bootstrap (resampling).

Both answer "given the data, what range of true rates is consistent with it?" —
the Wilson interval analytically for a proportion, the bootstrap empirically for
any statistic. Wilson is the project's default (correct at the extremes and for
small n, unlike the normal approximation); the bootstrap is the general-purpose
fallback and a cross-check on Wilson for proportions.
"""
from __future__ import annotations

import math
import random
from typing import Callable, List, Sequence, Tuple

from .mathfns import norm_ppf


def wilson_interval(successes: int, n: int, confidence: float = 0.95) -> Tuple[float, float]:
    """Wilson score interval for a binomial proportion. Returns (lo, hi) in [0,1].
    n == 0 returns (0.0, 1.0): no data, no information."""
    if successes < 0 or n < 0 or successes > n:
        raise ValueError("require 0 <= successes <= n")
    if n == 0:
        return (0.0, 1.0)
    z = norm_ppf((1 + confidence) / 2)
    phat = successes / n
    z2 = z * z
    denom = 1 + z2 / n
    center = (phat + z2 / (2 * n)) / denom
    half = (z * math.sqrt(phat * (1 - phat) / n + z2 / (4 * n * n))) / denom
    return (max(0.0, center - half), min(1.0, center + half))


def _percentile(sorted_vals: List[float], q: float) -> float:
    """Nearest-rank percentile (deterministic, no interpolation ambiguity)."""
    if not sorted_vals:
        raise ValueError("empty sample")
    idx = max(0, min(len(sorted_vals) - 1, int(round(q * (len(sorted_vals) - 1)))))
    return sorted_vals[idx]


def bootstrap_ci(data: Sequence[float], confidence: float = 0.95,
                 iters: int = 2000, seed: int = 0,
                 statistic: Callable[[Sequence[float]], float] = None
                 ) -> Tuple[float, float]:
    """Percentile bootstrap CI for `statistic` (default: mean). Deterministic:
    resampling uses a seeded RNG, so the same (data, seed) gives the same CI."""
    n = len(data)
    if n == 0:
        raise ValueError("bootstrap requires a non-empty sample")
    stat = statistic or (lambda s: sum(s) / len(s))
    rng = random.Random(seed)
    reps: List[float] = []
    for _ in range(iters):
        sample = [data[rng.randrange(n)] for _ in range(n)]
        reps.append(stat(sample))
    reps.sort()
    alpha = 1 - confidence
    return (_percentile(reps, alpha / 2), _percentile(reps, 1 - alpha / 2))
