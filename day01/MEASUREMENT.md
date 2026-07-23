# MEASUREMENT.md — FAULTLINE measurement contract (v1.0.0)

This document is the contract that makes every number FAULTLINE reports honest.
If a measurement is not defined here, it does not count.

## 1. Unit of measurement

The atomic measurement is one **oracle verdict** over a `(question, response)`
pair:

```
response = { "answer": str, "cited_sources": [doc_id, ...] }
verdict  = oracle_check(question, response)
         = { correct, cited_required, passed, ... }
```

- `correct`        — the question's unique answer token appears in `answer`
  (after `normalize`: casefold + whitespace-collapse).
- `cited_required` — `question.required_source` is in `cited_sources`.
- `passed`         — `correct AND cited_required`.

A system's score on a seed is `sum(passed) / len(questions)`. Nothing else is a
headline metric in FAULTLINE.

## 2. Why BOTH correct and cited (the honesty rule)

A right answer with the wrong (or no) citation is **not** counted as a pass.
Requiring the source that actually contains the fact separates *retrieval* from
*lucky guessing / parametric recall*. Rewarding a correct-but-ungrounded answer
would let a system look good on a faultline it never actually crossed. See
hand-check cases 3–5 in `evidence/oracle_handcheck.json`.

## 3. Determinism guarantees (the pass/fail gate for Day 1)

- **Environment.** `build_env(seed)` is a pure function of `seed`. The only
  entropy source is `random.Random(seed)` (Mersenne Twister — specified and
  stable across CPython versions and OSes). Output ordering never depends on
  `set`/`dict` hash order; every order is generation order or an explicit sort.
- **Serialization.** `canonical_bytes` = `json.dumps(sort_keys=True,
  ensure_ascii=True, indent=2)` + single trailing `\n`. No timestamps, host
  names, paths, or `PYTHONHASHSEED` leak into output.
- **Oracle.** `oracle_check` is a pure function of `(question, response)` — no
  model calls, no clock, no randomness.

"Identical output" is defined precisely as **equal `canonical_bytes`** (equally,
equal sha256 of those bytes).

## 4. What is verified, and how

| Property                                   | Evidence |
|--------------------------------------------|----------|
| Same seed → byte-identical (same process)  | `tests/test_determinism.py::test_same_seed_byte_identical_in_process` |
| Byte-identical across processes & hashseeds| `tests/test_determinism.py::test_byte_identical_across_fresh_processes_and_hashseeds`, `evidence/determinism_report.txt` |
| Distinct seeds → distinct envs (20 seeds)  | `tests/test_determinism.py::test_different_seeds_differ`, `evidence/seed_digests.tsv` |
| Oracle is deterministic                    | `tests/test_determinism.py::test_oracle_is_deterministic` |
| Each answer has exactly one source         | `tests/test_oracle.py::test_required_source_is_unique_per_answer_token` |
| Oracle matches human judgment (10 cases)   | `scripts/handcheck.py`, `evidence/oracle_handcheck.json` |

## 5. Reproduce

```
python -m pytest tests/ -v                 # determinism + oracle gate
python scripts/experiment_determinism.py   # 20 seeds × 2 processes → report
python scripts/handcheck.py                # 10 hand-checked oracle cases
python scripts/gen.py --seed 7             # emit a canonical environment
```

## 6. Scope / non-goals (v1.0.0)

- No retrieval or model system is scored yet — Day 1 builds only the *ruler*.
- Answer matching is exact-token containment. It is intentionally strict; the
  unique coined tokens make paraphrase-tolerance unnecessary and ambiguity
  impossible. Any loosening is a spec change and bumps `SPEC_VERSION`.

## 7. Change control

Any change to vocabularies, generation order, templates, `canonical_bytes`, or
oracle logic changes historical numbers and **must** bump `SPEC_VERSION` in
`faultline/env.py` and be recorded in `DECISIONS.md`.
