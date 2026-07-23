"""The oracle judges correctness; corruptions are malformed or schema-valid-wrong."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1].parent / "day08"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1].parent / "day09"))

from faultline_detect.schema import VALUE_MIN, VALUE_MAX, is_valid

from faultline_contracts import F3_SCHEMA_VALID, apply_corruption, oracle
from faultline_contracts.oracle import expected_output

PAYLOAD = {"step": "retrieve", "index": 3}
COMP = "tool.retrieve"


def clean():
    return expected_output(COMP, PAYLOAD)


def test_oracle_accepts_clean_and_rejects_any_change():
    c = clean()
    assert oracle.is_correct(COMP, PAYLOAD, c)
    wrong = dict(c); wrong["value"] = c["value"] + 10
    assert not oracle.is_correct(COMP, PAYLOAD, wrong)
    assert oracle.diff(COMP, PAYLOAD, wrong)["value"] == {"expected": c["value"], "got": c["value"] + 10}


def test_malformed_kinds_break_the_schema():
    for kind in ("malformed_range", "malformed_tokens"):
        out = apply_corruption(kind, 2, clean())
        assert not is_valid(out), f"{kind} should be schema-invalid"
        assert F3_SCHEMA_VALID[kind] is False


def test_schema_valid_kinds_pass_the_schema_but_are_wrong():
    for kind in ("nonmultiple", "drift_value", "offbase_tokens"):
        out = apply_corruption(kind, 2, clean())
        assert F3_SCHEMA_VALID[kind] is True
        # nonmultiple is schema-valid too (in range int); all three pass schema
        assert is_valid(out), f"{kind} should be schema-valid"
        assert not oracle.is_correct(COMP, PAYLOAD, out), f"{kind} must be wrong"


def test_drift_value_is_a_different_in_range_round_ten():
    c = clean()
    out = apply_corruption("drift_value", 2, c)
    assert out["value"] != c["value"]
    assert VALUE_MIN <= out["value"] <= VALUE_MAX
    assert out["value"] % 10 == 0


def test_nonmultiple_is_not_a_round_ten():
    out = apply_corruption("nonmultiple", 2, clean())
    assert out["value"] % 10 != 0


def test_corruption_is_deterministic():
    a = apply_corruption("drift_value", 3, clean())
    b = apply_corruption("drift_value", 3, clean())
    assert a == b
