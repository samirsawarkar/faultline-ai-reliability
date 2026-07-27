"""Subgroup slicing, the min-sample + multiple-comparison gate, and Holm."""
from __future__ import annotations

import faultline_subgroups as sg
from faultline_subgroups.gate import MIN_SAMPLES, holm_bonferroni, one_proportion_p


def test_min_sample_flags_small_subgroups():
    rows = [{"g": "x", "correct": True}] * 3 + [{"g": "y", "correct": True}] * 6
    sub = {s["dims"]["g"]: s for s in sg.slice_by(rows, ["g"])}
    assert sub["x"]["reportable"] is False and sub["x"]["insufficient"] is True
    assert sub["y"]["reportable"] is True
    assert MIN_SAMPLES == 5


def test_holm_is_step_down_and_conservative():
    # one tiny p among many large ones: only the tiny one may survive
    ps = [0.001, 0.2, 0.3, 0.4, 0.5]
    rej = holm_bonferroni(ps, alpha=0.05)
    assert rej[0] is True and not any(rej[1:])
    # all large -> none rejected
    assert holm_bonferroni([0.2, 0.3, 0.4]) == [False, False, False]


def test_one_proportion_p_is_small_for_a_clear_difference():
    assert one_proportion_p(20, 20, 0.5) < 0.001     # 100% vs 50% with n=20
    assert one_proportion_p(10, 20, 0.5) == 1.0       # 50% vs 50% -> no difference


def test_ci_contradiction_requires_interval_to_exclude_headline():
    # a subgroup at 1.0 (n=18) excludes a 0.5 headline; a subgroup at 0.6 (n=5) does not
    gated = sg.apply_gate(
        [{"dims": {"a": 1}, **sg.subgroup_rate(18, 18)},
         {"dims": {"a": 2}, **sg.subgroup_rate(3, 5)}], headline_rate=0.5)
    by = {s["dims"]["a"]: s for s in gated}
    assert by[1]["ci_excludes_headline"] is True
    assert by[2]["ci_excludes_headline"] is False


def test_slice_is_deterministic():
    rows = sg.detection_rows()
    assert sg.slice_by(rows, ["fault"]) == sg.slice_by(rows, ["fault"])
