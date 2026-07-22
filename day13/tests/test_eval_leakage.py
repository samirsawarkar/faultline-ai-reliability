"""Immutable eval results + the leakage controls and the two attacks.

Fail condition: dataset versions, splits, or leakage controls are ambiguous.
These tests show each is unambiguous and enforced.
"""
from __future__ import annotations

import dataclasses

from faultline_eval import (
    attempt_stale_reuse,
    attempt_train_test_contamination,
    audit,
    build_dataset,
    evaluate,
    label_leakage_check,
    split_disjoint,
    validate_result,
)


def test_eval_result_is_immutable_and_bound_to_versions():
    ds = build_dataset()
    r = evaluate(ds, "test")
    assert r.dataset_version == ds.version
    assert r.code_version and r.result_id
    with __import__("pytest").raises(dataclasses.FrozenInstanceError):
        r.sample_count = 0  # type: ignore[misc]


def test_eval_is_deterministic():
    ds = build_dataset()
    assert evaluate(ds, "test").to_dict() == evaluate(ds, "test").to_dict()


def test_result_is_fresh_against_its_own_dataset():
    ds = build_dataset()
    assert validate_result(evaluate(ds, "test"), ds) == "fresh"


def test_train_test_contamination_is_detected():
    a = attempt_train_test_contamination(build_dataset())
    assert a["clean_before"] is True
    assert a["detected_after"] is True and a["leaked_ids"]


def test_stale_result_reuse_is_blocked():
    a = attempt_stale_reuse(build_dataset())
    assert a["versions_differ"] is True
    assert a["result_verdict_on_v1"] == "fresh"
    assert a["result_verdict_on_v2"] == "stale"
    assert a["stale_reuse_blocked"] is True


def test_no_label_leakage():
    assert label_leakage_check(build_dataset())["no_label_leakage"] is True


def test_split_disjoint_and_full_audit_passes():
    ds = build_dataset()
    assert split_disjoint(ds) is True
    assert audit(ds)["passed"] is True
