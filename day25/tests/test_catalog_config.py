"""Incident specification, configuration, and source-provenance gates."""
from dataclasses import replace
from pathlib import Path

import pytest

from faultline_postmortem import (
    INCIDENTS,
    canonical_config,
    get_incident,
)


def test_catalog_has_two_complete_unique_incidents():
    assert len(INCIDENTS) == 2
    assert len({item.incident_id for item in INCIDENTS}) == 2
    assert len({item.seed for item in INCIDENTS}) == 2
    for item in INCIDENTS:
        assert item.impact
        assert item.detection
        assert item.root_cause
        assert item.contributing_factors
        assert item.corrective_actions
        assert item.regression_test_id
        assert item.regression_predicate


def test_unknown_incident_is_refused():
    with pytest.raises(ValueError, match="unknown incident"):
        get_incident("INC-25-999")


def test_config_rejects_invalid_envelopes():
    config = canonical_config()
    with pytest.raises(ValueError, match="positive"):
        replace(config, cascade_cost_budget=0).validate()
    with pytest.raises(ValueError, match="before the deadline"):
        replace(config, hedge_start_latency=45).validate()
    with pytest.raises(ValueError, match="fit the deadline"):
        replace(config, hedge_completion_latency=46).validate()


def test_source_artifacts_exist():
    root = Path(__file__).resolve().parents[2]
    for incident in INCIDENTS:
        assert (root / incident.source_artifact).is_file()


def test_source_evidence_matches_frozen_days(postmortem_report):
    sources = postmortem_report["source_evidence"]
    assert sources["INC-25-001"]["matched"]
    assert sources["INC-25-001"]["seed"] == 2026080207
    assert sources["INC-25-002"]["matched"]
    assert sources["INC-25-002"]["latency_budget_abort_count"] == 105
