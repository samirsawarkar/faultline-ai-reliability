"""Phase 2 Corpus generator.

Deterministic multi-hop corpus composed on top of day01 build_env.
Implements a Phase-2 link layer to enable genuine sequential retrieval across distinct documents.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import random
from pathlib import Path
from typing import Any, Dict, List, Literal, Sequence, Tuple

from pydantic import BaseModel, ConfigDict, Field

from faultline_p2.env._day01_env import _ATTRIBUTES, build_env

SPEC_VERSION = "2.0.0"
_STRICT = ConfigDict(extra="forbid")

_TIER_HOPS = {"T1": 1, "T2": 3, "T3": 5}

_ATTR_DESCRIPTIONS: Dict[str, str] = {
    "internal_codename": "internal codename",
    "headquarters_district": "headquarters district",
    "flagship_product": "flagship product",
    "external_auditor": "external auditor",
    "archival_reference": "archival reference",
}


class HopStep(BaseModel):
    model_config = _STRICT
    hop_index: int = Field(ge=1)
    prompt: str
    answer: str
    required_source: str
    entity: str
    attribute: str


class Scenario(BaseModel):
    model_config = _STRICT
    scenario_id: str
    tier: Literal["T1", "T2", "T3"]
    hops: int
    pool: Literal["standard", "reserved"]
    prompt: str
    question_chain: List[HopStep]
    final_answer: str
    required_source: str
    required_sources: List[str]
    document_ids: List[str]


class Corpus(BaseModel):
    model_config = _STRICT
    spec_version: str
    master_seed: int
    scenario_count: int
    standard_count: int
    reserved_count: int
    tier_counts: Dict[str, int]
    documents: List[Dict[str, Any]]
    scenarios: List[Scenario]

    def canonical_bytes(self) -> bytes:
        text = json.dumps(
            self.model_dump(),
            sort_keys=True,
            ensure_ascii=True,
            indent=2,
            separators=(",", ": "),
        )
        return (text + "\n").encode("utf-8")

    @property
    def content_hash(self) -> str:
        return hashlib.sha256(self.canonical_bytes()).hexdigest()


def _build_multihop_scenario(
    scenario_id: str,
    tier: Literal["T1", "T2", "T3"],
    pool: Literal["standard", "reserved"],
    entity_chain: Sequence[str],
    target_attrs: Sequence[str],
    questions_by_entity: Dict[str, Dict[str, Dict[str, Any]]],
    doc_by_id: Dict[str, Dict[str, Any]],
    corpus_link_docs: List[Dict[str, Any]],
    all_doc_ids: List[str],
) -> Scenario:
    hops = _TIER_HOPS[tier]
    if len(entity_chain) != hops:
        raise ValueError(f"Entity chain length {len(entity_chain)} does not match tier {tier} hops {hops}")

    chain: List[HopStep] = []
    scenario_link_doc_ids: List[str] = []
    for idx, (ent, target_attr) in enumerate(zip(entity_chain, target_attrs), start=1):
        q = questions_by_entity[ent][target_attr]
        answer = q["answer"]
        req_source = q["required_source"]

        # Data integrity check
        if answer not in doc_by_id[req_source]["text"]:
            raise ValueError(f"Answer {answer} not found in required source {req_source}")

        if idx == 1:
            prompt = q["prompt"]
        else:
            prev_attr = target_attrs[idx - 2]
            prev_ans = chain[idx - 2].answer
            prev_desc = _ATTR_DESCRIPTIONS[prev_attr]
            curr_desc = _ATTR_DESCRIPTIONS[target_attr]

            # Create Phase-2 link layer document mapping prev_ans -> ent
            link_doc_id = f"link-{scenario_id}-hop{idx}"
            link_doc_text = (
                f"Affiliation record: The organization holding {prev_desc} {prev_ans} "
                f"is officially affiliated with {ent}."
            )
            link_doc = {
                "id": link_doc_id,
                "title": f"Affiliation record {scenario_id}-hop{idx}",
                "text": link_doc_text,
            }
            corpus_link_docs.append(link_doc)
            scenario_link_doc_ids.append(link_doc_id)

            # Adversarially sound hop prompt: references ONLY prev_ans, gives NO tokens of target entity
            prompt = (
                f"The organization holding {prev_desc} {prev_ans} is affiliated with "
                f"a partner organization. What is the {curr_desc} of that partner organization?"
            )

        chain.append(
            HopStep(
                hop_index=idx,
                prompt=prompt,
                answer=answer,
                required_source=req_source,
                entity=ent,
                attribute=target_attr,
            )
        )

    if hops == 1:
        composite_prompt = chain[0].prompt
    else:
        lines = [f"Step 1: {chain[0].prompt}"]
        for idx in range(1, hops):
            prev_desc = _ATTR_DESCRIPTIONS[target_attrs[idx - 1]]
            curr_desc = _ATTR_DESCRIPTIONS[target_attrs[idx]]
            lines.append(
                f"Step {idx + 1}: The organization holding {prev_desc} from Step {idx} is affiliated with "
                f"a partner organization. What is the {curr_desc} of that partner organization?"
            )
        lines.append(f"Provide the final answer for Step {hops}.")
        composite_prompt = " ".join(lines)

    final_hop = chain[-1]
    required_sources = [h.required_source for h in chain]

    return Scenario(
        scenario_id=scenario_id,
        tier=tier,
        hops=hops,
        pool=pool,
        prompt=composite_prompt,
        question_chain=chain,
        final_answer=final_hop.answer,
        required_source=final_hop.required_source,
        required_sources=required_sources,
        document_ids=list(all_doc_ids) + scenario_link_doc_ids,
    )


def build_corpus(seed: int = 42) -> Corpus:
    """Deterministic 350-scenario corpus with true multi-hop link-layer traversal.

    Composition:
      - 200 standard (67 T1 / 67 T2 / 66 T3)
      - 150 reserved hard pool (150 T3)
      - 150 distinct fact entities + 50 distractors = 200 base documents + Phase-2 link documents
      - Document reuse bound: no document anchors > 3 scenarios' final hop.
    """
    n_entities = 150
    n_distractors = 50
    env = build_env(seed=seed, n_entities=n_entities, n_distractors=n_distractors)

    documents = list(env["documents"])
    doc_by_id = {d["id"]: d for d in documents}

    questions_by_entity: Dict[str, Dict[str, Dict[str, Any]]] = {}
    for q in env["questions"]:
        ent = q["entity"]
        if ent not in questions_by_entity:
            questions_by_entity[ent] = {}
        questions_by_entity[ent][q["attribute"]] = q

    fact_docs = [d for d in documents if not d["title"].startswith("Analyst memo")]
    entity_names = [d["title"] for d in fact_docs]

    # Partition entities: 100 standard (0..99), 50 reserved (100..149)
    standard_entities = entity_names[:100]
    reserved_entities = entity_names[100:150]

    attr_keys = sorted(_ATTRIBUTES.keys())

    rng_standard = random.Random((seed * 1_000_003 + 100_000) & 0x7FFFFFFFFFFFFFFF)
    rng_reserved = random.Random((seed * 1_000_003 + 200_000) & 0x7FFFFFFFFFFFFFFF)

    scenarios: List[Scenario] = []
    tier_counts = {"T1": 0, "T2": 0, "T3": 0}
    link_documents: List[Dict[str, Any]] = []
    all_doc_ids = [d["id"] for d in documents]

    seq = 0

    # 1. Standard Pool T1 (67 scenarios, 1 hop)
    t1_entities = rng_standard.sample(standard_entities, k=67)
    for ent in t1_entities:
        seq += 1
        attr = rng_standard.choice(attr_keys)
        sc = _build_multihop_scenario(
            scenario_id=f"s-{seq:04d}",
            tier="T1",
            pool="standard",
            entity_chain=[ent],
            target_attrs=[attr],
            questions_by_entity=questions_by_entity,
            doc_by_id=doc_by_id,
            corpus_link_docs=link_documents,
            all_doc_ids=all_doc_ids,
        )
        scenarios.append(sc)
        tier_counts["T1"] += 1

    # 2. Standard Pool T2 (67 scenarios, 3 hops)
    t2_final_entities = (standard_entities * 2)[:67]
    rng_standard.shuffle(t2_final_entities)
    for ent3 in t2_final_entities:
        seq += 1
        others = [e for e in standard_entities if e != ent3]
        ent1, ent2 = rng_standard.sample(others, k=2)
        chain_entities = [ent1, ent2, ent3]
        target_attrs = [rng_standard.choice(attr_keys) for _ in range(3)]

        sc = _build_multihop_scenario(
            scenario_id=f"s-{seq:04d}",
            tier="T2",
            pool="standard",
            entity_chain=chain_entities,
            target_attrs=target_attrs,
            questions_by_entity=questions_by_entity,
            doc_by_id=doc_by_id,
            corpus_link_docs=link_documents,
            all_doc_ids=all_doc_ids,
        )
        scenarios.append(sc)
        tier_counts["T2"] += 1

    # 3. Standard Pool T3 (66 scenarios, 5 hops)
    t3_std_final_entities = (standard_entities * 2)[67:133]
    rng_standard.shuffle(t3_std_final_entities)
    for ent5 in t3_std_final_entities:
        seq += 1
        others = [e for e in standard_entities if e != ent5]
        ent1, ent2, ent3, ent4 = rng_standard.sample(others, k=4)
        chain_entities = [ent1, ent2, ent3, ent4, ent5]
        target_attrs = [rng_standard.choice(attr_keys) for _ in range(5)]

        sc = _build_multihop_scenario(
            scenario_id=f"s-{seq:04d}",
            tier="T3",
            pool="standard",
            entity_chain=chain_entities,
            target_attrs=target_attrs,
            questions_by_entity=questions_by_entity,
            doc_by_id=doc_by_id,
            corpus_link_docs=link_documents,
            all_doc_ids=all_doc_ids,
        )
        scenarios.append(sc)
        tier_counts["T3"] += 1

    # 4. Reserved Hard Pool T3 (150 scenarios, 5 hops)
    res_final_entities = reserved_entities * 3
    rng_reserved.shuffle(res_final_entities)
    for ent5 in res_final_entities:
        seq += 1
        others = [e for e in reserved_entities if e != ent5]
        ent1, ent2, ent3, ent4 = rng_reserved.sample(others, k=4)
        chain_entities = [ent1, ent2, ent3, ent4, ent5]
        target_attrs = [rng_reserved.choice(attr_keys) for _ in range(5)]

        sc = _build_multihop_scenario(
            scenario_id=f"r-{seq:04d}",
            tier="T3",
            pool="reserved",
            entity_chain=chain_entities,
            target_attrs=target_attrs,
            questions_by_entity=questions_by_entity,
            doc_by_id=doc_by_id,
            corpus_link_docs=link_documents,
            all_doc_ids=all_doc_ids,
        )
        scenarios.append(sc)
        tier_counts["T3"] += 1

    if len(scenarios) != 350:
        raise ValueError(f"Expected 350 scenarios, got {len(scenarios)}")

    # Combine base documents with link documents
    all_corpus_documents = documents + link_documents

    return Corpus(
        spec_version=SPEC_VERSION,
        master_seed=seed,
        scenario_count=350,
        standard_count=200,
        reserved_count=150,
        tier_counts=tier_counts,
        documents=all_corpus_documents,
        scenarios=scenarios,
    )


def main():
    parser = argparse.ArgumentParser(description="Generate FAULTLINE Phase 2 corpus")
    parser.add_argument("--seed", type=int, default=42, help="Master seed")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("projects/_corpus/corpus.json"),
        help="Output path for corpus JSON",
    )
    args = parser.parse_args()

    corpus = build_corpus(seed=args.seed)
    raw_bytes = corpus.canonical_bytes()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(raw_bytes)

    h = hashlib.sha256(raw_bytes).hexdigest()
    print(f"CORPUS_HASH={h}")
    print(f"WROTE={args.output} ({len(raw_bytes)} bytes, {corpus.scenario_count} scenarios)")


if __name__ == "__main__":
    main()
