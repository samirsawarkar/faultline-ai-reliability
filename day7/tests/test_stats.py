"""Wilson interval behaves at the extremes (the reason we don't use normal-approx)."""
from __future__ import annotations

from faultline_hops import wilson_interval


def test_perfect_sample_is_not_zero_width():
    lo, hi = wilson_interval(500, 500)
    assert hi == 1.0 or hi > 0.99
    assert lo < 1.0  # never claims certainty from a finite sample
    assert lo > 0.9


def test_interval_within_unit_and_ordered():
    for s, n in [(0, 100), (1, 100), (50, 100), (99, 100), (100, 100)]:
        lo, hi = wilson_interval(s, n)
        assert 0.0 <= lo <= hi <= 1.0


def test_more_samples_tighten_interval():
    lo1, hi1 = wilson_interval(9, 10)
    lo2, hi2 = wilson_interval(900, 1000)
    assert (hi2 - lo2) < (hi1 - lo1)


def test_empty_sample_is_degenerate():
    assert wilson_interval(0, 0) == (0.0, 0.0)
