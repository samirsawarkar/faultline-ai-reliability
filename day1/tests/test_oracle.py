"""Oracle correctness tests (complements the hand-check script)."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from faultline import build_env, oracle_check  # noqa: E402


def _q():
    return build_env(11)["questions"][0]


def test_pass_requires_both_correct_and_cited():
    q = _q()
    v = oracle_check(q, {"answer": q["answer"], "cited_sources": [q["required_source"]]})
    assert v["passed"] is True


def test_wrong_answer_fails_even_if_cited():
    q = _q()
    v = oracle_check(q, {"answer": "not-a-real-token", "cited_sources": [q["required_source"]]})
    assert v["correct"] is False
    assert v["passed"] is False


def test_answer_embedded_in_sentence_is_correct():
    q = _q()
    v = oracle_check(q, {"answer": f"The answer is {q['answer']} per the file.",
                         "cited_sources": [q["required_source"]]})
    assert v["correct"] is True


def test_case_and_whitespace_insensitive():
    q = _q()
    messy = f"   {q['answer'].upper()}\t"
    v = oracle_check(q, {"answer": messy, "cited_sources": [q["required_source"]]})
    assert v["correct"] is True


def test_extra_citations_do_not_break_pass():
    q = _q()
    v = oracle_check(q, {"answer": q["answer"],
                         "cited_sources": ["doc-9999", q["required_source"], "doc-8888"]})
    assert v["passed"] is True


def test_required_source_is_unique_per_answer_token():
    """Structural guarantee: each answer token appears in exactly one document."""
    env = build_env(5)
    docs = env["documents"]
    for q in env["questions"]:
        holders = [d["id"] for d in docs if q["answer"] in d["text"]]
        assert holders == [q["required_source"]], (
            f"answer {q['answer']!r} must live in exactly its required source"
        )
