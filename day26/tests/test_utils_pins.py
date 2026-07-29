"""Low-level deterministic helpers and exact pin contracts."""
import json
from pathlib import Path

import pytest

from faultline_repro import (
    audit_container_contract,
    audit_pins,
    canonical_digest,
    json_pointer,
)

ROOT = Path(__file__).resolve().parents[2]


def test_json_pointer_resolves_dicts_lists_and_escaped_tokens():
    document = {"a/b": [{"~key": 7}]}
    assert json_pointer(document, "/a~1b/0/~0key") == 7


def test_json_pointer_refuses_relative_syntax():
    with pytest.raises(ValueError, match="begin"):
        json_pointer({"value": 1}, "value")


def test_canonical_digest_ignores_mapping_insertion_order():
    assert canonical_digest({"a": 1, "b": 2}) == canonical_digest(
        {"b": 2, "a": 1}
    )


def test_every_runtime_dependency_action_and_image_is_exactly_pinned():
    audit = audit_pins()
    assert audit["passed"]
    assert all(audit["checks"].values())


def test_seed_pins_match_frozen_result_artifacts():
    pins = json.loads((ROOT / "day26/pins.json").read_text())
    day07 = json.loads((ROOT / "day07/evidence/q1_results.json").read_text())
    day21 = json.loads(
        (ROOT / "day21/evidence/availability_quality_comparison.json").read_text()
    )
    day24 = json.loads(
        (ROOT / "day24/evidence/policy_comparison.json").read_text()
    )
    day25 = json.loads(
        (ROOT / "day25/evidence/incident_reports.json").read_text()
    )
    assert pins["seeds"]["day07_q1_master"] == day07["config"]["master_seed"]
    assert (
        pins["seeds"]["day21_q4_base"]
        == day21["params"]["seed_base"]
    )
    assert pins["seeds"]["day24_q5_base"] == day24["config"]["seed_base"]
    assert pins["seeds"]["day25_incidents"] == sorted(
        report["seed"] for report in day25.values()
    )


def test_dockerfile_matches_the_pinned_clean_build_contract():
    audit = audit_container_contract()
    assert audit["passed"]
    assert all(audit["checks"].values())
