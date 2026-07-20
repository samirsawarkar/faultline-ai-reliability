"""Scoring against truth + the false-negative analysis (the mission's fail cond.).

Fail condition: schema-valid semantic corruption is treated as detected without
evidence. These tests prove the opposite — the escapes are counted as MISSES and
shipped with oracle evidence.
"""
from __future__ import annotations

from faultline_contracts import (
    build_report,
    escaped_false_negatives,
    per_kind_detection,
    score_detection,
    severity_invariance,
)
from faultline_contracts.experiment import f3_specs, f4_specs
from faultline_contracts.runner import run_contracts

SEED = 20260720


def test_report_is_deterministic():
    assert build_report() == build_report()


def test_schema_valid_escapes_are_counted_as_false_negatives_not_detections():
    obs, truth, _ = run_contracts(f3_specs(), SEED)
    conf = score_detection(obs, truth, "F3")
    # 5 F3 faults: 3 caught (2 malformed + 1 nonmultiple), 2 escape (drift/offbase)
    assert conf.tp == 3 and conf.fn == 2
    assert conf.recall < 1.0                      # escapes are NOT counted as caught
    assert conf.precision == 1.0                  # nothing clean is flagged


def test_escaped_false_negatives_are_wrong_and_undetected_with_evidence():
    obs, truth, _ = run_contracts(f3_specs(), SEED)
    escapes = escaped_false_negatives(obs, truth)
    kinds = {e["injected_kind"] for e in escapes}
    assert kinds == {"drift_value", "offbase_tokens"}
    for e in escapes:
        assert e["classifier_class"] == "ok"      # detector said fine
        assert e["schema_valid"] is True
        assert e["invariant_ok"] is True
        assert e["oracle_verdict"] == "wrong"     # oracle proves it wrong
        assert e["diff"]                          # concrete expected-vs-got evidence


def test_provider_errors_are_fully_detected():
    obs, truth, _ = run_contracts(f4_specs(), SEED)
    conf = score_detection(obs, truth, "F4")
    assert conf.recall == 1.0 and conf.precision == 1.0


def test_escape_is_severity_invariant():
    inv = severity_invariance()
    for kind in ("drift_value", "offbase_tokens"):
        assert all(rate == 0.0 for rate in inv[kind].values())   # never caught
    for kind in ("malformed_range", "malformed_tokens", "nonmultiple"):
        assert all(rate == 1.0 for rate in inv[kind].values())   # always caught


def test_per_kind_detection_partitions_correctly():
    obs, truth, _ = run_contracts(f3_specs(), SEED)
    pk = per_kind_detection(obs, truth)
    assert pk["drift_value"]["detection_rate"] == 0.0
    assert pk["malformed_range"]["detection_rate"] == 1.0
