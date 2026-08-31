"""Tests for faultline_p2.env.corpus."""
import subprocess
import sys

from faultline_p2.env.corpus import Corpus, build_corpus


def test_corpus_scenario_counts_and_tiers():
    corpus = build_corpus(seed=42)
    assert isinstance(corpus, Corpus)
    assert corpus.scenario_count == 300
    assert len(corpus.scenarios) == 300
    assert corpus.standard_count == 200
    assert corpus.reserved_count == 100

    standard = [s for s in corpus.scenarios if s.pool == "standard"]
    reserved = [s for s in corpus.scenarios if s.pool == "reserved"]

    assert len(standard) == 200
    assert len(reserved) == 100

    tier_hops = {"T1": 1, "T2": 3, "T3": 5}
    for s in corpus.scenarios:
        assert s.hops == tier_hops[s.tier], f"Scenario {s.scenario_id} tier {s.tier} hop mismatch: {s.hops}"
        assert len(s.question_chain) == s.hops
        assert len(s.required_sources) == s.hops
        assert s.required_source == s.question_chain[-1].required_source
        assert s.final_answer == s.question_chain[-1].answer


def test_corpus_required_sources_resolvable_and_unique():
    corpus = build_corpus(seed=42)
    for s in corpus.scenarios:
        doc_ids = {d["id"] for d in s.documents}
        # Every required source must resolve to a valid document in the scenario
        for req_src in s.required_sources:
            assert req_src in doc_ids, f"Required source {req_src} not found in scenario {s.scenario_id} docs"

        for hop in s.question_chain:
            # The required source doc must contain the answer token
            target_doc = next(d for d in s.documents if d["id"] == hop.required_source)
            assert hop.answer in target_doc["text"], (
                f"Hop {hop.hop_index} answer {hop.answer} not in doc {hop.required_source}"
            )
            # Other documents must not contain the unique coined token
            other_docs_with_answer = [
                d["id"] for d in s.documents if d["id"] != hop.required_source and hop.answer in d["text"]
            ]
            assert not other_docs_with_answer, (
                f"Answer {hop.answer} leaked into non-required docs: {other_docs_with_answer}"
            )


def test_corpus_cross_process_determinism():
    cmd = [
        sys.executable,
        "-c",
        "from faultline_p2.env.corpus import build_corpus; print(build_corpus(42).content_hash)",
    ]

    res1 = subprocess.run(cmd, capture_output=True, text=True, check=True, env={"PYTHONHASHSEED": "0"})
    res2 = subprocess.run(cmd, capture_output=True, text=True, check=True, env={"PYTHONHASHSEED": "999999"})

    hash1 = res1.stdout.strip()
    hash2 = res2.stdout.strip()

    assert hash1 == hash2, f"Corpus hash mismatch under different PYTHONHASHSEED: {hash1} != {hash2}"
    assert len(hash1) == 64
