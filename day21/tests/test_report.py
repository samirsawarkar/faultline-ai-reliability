"""Q4 report, paired inference, and the mission fail-condition gate."""
from __future__ import annotations

import faultline_fallback_quality as fq


def test_paired_availability_and_counterfactual_quality_differences_are_significant():
    tests = fq.build_report()["comparison"]["paired_tests"]
    assert tests["availability_primary_vs_fallback_enabled"]["significant_at_0.05"] is True
    quality = tests["expected_primary_vs_fallback_quality_on_outage_slice"]
    assert quality["table"]["a_only"] == 30
    assert quality["significant_at_0.05"] is True


def test_q4_report_is_deterministic():
    assert fq.build_report() == fq.build_report()


def test_fail_condition_requires_fallback_quality_next_to_availability():
    report = fq.build_report()
    gate = report["fail_condition_guard"]
    assert gate["availability_reported"] is True
    assert gate["fallback_quality_measured"] is True
    assert gate["quality_and_availability_reported_together"] is True
    assert gate["judge_used_for_core_scoring"] is False
    assert gate["passed"] is True


def test_q4_findings_include_explicit_judge_caveats():
    report = fq.build_report()
    caveats = " ".join(report["q4_findings"]["judge_caveats"]).lower()
    assert "not validated for standalone use" in caveats
    assert "forbidden from core success scoring" in caveats
    assert "borderline_tokens" in caveats
    assert report["q4_findings"]["answer"] == "yes_in_this_experiment"
