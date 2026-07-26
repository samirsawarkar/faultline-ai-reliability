"""Rubric, validation set, and the agreement/bias metrics (with a known-value check)."""
from __future__ import annotations

import faultline_judge as j


def test_validation_set_shape_and_labels():
    data = j.items()
    assert len(data) == 24
    slices = {}
    for it in data:
        slices.setdefault(it["slice"], 0)
        slices[it["slice"]] += 1
        assert it["human_label"] in ("accept", "reject")
        assert "reference" in it and "candidate" in it
    assert slices == {"clear_accept": 6, "clear_reject": 6,
                      "borderline_tokens": 6, "borderline_extra": 6}


def test_rubric_gold_matches_authored_human_labels():
    # the trusted labels must be exactly the strict rubric applied
    for it in j.items():
        expected = "accept" if j.gold_acceptable(it["reference"], it["candidate"]) else "reject"
        assert it["human_label"] == expected


def test_cohen_kappa_known_value():
    a = ["accept", "accept", "reject", "reject"]
    b = ["accept", "reject", "reject", "reject"]
    # po=0.75, pe=0.5 -> kappa=0.5
    assert abs(j.cohen_kappa(a, b) - 0.5) < 1e-9


def test_raw_agreement_and_kappa_bounds():
    same = ["accept"] * 5
    assert j.raw_agreement(same, same) == 1.0
    assert j.cohen_kappa(same, same) == 1.0


def test_judge_is_blind_to_the_human_label():
    # the judge never receives the label; flipping it cannot change the verdict
    it = j.items()[0]
    v1 = j.SimulatedJudge().accept(it["reference"], it["candidate"])
    it2 = dict(it); it2["human_label"] = "reject" if it["human_label"] == "accept" else "accept"
    v2 = j.SimulatedJudge().accept(it2["reference"], it2["candidate"])
    assert v1 == v2


def test_positional_bias_detector_recovers_a_known_bias():
    pairs = j.pairs()
    biased = j.positional_bias(pairs, j.SimulatedJudge(positional=True, first_preference=1.0).compare_positions)
    fair = j.positional_bias(pairs, j.SimulatedJudge(positional=False).compare_positions)
    assert biased["by_kind"]["close"]["bias_rate"] == 1.0   # known bias recovered
    assert biased["by_kind"]["clear"]["bias_rate"] == 0.0    # clear pairs unaffected
    assert fair["positional_bias_rate"] == 0.0               # control shows no bias
