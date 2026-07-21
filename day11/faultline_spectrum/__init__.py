"""FAULTLINE Day 11: F5/F6 — completing the six-fault spectrum.

F5 (context corruption, semantic detection) + F6 (loop exhaustion, deterministic
detection), plus the deterministic-vs-semantic map across F1-F6 and the Q2 split
hypothesis. Builds on Days 8 (truth), 9 (F1/F2 + scoring), 10 (F3/F4 + oracle).

Public surface:
    task:       run_task, is_correct, RunResult, M_STEPS, STEP_BUDGET, EXPECTED_*
    spec:       SpectrumFaultSpec, F5_KINDS, F6_KINDS, DETECTION_NATURE
    detectors:  repetition_detect, budget_detect, loop_detect, context_integrity_detect
    runner:     run_batch, RunObservation
    score:      score_f5, score_f6, semantic_escapes, f5_positives, f6_positives
    spectrum_map: build_map
    experiment: build_report, q2_split_hypothesis, f5_specs, f6_specs
    cards:      fault_cards
"""
from . import task
from .cards import fault_cards
from .detectors import (
    budget_detect,
    context_integrity_detect,
    loop_detect,
    repetition_detect,
)
from .experiment import build_report, f5_specs, f6_specs, q2_split_hypothesis
from .runner import RunObservation, run_batch
from .score import (
    f5_positives,
    f6_positives,
    score_f5,
    score_f6,
    semantic_escapes,
    truth_is_f5,
    truth_is_f6,
)
from .spec import (
    ALL_KINDS,
    DETECTION_NATURE,
    F5_KINDS,
    F6_KINDS,
    SpectrumFaultSpec,
)
from .spectrum_map import build_map
from .task import (
    EXPECTED_CONTEXT,
    EXPECTED_FINAL,
    M_STEPS,
    STEP_BUDGET,
    RunResult,
    is_correct,
    run_task,
)

__all__ = [
    "task", "run_task", "is_correct", "RunResult", "M_STEPS", "STEP_BUDGET",
    "EXPECTED_CONTEXT", "EXPECTED_FINAL",
    "SpectrumFaultSpec", "F5_KINDS", "F6_KINDS", "DETECTION_NATURE", "ALL_KINDS",
    "repetition_detect", "budget_detect", "loop_detect", "context_integrity_detect",
    "run_batch", "RunObservation",
    "score_f5", "score_f6", "semantic_escapes", "f5_positives", "f6_positives",
    "truth_is_f5", "truth_is_f6",
    "build_map",
    "build_report", "q2_split_hypothesis", "f5_specs", "f6_specs",
    "fault_cards",
]
