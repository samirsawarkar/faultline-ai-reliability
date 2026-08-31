"""The case study has four layers and exactly five source-bound numbers."""
import pytest

from faultline_brief.audit import audit_day29
from faultline_brief.demo import build_demo
from faultline_brief.evidence import DAY, load_json

CASE_SPEC = load_json(DAY / "case_study.json")


@pytest.fixture(scope="module")
def audit():
    return audit_day29(build_demo())


def test_case_study_has_exactly_four_layers(audit):
    assert audit["checks"]["case_study_exactly_four_layers"] is True
    assert audit["case_study"]["layer_headings"] == [
        "## Layer 1 · Decision",
        "## Layer 2 · Incident",
        "## Layer 3 · Evidence",
        "## Layer 4 · Boundary",
    ]


def test_case_study_is_one_page_and_under_three_minutes(audit):
    assert audit["case_study"]["word_count"] <= 500
    assert audit["case_study"]["estimated_read_seconds"] <= 180


def test_exactly_five_numbers_are_declared(audit):
    numbers = audit["case_study"]["five_numbers"]
    assert numbers["declared_count"] == 5
    assert numbers["exactly_five"] is True
    assert numbers["passed"] is True


@pytest.mark.parametrize(
    "number",
    CASE_SPEC["verified_numbers"],
    ids=[item["id"] for item in CASE_SPEC["verified_numbers"]],
)
def test_each_case_number_matches_committed_result(number, audit):
    records = {
        item["id"]: item
        for item in audit["case_study"]["five_numbers"]["records"]
    }
    assert records[number["id"]]["matched"] is True
    assert records[number["id"]]["resolved"] == number["token"]


def test_case_study_states_simulator_boundary():
    text = (DAY / "CASE-STUDY.md").read_text(encoding="utf-8")
    assert "configured simulator incident" in text
    assert "does not prove" in text
    assert "in production" in text


def test_publication_bundle_has_repo_article_demo_and_case(audit):
    bundle = audit["publication_bundle"]
    assert bundle["passed"] is True
    assert [item["role"] for item in bundle["artifacts"]] == [
        "repository",
        "article",
        "demo",
        "case_study",
    ]
    assert all(item["exists"] and item["sha256"] for item in bundle["artifacts"])
