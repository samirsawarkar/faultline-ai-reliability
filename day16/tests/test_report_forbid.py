"""The validation verdict + the fail-condition guards.

Fail condition: the judge is used without validation against trusted human labels.
These tests prove the judge is validated first, forbidden from core scoring, and
that an unvalidated real judge cannot be used at all.
"""
from __future__ import annotations

import pytest

import faultline_judge as j


def test_report_is_deterministic():
    assert j.build_report() == j.build_report()


def test_judge_measured_against_human_ceiling_not_perfection():
    r = j.build_report()
    judge_k = r["judge_vs_human"]["cohen_kappa"]
    ceiling_k = r["human_ceiling_inter_rater"]["cohen_kappa"]
    assert judge_k < ceiling_k          # judge is below the human reliability ceiling
    assert 0.0 <= judge_k <= 1.0


def test_failure_slice_is_surfaced():
    r = j.build_report()
    assert "borderline_tokens" in r["failure_slices"]     # not hidden in an aggregate


def test_judge_is_forbidden_from_core_scoring():
    r = j.build_report()
    assert r["verdict"]["forbidden_from_core_success_scoring"] is True
    # given moderate kappa + positional bias + a failure slice, it is not standalone-validated
    assert r["verdict"]["validated_for_standalone_use"] is False


def test_judge_card_states_the_prohibition():
    card = j.judge_card(j.build_report())
    assert "MUST NOT contribute to core success scoring" in card
    assert "oracle" in card.lower()


def test_real_judge_cannot_be_used_without_client_and_validation():
    with pytest.raises(NotImplementedError):
        j.RealJudgeAdapter().accept({"value": 10, "tokens": [0, 1, 2, 3]},
                                    {"value": 10, "tokens": [0, 1, 2, 3]})
