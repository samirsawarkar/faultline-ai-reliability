"""FAULTLINE Day 22: six recovery mechanisms compared across all six faults."""
from .ceilings import CeilingPolicy, CeilingResult, run_with_ceilings
from .matrix import FAULTS, MECHANISMS, build_matrix, compare_pair
from .render import render_matrix
from .repetition import RepetitionPolicy, RepetitionResult, run_repetition_recovery
from .report import build_report
from .scenario import N_PER_FAULT, Trial, build_trials

__all__ = [
    "CeilingPolicy",
    "CeilingResult",
    "run_with_ceilings",
    "RepetitionPolicy",
    "RepetitionResult",
    "run_repetition_recovery",
    "FAULTS",
    "MECHANISMS",
    "N_PER_FAULT",
    "Trial",
    "build_trials",
    "compare_pair",
    "build_matrix",
    "build_report",
    "render_matrix",
]
