from __future__ import annotations

from faultline_launch.defense import build_defense_report, score_answer
from faultline_launch.evidence import DAY30, EVIDENCE, load_json


def test_ten_core_answers_flip_red_to_green() -> None:
    report = build_defense_report()
    assert report["question_count"] == 10
    assert report["baseline_failed_questions"]
    assert report["final_failed_questions"] == []
    assert report["red_to_green"] is True
    assert report["all_evidence_verified"] is True


def test_every_final_answer_has_all_spoken_elements() -> None:
    source = load_json(DAY30 / "defense_questions.json")
    for question in source["questions"]:
        result = score_answer(question, question["repaired_answer"])
        assert result["passed"], (question["id"], result["missing"])
        assert result["criteria"]["closed_book_surface"] is True


def test_weakest_answer_repair_is_measured() -> None:
    weakest = build_defense_report()["weakest_answer"]
    assert weakest["id"] == "D30-Q01"
    assert weakest["concept"] == "model-form uncertainty"
    assert weakest["baseline_score"] < weakest["final_score"]


def test_recording_is_bound_to_transcript() -> None:
    report = build_defense_report()
    manifest = load_json(EVIDENCE / "defense_recording.json")
    assert report["recording"]["valid"] is True
    assert report["recording"]["synthetic_narration"] is True
    assert report["recording"]["human_proficiency_claimed"] is False
    assert manifest["duration_seconds"] >= 300
    assert manifest["human_participant"] is False


def test_missing_limitation_fails_answer() -> None:
    question = load_json(DAY30 / "defense_questions.json")["questions"][7]
    damaged = question["repaired_answer"].replace(
        "The synthetic oracle removes classifier errors that production must pay for.",
        "",
    )
    result = score_answer(question, damaged)
    assert result["passed"] is False
    assert "limitation" in result["missing"]
