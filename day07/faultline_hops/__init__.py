"""FAULTLINE Day 7: how end-to-end reliability changes as tool hops grow (Q1).

    SweepConfig / run_sweep      -> hop-count sweep + per-step accounting
    build_curves                 -> measured / naive / corrected curves + CIs
    build_q1                     -> the assembled Q1 finding
    check_gate                   -> observability gate (every run backed by a record)
    investigate_divergence       -> explain the divergence, prove no trace gaps
    render_svg                   -> measured-vs-naive figure
    wilson_interval              -> Wilson 95% CI
"""
from .figure import render_svg
from .model import build_curves
from .observability import (
    ObservabilityGateError,
    check_gate,
    investigate_divergence,
)
from .report import build_q1
from .simulator import hop_probability, run_once
from .stats import wilson_interval
from .sweep import SweepConfig, SweepResult, run_sweep

__all__ = [
    "SweepConfig",
    "SweepResult",
    "run_sweep",
    "build_curves",
    "build_q1",
    "check_gate",
    "ObservabilityGateError",
    "investigate_divergence",
    "render_svg",
    "wilson_interval",
    "hop_probability",
    "run_once",
]
