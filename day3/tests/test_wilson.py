"""Wilson interval: known values and the properties that motivate using it."""
import math

import pytest

from faultline_baseline import wilson_interval


def test_zero_successes_gives_zero_lower_bound_and_positive_upper():
    low, high = wilson_interval(0, 10)
    assert low == 0.0
    # Classic reference value for 0/10 at 95%: upper ~ 0.2775.
    assert high == pytest.approx(0.2775, abs=1e-3)


def test_all_successes_never_claims_zero_width():
    low, high = wilson_interval(10, 10)
    assert high == 1.0
    assert low == pytest.approx(0.7225, abs=1e-3)  # mirror of the 0/10 case
    assert low < 1.0  # the whole point: not a zero-width "certainty"


def test_symmetric_case_is_symmetric_about_half():
    low, high = wilson_interval(5, 10)
    assert low == pytest.approx(0.2366, abs=1e-3)
    assert high == pytest.approx(0.7634, abs=1e-3)
    assert (low + high) / 2 == pytest.approx(0.5, abs=1e-6)


def test_interval_contains_point_estimate_and_stays_in_unit():
    for k, n in [(1, 3), (7, 20), (499, 500), (250, 500)]:
        low, high = wilson_interval(k, n)
        assert 0.0 <= low <= k / n <= high <= 1.0


def test_more_data_shrinks_the_interval():
    w_small = wilson_interval(50, 100)
    w_big = wilson_interval(500, 1000)
    width = lambda w: w[1] - w[0]
    assert width(w_big) < width(w_small)


def test_rejects_impossible_counts():
    with pytest.raises(ValueError):
        wilson_interval(11, 10)


def test_n_zero_is_degenerate_not_a_crash():
    assert wilson_interval(0, 0) == (0.0, 0.0)
