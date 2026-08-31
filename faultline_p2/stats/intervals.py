"""Confidence intervals — Wilson score and bootstrap."""
from __future__ import annotations

import math
import random
from typing import Callable, List, Optional, Sequence, Tuple

from faultline_p2.stats.mathfns import norm_ppf


def wilson(successes: int, n: int, z: float = 1.96) -> Tuple[float, float]:
    """Wilson score interval for a binomial proportion. Returns (lo, hi) in [0, 1].

    n == 0 returns (0.0, 1.0).
    """
    if successes < 0 or n < 0 or successes > n:
        raise ValueError(f"require 0 <= successes <= n, got successes={successes}, n={n}")
    if n == 0:
        return (0.0, 1.0)
    phat = successes / n
    z2 = z * z
    denom = 1 + z2 / n
    center = (phat + z2 / (2 * n)) / denom
    half = (z * math.sqrt(phat * (1 - phat) / n + z2 / (4 * n * n))) / denom
    return (max(0.0, center - half), min(1.0, center + half))


def wilson_interval(successes: int, n: int, confidence: float = 0.95) -> Tuple[float, float]:
    """Wilson interval computing z from confidence level."""
    if successes < 0 or n < 0 or successes > n:
        raise ValueError(f"require 0 <= successes <= n, got successes={successes}, n={n}")
    if n == 0:
        return (0.0, 1.0)
    z = norm_ppf((1 + confidence) / 2)
    return wilson(successes, n, z=z)


def _percentile(sorted_vals: List[float], q: float) -> float:
    """Nearest-rank percentile (deterministic)."""
    if not sorted_vals:
        raise ValueError("empty sample")
    idx = max(0, min(len(sorted_vals) - 1, int(round(q * (len(sorted_vals) - 1)))))
    return sorted_vals[idx]


def bootstrap(
    data: Sequence[float],
    statistic: Optional[Callable[[Sequence[float]], float]] = None,
    n_resamples: int = 10_000,
    seed: int = 42,
    confidence: float = 0.95,
) -> Tuple[float, float]:
    """Seeded, reproducible percentile bootstrap confidence interval."""
    n = len(data)
    if n == 0:
        raise ValueError("bootstrap requires a non-empty sample")
    stat = statistic or (lambda s: sum(s) / len(s))
    rng = random.Random(seed)
    reps: List[float] = []
    for _ in range(n_resamples):
        sample = [data[rng.randrange(n)] for _ in range(n)]
        reps.append(stat(sample))
    reps.sort()
    alpha = 1 - confidence
    return (_percentile(reps, alpha / 2), _percentile(reps, 1 - alpha / 2))


# Alias for backwards compatibility
bootstrap_ci = bootstrap
