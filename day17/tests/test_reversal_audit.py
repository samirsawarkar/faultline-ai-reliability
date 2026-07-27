"""Reversal detection + the audit that enforces the fail condition.

Fail condition: a subgroup contradicts the headline and is ignored. These tests
prove the reversal detector works, every contradiction is acknowledged, and the
audit FAILS the moment one is dropped.
"""
from __future__ import annotations

import copy

import faultline_subgroups as sg


def test_reversal_detector_recovers_known_simpson_paradox():
    v = sg.verify_reversal_detector()
    assert v["detector_recovers_known_paradox"] is True
    assert len(v["reversal_slices"]) == 2      # both slices reverse the aggregate


def test_real_det_vs_sem_reversal_is_found_and_surfaced():
    r = sg.build_report()
    rev = r["detection"]["deterministic_vs_semantic_reversal"]
    assert rev["has_reversal"] is True
    # aggregate deterministic >= semantic, but a severity slice reverses it
    assert rev["aggregate"]["order"] == "a>=b"
    assert any(s["order"] == "b>a" for s in rev["reversal_slices"])
    assert "reversal:severity=3" in r["contradictions_detected"]


def test_every_contradiction_is_acknowledged():
    r = sg.build_report()
    assert set(r["contradictions_detected"]) == set(r["contradictions_acknowledged"])
    assert sg.run_audit(r)["no_contradiction_ignored"] is True


def test_audit_fails_if_a_contradiction_is_ignored():
    r = sg.build_report()
    assert r["contradictions_acknowledged"], "expected at least one contradiction"
    tampered = copy.deepcopy(r)
    tampered["contradictions_acknowledged"].pop()      # silently drop one
    aud = sg.run_audit(tampered)
    assert aud["no_contradiction_ignored"] is False
    assert aud["audit_passed"] is False                # the gate has teeth


def test_gate_and_audit_pass_on_the_honest_report():
    r = sg.build_report()
    assert r["measurement_gate"]["passed"] is True
    assert sg.run_audit(r)["audit_passed"] is True


def test_low_severity_faults_are_surfaced_as_contradictions():
    # low-severity F1/F2 are systematically missed (below schema range / budget);
    # that subgroup failure must be surfaced, not hidden by the aggregate.
    r = sg.build_report()
    keys = r["contradictions_detected"]
    assert any("severity=1" in k for k in keys)
    assert "hop:1" in keys and "hop:2" in keys        # naive-overpredicts fails early
