"""Paired-run design + McNemar's test for two systems on the SAME samples.

When two systems are evaluated on identical seeded samples, their outcomes are
PAIRED: the sample-to-sample difficulty cancels, and the only thing that matters
for "is A different from B?" is the DISCORDANT pairs — cases where exactly one of
them was right. McNemar's test looks at just those.

`paired_table` builds the 2x2 contingency from two aligned correctness lists;
`mcnemar_test` returns both the continuity-corrected chi-square p and (for small
discordant counts) the exact binomial p, and recommends which to trust.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Sequence

from .mathfns import binom_two_sided_p, chi2_sf_df1

EXACT_THRESHOLD = 25          # use exact binomial when discordant pairs are few


@dataclass(frozen=True)
class PairedTable:
    both_correct: int         # n11
    a_only: int               # n10: A correct, B wrong
    b_only: int               # n01: A wrong, B correct
    both_wrong: int           # n00

    @property
    def n(self) -> int:
        return self.both_correct + self.a_only + self.b_only + self.both_wrong

    @property
    def discordant(self) -> int:
        return self.a_only + self.b_only

    def to_dict(self) -> Dict[str, int]:
        return {"both_correct": self.both_correct, "a_only": self.a_only,
                "b_only": self.b_only, "both_wrong": self.both_wrong,
                "n": self.n, "discordant": self.discordant}


def paired_table(a_correct: Sequence[bool], b_correct: Sequence[bool]) -> PairedTable:
    if len(a_correct) != len(b_correct):
        raise ValueError("paired lists must have equal length")
    n11 = n10 = n01 = n00 = 0
    for a, b in zip(a_correct, b_correct):
        if a and b:
            n11 += 1
        elif a and not b:
            n10 += 1
        elif not a and b:
            n01 += 1
        else:
            n00 += 1
    return PairedTable(both_correct=n11, a_only=n10, b_only=n01, both_wrong=n00)


def mcnemar_test(b: int, c: int, correction: bool = True) -> Dict[str, Any]:
    """McNemar's test on the two discordant counts (order-independent).

    b, c are the off-diagonal cells (A-only and B-only). Returns the corrected
    chi-square statistic + p, the exact binomial p, and which to report."""
    n = b + c
    exact_p = binom_two_sided_p(b, c)
    if n == 0:
        chi2 = 0.0
        chi2_p = 1.0
    else:
        diff = abs(b - c)
        chi2 = ((diff - 1) ** 2 / n) if correction else (diff ** 2 / n)
        chi2 = max(0.0, chi2)
        chi2_p = chi2_sf_df1(chi2)
    use_exact = n < EXACT_THRESHOLD
    return {
        "b": b, "c": c, "n_discordant": n,
        "chi2_statistic": chi2, "chi2_p_value": chi2_p, "continuity_correction": correction,
        "exact_p_value": exact_p,
        "recommended": "exact" if use_exact else "chi2",
        "p_value": exact_p if use_exact else chi2_p,
        "significant_at_0.05": (exact_p if use_exact else chi2_p) < 0.05,
    }


def mcnemar_from_pairs(a_correct: Sequence[bool], b_correct: Sequence[bool],
                       correction: bool = True) -> Dict[str, Any]:
    t = paired_table(a_correct, b_correct)
    result = mcnemar_test(t.a_only, t.b_only, correction=correction)
    result["table"] = t.to_dict()
    return result
