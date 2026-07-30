"""Checkpoint 28 and the fail condition are executable."""
from copy import deepcopy

from faultline_publication import audit_publication, build_checkpoint, build_figures
from faultline_publication.evidence import EVIDENCE, load_json


def test_checkpoint_28_passes():
    checkpoint = build_checkpoint(audit_publication(), build_figures())
    assert checkpoint["checkpoint"] == 28
    assert checkpoint["figure_count"] == 5
    assert checkpoint["claim_count"] == 29
    assert checkpoint["passed"] is True
    assert checkpoint["fail_condition_triggered"] is False


def test_fail_condition_flips_when_claim_audit_fails():
    audit = deepcopy(audit_publication())
    audit["passed"] = False
    checkpoint = build_checkpoint(audit, build_figures())
    assert checkpoint["checks"]["fail_condition_not_triggered"] is False
    assert checkpoint["passed"] is False
    assert checkpoint["fail_condition_triggered"] is True


def test_committed_checkpoint_matches_live_checkpoint():
    expected = build_checkpoint(audit_publication(), build_figures())
    assert load_json(EVIDENCE / "checkpoint_28.json") == expected
