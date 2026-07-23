"""Plain-English interpretation of an interval and a paired test.

The numbers are only useful if a reader knows what they do and do NOT license.
These functions turn a Wilson interval and a McNemar result into a careful English
sentence — the same words the INTERPRETATION.md guide uses.
"""
from __future__ import annotations

from typing import Any, Dict

from .intervals import wilson_interval


def interpret_interval(successes: int, n: int, confidence: float = 0.95) -> str:
    if n == 0:
        return "No samples: the rate is entirely unknown (95% CI [0, 1])."
    lo, hi = wilson_interval(successes, n, confidence)
    pct = 100 * confidence
    return (
        f"Observed rate {successes}/{n} = {successes / n:.1%}. "
        f"{pct:.0f}% Wilson CI [{lo:.1%}, {hi:.1%}]: with this much data the true "
        f"rate is consistent with anything in that band. Two rates whose intervals "
        f"overlap are NOT distinguishable at this sample size — collect more samples "
        f"to narrow the band.")


def interpret_mcnemar(result: Dict[str, Any], name_a: str = "A", name_b: str = "B") -> str:
    b, c = result["b"], result["c"]              # b = A-only correct, c = B-only correct
    n = result["n_discordant"]
    p = result["p_value"]
    method = result["recommended"]
    if n == 0:
        return (f"{name_a} and {name_b} agreed on every sample (no discordant pairs). "
                f"McNemar has nothing to test; p = 1.0. Any accuracy difference is 0.")
    winner = name_b if c > b else name_a
    sig = "significant" if p < 0.05 else "NOT significant"
    return (
        f"Of {n} discordant pairs, {name_a} alone was right on {b} and {name_b} alone "
        f"on {c}. Only these discordant pairs carry information about a difference. "
        f"McNemar ({method}) p = {p:.4f}, so the difference favouring {winner} is {sig} "
        f"at 0.05. Concordant pairs (both right or both wrong) are correctly ignored.")
