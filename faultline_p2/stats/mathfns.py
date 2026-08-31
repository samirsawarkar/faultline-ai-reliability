"""Numerical primitives for statistical functions (pure standard library)."""
from __future__ import annotations

import math


def norm_cdf(x: float) -> float:
    """Standard normal CDF via erfc."""
    return 0.5 * math.erfc(-x / math.sqrt(2.0))


_A = [
    -3.969683028665376e01,
    2.209460984245205e02,
    -2.759285104469687e02,
    1.383577518672690e02,
    -3.066479806614716e01,
    2.506628277459239e00,
]
_B = [
    -5.447609879822406e01,
    1.615858368580409e02,
    -1.556989798598866e02,
    6.680131188771972e01,
    -1.328068155288572e01,
]
_C = [
    -7.784894002430293e-03,
    -3.223964580411365e-01,
    -2.400758277161838e00,
    -2.549732539343734e00,
    4.374664141464968e00,
    2.938163982698783e00,
]
_D = [
    7.784695709041462e-03,
    3.224671290700398e-01,
    2.445134137142996e00,
    3.754408661907416e00,
]
_PLOW = 0.02425


def norm_ppf(p: float) -> float:
    """Inverse standard normal CDF (quantile function)."""
    if not (0.0 < p < 1.0):
        raise ValueError("norm_ppf requires 0 < p < 1")
    if p < _PLOW:
        q = math.sqrt(-2 * math.log(p))
        x = (
            ((((_C[0] * q + _C[1]) * q + _C[2]) * q + _C[3]) * q + _C[4]) * q
            + _C[5]
        ) / ((((_D[0] * q + _D[1]) * q + _D[2]) * q + _D[3]) * q + 1)
    elif p <= 1 - _PLOW:
        q = p - 0.5
        r = q * q
        x = (
            (
                ((((_A[0] * r + _A[1]) * r + _A[2]) * r + _A[3]) * r + _A[4])
                * r
                + _A[5]
            )
            * q
            / (
                (
                    (((_B[0] * r + _B[1]) * r + _B[2]) * r + _B[3]) * r
                    + _B[4]
                )
                * r
                + 1
            )
        )
    else:
        q = math.sqrt(-2 * math.log(1 - p))
        x = -(
            ((((_C[0] * q + _C[1]) * q + _C[2]) * q + _C[3]) * q + _C[4]) * q
            + _C[5]
        ) / ((((_D[0] * q + _D[1]) * q + _D[2]) * q + _D[3]) * q + 1)
    # Halley refinement step
    e = norm_cdf(x) - p
    u = e * math.sqrt(2 * math.pi) * math.exp(x * x / 2)
    x = x - u / (1 + x * u / 2)
    return x


def chi2_sf_df1(x: float) -> float:
    """Survival function P(X > x) for chi-square with df=1."""
    if x <= 0:
        return 1.0
    return math.erfc(math.sqrt(x / 2.0))


def binom_pmf(k: int, n: int, p: float = 0.5) -> float:
    return math.comb(n, k) * (p**k) * ((1 - p) ** (n - k))


def binom_two_sided_p(b: int, c: int) -> float:
    """Exact two-sided binomial p for McNemar."""
    n = b + c
    if n == 0:
        return 1.0
    k = min(b, c)
    tail = sum(binom_pmf(i, n, 0.5) for i in range(k + 1))
    return min(1.0, 2.0 * tail)
