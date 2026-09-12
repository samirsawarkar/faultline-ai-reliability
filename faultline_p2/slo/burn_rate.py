"""Google SRE Multiwindow Multi-Burn-Rate alert arithmetic."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Literal, Optional


@dataclass(frozen=True)
class BurnRateResult:
    error_rate: float
    error_budget: float
    burn_rate: float
    window_hours: float
    compliance_period_hours: float
    budget_consumed_fraction: float
    budget_consumed_percent: float


@dataclass(frozen=True)
class AlertEvaluation:
    slo_id: str
    burn_rate: float
    fast_burn_fired: bool
    slow_burn_fired: bool
    severity: Literal["ok", "page", "ticket"]
    short_window_budget_consumed_pct: float
    long_window_budget_consumed_pct: float
    message: str


def compute_burn_rate(
    error_rate: float,
    error_budget: float,
    window_hours: float = 1.0,
    compliance_period_hours: float = 720.0,
) -> BurnRateResult:
    """Compute SRE burn rate and budget consumption percentage.
    
    burn_rate = observed_error_rate / error_budget
    budget_consumed = burn_rate * (window_hours / compliance_period_hours)
    """
    if error_budget <= 0.0:
        raise ValueError("error_budget must be positive")
    if compliance_period_hours <= 0.0:
        raise ValueError("compliance_period_hours must be positive")

    burn_rate = round(error_rate / error_budget, 6)
    consumed_fraction = (burn_rate * window_hours) / compliance_period_hours
    consumed_percent = round(consumed_fraction * 100.0, 4)

    return BurnRateResult(
        error_rate=error_rate,
        error_budget=error_budget,
        burn_rate=burn_rate,
        window_hours=window_hours,
        compliance_period_hours=compliance_period_hours,
        budget_consumed_fraction=consumed_fraction,
        budget_consumed_percent=consumed_percent,
    )


def evaluate_burn_rate_alert(
    slo_id: str,
    error_rate: float,
    error_budget: float,
    fast_burn_threshold: float = 14.4,
    slow_burn_threshold: float = 6.0,
    short_window_hours: float = 1.0,
    long_window_hours: float = 6.0,
    compliance_period_hours: float = 720.0,
) -> AlertEvaluation:
    """Evaluate fast-burn (Page) and slow-burn (Ticket) rules against error rate."""
    short_burn = compute_burn_rate(
        error_rate=error_rate,
        error_budget=error_budget,
        window_hours=short_window_hours,
        compliance_period_hours=compliance_period_hours,
    )
    long_burn = compute_burn_rate(
        error_rate=error_rate,
        error_budget=error_budget,
        window_hours=long_window_hours,
        compliance_period_hours=compliance_period_hours,
    )

    fast_fired = short_burn.burn_rate >= fast_burn_threshold
    slow_fired = long_burn.burn_rate >= slow_burn_threshold

    if fast_fired:
        severity: Literal["ok", "page", "ticket"] = "page"
        msg = (
            f"[PAGE] SLO '{slo_id}' Fast-Burn Alert! Burn rate {short_burn.burn_rate}x >= {fast_burn_threshold}x "
            f"over {short_window_hours}h. Consumed {short_burn.budget_consumed_percent}% budget."
        )
    elif slow_fired:
        severity = "ticket"
        msg = (
            f"[TICKET] SLO '{slo_id}' Slow-Burn Alert. Burn rate {long_burn.burn_rate}x >= {slow_burn_threshold}x "
            f"over {long_window_hours}h. Consumed {long_burn.budget_consumed_percent}% budget."
        )
    else:
        severity = "ok"
        msg = (
            f"[OK] SLO '{slo_id}' Healthy. Burn rate {short_burn.burn_rate}x is within budget "
            f"(consumed {short_burn.budget_consumed_percent}% in {short_window_hours}h)."
        )

    return AlertEvaluation(
        slo_id=slo_id,
        burn_rate=short_burn.burn_rate,
        fast_burn_fired=fast_fired,
        slow_burn_fired=slow_fired,
        severity=severity,
        short_window_budget_consumed_pct=short_burn.budget_consumed_percent,
        long_window_budget_consumed_pct=long_burn.budget_consumed_percent,
        message=msg,
    )
