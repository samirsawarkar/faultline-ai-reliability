"""Wilson score interval and small deterministic summary helpers.

Why Wilson (see LEARN-wilson.md): the naive "normal approximation" interval
p +/- z*sqrt(p(1-p)/n) is badly wrong at the extremes — at p=1.0 it returns a
zero-width interval, claiming perfect certainty from a finite sample. The Wilson
score interval stays inside [0,1], never collapses to zero width at p=0 or p=1,
and behaves well for small n. Every success-rate uncertainty in the baseline uses
it, so 500/500 reads as "[0.992, 1.000]", not "exactly 1.0 forever".
"""
from __future__ import annotations

import math
from typing import List, Sequence, Tuple


def wilson_interval(successes: int, n: int, z: float = 1.96) -> Tuple[float, float]:
    """Wilson score interval for a binomial proportion. Returns (low, high)."""
    if n < 0 or successes < 0 or successes > n:
        raise ValueError("require 0 <= successes <= n")
    if n == 0:
        return (0.0, 0.0)
    p = successes / n
    z2 = z * z
    denom = 1.0 + z2 / n
    center = (p + z2 / (2 * n)) / denom
    half = (z / denom) * math.sqrt(p * (1 - p) / n + z2 / (4 * n * n))
    low = max(0.0, center - half)
    high = min(1.0, center + half)
    return (low, high)


def mean(xs: Sequence[float]) -> float:
    return sum(xs) / len(xs) if xs else 0.0


def median(xs: Sequence[float]) -> float:
    if not xs:
        return 0.0
    s = sorted(xs)
    m = len(s) // 2
    if len(s) % 2 == 1:
        return float(s[m])
    return (s[m - 1] + s[m]) / 2.0


def percentile(xs: Sequence[float], q: float) -> float:
    """Nearest-rank percentile (q in [0,100]). Deterministic, no interpolation."""
    if not xs:
        return 0.0
    s = sorted(xs)
    rank = math.ceil(q / 100.0 * len(s))
    rank = min(max(rank, 1), len(s))
    return float(s[rank - 1])


def round6(x: float) -> float:
    """Fixed rounding at the serialization boundary -> stable git diffs."""
    return round(x, 6)


def histogram(values: Sequence[int]) -> dict:
    out: dict = {}
    for v in values:
        out[str(v)] = out.get(str(v), 0) + 1
    return dict(sorted(out.items(), key=lambda kv: int(kv[0])))
