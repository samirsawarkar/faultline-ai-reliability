"""The 10-field fault specification: exactly ten fields, and every field guarded."""
from __future__ import annotations

import dataclasses

import pytest

from faultline_inject import FaultSpec, MODES, SPEC_VERSION, TRIGGERS


def a_spec(**over):
    base = dict(
        fault_id="F-01", component="tool.retrieve", mode="corrupt", severity=3,
        trigger="call_index", trigger_value="2", seed=7, rate=1.0,
        label="fault:corrupt", spec_version=SPEC_VERSION,
    )
    base.update(over)
    return FaultSpec(**base)


def test_spec_has_exactly_ten_fields():
    assert len(dataclasses.fields(FaultSpec)) == 10
    assert len(FaultSpec.FIELDS) == 10


def test_valid_spec_validates_and_roundtrips():
    s = a_spec().validate()
    assert FaultSpec.from_dict(s.to_dict()) == s


def test_from_dict_rejects_unknown_field():
    d = a_spec().to_dict()
    d["extra"] = "nope"
    with pytest.raises(ValueError):
        FaultSpec.from_dict(d)


@pytest.mark.parametrize("bad", [
    dict(mode="melt"),                 # unknown mode
    dict(trigger="whenever"),          # unknown trigger
    dict(severity=0), dict(severity=6),  # severity out of band
    dict(severity=True),               # bool is not a severity
    dict(rate=1.5),                    # rate out of band
    dict(fault_id=""), dict(component=""), dict(label=""),
    dict(spec_version="0.9"),          # version mismatch
    dict(trigger="every_n", trigger_value="0"),   # every_n needs >= 1
    dict(trigger="call_index", trigger_value="x"),  # not an int
    dict(trigger="input_match", trigger_value=""),  # empty prefix
])
def test_invalid_specs_are_rejected(bad):
    with pytest.raises(ValueError):
        a_spec(**bad).validate()


def test_deterministic_trigger_cannot_hide_behind_partial_rate():
    # a call_index fault with rate 0.5 is a contradiction: deterministic triggers
    # fire on a condition, not a fraction.
    with pytest.raises(ValueError):
        a_spec(trigger="call_index", trigger_value="2", rate=0.5).validate()


def test_probabilistic_trigger_allows_partial_rate():
    a_spec(trigger="probabilistic", trigger_value="", rate=0.5).validate()


def test_spec_is_frozen_and_hashable():
    s = a_spec()
    with pytest.raises(dataclasses.FrozenInstanceError):
        s.severity = 5  # type: ignore[misc]
    assert hash(s) == hash(a_spec())


def test_modes_and_triggers_are_closed_sets():
    assert set(MODES) == {"error", "corrupt", "truncate", "drop", "duplicate", "stall"}
    assert set(TRIGGERS) == {"call_index", "every_n", "input_match", "probabilistic"}
