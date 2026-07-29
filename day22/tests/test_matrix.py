"""The 6×6 paired experiment and its outcome/cost/latency contract."""
from __future__ import annotations

import faultline_recovery_matrix as rm


def test_matrix_has_all_36_mechanism_fault_cells():
    matrix = rm.build_matrix()
    assert matrix["design"]["cells"] == 36
    assert len(matrix["cells"]) == 36
    assert {cell["mechanism"] for cell in matrix["cells"]} == set(rm.MECHANISMS)
    assert {cell["fault"] for cell in matrix["cells"]} == set(rm.FAULTS)


def test_every_cell_has_aligned_paired_outcome_cost_latency_evidence():
    matrix = rm.build_matrix()
    for cell in matrix["cells"]:
        paired = cell["paired"]
        assert paired["n"] == 24
        assert paired["same_seed_population"] is True
        assert "success_mcnemar" in paired
        assert "availability_mcnemar" in paired
        assert "cost_delta" in paired
        assert "latency_delta" in paired
        assert cell["paired_evidence_complete"] is True


def test_each_mechanism_has_aggregate_paired_evidence():
    matrix = rm.build_matrix()
    for mechanism in rm.MECHANISMS:
        summary = matrix["mechanism_summaries"][mechanism]
        assert summary["paired"]["n"] == 144
        assert summary["paired"]["same_seed_population"] is True
        assert summary["with_mechanism"]["n"] == 144


def test_narrow_mechanisms_help_their_target_faults():
    matrix = rm.build_matrix()
    cells = {
        (cell["mechanism"], cell["fault"]): cell for cell in matrix["cells"]
    }
    assert cells[("M1_repair_retry", "F1")]["paired"]["outcome_recoveries"] == 12
    assert cells[("M2_timeout_backoff", "F2")]["paired"]["outcome_recoveries"] == 12
    assert cells[("M4_provider_fallback", "F4")]["paired"]["outcome_recoveries"] == 12
    assert cells[("M6_repetition_recovery", "F6")]["paired"]["outcome_recoveries"] == 12


def test_m5_contains_f6_and_m3_cuts_provider_calls_at_a_cost():
    matrix = rm.build_matrix()
    cells = {
        (cell["mechanism"], cell["fault"]): cell for cell in matrix["cells"]
    }
    m5 = cells[("M5_step_cost_ceilings", "F6")]
    assert m5["with_mechanism"]["contained"]["count"] >= 18
    assert m5["paired"]["cost_delta"]["mean"] < 0
    m3 = cells[("M3_circuit_breaker", "F4")]
    assert m3["paired"]["cost_delta"]["mean"] < 0
    assert "false_open_blocked_healthy" in m3["recovery_induced_harms"]["by_type"]


def test_every_recovery_induced_harm_is_measured_and_reconciled():
    matrix = rm.build_matrix()
    audit = matrix["recovery_induced_harm_audit"]
    assert audit["all_mechanisms_measured"] is True
    assert audit["all_harms_surfaced"] is True
    assert audit["cell_total_reconciles"] is True
    for mechanism in rm.MECHANISMS:
        assert audit["by_mechanism"][mechanism]["count"] > 0


def test_matrix_is_deterministic():
    assert rm.build_matrix() == rm.build_matrix()
