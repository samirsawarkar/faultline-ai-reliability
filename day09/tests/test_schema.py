"""The output schema catches structural corruption and passes clean output."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1].parent / "day08"))

from faultline_inject import DemoChannel

from faultline_detect import VALUE_MAX, is_valid, validate_output


def clean(i=0):
    return DemoChannel().call("tool.x", {"step": "retrieve", "index": i})


def test_clean_output_is_valid_for_every_default_index():
    for i in range(12):
        assert is_valid(clean(i)), f"clean output at index {i} should validate"


def test_value_out_of_range_is_caught():
    bad = clean(0)
    bad["value"] = VALUE_MAX + 1
    codes = [v.code for v in validate_output(bad)]
    assert "value_range" in codes


def test_short_and_long_token_lists_are_caught():
    short = clean(0); short["tokens"] = [0, 1, 2]
    long = clean(0); long["tokens"] = [0, 1, 2, 3, 4]
    assert "tokens_length" in [v.code for v in validate_output(short)]
    assert "tokens_length" in [v.code for v in validate_output(long)]


def test_non_consecutive_tokens_are_caught():
    bad = clean(0); bad["tokens"] = [0, 1, 3, 4]
    assert "tokens_not_consecutive" in [v.code for v in validate_output(bad)]


def test_empty_and_missing_fields():
    assert "bad_step" in [v.code for v in validate_output({"step": "", "value": 10, "tokens": [0, 1, 2, 3]})]
    assert validate_output("not-a-dict")[0].code == "not_an_object"
    assert validate_output(None)[0].code == "not_an_object"


def test_bool_is_not_an_int_value():
    bad = clean(0); bad["value"] = True
    assert "value_type" in [v.code for v in validate_output(bad)]
