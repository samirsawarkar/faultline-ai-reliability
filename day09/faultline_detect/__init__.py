"""FAULTLINE Day 9: F1/F2 fault families with deterministic detectors + scoring.

Builds on Day 8's injector (faultline_inject). Public surface:
    schema:     validate_output, is_valid, Violation, VALUE_MIN/MAX, TOKENS_LEN
    injectors:  f1_corruption_spec, f2_latency_spec, F1_MODES, F2_MODE, is_f1, is_f2
    latency:    BASE_LATENCY, DEFAULT_BUDGET, duration, breaches_budget
    detectors:  schema_detect, duration_detect, SchemaSignal, DurationSignal
    runner:     run, Observation
    score:      Confusion, score, schema_positives, duration_positives,
                truth_is_f1, truth_is_f2
    experiment: sweep_f1, sweep_f2, f2_budget_sensitivity, specificity, build_report
    cards:      fault_cards
"""
from .cards import fault_cards
from .detectors import (
    DurationSignal,
    SchemaSignal,
    duration_detect,
    schema_detect,
)
from .experiment import (
    build_report,
    f2_budget_sensitivity,
    specificity,
    sweep_f1,
    sweep_f2,
)
from .injectors import (
    F1_MODES,
    F2_MODE,
    f1_corruption_spec,
    f2_latency_spec,
    is_f1,
    is_f2,
)
from .latency import BASE_LATENCY, DEFAULT_BUDGET, breaches_budget, duration
from .runner import Observation, run
from .schema import TOKENS_LEN, VALUE_MAX, VALUE_MIN, Violation, is_valid, validate_output
from .score import (
    Confusion,
    duration_positives,
    schema_positives,
    score,
    truth_is_f1,
    truth_is_f2,
)

__all__ = [
    "validate_output", "is_valid", "Violation", "VALUE_MIN", "VALUE_MAX", "TOKENS_LEN",
    "f1_corruption_spec", "f2_latency_spec", "F1_MODES", "F2_MODE", "is_f1", "is_f2",
    "BASE_LATENCY", "DEFAULT_BUDGET", "duration", "breaches_budget",
    "schema_detect", "duration_detect", "SchemaSignal", "DurationSignal",
    "run", "Observation",
    "Confusion", "score", "schema_positives", "duration_positives",
    "truth_is_f1", "truth_is_f2",
    "sweep_f1", "sweep_f2", "f2_budget_sensitivity", "specificity", "build_report",
    "fault_cards",
]
