"""FAULTLINE Day 10: F3/F4 — schema-valid wrong data vs explicit provider errors.

Builds on Day 8 (injection truth) and Day 9 (schema detector + scoring).

Public surface:
    oracle:     expected_output, is_correct, diff
    spec:       ContractFaultSpec, F3_KINDS, F4_KINDS, F3_SCHEMA_VALID
    corruption: apply_corruption, ProviderError
    runner:     run_contracts, Observation
    detectors:  classify, invariant_detect, provider_error_detect, detected_faulty,
                CLASSES (OK/PROVIDER_ERROR/MALFORMED/INVARIANT_VIOLATION)
    breaker:    run_breaker, BreakerTrace
    score:      score_detection, escaped_false_negatives, per_kind_detection,
                classifier_positives, truth_is_f3, truth_is_f4
    experiment: build_report, mixed_specs, severity_invariance, classifier_boundaries
    cards:      fault_cards
"""
from . import oracle
from .breaker import BreakerTrace, run_breaker
from .cards import fault_cards
from .corruption import ProviderError, apply_corruption
from .detectors import (
    CLASSES,
    INVARIANT_VIOLATION,
    MALFORMED,
    OK,
    PROVIDER_ERROR,
    classify,
    detected_faulty,
    invariant_detect,
    provider_error_detect,
)
from .experiment import (
    build_report,
    classifier_boundaries,
    mixed_specs,
    severity_invariance,
)
from .runner import Observation, run_contracts
from .score import (
    classifier_positives,
    escaped_false_negatives,
    per_kind_detection,
    score_detection,
    truth_is_f3,
    truth_is_f4,
)
from .spec import (
    ALL_KINDS,
    F3_KINDS,
    F3_SCHEMA_VALID,
    F4_KINDS,
    ContractFaultSpec,
)

__all__ = [
    "oracle",
    "ContractFaultSpec", "F3_KINDS", "F4_KINDS", "F3_SCHEMA_VALID", "ALL_KINDS",
    "apply_corruption", "ProviderError",
    "run_contracts", "Observation",
    "classify", "invariant_detect", "provider_error_detect", "detected_faulty",
    "CLASSES", "OK", "PROVIDER_ERROR", "MALFORMED", "INVARIANT_VIOLATION",
    "run_breaker", "BreakerTrace",
    "score_detection", "escaped_false_negatives", "per_kind_detection",
    "classifier_positives", "truth_is_f3", "truth_is_f4",
    "build_report", "mixed_specs", "severity_invariance", "classifier_boundaries",
    "fault_cards",
]
