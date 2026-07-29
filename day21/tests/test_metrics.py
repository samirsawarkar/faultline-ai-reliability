"""Paired scenario, denominator discipline, quality, and provenance metrics."""
from __future__ import annotations

import faultline_fallback_quality as fq


def test_paired_records_share_every_seed_and_are_deterministic():
    first = fq.build_paired_records()
    second = fq.build_paired_records()
    assert first == second
    assert len(first["primary_only"]) == len(first["fallback_enabled"]) == 120
    assert [r["seed"] for r in first["primary_only"]] == [
        r["seed"] for r in first["fallback_enabled"]
    ]


def test_availability_and_quality_denominators_are_both_reported():
    paired = fq.build_paired_records()
    primary = fq.summarize(paired["primary_only"])
    fallback = fq.summarize(paired["fallback_enabled"])
    assert primary["availability"]["rate"] == 0.6667
    assert fallback["availability"]["rate"] == 1.0
    assert primary["strict_quality_given_answered"]["rate"] == 1.0
    assert fallback["strict_quality_given_answered"]["rate"] == 0.75
    assert primary["strict_quality_service_rate"]["rate"] == 0.6667
    assert fallback["strict_quality_service_rate"]["rate"] == 0.75


def test_fallback_quality_is_measured_not_inferred_from_availability():
    records = fq.build_paired_records()["fallback_enabled"]
    metrics = fq.summarize(records)
    quality = metrics["fallback_quality"]
    assert quality["fallback_answers"] == 40
    assert quality["strictly_acceptable"]["count"] == 10
    assert quality["silently_degraded"]["count"] == 30
    assert quality["flagged_degraded"]["count"] == 0


def test_provenance_is_complete_and_consistent_despite_silent_bad_answers():
    records = fq.build_paired_records()["fallback_enabled"]
    metrics = fq.summarize(records)
    assert metrics["provenance"]["complete"]["rate"] == 1.0
    assert metrics["provenance"]["consistent"]["rate"] == 1.0
    assert metrics["provenance"]["fallback_rate"]["rate"] == 0.3333
    assert all(fq.provenance_consistent(record) for record in records)
