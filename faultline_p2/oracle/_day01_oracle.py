"""The oracle: the single, deterministic judge of correctness.

Why an oracle instead of eyeballing (see MEASUREMENT.md, "Why an oracle"):
  A metric is only honest if the same input always yields the same verdict,
  independent of who is looking or when. `oracle_check` is a pure function of
  (question, response). It never calls a model, never uses wall-clock time,
  never uses randomness. Every later score in FAULTLINE is a count of these
  verdicts, so the oracle is where honesty is either won or lost.

A response PASSES only if BOTH hold:
  1. correct         -> the required answer token appears in the model's answer.
  2. cited_required  -> the model cited the one document that actually contains
                        the answer (grounding, not lucky guessing).

Requiring the source is what makes the number faultline-honest: a system that
emits the right token while citing a distractor did NOT retrieve the fact, and
the oracle refuses to reward it.
"""
from __future__ import annotations

import re
from typing import Any, Dict, List

_WS = re.compile(r"\s+")


def normalize(s: str) -> str:
    """Casefold + collapse whitespace. Deterministic, no locale surprises."""
    return _WS.sub(" ", str(s).strip()).lower()


def oracle_check(question: Dict[str, Any], response: Dict[str, Any]) -> Dict[str, Any]:
    """Judge one response against one question.

    question: an item from build_env()["questions"] (needs `answer`,
              `required_source`).
    response: {"answer": str, "cited_sources": [doc_id, ...]}.

    Returns a verdict dict; `passed` is the honest bit that later numbers sum.
    """
    expected = normalize(question["answer"])
    got = normalize(response.get("answer", ""))
    # Exact token containment: the coined answer token is globally unique, so
    # substring containment cannot be satisfied by any other answer's value.
    correct = bool(expected) and expected in got

    cited: List[str] = list(response.get("cited_sources", []))
    cited_required = question["required_source"] in cited

    return {
        "question_id": question.get("id"),
        "correct": correct,
        "cited_required": cited_required,
        "passed": correct and cited_required,
        "expected_answer": question["answer"],
        "required_source": question["required_source"],
    }
