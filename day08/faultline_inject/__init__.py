"""FAULTLINE Day 8: reproducible fault injection with independent ground truth.

Public surface:
    FaultSpec, MODES, TRIGGERS, SPEC_VERSION   the 10-field fault contract
    fires, component_matches                   deterministic triggers (the WHEN)
    apply_fault, InjectedFaultError            deterministic effects (the WHAT)
    InjectingChannel, DemoChannel, digest      the boundary wrapper
    GroundTruthLog, TruthEntry, CLEAN_LABEL    out-of-band labels (independent)
    build_report, assert_deterministic,
      leakage_scan, run_boundary, default_calls  injection integrity
"""
from .boundary import DemoChannel, InjectingChannel, digest
from .faults import InjectedFaultError, apply_fault
from .integrity import (
    assert_deterministic,
    build_report,
    default_calls,
    leakage_scan,
    run_boundary,
)
from .spec import MODES, SPEC_VERSION, TRIGGERS, FaultSpec
from .triggers import component_matches, fires
from .truth import CLEAN_LABEL, GroundTruthLog, TruthEntry

__all__ = [
    "FaultSpec",
    "MODES",
    "TRIGGERS",
    "SPEC_VERSION",
    "fires",
    "component_matches",
    "apply_fault",
    "InjectedFaultError",
    "InjectingChannel",
    "DemoChannel",
    "digest",
    "GroundTruthLog",
    "TruthEntry",
    "CLEAN_LABEL",
    "build_report",
    "assert_deterministic",
    "leakage_scan",
    "run_boundary",
    "default_calls",
]
