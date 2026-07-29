"""Attacks, composition conclusion, and Checkpoint-22 fail-condition gates."""
from __future__ import annotations

import faultline_recovery_matrix as rm


def test_attacks_surface_ceiling_and_repetition_failure_modes():
    report = rm.build_report()
    ceilings = report["attacks"]["ceilings"]
    repetition = report["attacks"]["repetition"]
    assert ceilings["all_bounds_hold"] is True
    assert repetition["transient_recovers"] is True
    assert repetition["persistent_terminates_bounded"] is True
    assert repetition["false_positive_surfaced"] is True


def test_fail_condition_guard_rejects_no_cell_or_harm():
    report = rm.build_report()
    gate = report["matrix"]["fail_condition_guard"]
    assert gate["observed_cells"] == gate["expected_cells"] == 36
    assert gate["unpaired_cells"] == []
    assert gate["every_mechanism_has_paired_evidence"] is True
    assert gate["every_mechanism_has_harm_audit"] is True
    assert gate["every_cell_has_outcome_cost_latency"] is True
    assert gate["all_recovery_induced_harms_measured"] is True
    assert gate["passed"] is True


def test_checkpoint_22_passes_all_requirements():
    checkpoint = rm.build_report()["checkpoint_22"]
    assert checkpoint == {
        "six_mechanism_matrix_complete": True,
        "paired_evidence_complete": True,
        "new_failures_measured": True,
        "ceilings_hold": True,
        "passed": True,
    }


def test_report_and_render_are_deterministic():
    first = rm.build_report()
    second = rm.build_report()
    assert first == second
    assert rm.render_matrix(first) == rm.render_matrix(second)
