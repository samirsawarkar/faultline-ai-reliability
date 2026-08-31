"""Tests for faultline_p2.env.corpus."""
import subprocess
import sys

from faultline_p2.env.corpus import Corpus, build_corpus


def test_shortcut_test_final_hop_does_not_identify_entity():
    """Shortcut test: for every T2 and T3 scenario, the final hop's prompt

    alone must NOT identify the final entity. If it does, the chain can be skipped.
    """
    corpus = build_corpus(seed=42)
    for s in corpus.scenarios:
        if s.tier in ("T2", "T3"):
            final_hop = s.question_chain[-1]
            assert final_hop.entity not in final_hop.prompt, (
                f"Shortcut vulnerability in scenario {s.scenario_id} ({s.tier}): "
                f"final hop prompt '{final_hop.prompt}' directly names entity '{final_hop.entity}'"
            )


def test_adversarial_chain_test():
    """Adversarial chain test:

    For every hop N >= 2: remove hop[N-1].answer from hop[N].prompt.
    Assert no token remaining in prompt resolves uniquely to hop[N].required_source.
    And for every multi-hop scenario: assert the final hop's prompt alone cannot identify its document.
    """
    import re
    corpus = build_corpus(seed=42)
    doc_by_id = {d["id"]: d for d in corpus.documents}

    hop_failures = 0
    total_hops_tested = 0
    scenario_failures = 0
    multihop_scenarios_tested = 0

    for s in corpus.scenarios:
        if s.hops > 1:
            multihop_scenarios_tested += 1

        for idx in range(1, len(s.question_chain)):
            total_hops_tested += 1
            prev_hop = s.question_chain[idx - 1]
            curr_hop = s.question_chain[idx]

            stripped_prompt = curr_hop.prompt.replace(prev_hop.answer, "")
            target_doc_text = doc_by_id[curr_hop.required_source]["text"]
            coined_tokens_in_stripped = re.findall(r"[A-Z][a-z]+-\d{4}", stripped_prompt)
            leaked_tokens = [tok for tok in coined_tokens_in_stripped if tok in target_doc_text]

            if leaked_tokens or curr_hop.entity in stripped_prompt:
                hop_failures += 1
                if idx == len(s.question_chain) - 1:
                    scenario_failures += 1

    assert hop_failures == 0, (
        f"Adversarial chain test failed: {hop_failures}/{total_hops_tested} hops leaked target document tokens "
        f"and {scenario_failures}/{multihop_scenarios_tested} multi-hop scenarios are solvable from final hop alone!"
    )


def test_distinct_documents_per_scenario():
    """Primary chain test: every hop in a scenario must require a distinct document."""
    corpus = build_corpus(seed=42)
    for s in corpus.scenarios:
        distinct_req_sources = set(s.required_sources)
        assert len(distinct_req_sources) == s.hops, (
            f"Scenario {s.scenario_id} ({s.tier}, {s.hops} hops) touches only {len(distinct_req_sources)} "
            f"distinct documents instead of {s.hops}: {s.required_sources}"
        )


def test_chain_dependency_test():
    """Chain dependency test: for every scenario, every hop N>1 must reference hop N-1's answer."""
    corpus = build_corpus(seed=42)
    for s in corpus.scenarios:
        for idx in range(1, len(s.question_chain)):
            prev_hop = s.question_chain[idx - 1]
            curr_hop = s.question_chain[idx]
            assert prev_hop.answer in curr_hop.prompt, (
                f"Chain broken in scenario {s.scenario_id} ({s.tier}) at hop {curr_hop.hop_index}: "
                f"prompt '{curr_hop.prompt}' does not reference prev answer '{prev_hop.answer}'"
            )


def test_document_reuse_bound():
    """Document reuse bound: no document anchors more than 3 scenarios' final hop."""
    from collections import Counter
    corpus = build_corpus(seed=42)
    final_doc_counts = Counter(s.required_source for s in corpus.scenarios)
    max_reuse = max(final_doc_counts.values())
    assert max_reuse <= 3, (
        f"Document reuse bound exceeded: max final-hop reuse is {max_reuse} > 3. "
        f"Top reused docs: {final_doc_counts.most_common(5)}"
    )


def test_corpus_scenario_counts_and_tiers():
    corpus = build_corpus(seed=42)
    assert isinstance(corpus, Corpus)
    assert corpus.scenario_count == 350
    assert len(corpus.scenarios) == 350
    assert corpus.standard_count == 200
    assert corpus.reserved_count == 150

    standard = [s for s in corpus.scenarios if s.pool == "standard"]
    reserved = [s for s in corpus.scenarios if s.pool == "reserved"]

    assert len(standard) == 200
    assert len(reserved) == 150

    assert corpus.tier_counts == {"T1": 67, "T2": 67, "T3": 216}  # 66 std + 150 res = 216 T3

    tier_hops = {"T1": 1, "T2": 3, "T3": 5}
    for s in corpus.scenarios:
        assert s.hops == tier_hops[s.tier], f"Scenario {s.scenario_id} tier {s.tier} hop mismatch: {s.hops}"
        assert len(s.question_chain) == s.hops
        assert len(s.required_sources) == s.hops
        assert s.required_source == s.question_chain[-1].required_source
        assert s.final_answer == s.question_chain[-1].answer


def test_corpus_scenario_uniqueness():
    """Prove that all scenario IDs and (prompt, final_answer) pairs are distinct."""
    corpus = build_corpus(seed=42)
    scenario_ids = [s.scenario_id for s in corpus.scenarios]
    assert len(scenario_ids) == len(set(scenario_ids)), "Duplicate scenario_id detected"

    prompt_answer_pairs = [(s.prompt, s.final_answer) for s in corpus.scenarios]
    assert len(prompt_answer_pairs) == len(set(prompt_answer_pairs)), "Duplicate (prompt, final_answer) detected"

    # Also verify standard pool and reserved pool have zero scenario overlap
    std_prompts = {s.prompt for s in corpus.scenarios if s.pool == "standard"}
    res_prompts = {s.prompt for s in corpus.scenarios if s.pool == "reserved"}
    assert std_prompts.isdisjoint(res_prompts), "Standard and reserved pools share scenarios"


def test_corpus_required_sources_resolvable_and_unique():
    corpus = build_corpus(seed=42)
    doc_by_id = {d["id"]: d for d in corpus.documents}
    fact_doc_ids = {d["id"] for d in corpus.documents if d["id"].startswith("doc-") and not d["title"].startswith("Analyst memo")}

    for s in corpus.scenarios:
        # Every required source must resolve to a valid document in the corpus
        for req_src in s.required_sources:
            assert req_src in doc_by_id, f"Required source {req_src} not found in corpus docs"

        for hop in s.question_chain:
            # The required source doc must contain the answer token
            target_doc = doc_by_id[hop.required_source]
            assert hop.answer in target_doc["text"], (
                f"Hop {hop.hop_index} answer {hop.answer} not in doc {hop.required_source}"
            )
            # Other FACT documents must not contain the unique coined token
            other_fact_docs_with_answer = [
                d["id"] for d in corpus.documents if d["id"] in fact_doc_ids and d["id"] != hop.required_source and hop.answer in d["text"]
            ]
            assert not other_fact_docs_with_answer, (
                f"Answer {hop.answer} leaked into non-required fact docs: {other_fact_docs_with_answer}"
            )

        # Final answer token must be globally unique to its required source within its scenario document environment
        final_hop = s.question_chain[-1]
        scenario_docs = [doc_by_id[doc_id] for doc_id in s.document_ids]
        scenario_docs_with_final = [d["id"] for d in scenario_docs if final_hop.answer in d["text"]]
        assert scenario_docs_with_final == [final_hop.required_source], (
            f"Final answer {final_hop.answer} appears in multiple docs within scenario {s.scenario_id}: {scenario_docs_with_final}"
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
