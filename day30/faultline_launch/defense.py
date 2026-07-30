from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from .evidence import DAY30, EVIDENCE, ROOT, load_json, resolve_pointer, sha256_file, words, write_json


CODE_REFERENCE = re.compile(r"(?:\.py\b|\bdef\s+|\bclass\s+|\bline\s+\d+|\bfunction\s+)", re.I)


def _contains_all(answer: str, terms: list[str]) -> bool:
    lowered = answer.casefold()
    return all(term.casefold() in lowered for term in terms)


def score_answer(question: dict[str, Any], answer: str) -> dict[str, Any]:
    criteria = {
        name: _contains_all(answer, terms)
        for name, terms in question["required_terms"].items()
    }
    criteria["closed_book_surface"] = CODE_REFERENCE.search(answer) is None
    return {
        "passed": all(criteria.values()),
        "score": sum(criteria.values()),
        "max_score": len(criteria),
        "criteria": criteria,
        "missing": [name for name, passed in criteria.items() if not passed],
        "word_count": len(words(answer)),
    }


def _verify_bindings(question: dict[str, Any]) -> list[dict[str, Any]]:
    verified: list[dict[str, Any]] = []
    for binding in question["evidence"]:
        artifact = ROOT / binding["artifact"]
        actual = resolve_pointer(load_json(artifact), binding["pointer"])
        expected = binding["expected"]
        verified.append(
            {
                **binding,
                "actual": actual,
                "passed": actual == expected,
            }
        )
    return verified


def render_transcript(questions: list[dict[str, Any]]) -> str:
    lines = [
        "# Recorded skeptical staff-level mock defense",
        "",
        "Format: ten closed-book questions. The candidate answers from the evidence",
        "model—decision, measured result, tradeoff, limitation, and reversal trigger—",
        "without opening implementation code.",
        "",
        "This recording demonstrates that complete evidence-led answers can be delivered",
        "aloud. It is synthetic narration of the prepared defense, not an empirical test",
        "of the repository author's unaided speaking performance.",
        "",
    ]
    for index, question in enumerate(questions, start=1):
        lines.extend(
            [
                f"## {index}. {question['title']}",
                "",
                f"**Interviewer:** {question['question']}",
                "",
                f"**Candidate:** {question['repaired_answer']}",
                "",
            ]
        )
    lines.extend(
        [
            "## Closing statement",
            "",
            "FAULTLINE does not prove a universal recovery policy. It proves a decision",
            "discipline: measure correct user-visible outcomes, pair comparisons, preserve",
            "provenance, enforce budgets, attack the winner, and withdraw the recommendation",
            "when the operating envelope changes.",
            "",
        ]
    )
    return "\n".join(lines)


def render_spoken_script(questions: list[dict[str, Any]]) -> str:
    lines = [
        "FAULTLINE skeptical staff-level mock defense.",
        "Ten closed-book questions. Answers state the decision, evidence, tradeoff, limitation, and reversal trigger.",
        "This is synthetic narration of the prepared defense, not a test of the author's unaided speaking performance.",
    ]
    for index, question in enumerate(questions, start=1):
        lines.extend(
            [
                f"Question {index}. {question['title']}.",
                f"Interviewer. {question['question']}",
                f"Candidate. {question['repaired_answer']}",
            ]
        )
    lines.append(
        "Closing statement. FAULTLINE proves a bounded decision discipline, not a universal recovery policy."
    )
    return "\n\n".join(lines) + "\n"


def build_defense_report() -> dict[str, Any]:
    source = load_json(DAY30 / "defense_questions.json")
    questions = source["questions"]
    results = []
    for question in questions:
        baseline = score_answer(question, question["initial_answer"])
        final = score_answer(question, question["repaired_answer"])
        bindings = _verify_bindings(question)
        results.append(
            {
                "id": question["id"],
                "title": question["title"],
                "core_decision": question["core_decision"],
                "baseline": baseline,
                "final": final,
                "repair": question["repair"],
                "weak_concept": question["weak_concept"],
                "evidence": bindings,
                "evidence_verified": all(item["passed"] for item in bindings),
            }
        )

    weakest = min(
        results,
        key=lambda item: (item["baseline"]["score"], item["id"]),
    )
    transcript = render_transcript(questions)
    transcript_path = EVIDENCE / "mock-defense-transcript.md"
    transcript_path.parent.mkdir(parents=True, exist_ok=True)
    transcript_path.write_text(transcript, encoding="utf-8")

    recording_path = EVIDENCE / "mock-defense.m4a"
    recording_manifest_path = EVIDENCE / "defense_recording.json"
    recording_manifest = (
        load_json(recording_manifest_path) if recording_manifest_path.exists() else None
    )
    recording_valid = bool(
        recording_path.exists()
        and recording_manifest
        and recording_manifest.get("audio_sha256") == sha256_file(recording_path)
        and recording_manifest.get("transcript_sha256") == sha256_file(transcript_path)
        and recording_manifest.get("duration_seconds", 0) >= 300
    )

    report = {
        "schema_version": "1.0.0",
        "question_count": len(results),
        "core_decision_count": len({item["core_decision"] for item in results}),
        "baseline_failed_questions": [
            item["id"] for item in results if not item["baseline"]["passed"]
        ],
        "final_failed_questions": [
            item["id"] for item in results if not item["final"]["passed"]
        ],
        "all_evidence_verified": all(item["evidence_verified"] for item in results),
        "weakest_answer": {
            "id": weakest["id"],
            "concept": weakest["weak_concept"],
            "baseline_score": weakest["baseline"]["score"],
            "final_score": weakest["final"]["score"],
            "repair": weakest["repair"],
        },
        "red_to_green": bool(
            any(not item["baseline"]["passed"] for item in results)
            and all(item["final"]["passed"] for item in results)
        ),
        "recording": {
            "path": "day30/evidence/mock-defense.m4a",
            "manifest_path": "day30/evidence/defense_recording.json",
            "present": recording_path.exists(),
            "valid": recording_valid,
            "synthetic_narration": True,
            "human_proficiency_claimed": False,
        },
        "transcript": {
            "path": "day30/evidence/mock-defense-transcript.md",
            "sha256": sha256_file(transcript_path),
            "word_count": len(words(transcript)),
        },
        "results": results,
        "passed": bool(
            len(results) == 10
            and all(item["final"]["passed"] for item in results)
            and all(item["evidence_verified"] for item in results)
            and recording_valid
        ),
    }
    write_json(EVIDENCE / "defense_report.json", report)
    return report
