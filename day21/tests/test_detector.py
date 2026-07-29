"""The validation-gated narrow judge and the silent-degradation attack."""
from __future__ import annotations

import pytest

import faultline_fallback_quality as fq
from faultline_judge import build_report as judge_report


def test_integration_refuses_missing_core_scoring_prohibition():
    validation = judge_report()
    validation["verdict"]["forbidden_from_core_success_scoring"] = False
    with pytest.raises(ValueError):
        fq.NarrowJudgeIntegration(validation=validation)


def test_integration_is_pointwise_advisory_and_not_core_scoring():
    policy = fq.NarrowJudgeIntegration().policy()
    assert policy["mode"] == "pointwise_only"
    assert policy["validated_for_standalone_use"] is False
    assert policy["forbidden_from_core_success_scoring"] is True
    assert policy["judge_contributes_to_core_success"] is False
    assert "borderline_tokens" in policy["known_failure_slices"]


def test_detector_reproduces_known_judge_failure_slice():
    records = fq.build_paired_records()["fallback_enabled"]
    scored = fq.score_detector(records)
    assert scored["confusion"] == {"tp": 20, "fp": 0, "fn": 10, "tn": 10}
    assert scored["recall"]["rate"] == 0.6667
    assert scored["precision"]["rate"] == 1.0
    assert {item["variant"] for item in scored["false_negatives"]} == {
        "borderline_tokens"
    }


def test_every_detector_false_negative_is_surfaced():
    scored = fq.score_detector(fq.build_paired_records()["fallback_enabled"])
    assert scored["all_false_negatives_surfaced"] is True
    assert len(scored["false_negatives"]) == scored["confusion"]["fn"]


def test_availability_only_monitor_is_fooled_but_quality_detector_fires():
    report = fq.build_report()
    attack = report["silent_degradation_attack"]
    assert attack["system_availability"] == 1.0
    assert attack["availability_only_monitor"]["alerts"] == 0
    assert attack["availability_only_monitor"]["fooled"] is True
    assert attack["degraded_flag_only_monitor"]["alerts"] == 0
    assert attack["degraded_flag_only_monitor"]["fooled"] is True
    assert attack["quality_detector"]["bad_answers_seen"] == 20
    assert attack["quality_detector"]["bad_answers_missed"] == 10
    assert attack["known_caveat_reproduced"] is True
