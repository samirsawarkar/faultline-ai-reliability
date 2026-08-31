"""Cold-viewer structural comprehension proxy and dead-weight attack."""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, List

from .evidence import DAY, estimated_read_seconds, load_json, word_count

PROOF_PREFIX = "> **What FAULTLINE proved:**"


def extract_proof(text: str) -> str:
    for line in text.splitlines():
        if line.startswith(PROOF_PREFIX):
            return line[len(PROOF_PREFIX):].strip()
    return ""


def _concept_pass(answer: str, alternatives: List[str]) -> bool:
    normalized = re.sub(r"\s+", " ", answer.lower())
    return any(item.lower() in normalized for item in alternatives)


def score_material(path: Path, rubric: Dict[str, Any]) -> Dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    answer = extract_proof(text)
    concepts = {
        concept["id"]: {
            "passed": _concept_pass(answer, concept["alternatives"]),
            "alternatives": concept["alternatives"],
        }
        for concept in rubric["required_concepts"]
    }
    words = word_count(text)
    reading_seconds = estimated_read_seconds(
        text, rubric["reading_words_per_minute"]
    )
    checks = {
        "proof_statement_extractable": bool(answer),
        "all_required_concepts_present": all(
            result["passed"] for result in concepts.values()
        ),
        "under_three_minute_reading_proxy": (
            reading_seconds <= rubric["max_reading_seconds"]
        ),
        "within_word_budget": words <= rubric["max_words"],
    }
    try:
        material = path.relative_to(DAY).as_posix()
    except ValueError:
        material = str(path)
    return {
        "material": material,
        "answer": answer,
        "word_count": words,
        "estimated_read_seconds": reading_seconds,
        "concepts": concepts,
        "checks": checks,
        "passed": all(checks.values()),
    }


def run_comprehension_attack() -> Dict[str, Any]:
    rubric = load_json(DAY / "comprehension_rubric.json")
    baseline = score_material(
        DAY / "evidence/cold-viewer-baseline.md", rubric
    )
    final = score_material(DAY / "DEMO.md", rubric)
    removed_words = baseline["word_count"] - final["word_count"]
    return {
        "method": "deterministic cold-viewer structural proxy",
        "human_participant": False,
        "method_caveat": (
            "This verifies that a context-free reader surface exposes a concise, "
            "rubric-complete proof statement; it is not an empirical human usability study."
        ),
        "rubric": rubric,
        "baseline": baseline,
        "final": final,
        "dead_weight_removed": {
            "words": removed_words,
            "reading_seconds": (
                baseline["estimated_read_seconds"]
                - final["estimated_read_seconds"]
            ),
            "baseline_failed": not baseline["passed"],
            "final_passed": final["passed"],
        },
        "cold_viewer_can_state_what_faultline_proved": (
            bool(final["answer"]) and final["passed"]
        ),
        "passed": (
            not baseline["passed"]
            and final["passed"]
            and removed_words > 0
        ),
    }
