"""The cold-viewer proxy rejects dead weight and extracts the final proof."""
from pathlib import Path

import pytest

from faultline_brief.comprehension import (
    extract_proof,
    run_comprehension_attack,
    score_material,
)
from faultline_brief.evidence import DAY, load_json


@pytest.fixture(scope="module")
def report():
    return run_comprehension_attack()


def test_baseline_fails_and_final_passes(report):
    assert report["baseline"]["passed"] is False
    assert report["final"]["passed"] is True
    assert report["passed"] is True


def test_cold_viewer_can_state_what_faultline_proved(report):
    assert report["cold_viewer_can_state_what_faultline_proved"] is True
    assert report["final"]["answer"].startswith(
        "In one seeded simulator incident"
    )


@pytest.mark.parametrize(
    "concept_id",
    [
        "scope",
        "controlled_comparison",
        "before",
        "after",
        "fix",
        "boundary",
    ],
)
def test_every_comprehension_concept_passes(concept_id, report):
    assert report["final"]["concepts"][concept_id]["passed"] is True


def test_dead_weight_was_removed(report):
    removed = report["dead_weight_removed"]
    assert removed["baseline_failed"] is True
    assert removed["final_passed"] is True
    assert removed["words"] > 0
    assert removed["reading_seconds"] > 0


def test_proxy_limitation_is_honest(report):
    assert report["human_participant"] is False
    assert "not an empirical human usability study" in report["method_caveat"]


def test_missing_proof_statement_fails_closed(tmp_path):
    material = tmp_path / "no-proof.md"
    material.write_text("# Demo\n\nA trace exists, but no result is stated.\n")
    rubric = load_json(DAY / "comprehension_rubric.json")
    result = score_material(material, rubric)
    assert result["passed"] is False
    assert result["checks"]["proof_statement_extractable"] is False


def test_extract_proof_ignores_unlabelled_prose():
    assert extract_proof("The system is green.") == ""
