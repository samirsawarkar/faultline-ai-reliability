"""Phase 2 Corpus generator.

Deterministic multi-hop corpus composed on top of day01 build_env.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import random
from pathlib import Path
from typing import Any, Dict, List, Literal

from pydantic import BaseModel, ConfigDict, Field

from faultline_p2.env._day01_env import _ATTRIBUTES, build_env

SPEC_VERSION = "2.0.0"
_STRICT = ConfigDict(extra="forbid")


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
    env_seed: int
    documents: List[Dict[str, Any]]


class Corpus(BaseModel):
    model_config = _STRICT
    spec_version: str
    master_seed: int
    scenario_count: int
    standard_count: int
    reserved_count: int
    tier_counts: Dict[str, int]
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


_TIER_HOPS = {"T1": 1, "T2": 3, "T3": 5}


def _generate_scenario(
    scenario_id: str,
    tier: Literal["T1", "T2", "T3"],
    pool: Literal["standard", "reserved"],
    seed: int,
) -> Scenario:
    rng = random.Random(seed)
    hops = _TIER_HOPS[tier]

    # Use a derived env_seed with sufficient entities for multi-hop
    env_seed = seed % 1_000_000
    n_entities = max(12, hops + 4)
    n_distractors = 6
    env = build_env(env_seed, n_entities=n_entities, n_distractors=n_distractors)

    # Documents and entities from build_env
    doc_by_id = {d["id"]: d for d in env["documents"]}
    # entities are in fact docs doc-0000..doc-(n_entities-1)
    fact_docs = [d for d in env["documents"] if not d["title"].startswith("Analyst memo")]

    # Sample hops distinct entities in deterministic order
    chosen_docs = rng.sample(fact_docs, k=hops)
    attr_keys = sorted(_ATTRIBUTES.keys())

    chain: List[HopStep] = []
    for idx, doc in enumerate(chosen_docs, 1):
        entity_name = doc["title"]
        attr = rng.choice(attr_keys)
        prompt = _ATTRIBUTES[attr].format(entity=entity_name)

        # Find answer for this entity and attribute from questions in env
        matching_q = next(
            q
            for q in env["questions"]
            if q["entity"] == entity_name and q["attribute"] == attr
        )
        answer = matching_q["answer"]
        req_source = matching_q["required_source"]

        # Verify uniqueness: answer appears only in req_source
        assert answer in doc_by_id[req_source]["text"]

        chain.append(
            HopStep(
                hop_index=idx,
                prompt=prompt,
                answer=answer,
                required_source=req_source,
                entity=entity_name,
                attribute=attr,
            )
        )

    if hops == 1:
        composite_prompt = chain[0].prompt
    else:
        steps_text = " -> ".join(
            f"Step {h.hop_index}: {h.prompt}" for h in chain
        )
        composite_prompt = (
            f"Solve the {hops}-step question chain: {steps_text}. "
            f"Provide the final answer for Step {hops}."
        )

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
        env_seed=env_seed,
        documents=env["documents"],
    )


def build_corpus(seed: int = 42) -> Corpus:
    """Deterministic 300-scenario corpus: 200 standard + 100 reserved hard pool."""
    scenarios: List[Scenario] = []

    # Standard pool: 200 scenarios (70 T1, 70 T2, 60 T3)
    standard_spec = [("T1", 70), ("T2", 70), ("T3", 60)]
    # Reserved pool: 100 scenarios (all 100 T3 hard)
    reserved_spec = [("T3", 100)]

    seq = 0
    tier_counts = {"T1": 0, "T2": 0, "T3": 0}

    # Generate standard pool
    for tier, count in standard_spec:
        for i in range(count):
            seq += 1
            scenario_id = f"s-{seq:04d}"
            # Disjoint deterministic seed lane per pool, tier, index
            scenario_seed = (seed * 1_000_003) + (1 * 100_000) + (seq * 1_000) + i
            sc = _generate_scenario(
                scenario_id=scenario_id,
                tier=tier,  # type: ignore
                pool="standard",
                seed=scenario_seed,
            )
            scenarios.append(sc)
            tier_counts[tier] += 1

    # Generate reserved hard pool
    for tier, count in reserved_spec:
        for i in range(count):
            seq += 1
            scenario_id = f"r-{seq:04d}"
            scenario_seed = (seed * 1_000_003) + (2 * 100_000) + (seq * 1_000) + i
            sc = _generate_scenario(
                scenario_id=scenario_id,
                tier=tier,  # type: ignore
                pool="reserved",
                seed=scenario_seed,
            )
            scenarios.append(sc)
            tier_counts[tier] += 1

    assert len(scenarios) == 300
    assert sum(1 for s in scenarios if s.pool == "standard") == 200
    assert sum(1 for s in scenarios if s.pool == "reserved") == 100

    return Corpus(
        spec_version=SPEC_VERSION,
        master_seed=seed,
        scenario_count=len(scenarios),
        standard_count=200,
        reserved_count=100,
        tier_counts=tier_counts,
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
