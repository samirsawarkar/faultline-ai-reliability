# FAULTLINE PHASE 2 — MASTER EXPERIMENT CONTRACT v1.0

**Frozen:** 2026-09-01
**Authority:** this document outranks every plan, work order, and README in the repo.
**Change policy:** never edited after this commit. Changes go in `AMENDMENTS.md` as
`A-NNN`, by the owner only. An amendment that breaks comparability with a published
result is not an amendment — it is a new experiment with a new contract version.

Every project's `results.json` must reference `MEC v1.0`.

---

## CORPUS

| | |
|---|---|
| generator | `faultline_p2.env.corpus.build_corpus`, composed on frozen `build_env` |
| master seed | **42** |
| spec version | 2.0.0 |
| content hash | `9d6d7fc7fbfd999d58157e6a88f256fd45aab97b4ea474b1a2852fe143d6a3a8` |
| scenario count | 350 — 200 standard + 150 reserved hard pool |
| standard pool | 67 T1 / 67 T2 / 66 T3 |
| reserved pool | 150 T3 (P6 draws its 150 from here; disjoint from standard) |
| tiers | T1 = 1 hop · T2 = 3 hops · T3 = 5 hops |
| document store | 1,164 unique — 300 fact · 60 distractor · 804 link (69.1%) |
| retrieval depth | T1 = 1 retrieval · T2 = 5 · T3 = 9 (`traversal_sources`) |
| regeneration | `make phase2-corpus` — deterministic under any `PYTHONHASHSEED` |

**Hop definition (this is the contract, not a description).** Hop N is answerable only
via hop N−1's answer. Enforced by test, not by intent:

- no hop prompt contains a token that uniquely identifies its own source document
  independently of the previous answer — measured 0/998
- no multi-hop scenario is solvable from its final hop alone — measured 0/283
- every hop N≥2 prompt carries exactly one identifying token, the previous answer
- fact-document reuse: ≤5 across all hops, ≤3 as a final hop (measured max 5 and 2)
- link document IDs are content-addressed and encode no scenario or hop position

**Link layer.** `build_env` mints globally unique tokens per (entity, attribute) and its
documents carry no cross-entity references, so sequential traversal is impossible without
a bridge. Phase 2 generates link documents mapping hop N−1's answer to entity N. This is
composition on top of `build_env`, never modification of it. See `DECISIONS.md` D-002.

---

## AGENT

| | |
|---|---|
| architecture | bounded reason → tool → observe |
| step cap | 8 |
| contracts | Pydantic v2 (2.13.4), `extra="forbid"` at every boundary |
| tools | 3 typed tools |
| harness | LiteLLM **1.98.0** (pinned) |
| temperature | 0.0 |
| max_tokens | 2048 |
| system prompt hash | **NOT YET SET** — authored at P1; setting it bumps this contract to v1.1 |

The system prompt does not exist at freeze time and no placeholder was invented. It is
the one field of this contract that is written after the freeze, once, and never again.

**Retrieval constraint (binding on P1).** The retrieval tool matches on content. Document
IDs are opaque to the agent and no ID encodes scenario identity or hop position. Exposing
IDs would let a model fetch the terminal link document and skip the chain, reintroducing
at runtime the defect the corpus design removes.

---

## ORACLE

| | |
|---|---|
| implementation | day01 `oracle_check`, **UNMODIFIED** |
| enforcement | sha256 `dc5eef1c64d6f2ba8e802d88bab1af90eaaa6bc778271d78525baba737d2be5f` |
| environment | day01 `build_env`, sha256 `6d3401305d705d4f72110754a3ee5de860aea9437c1eb7512f2038a34810816f` |
| pass condition | answer correct AND cites the one source holding the fact |
| authority | pure function · never an LLM · never overridden |

Both files are byte-for-byte copies under `faultline_p2/`, held by
`tests/phase2/test_frozen_copies.py`. Drift fails CI. "Unmodified" is a test, not a promise.

If real traces grade badly, the harness is wrong. The oracle is never adjusted to fit.

---

## MODEL LADDER — **PROVISIONAL**

Pre-flight authenticated **zero** rungs; no API credentials were configured in the build
environment. The prices and version strings below are configured values, not measured
ones. **This block is provisional and must be re-run and amended before the first paid
sweep.** Everything else in this contract is frozen.

| Rung | Model | $/1M in | $/1M out | Status |
|---|---|---|---|---|
| R1 | gemini-2.5-flash-lite | 0.10 | 0.40 | unverified |
| R2 | deepseek-v4-flash | 0.14 | 0.28 | unverified |
| R3 | deepseek-v4-pro | 0.435 | 0.87 | unverified |
| R4 | minimax-m3 | 0.60 | 2.40 | unverified |
| R5 | glm-5.2 | 1.40 | 4.40 | unverified |
| R6 | sonnet-class anchor | ~3 | ~15 | unverified |

Each model is pinned to ONE named endpoint. Provider, model version, and quantization are
logged in every span. Routing marketplaces are not the substrate — they are P7's subject.

All sweeps run OFF-PEAK. Peak rates are roughly 2×; that is a line item, not a detail.

---

## METRICS

**Primary** — `grounded_pass_rate` (oracle-verified: correct AND grounded) · `pass^k`
(all k trials succeed, averaged over scenarios; Yao et al. 2024).

**Secondary** — pass@1 · cost/run · tokens/run · latency p50/p95 · steps/run ·
judge TPR, TNR, Cohen's κ, corrected prevalence.

---

## STATISTICS

| | |
|---|---|
| intervals | Wilson 95% on every proportion, no exceptions |
| paired | McNemar — exact binomial when discordant < 25, chi-square above |
| bootstrap | 10,000 resamples, seeded |
| implementation | `faultline_p2.stats`, validated against day14 committed evidence |

**Declared power.** n=200 paired detects ~10 pp at 80%. Differences below 10 pp are
reported **INCONCLUSIVE**, never as "no difference". Per-tier n≈67 in the standard pool
gives roughly ±11 pp — declared before the run, not discovered after.

---

## JUDGE

Secondary instrument. Never overrides the oracle. Model pinned and frozen at P5.
Train/dev/test splits content-addressed. The test set is read **once**.

---

## BUDGET

Hard ceiling **USD 150**. Per-project caps live in `faultline_p2/cost` and are read from
this contract. Reaching a cap is a stop: halt, log, report. Never borrow from another
project. Every paid call requires explicit `--confirm` and prints a dry-run estimate first.

| P1 | P2 | P3 | P4 | P5 | P6 | P7 | P8 | P9 | P10 | P11 | P12 | reserve |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| $2 | $0 | $5 | $0 | $10 | $45 | $5 | $10 | $6 | $8 | $5 | $6 | $48 |

---

## ARTIFACTS

Every project ships `README.md`, `DECISIONS.md`, `results.json` (referencing MEC v1.0),
one figure, one `make` target, and raw traces — committed or hash-manifested, never
summarized-only. One make target per project, deterministic given the seed.

---

## PUBLICATION CRITERIA

A result publishes if it was pre-registered, is powered or explicitly declared
underpowered, is reproducible by one command, and is honest about limitations.

**A null result meeting these criteria publishes. No exceptions.**
