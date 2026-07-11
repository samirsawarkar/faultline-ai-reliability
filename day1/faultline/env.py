"""Deterministic environment generator for FAULTLINE.

Contract (see MEASUREMENT.md):
  - build_env(seed) is a pure function of `seed` only.
  - Same seed  -> byte-identical canonical serialization, on any machine,
    under any PYTHONHASHSEED, in any process.
  - Different seed -> different environment (with overwhelming probability).

Determinism rules enforced here:
  1. The ONLY source of entropy is random.Random(seed) (Mersenne Twister,
     specified and stable across CPython versions and platforms).
  2. We never iterate over a set or a hash-ordered dict to build output;
     every ordering is either generation order or an explicit sort.
  3. Every answer VALUE is a globally unique coined token, so each question
     maps to exactly one document -> the "required source" is well defined.
  4. Serialization is canonical: sort_keys, ascii, fixed indent, LF, one
     trailing newline. No timestamps, no host info, no PYTHONHASHSEED leakage.
"""
from __future__ import annotations

import hashlib
import json
import random
from typing import Any, Dict, List

SPEC_VERSION = "1.0.0"

# ---- Fixed vocabularies (order is part of the contract; do not reorder) ----
# Reordering any of these lists changes generated output for a given seed and
# is therefore a breaking change requiring a SPEC_VERSION bump.
_ENTITY_PREFIX = [
    "Aster", "Borel", "Cinder", "Dovetail", "Ember", "Fathom",
    "Girona", "Halcyon", "Ironwood", "Juniper", "Kestrel", "Lodestar",
    "Marrow", "Nimbus", "Orrery", "Peregrine", "Quill", "Riven",
    "Solace", "Tamarisk", "Umbra", "Verdigris", "Willow", "Xebec",
    "Yarrow", "Zephyr",
]
_ENTITY_SUFFIX = ["Labs", "Works", "Foundry", "Collective", "Systems", "Union"]

# attribute key -> question template. Keys are sorted before use so the set of
# attributes offered is deterministic regardless of dict literal order.
_ATTRIBUTES: Dict[str, str] = {
    "internal_codename": "What is the internal codename of {entity}?",
    "headquarters_district": "In which district is {entity} headquartered?",
    "flagship_product": "What is the flagship product of {entity}?",
    "external_auditor": "Which firm is the external auditor of {entity}?",
    "archival_reference": "What is the archival reference of {entity}?",
}

# Token stems used to coin unique answer values.
_TOKEN_STEM = [
    "Alto", "Basalt", "Cobalt", "Drift", "Ferro", "Gossamer",
    "Helix", "Indigo", "Jade", "Kelvin", "Lumen", "Mica",
    "Nyx", "Onyx", "Prism", "Quartz", "Rune", "Sable",
    "Talc", "Ultra", "Vellum", "Wisp", "Xeno", "Yolk", "Zinc",
]


def _coin_token(index: int) -> str:
    """Globally unique, human-readable token. Uniqueness comes from `index`."""
    stem = _TOKEN_STEM[index % len(_TOKEN_STEM)]
    return f"{stem}-{4000 + index:04d}"


def build_env(seed: int, n_entities: int = 12, n_distractors: int = 6) -> Dict[str, Any]:
    """Return the deterministic environment for `seed`.

    The structure:
      documents:  fact docs (one per entity) + distractor docs (noise, no
                  answer-bearing values). Distractors mention entity names so
                  naive keyword retrieval is tempted into a wrong required source.
      questions:  one question per (entity, attribute) pair. Each carries the
                  correct answer and the single required_source doc id.
    """
    if not isinstance(seed, int):
        raise TypeError(f"seed must be int, got {type(seed).__name__}")

    rng = random.Random(seed)
    attr_keys = sorted(_ATTRIBUTES)  # explicit sort: hash-independent ordering

    # --- Build entities with globally-unique answer values ---
    token_counter = 0
    entities: List[Dict[str, Any]] = []
    used_names = set()
    for i in range(n_entities):
        # Draw a unique display name deterministically from the seeded RNG.
        while True:
            name = f"{rng.choice(_ENTITY_PREFIX)} {rng.choice(_ENTITY_SUFFIX)}"
            if name not in used_names:
                used_names.add(name)
                break
        facts = {}
        for attr in attr_keys:
            facts[attr] = _coin_token(token_counter)
            token_counter += 1
        entities.append({"name": name, "doc_id": f"doc-{i:04d}", "facts": facts})

    # --- Fact documents (one per entity) ---
    documents: List[Dict[str, Any]] = []
    for ent in entities:
        sentences = [f"{ent['name']} is a registered organization in the FAULTLINE corpus."]
        for attr in attr_keys:  # sorted -> stable sentence order
            label = attr.replace("_", " ")
            sentences.append(f"The {label} of {ent['name']} is {ent['facts'][attr]}.")
        documents.append({
            "id": ent["doc_id"],
            "title": ent["name"],
            "text": " ".join(sentences),
        })

    # --- Distractor documents: mention entities, contain NO answer values ---
    for d in range(n_distractors):
        subjects = rng.sample([e["name"] for e in entities],
                              k=min(2, len(entities)))
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

    # --- Questions: one per (entity, attribute) ---
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
        "counts": {
            "documents": len(documents),
            "questions": len(questions),
            "entities": len(entities),
            "distractors": n_distractors,
        },
        "documents": documents,
        "questions": questions,
    }


def canonical_bytes(obj: Any) -> bytes:
    """Byte-stable JSON. This exact function defines 'identical output'."""
    text = json.dumps(
        obj,
        sort_keys=True,       # key order independent of construction/hash
        ensure_ascii=True,    # no locale/encoding drift
        indent=2,
        separators=(",", ": "),
    )
    return (text + "\n").encode("utf-8")  # LF + single trailing newline


def env_digest(seed: int) -> str:
    """sha256 hex of the canonical env bytes for `seed`."""
    return hashlib.sha256(canonical_bytes(build_env(seed))).hexdigest()
