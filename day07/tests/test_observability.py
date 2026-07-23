"""Observability gate: every run backed by a complete record; gaps are caught."""
from __future__ import annotations

import copy

import pytest

from faultline_hops import (
    SweepConfig,
    build_curves,
    check_gate,
    investigate_divergence,
    run_sweep,
)
from faultline_hops.observability import ObservabilityGateError


def test_gate_passes_on_clean_sweep():
    sweep = run_sweep(SweepConfig())
    g = check_gate(sweep)
    assert g["gate_passed"] is True
    assert g["trace_gaps"] == 0
    assert g["runs"] == g["runs_expected"]


def test_gate_detects_missing_run():
    sweep = run_sweep(SweepConfig(trials=50, max_hops=4))
    sweep.runs.pop()  # drop a run -> count mismatch
    with pytest.raises(ObservabilityGateError):
        check_gate(sweep)


def test_gate_detects_hop_record_gap():
    sweep = run_sweep(SweepConfig(trials=50, max_hops=4))
    victim = copy.copy(sweep.runs[0])
    victim.hops_reached = victim.hops_reached + 1  # claim a hop with no record
    sweep.runs[0] = victim
    with pytest.raises(ObservabilityGateError):
        check_gate(sweep)


def test_divergence_investigation_has_traced_examples_without_gaps():
    sweep = run_sweep(SweepConfig())
    curves = build_curves(sweep)
    inv = investigate_divergence(sweep, curves)
    assert inv["divergence_hop"] is not None
    assert inv["trace_gaps_in_examples"] == 0
    assert inv["example_fail"]["success"] is False
    assert inv["example_pass"]["success"] is True
    assert inv["example_fail"]["spans_complete"] is True
