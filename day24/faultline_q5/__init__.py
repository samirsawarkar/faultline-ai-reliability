"""FAULTLINE Day 24: Q5 — user-visible cascade success per cost and latency."""
from .experiment import build_experiment
from .metrics import compare_paired, summarize_policy
from .policies import POLICIES, PolicyOutcome, evaluate_policy
from .render import render_q5
from .report import build_report
from .scenario import (
    BASE_CONFIG,
    N,
    ExperimentConfig,
    build_trials,
)
from .selection import SelectionThresholds, select_policy

__all__ = [
    "N",
    "BASE_CONFIG",
    "ExperimentConfig",
    "build_trials",
    "POLICIES",
    "PolicyOutcome",
    "evaluate_policy",
    "summarize_policy",
    "compare_paired",
    "SelectionThresholds",
    "select_policy",
    "build_experiment",
    "build_report",
    "render_q5",
]
