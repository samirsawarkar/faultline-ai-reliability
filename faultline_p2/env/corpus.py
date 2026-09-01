"""Phase 2 Corpus generator.

Deterministic multi-hop corpus with a Phase-2 link layer.
Guarantees:
  - Genuine sequential multi-hop retrieval across distinct documents.
  - Any-hop fact document reuse bounded at <= 5.
  - Opaque, content-addressed link layer document IDs without metadata leakage.
  - Traversal sources declared in full (1 for T1, 5 for T2, 9 for T3).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import random
from pathlib import Path
from typing import Any, Dict, List, Literal, Sequence, Tuple

from pydantic import BaseModel, ConfigDict, Field

from faultline_p2.env._day01_env import (
    _ATTRIBUTES,
    _ENTITY_PREFIX,
    _ENTITY_SUFFIX,
    _coin_token,
)

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

_SECTOR_PREFIXES = ["Alpha", "Beta"]


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
    traversal_sources: List[str]
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


def _build_base_environment(seed: int, n_entities: int = 300, n_distractors: int = 60) -> Dict[str, Any]:
    """Deterministic environment of 300 unique entities and 60 distractors."""
    rng = random.Random(seed)
    attr_keys = sorted(_ATTRIBUTES.keys())

    # Build 300 unique entity names across 2 sectors (150 per sector)
    # Sector 0 (Standard): "{prefix} {suffix}"
    # Sector 1 (Reserved): "{prefix} {suffix} (Sector Beta)"
    entities: List[Dict[str, Any]] = []
    used_names = set()
    token_counter = 0

    for i in range(n_entities):
        sector_idx = i // 150
        while True:
            base_name = f"{rng.choice(_ENTITY_PREFIX)} {rng.choice(_ENTITY_SUFFIX)}"
            if sector_idx == 0:
                name = base_name
            else:
                name = f"{base_name} (Sector Beta)"
            if name not in used_names:
                used_names.add(name)
                break

        facts = {}
        for attr in attr_keys:
            facts[attr] = _coin_token(token_counter)
            token_counter += 1

        entities.append({"name": name, "doc_id": f"doc-{i:04d}", "facts": facts})

    documents: List[Dict[str, Any]] = []
    for ent in entities:
        sentences = [f"{ent['name']} is a registered organization in the FAULTLINE corpus."]
        for attr in attr_keys:
            label = attr.replace("_", " ")
            sentences.append(f"The {label} of {ent['name']} is {ent['facts'][attr]}.")
        documents.append({
            "id": ent["doc_id"],
            "title": ent["name"],
            "text": " ".join(sentences),
        })

    for d in range(n_distractors):
        subjects = rng.sample([e["name"] for e in entities], k=min(2, len(entities)))
        text = (
            f"An analyst memo discusses {subjects[0]}"
            + (f" and {subjects[1]}" if len(subjects) > 1 else "")
            + ". It reviews market sentiment and partnerships but records no"
              " codenames, districts, products, auditors, or archival references."
        )
        documents.append({
            "id": f"doc-{n_entities + d:04d}",
            "title": f"Analyst memo {d:04d}",
            "text": text,
        })

    questions: List[Dict[str, Any]] = []
    qn = 0
    for ent in entities:
        for attr in attr_keys:
            prompt = _ATTRIBUTES[attr].format(entity=ent["name"])
            questions.append({
                "id": f"q-{qn:04d}",
                "prompt": prompt,
                "answer": ent["facts"][attr],
                "required_source": ent["doc_id"],
                "entity": ent["name"],
                "attribute": attr,
            })
            qn += 1

    return {
        "spec_version": SPEC_VERSION,
        "seed": seed,
        "entities": entities,
        "documents": documents,
        "questions": questions,
    }


def _build_multihop_scenario(
    scenario_id: str,
    tier: Literal["T1", "T2", "T3"],
    pool: Literal["standard", "reserved"],
    entity_chain: Sequence[str],
    target_attrs: Sequence[str],
    questions_by_entity: Dict[str, Dict[str, Dict[str, Any]]],
    doc_by_id: Dict[str, Dict[str, Any]],
    corpus_link_docs: List[Dict[str, Any]],
    all_base_doc_ids: List[str],
) -> Scenario:
    hops = _TIER_HOPS[tier]
    if len(entity_chain) != hops:
        raise ValueError(f"Entity chain length {len(entity_chain)} does not match tier {tier} hops {hops}")

    chain: List[HopStep] = []
    traversal_sources: List[str] = []
    scenario_link_doc_ids: List[str] = []

    for idx, (ent, target_attr) in enumerate(zip(entity_chain, target_attrs), start=1):
        q = questions_by_entity[ent][target_attr]
        answer = q["answer"]
        req_source = q["required_source"]

        if answer not in doc_by_id[req_source]["text"]:
            raise ValueError(f"Answer {answer} not found in required source {req_source}")

        if idx == 1:
            prompt = q["prompt"]
            traversal_sources.append(req_source)
        else:
            prev_attr = target_attrs[idx - 2]
            prev_ans = chain[idx - 2].answer
            prev_desc = _ATTR_DESCRIPTIONS[prev_attr]
            curr_desc = _ATTR_DESCRIPTIONS[target_attr]

            # Content-addressed opaque link document ID
            link_doc_text = (
                f"Affiliation record: The organization holding {prev_desc} {prev_ans} "
                f"is officially affiliated with {ent}."
            )
            raw_hash = hashlib.sha256(link_doc_text.encode("utf-8")).hexdigest()[:12]
            link_doc_id = f"link-{raw_hash}"

            link_doc = {
                "id": link_doc_id,
                "title": f"Affiliation record {link_doc_id}",
                "text": link_doc_text,
            }
            corpus_link_docs.append(link_doc)
            scenario_link_doc_ids.append(link_doc_id)
            traversal_sources.append(link_doc_id)
            traversal_sources.append(req_source)

            # Adversarially sound prompt referencing ONLY previous answer
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
        traversal_sources=traversal_sources,
        document_ids=list(all_base_doc_ids) + scenario_link_doc_ids,
    )


def build_corpus(seed: int = 42) -> Corpus:
    """Deterministic 350-scenario corpus with bounded <=5 any-hop fact reuse.

    Composition:
      - 200 standard (67 T1 / 67 T2 / 66 T3)
      - 150 reserved hard pool (150 T3)
      - 300 distinct fact entities (150 standard, 150 reserved) + 60 distractors = 360 base docs
      - 998 content-addressed opaque link documents
      - Total documents = 1,358 documents
      - Any-hop fact reuse strictly bounded at <= 5.
    """
    n_entities = 300
    n_distractors = 60
    env = _build_base_environment(seed=seed, n_entities=n_entities, n_distractors=n_distractors)

    documents = list(env["documents"])
    doc_by_id = {d["id"]: d for d in documents}
    all_base_doc_ids = [d["id"] for d in documents]

    questions_by_entity: Dict[str, Dict[str, Dict[str, Any]]] = {}
    for q in env["questions"]:
        ent = q["entity"]
        if ent not in questions_by_entity:
            questions_by_entity[ent] = {}
        questions_by_entity[ent][q["attribute"]] = q

    fact_docs = [d for d in documents if not d["title"].startswith("Analyst memo")]
    entity_names = [d["title"] for d in fact_docs]

    # Partition 300 entities: 150 standard (0..149), 150 reserved (150..299)
    standard_entities = entity_names[:150]
    reserved_entities = entity_names[150:300]

    attr_keys = sorted(_ATTRIBUTES.keys())

    rng_standard = random.Random((seed * 1_000_003 + 100_000) & 0x7FFFFFFFFFFFFFFF)
    rng_reserved = random.Random((seed * 1_000_003 + 200_000) & 0x7FFFFFFFFFFFFFFF)

    used_outbound_attrs = {e: set() for e in entity_names}

    scenarios: List[Scenario] = []
    tier_counts = {"T1": 0, "T2": 0, "T3": 0}
    link_documents: List[Dict[str, Any]] = []

    # Bounded allocation for standard pool entities (150 entities, 598 hops):
    # 66 T3 (330 hops), 67 T2 (201 hops), 67 T1 (67 hops) -> any-hop reuse <= 5, final-hop reuse <= 2
    std_all_usage = {i: 0 for i in range(150)}
    std_final_usage = {i: 0 for i in range(150)}

    # Plan T3 (66 quints):
    t3_std_chains_idx: List[List[int]] = []
    for _ in range(66):
        cands_final = sorted(range(150), key=lambda x: (std_final_usage[x], std_all_usage[x], x))
        cands_nonfinal = sorted(range(150), key=lambda x: (std_all_usage[x], x))
        final_e = cands_final[0]
        non_finals = [c for c in cands_nonfinal if c != final_e][:4]
        quint = non_finals + [final_e]
        for c in quint:
            std_all_usage[c] += 1
        std_final_usage[final_e] += 1
        t3_std_chains_idx.append(quint)

    # Plan T2 (67 triples):
    t2_std_chains_idx: List[List[int]] = []
    for _ in range(67):
        cands_final = sorted(range(150), key=lambda x: (std_final_usage[x], std_all_usage[x], x))
        cands_nonfinal = sorted(range(150), key=lambda x: (std_all_usage[x], x))
        final_e = cands_final[0]
        non_finals = [c for c in cands_nonfinal if c != final_e][:2]
        triple = non_finals + [final_e]
        for c in triple:
            std_all_usage[c] += 1
        std_final_usage[final_e] += 1
        t2_std_chains_idx.append(triple)

    # Plan T1 (67 singles):
    t1_std_chains_idx: List[List[int]] = []
    for _ in range(67):
        cands_final = sorted(range(150), key=lambda x: (std_final_usage[x], std_all_usage[x], x))
        final_e = cands_final[0]
        std_all_usage[final_e] += 1
        std_final_usage[final_e] += 1
        t1_std_chains_idx.append([final_e])

    # Plan Reserved T3 (150 quints across 150 reserved entities):
    # Shifted cyclic schedule -> exactly 5 uses per reserved entity!
    t3_res_chains_idx: List[List[int]] = []
    for i in range(150):
        quint = [
            (i + 0) % 150,
            (i + 30) % 150,
            (i + 60) % 150,
            (i + 90) % 150,
            (i + 120) % 150,
        ]
        t3_res_chains_idx.append(quint)

    seq = 0

    # 1. Standard Pool T1 (67 scenarios)
    for chain_idx in t1_std_chains_idx:
        seq += 1
        ent = standard_entities[chain_idx[0]]
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
            all_base_doc_ids=all_base_doc_ids,
        )
        scenarios.append(sc)
        tier_counts["T1"] += 1

    # 2. Standard Pool T2 (67 scenarios)
    for chain_idx in t2_std_chains_idx:
        seq += 1
        chain_ents = [standard_entities[i] for i in chain_idx]
        target_attrs = []
        for i, ent in enumerate(chain_ents):
            if i < len(chain_ents) - 1:
                avail = [a for a in attr_keys if a not in used_outbound_attrs[ent]]
                if not avail:
                    raise RuntimeError(f"No available attributes left for {ent} (any-hop non-final reuse limit exceeded)")
                attr = rng_standard.choice(avail)
                used_outbound_attrs[ent].add(attr)
                target_attrs.append(attr)
            else:
                target_attrs.append(rng_standard.choice(attr_keys))
        sc = _build_multihop_scenario(
            scenario_id=f"s-{seq:04d}",
            tier="T2",
            pool="standard",
            entity_chain=chain_ents,
            target_attrs=target_attrs,
            questions_by_entity=questions_by_entity,
            doc_by_id=doc_by_id,
            corpus_link_docs=link_documents,
            all_base_doc_ids=all_base_doc_ids,
        )
        scenarios.append(sc)
        tier_counts["T2"] += 1

    # 3. Standard Pool T3 (66 scenarios)
    for chain_idx in t3_std_chains_idx:
        seq += 1
        chain_ents = [standard_entities[i] for i in chain_idx]
        target_attrs = []
        for i, ent in enumerate(chain_ents):
            if i < len(chain_ents) - 1:
                avail = [a for a in attr_keys if a not in used_outbound_attrs[ent]]
                if not avail:
                    raise RuntimeError(f"No available attributes left for {ent} (any-hop non-final reuse limit exceeded)")
                attr = rng_standard.choice(avail)
                used_outbound_attrs[ent].add(attr)
                target_attrs.append(attr)
            else:
                target_attrs.append(rng_standard.choice(attr_keys))
        sc = _build_multihop_scenario(
            scenario_id=f"s-{seq:04d}",
            tier="T3",
            pool="standard",
            entity_chain=chain_ents,
            target_attrs=target_attrs,
            questions_by_entity=questions_by_entity,
            doc_by_id=doc_by_id,
            corpus_link_docs=link_documents,
            all_base_doc_ids=all_base_doc_ids,
        )
        scenarios.append(sc)
        tier_counts["T3"] += 1

    # 4. Reserved Hard Pool T3 (150 scenarios)
    for chain_idx in t3_res_chains_idx:
        seq += 1
        chain_ents = [reserved_entities[i] for i in chain_idx]
        target_attrs = []
        for i, ent in enumerate(chain_ents):
            if i < len(chain_ents) - 1:
                avail = [a for a in attr_keys if a not in used_outbound_attrs[ent]]
                if not avail:
                    raise RuntimeError(f"No available attributes left for {ent} (any-hop non-final reuse limit exceeded)")
                attr = rng_reserved.choice(avail)
                used_outbound_attrs[ent].add(attr)
                target_attrs.append(attr)
            else:
                target_attrs.append(rng_reserved.choice(attr_keys))
        sc = _build_multihop_scenario(
            scenario_id=f"r-{seq:04d}",
            tier="T3",
            pool="reserved",
            entity_chain=chain_ents,
            target_attrs=target_attrs,
            questions_by_entity=questions_by_entity,
            doc_by_id=doc_by_id,
            corpus_link_docs=link_documents,
            all_base_doc_ids=all_base_doc_ids,
        )
        scenarios.append(sc)
        tier_counts["T3"] += 1

    if len(scenarios) != 350:
        raise ValueError(f"Expected 350 scenarios, got {len(scenarios)}")

    # Deduplicate link documents by ID (content-addressed records shared across chains)
    unique_link_docs: Dict[str, Dict[str, Any]] = {}
    for d in link_documents:
        if d["id"] not in unique_link_docs:
            unique_link_docs[d["id"]] = d

    all_corpus_documents = documents + list(unique_link_docs.values())
    if len(all_corpus_documents) != len({d["id"] for d in all_corpus_documents}):
        raise ValueError("Duplicate document IDs detected in corpus documents!")

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
