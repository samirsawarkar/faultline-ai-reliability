"""Wilson + bootstrap intervals: reference values, invariants, and edge cases."""
from __future__ import annotations

import pytest

from faultline_stats import bootstrap_ci, wilson_interval


def test_wilson_reference_values():
    lo, hi = wilson_interval(5, 10)
    assert abs(lo - 0.2366) < 1e-3 and abs(hi - 0.7634) < 1e-3
    assert abs(wilson_interval(10, 10)[0] - 0.7225) < 1e-3
    assert abs(wilson_interval(0, 10)[1] - 0.2775) < 1e-3


def test_wilson_bounds_are_in_unit_interval():
    for k, n in [(0, 1), (1, 1), (3, 7), (99, 100), (0, 100)]:
        lo, hi = wilson_interval(k, n)
        assert 0.0 <= lo <= hi <= 1.0


def test_wilson_extremes_touch_the_boundary():
    # analytically the far bound is exactly 0/1; allow float rounding
    assert abs(wilson_interval(10, 10)[1] - 1.0) < 1e-12   # p=1 -> upper is 1
    assert abs(wilson_interval(0, 10)[0] - 0.0) < 1e-12    # p=0 -> lower is 0


def test_wilson_swap_symmetry():
    # CI for k/n and (n-k)/n are mirror images about 0.5
    lo1, hi1 = wilson_interval(3, 10)
    lo2, hi2 = wilson_interval(7, 10)
    assert abs(lo1 - (1 - hi2)) < 1e-12 and abs(hi1 - (1 - lo2)) < 1e-12


def test_wilson_n_zero_is_full_uncertainty():
    assert wilson_interval(0, 0) == (0.0, 1.0)


def test_wilson_wider_for_smaller_n():
    w_small = wilson_interval(1, 2)
    w_big = wilson_interval(50, 100)
    assert (w_small[1] - w_small[0]) > (w_big[1] - w_big[0])


def test_wilson_rejects_bad_counts():
    with pytest.raises(ValueError):
        wilson_interval(5, 3)


def test_bootstrap_is_deterministic():
    d = [1, 0, 1, 1, 0, 1]
    assert bootstrap_ci(d, seed=3) == bootstrap_ci(d, seed=3)


def test_bootstrap_degenerate_is_a_point():
    assert bootstrap_ci([1.0] * 25, seed=0) == (1.0, 1.0)


def test_bootstrap_agrees_with_wilson_on_a_proportion():
    data = [1] * 80 + [0] * 20
    blo, bhi = bootstrap_ci(data, seed=0, iters=3000)
    wlo, whi = wilson_interval(80, 100)
    assert abs(blo - wlo) < 0.05 and abs(bhi - whi) < 0.05


def test_bootstrap_empty_raises():
    with pytest.raises(ValueError):
        bootstrap_ci([], seed=0)
