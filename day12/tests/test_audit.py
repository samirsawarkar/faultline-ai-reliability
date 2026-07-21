"""The reproducibility + ground-truth integrity audit passes for all six faults."""
from __future__ import annotations

from faultline_catalog import canonical_trace, run_audit


def test_audit_passes_end_to_end():
    a = run_audit()
    assert a["audit_passed"] is True


def test_all_faults_reproduce_byte_identically():
    a = run_audit()
    assert a["all_reproducible"] is True
    assert a["catalog_reproducible"] is True


def test_no_label_leakage_across_the_catalog():
    a = run_audit()
    assert a["no_label_leakage"] is True
    assert all(v == [] for v in a["label_leaks"].values())


def test_all_cards_complete_and_scored_vs_truth():
    a = run_audit()
    assert a["all_cards_complete"] is True
    assert a["all_detectors_scored_vs_truth"] is True


def test_canonical_trace_is_labelled_and_gapless():
    for fid in ("F1", "F2", "F3", "F4", "F5", "F6"):
        pack = canonical_trace(fid)
        spans = pack["trace"]["spans"]
        assert spans and all(s["end_seq"] is not None for s in spans)   # complete spans
        assert pack["ground_truth"]["count"] >= 1                        # labelled
