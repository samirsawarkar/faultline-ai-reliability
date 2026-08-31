"""Tests for faultline_p2.stats."""
import json
import math
import subprocess
import sys
from pathlib import Path

import pytest

from faultline_p2.stats.intervals import bootstrap, wilson, wilson_interval
from faultline_p2.stats.mathfns import norm_ppf
from faultline_p2.stats.paired import mcnemar
from faultline_p2.stats.passk import naive_p_k, pass_hat_k

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


def test_agreement_with_day14_stats_verification():
    stats_ev_path = REPO_ROOT / "day14" / "evidence" / "stats_verification.json"
    with open(stats_ev_path, "r", encoding="utf-8") as f:
        ev = json.load(f)

    # 1. norm_ppf reference values
    for p_str, expected_z in ev["checks"]["norm_ppf_reference"]["expected"].items():
        p_val = float(p_str)
        z = norm_ppf(p_val)
        assert math.isclose(z, expected_z, abs_tol=1e-6), f"norm_ppf({p_val}): {z} != {expected_z}"

    # 2. Wilson reference values (0/10, 5/10, 10/10)
    for frac_str, (exp_lo, exp_hi) in ev["checks"]["wilson_reference_values"]["expected"].items():
        k_str, n_str = frac_str.split("/")
        k, n = int(k_str), int(n_str)
        lo, hi = wilson_interval(k, n, confidence=0.95)
        assert round(lo, 4) == exp_lo, f"wilson({k}/{n}) lo: {round(lo, 4)} != {exp_lo}"
        assert round(hi, 4) == exp_hi, f"wilson({k}/{n}) hi: {round(hi, 4)} != {exp_hi}"

    # 3. McNemar checks
    # exact 1 vs 5 -> p = 0.21875
    res_exact = mcnemar(1, 5)
    assert res_exact["recommended"] == "exact"
    assert math.isclose(res_exact["exact_p_value"], 0.21875, abs_tol=1e-5)
    assert math.isclose(res_exact["p_value"], 0.21875, abs_tol=1e-5)

    # chi2 10 vs 2 -> chi2 statistic = (8 - 1)^2 / 12 = 49 / 12
    res_10_2 = mcnemar(10, 2)
    assert math.isclose(res_10_2["chi2_statistic"], 49 / 12, abs_tol=1e-5)


def test_agreement_with_day14_paired_comparison():
    paired_ev_path = REPO_ROOT / "day14" / "evidence" / "paired_comparison.json"
    with open(paired_ev_path, "r", encoding="utf-8") as f:
        ev = json.load(f)

    # b=0, c=20 discordant (n=20 < 25 -> exact recommended)
    mcn = ev["mcnemar"]
    res = mcnemar(b=mcn["b"], c=mcn["c"])
    assert res["b"] == 0
    assert res["c"] == 20
    assert res["n_discordant"] == 20
    assert res["recommended"] == "exact"
    assert math.isclose(res["chi2_statistic"], mcn["chi2_statistic"], abs_tol=1e-5)
    assert math.isclose(res["chi2_p_value"], mcn["chi2_p_value"], abs_tol=1e-5)
    assert math.isclose(res["exact_p_value"], mcn["exact_p_value"], abs_tol=1e-10)
    assert res["significant_at_0.05"] == mcn["significant_at_0.05"]


def test_wilson_property_grid():
    # Grid of n and k including boundaries k=0 and k=n
    n_values = [1, 2, 5, 10, 50, 100, 500, 1000]
    for n in n_values:
        for k in range(0, n + 1, max(1, n // 10)):
            lo, hi = wilson(k, n)
            phat = k / n
            assert 0.0 <= lo <= 1.0, f"Wilson lo {lo} out of [0, 1] for k={k}, n={n}"
            assert 0.0 <= hi <= 1.0, f"Wilson hi {hi} out of [0, 1] for k={k}, n={n}"
            assert lo <= hi, f"Wilson lo {lo} > hi {hi} for k={k}, n={n}"
            assert lo <= phat + 1e-12, f"Wilson lo {lo} > phat {phat} for k={k}, n={n}"
            assert hi >= phat - 1e-12, f"Wilson hi {hi} < phat {phat} for k={k}, n={n}"

    # Edge cases
    assert wilson(0, 0) == (0.0, 1.0)
    with pytest.raises(ValueError):
        wilson(-1, 10)
    with pytest.raises(ValueError):
        wilson(11, 10)


def test_bootstrap_cross_process_determinism():
    cmd = [
        sys.executable,
        "-c",
        "from faultline_p2.stats.intervals import bootstrap; "
        "data = [1.0, 0.0, 1.0, 1.0, 0.0, 1.0, 0.0, 1.0, 1.0, 1.0]; "
        "print(bootstrap(data, n_resamples=1000, seed=12345))",
    ]

    res1 = subprocess.run(cmd, capture_output=True, text=True, check=True, env={"PYTHONHASHSEED": "0"})
    res2 = subprocess.run(cmd, capture_output=True, text=True, check=True, env={"PYTHONHASHSEED": "999999"})

    assert res1.stdout.strip() == res2.stdout.strip(), (
        f"Bootstrap output differed across processes: {res1.stdout} != {res2.stdout}"
    )


def test_passk_metrics():
    # Scenario 1: [True, True, True]
    # Scenario 2: [True, False, True]
    # Scenario 3: [True, True, False]
    # Scenario 4: [True, True, True]
    trials = [
        [True, True, True],
        [True, False, True],
        [True, True, False],
        [True, True, True],
    ]

    # k=1: all 4 scenarios passed trial 1 -> pass_hat_1 = 1.0
    assert pass_hat_k(trials, k=1) == 1.0
    # k=2: scenarios 1, 3, 4 passed both trials -> pass_hat_2 = 3/4 = 0.75
    assert pass_hat_k(trials, k=2) == 0.75
    # k=3: scenarios 1, 4 passed all 3 trials -> pass_hat_3 = 2/4 = 0.50
    assert pass_hat_k(trials, k=3) == 0.50

    # naive_p_k:
    p1 = 0.8
    assert math.isclose(naive_p_k(p1, k=1), 0.8)
    assert math.isclose(naive_p_k(p1, k=2), 0.64)
    assert math.isclose(naive_p_k(p1, k=3), 0.512)

    with pytest.raises(ValueError):
        naive_p_k(1.5, 3)
    with pytest.raises(ValueError):
        pass_hat_k(trials, k=0)
