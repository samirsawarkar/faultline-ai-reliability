"""The mixed classifier's boundary + the circuit-breaker signal."""
from __future__ import annotations

from faultline_contracts import (
    INVARIANT_VIOLATION,
    MALFORMED,
    OK,
    PROVIDER_ERROR,
    apply_corruption,
    classify,
    invariant_detect,
    oracle,
    provider_error_detect,
    run_breaker,
)
from faultline_contracts.oracle import expected_output

COMP = "tool.retrieve"
PAYLOAD = {"step": "retrieve", "index": 3}


def clean():
    return expected_output(COMP, PAYLOAD)


def test_classify_precedence_and_boundary():
    assert classify(True, None) == PROVIDER_ERROR                    # explicit error wins
    assert classify(False, apply_corruption("malformed_range", 2, clean())) == MALFORMED
    assert classify(False, apply_corruption("nonmultiple", 2, clean())) == INVARIANT_VIOLATION
    # the escapes: schema-valid, invariant-respecting -> classified OK
    assert classify(False, apply_corruption("drift_value", 2, clean())) == OK
    assert classify(False, apply_corruption("offbase_tokens", 2, clean())) == OK
    assert classify(False, clean()) == OK


def test_escapes_are_classified_ok_but_are_actually_wrong():
    for kind in ("drift_value", "offbase_tokens"):
        out = apply_corruption(kind, 2, clean())
        assert classify(False, out) == OK                 # detector says fine
        assert not oracle.is_correct(COMP, PAYLOAD, out)  # oracle says wrong


def test_invariant_detects_nonmultiple_only():
    assert invariant_detect(apply_corruption("nonmultiple", 2, clean())).ok is False
    assert invariant_detect(apply_corruption("drift_value", 2, clean())).ok is True
    assert invariant_detect(clean()).ok is True


def test_provider_error_detector_is_explicit():
    assert provider_error_detect(True) is True
    assert provider_error_detect(False) is False


def test_breaker_opens_at_threshold_and_stays_open():
    flags = [False, True, False, True, False, False]      # errors at 1 and 3
    tr = run_breaker(flags, window=3, threshold=2)         # 2 errors within seq1..3
    assert tr.opened_at == 3
    assert tr.states[3:] == ["open"] * (len(flags) - 3)
    assert tr.states[:3] == ["closed", "closed", "closed"]


def test_breaker_stays_closed_below_threshold():
    tr = run_breaker([False, True, False, False, True], window=2, threshold=2)
    assert tr.opened_at is None
    assert all(s == "closed" for s in tr.states)
