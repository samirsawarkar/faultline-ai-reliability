"""Pass^k decay metrics: measured pass_hat_k vs naive_p_k prediction.

These two functions are strictly separate and independent.
Neither function calls or depends on the other.
"""
from __future__ import annotations

from typing import Sequence


def pass_hat_k(per_scenario_trials: Sequence[Sequence[bool]], k: int) -> float:
    """Empirical pass^k: fraction of scenarios where all k trials passed.

    Note: This evaluates the first k trials (scenario_trials[:k]) directly for exactly
    k executed trials (e.g. k=3 with 3 trials). It does not perform combinatorial
    subset-averaging over larger trial sets (N > k).
    """
    if not per_scenario_trials:
        return 0.0
    if k <= 0:
        raise ValueError(f"k must be positive integer, got {k}")

    passed_all_k = 0
    for scenario_trials in per_scenario_trials:
        if len(scenario_trials) < k:
            raise ValueError(
                f"scenario has {len(scenario_trials)} trials, fewer than required k={k}"
            )
        if all(scenario_trials[:k]):
            passed_all_k += 1

    return passed_all_k / len(per_scenario_trials)


def naive_p_k(p: float, k: int) -> float:
    """Theoretical i.i.d. prediction for pass^k: p ** k."""
    if not (0.0 <= p <= 1.0):
        raise ValueError(f"p must be a probability in [0, 1], got {p}")
    if k <= 0:
        raise ValueError(f"k must be positive integer, got {k}")
    return float(p**k)
