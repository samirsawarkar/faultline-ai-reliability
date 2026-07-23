"""Independent verification of every statistical utility.

"Verify" here does not mean "re-run our own code and check it equals itself." Each
utility is checked against something INDEPENDENT of its implementation:

  * Wilson bounds are plugged back into the score EQUATION they solve
    ((phat - p*)^2 == z^2 * p*(1-p*)/n) — a different expression than the closed
    form used to produce them.
  * norm_ppf / chi2_sf are checked against published reference values AND
    cross-checked against each other (chi2_1 == Z^2).
  * McNemar's exact p is checked against a hand-computable binomial sum.
  * bootstrap is checked for determinism, a degenerate closed form, and agreement
    with Wilson on a proportion.

`verify_all()` returns a report; the test suite asserts `all_passed`.
"""
from __future__ import annotations

import math
from typing import Any, Dict

from .intervals import bootstrap_ci, wilson_interval
from .mathfns import chi2_sf_df1, norm_cdf, norm_ppf
from .paired import binom_two_sided_p, mcnemar_test


def _wilson_score_residual(k: int, n: int, conf: float = 0.95) -> float:
    """Max residual of the Wilson bounds in the score equation they must satisfy."""
    lo, hi = wilson_interval(k, n, conf)
    z = norm_ppf((1 + conf) / 2)
    phat = k / n
    res = 0.0
    for p in (lo, hi):
        if 0.0 < p < 1.0:                       # interior bounds satisfy the equation
            lhs = (phat - p) ** 2
            rhs = z * z * p * (1 - p) / n
            res = max(res, abs(lhs - rhs))
    return res


def verify_all() -> Dict[str, Any]:
    checks: Dict[str, Any] = {}

    # 1. Wilson via the score equation (independent of the closed form)
    residuals = {f"{k}/{n}": _wilson_score_residual(k, n)
                 for (k, n) in [(5, 10), (1, 20), (80, 100), (3, 7), (25, 50)]}
    checks["wilson_score_equation"] = {
        "max_residual": max(residuals.values()), "residuals": residuals,
        "ok": max(residuals.values()) < 1e-9}

    # 2. Wilson against textbook reference values (95%)
    ref = {"10/10": (0.7225, 1.0), "0/10": (0.0, 0.2775), "5/10": (0.2366, 0.7634)}
    wilson_ref_ok = True
    got = {}
    for key, (elo, ehi) in ref.items():
        k, n = map(int, key.split("/"))
        lo, hi = wilson_interval(k, n)
        got[key] = [round(lo, 4), round(hi, 4)]
        wilson_ref_ok &= abs(lo - elo) < 1e-3 and abs(hi - ehi) < 1e-3
    checks["wilson_reference_values"] = {"expected": {k: list(v) for k, v in ref.items()},
                                         "got": got, "ok": wilson_ref_ok}

    # 3. norm_ppf against known quantiles
    zref = {0.975: 1.959963985, 0.95: 1.644853627, 0.995: 2.575829304, 0.75: 0.674489750}
    z_ok = all(abs(norm_ppf(p) - z) < 1e-6 for p, z in zref.items())
    checks["norm_ppf_reference"] = {"expected": zref, "ok": z_ok}

    # 4. chi2 sf: reference critical values + cross-check chi2_1 == Z^2
    chi_ref = {3.8414588: 0.05, 6.6348966: 0.01, 2.7055435: 0.10}
    chi_ok = all(abs(chi2_sf_df1(x) - p) < 1e-4 for x, p in chi_ref.items())
    cross = abs(chi2_sf_df1(1.96 ** 2) - 2 * (1 - norm_cdf(1.96))) < 1e-9
    checks["chi2_sf_reference"] = {"expected": chi_ref, "critical_ok": chi_ok,
                                   "cross_check_Zsq": cross, "ok": chi_ok and cross}

    # 5. McNemar: exact binomial hand value + corrected chi-square value
    exact_ok = abs(binom_two_sided_p(1, 5) - 0.21875) < 1e-12
    m = mcnemar_test(10, 2)
    chi_p_ok = abs(m["chi2_statistic"] - 49 / 12) < 1e-9 and abs(m["chi2_p_value"] - 0.0433) < 2e-3
    empty_ok = mcnemar_test(0, 0)["p_value"] == 1.0
    checks["mcnemar"] = {"exact_1_5_is_0.21875": exact_ok,
                         "chi2_10_2_is_49_over_12": chi_p_ok,
                         "empty_is_p1": empty_ok,
                         "ok": exact_ok and chi_p_ok and empty_ok}

    # 6. bootstrap: determinism, degenerate closed form, agreement with Wilson
    det = bootstrap_ci([1, 0, 1, 1, 0], seed=7) == bootstrap_ci([1, 0, 1, 1, 0], seed=7)
    degen = bootstrap_ci([1.0] * 20, seed=0) == (1.0, 1.0)
    data = [1] * 80 + [0] * 20
    blo, bhi = bootstrap_ci(data, seed=0, iters=3000)
    wlo, whi = wilson_interval(80, 100)
    agree = abs(blo - wlo) < 0.05 and abs(bhi - whi) < 0.05
    checks["bootstrap"] = {"deterministic": det, "degenerate_point": degen,
                           "agrees_with_wilson": agree, "bootstrap": [round(blo, 4), round(bhi, 4)],
                           "wilson": [round(wlo, 4), round(whi, 4)],
                           "ok": det and degen and agree}

    all_passed = all(c["ok"] for c in checks.values())
    return {"all_passed": all_passed, "checks": checks}
