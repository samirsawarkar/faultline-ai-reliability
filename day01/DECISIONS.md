# DECISIONS.md — FAULTLINE decision log

Append-only. Each entry: date, decision, why, and what it would take to reverse.

---

### 2026-07-11 · D-001 · Determinism is a gate, not a nicety
**Decision.** The Day-1 environment and oracle must be bit-for-bit reproducible;
non-determinism is a hard failure, not a warning.
**Why.** Every later FAULTLINE number is a count of oracle verdicts over seeded
environments. If the ruler shifts between runs, no downstream comparison is
trustworthy. Honesty has to be built in at the bottom.
**Reversal cost.** None desired; this is foundational.

### 2026-07-11 · D-002 · `random.Random(seed)` as the only entropy source
**Decision.** Use Python's seeded Mersenne Twister; forbid `set`/`dict`-order
iteration in output construction; sort or use generation order everywhere.
**Why.** MT with a fixed seed is specified and stable across CPython versions
and platforms. Hash-order iteration is the classic silent determinism leak
(varies with `PYTHONHASHSEED`), so we ban it and test against it directly.
**Reversal cost.** Swapping RNG changes all seeds → `SPEC_VERSION` bump.

### 2026-07-11 · D-003 · Canonical serialization defines "identical"
**Decision.** `canonical_bytes` = `json.dumps(sort_keys, ensure_ascii, indent=2)`
+ single trailing `\n`; sha256 of these bytes is the comparison key.
**Why.** "Same output" needs one precise definition. Sorted keys make output
independent of construction order; ASCII avoids encoding drift; no timestamps or
host data means no environmental leakage.
**Reversal cost.** Any format change alters every digest → `SPEC_VERSION` bump.

### 2026-07-11 · D-004 · Answer values are globally-unique coined tokens
**Decision.** Every answer is a unique token like `Prism-4014`; entities and
attributes are semantic flavor, but the *value* is unique corpus-wide.
**Why.** It guarantees each question has exactly ONE document containing its
answer, so "required source" is unambiguous and exact-substring matching cannot
be satisfied by a different answer. This is enforced by a test.
**Reversal cost.** Realistic (collision-prone) values would need a different
oracle matcher; deferred, would bump `SPEC_VERSION`.

### 2026-07-11 · D-005 · The oracle requires the source, not just the answer
**Decision.** `passed = correct AND cited_required`.
**Why.** FAULTLINE is about whether systems *ground* their answers. A correct
token with a missing/wrong citation is retrieval failure masquerading as
success; the oracle refuses to reward it. This is the core measurement stance.
**Reversal cost.** Dropping the citation requirement would redefine every score;
would bump `SPEC_VERSION`.

### 2026-07-11 · D-006 · Distractor documents in the corpus
**Decision.** Include memo documents that name entities but carry no answer
tokens.
**Why.** Without noise, naive keyword retrieval trivially wins and the required-
source rule is untested. Distractors give the oracle something to catch (see
hand-check case 4).
**Reversal cost.** Cosmetic count change; still a `SPEC_VERSION` bump because
digests move.

### 2026-07-11 · D-007 · Hand-check is enforced, not just displayed
**Decision.** `scripts/handcheck.py` encodes the human-expected verdict for each
of 10 cases and exits non-zero on any disagreement.
**Why.** "Hand-checking 10 cases" should leave a durable, re-runnable artifact,
not a one-time eyeball. The script *is* the record of that judgment.
**Reversal cost.** None; additive.
