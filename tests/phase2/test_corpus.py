"""Tests for faultline_p2.env.corpus."""
import re
import subprocess
import sys
from collections import Counter

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


def test_any_hop_document_reuse_bound():
    """Any-hop reuse bound: no fact document is used in any hop more than 5 times across all 350 scenarios."""
    corpus = build_corpus(seed=42)
    all_hop_counts = Counter()
    for s in corpus.scenarios:
        for hop in s.question_chain:
            all_hop_counts[hop.required_source] += 1

    max_any_hop = max(all_hop_counts.values())
    assert max_any_hop <= 5, (
        f"Any-hop reuse bound exceeded: max reuse is {max_any_hop} > 5. "
        f"Top reused docs: {all_hop_counts.most_common(5)}"
    )

    final_doc_counts = Counter(s.required_source for s in corpus.scenarios)
    max_final = max(final_doc_counts.values())
    assert max_final <= 3, f"Final-hop reuse bound exceeded: max {max_final} > 3"


def test_traversal_sources_present_and_sound():
    """traversal_sources lists all required fact and link documents in exact sequential traversal order."""
    corpus = build_corpus(seed=42)
    expected_lengths = {"T1": 1, "T2": 5, "T3": 9}

    for s in corpus.scenarios:
        assert len(s.traversal_sources) == expected_lengths[s.tier], (
            f"Scenario {s.scenario_id} ({s.tier}) traversal_sources length mismatch: "
            f"{len(s.traversal_sources)} != {expected_lengths[s.tier]}"
        )
        # Verify required_sources matches fact docs in traversal_sources in order
        fact_sources_in_traversal = [src for src in s.traversal_sources if src.startswith("doc-")]
        assert fact_sources_in_traversal == s.required_sources, (
            f"Scenario {s.scenario_id} fact docs in traversal order mismatch required_sources"
        )
        assert s.required_source == s.traversal_sources[-1]


def test_link_doc_ids_opaque_and_content_addressed():
    """Link document IDs and titles must be opaque/content-addressed without leaking scenario ID or hop position."""
    corpus = build_corpus(seed=42)
    link_docs = [d for d in corpus.documents if d["id"].startswith("link-")]
    assert len(link_docs) == 998, f"Expected 998 unique link documents, got {len(link_docs)}"

    for doc in link_docs:
        # Must not contain scenario prefixes or hop positions
        assert not re.search(r"s-\d|r-\d|hop|tier|step", doc["id"], re.I), (
            f"Link document id leaks metadata: {doc['id']}"
        )
        assert not re.search(r"s-\d|r-\d|hop|tier|step", doc["title"], re.I), (
            f"Link document title leaks metadata: {doc['title']}"
        )


def test_corpus_document_ids_unique():
    """All documents in the corpus store must have strictly unique document IDs."""
    corpus = build_corpus(seed=42)
    doc_ids = [d["id"] for d in corpus.documents]
    assert len(doc_ids) == len(set(doc_ids)), f"Duplicate document IDs detected in corpus.documents ({len(doc_ids)} vs {len(set(doc_ids))})"
    assert len(corpus.documents) == 1358, f"Expected exactly 1358 unique documents, got {len(corpus.documents)}"


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

    assert corpus.tier_counts == {"T1": 67, "T2": 67, "T3": 216}

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

    std_prompts = {s.prompt for s in corpus.scenarios if s.pool == "standard"}
    res_prompts = {s.prompt for s in corpus.scenarios if s.pool == "reserved"}
    assert std_prompts.isdisjoint(res_prompts), "Standard and reserved pools share scenarios"


def test_corpus_required_sources_resolvable_and_unique():
    corpus = build_corpus(seed=42)
    doc_by_id = {d["id"]: d for d in corpus.documents}
    fact_doc_ids = {d["id"] for d in corpus.documents if d["id"].startswith("doc-") and not d["title"].startswith("Analyst memo")}

    for s in corpus.scenarios:
        for req_src in s.required_sources:
            assert req_src in doc_by_id, f"Required source {req_src} not found in corpus docs"

        for hop in s.question_chain:
            target_doc = doc_by_id[hop.required_source]
            assert hop.answer in target_doc["text"], (
                f"Hop {hop.hop_index} answer {hop.answer} not in doc {hop.required_source}"
            )
            other_fact_docs_with_answer = [
                d["id"] for d in corpus.documents if d["id"] in fact_doc_ids and d["id"] != hop.required_source and hop.answer in d["text"]
            ]
            assert not other_fact_docs_with_answer, (
                f"Answer {hop.answer} leaked into non-required fact docs: {other_fact_docs_with_answer}"
            )

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
