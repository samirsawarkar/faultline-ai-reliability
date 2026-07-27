"""FAULTLINE Day 19: Q3 — the retry crossover (where retries stop helping).

A parameterized retry sweep with success-per-cost and tail-latency reporting, a
crossover analysis, an independent-vs-correlated paired experiment with a retry
storm, and a defensible recommended retry region capped by cost + tail ceilings.

Public surface:
    sweep:     sweep, sweep_point, success_flags, N, KMAX, SEED, ...
    crossover: crossover, fail_condition_check, COST_CEILING_AMP, P99_BUDGET, MIN_MARGINAL_SUCCESS
    figure:    render_svg
    report:    build_report
"""
from . import crossover, figure, report, sweep
from .crossover import (COST_CEILING_AMP, MIN_MARGINAL_SUCCESS, P99_BUDGET,
                        crossover as crossover_of, fail_condition_check)
from .figure import render_svg
from .report import build_report
from .sweep import success_flags, sweep, sweep_point

__all__ = [
    "sweep", "sweep_point", "success_flags",
    "crossover_of", "fail_condition_check", "COST_CEILING_AMP", "P99_BUDGET",
    "MIN_MARGINAL_SUCCESS", "render_svg", "build_report",
    "crossover", "figure", "report",
]
