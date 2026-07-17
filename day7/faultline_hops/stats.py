"""Wilson score interval (mirrors Day 3's approach; kept local so Day 7 stays
stdlib-only).

Wilson over the normal approximation because at p=1.0 the naive interval
collapses to zero width, falsely claiming certainty from a finite sample. Wilson
stays in [0,1] and never collapses. See LEARN-compounding.md.
"""
from __future__ import annotations

import math
from typing import Tuple

Z95 = 1.959963984540054  # 95% two-sided


def wilson_interval(successes: int, n: int, z: float = Z95) -> Tuple[float, float]:
    if n < 0 or successes < 0 or successes > n:
        raise ValueError("require 0 <= successes <= n")
    if n == 0:
        return (0.0, 0.0)
    p = successes / n
    z2 = z * z
    denom = 1.0 + z2 / n
    center = (p + z2 / (2 * n)) / denom
    half = (z / denom) * math.sqrt(p * (1 - p) / n + z2 / (4 * n * n))
    return (max(0.0, center - half), min(1.0, center + half))


def rate(successes: int, n: int) -> float:
    return successes / n if n else 0.0
