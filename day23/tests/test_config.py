"""One seed + one validated configuration defines the incident."""
from __future__ import annotations

import pytest

import faultline_cascade as fc


def test_canonical_config_is_serializable_and_valid():
    config = fc.canonical_config()
    assert config.validate() is config
    assert config.to_dict()["initiating_fault"] == "F2:primary_latency_spike"
    assert config.to_dict()["scenario_version"] == "1.0.0"


def test_config_rejects_invalid_bounds_and_breaker():
    with pytest.raises(ValueError):
        fc.CascadeConfig(total_cost_budget=0).validate()
    with pytest.raises(ValueError):
        fc.CascadeConfig(
            breaker_failure_threshold=3, breaker_window=2
        ).validate()


def test_non_triggering_seed_is_refused_not_relabelled_as_the_incident():
    with pytest.raises(ValueError):
        fc.run_cascade(20260802, fc.canonical_config())
