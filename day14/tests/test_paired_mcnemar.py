"""Paired table + McNemar's test: known values and adversarial edge cases."""
from __future__ import annotations

from faultline_stats import mcnemar_from_pairs, mcnemar_test, paired_table


def test_paired_table_counts():
    a = [True, True, False, False]
    b = [True, False, True, False]
    t = paired_table(a, b)
    assert (t.both_correct, t.a_only, t.b_only, t.both_wrong) == (1, 1, 1, 1)
    assert t.n == 4 and t.discordant == 2


def test_mcnemar_exact_hand_value():
    # b=1, c=5: 2*(C(6,0)+C(6,1))/2^6 = 14/64 = 0.21875
    assert abs(mcnemar_test(1, 5)["exact_p_value"] - 0.21875) < 1e-12


def test_mcnemar_corrected_chi2_value():
    m = mcnemar_test(10, 2)
    assert abs(m["chi2_statistic"] - 49 / 12) < 1e-9
    assert abs(m["chi2_p_value"] - 0.0433) < 2e-3


def test_mcnemar_no_discordant_pairs_is_p1():
    m = mcnemar_test(0, 0)
    assert m["p_value"] == 1.0 and m["significant_at_0.05"] is False


def test_mcnemar_symmetric_counts_not_significant():
    m = mcnemar_test(6, 6)
    assert m["p_value"] > 0.05 and m["significant_at_0.05"] is False


def test_mcnemar_small_counts_use_exact():
    m = mcnemar_test(0, 8)
    assert m["recommended"] == "exact"
    assert m["p_value"] == m["exact_p_value"]


def test_mcnemar_large_counts_use_chi2():
    m = mcnemar_test(30, 5)
    assert m["recommended"] == "chi2"
    assert m["p_value"] == m["chi2_p_value"]


def test_mcnemar_order_independence():
    assert mcnemar_test(3, 9)["p_value"] == mcnemar_test(9, 3)["p_value"]


def test_mcnemar_from_pairs_direction():
    # B strictly better: A wrong & B right on 6 pairs, never the reverse.
    # 6 one-directional discordant pairs -> exact p = 2*(1/2)^6 = 0.03125 < 0.05.
    a = [False] * 6 + [True] * 6
    b = [True] * 12
    m = mcnemar_from_pairs(a, b)
    assert m["b"] == 0 and m["c"] == 6
    assert abs(m["p_value"] - 0.03125) < 1e-12
    assert m["significant_at_0.05"] is True
