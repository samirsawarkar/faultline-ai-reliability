# FAULTLINE Phase 2 — Decision Log

Append-only. Date · id · decision · why · reversal cost.

> **Note on numbering:** This log uses `D-0NN` for tactical and engineering implementation decisions. Program-level decisions `D1`–`D7` are defined in `planning/cto/PHASE2-BUILD.md`.

---

### 2026-08-31 · D-001 · Phase 2 clean-room stats implementation and validation strategy

**Decision.** Implement `faultline_p2.stats` with clean-room, self-contained standard library modules (`intervals.py`, `paired.py`, `mathfns.py`, `passk.py`) validated directly against committed Day 14 evidence fixtures (`stats_verification.json` and `paired_comparison.json`).

**Why.** While Day 14's core modules (`intervals.py`, `paired.py`, `mathfns.py`) are self-contained, Day 14's test suite and packaging depend on test fixtures (`day14/tests/conftest.py`) and legacy experiment harness code. A clean-room implementation in `faultline_p2.stats` provides a minimal, typed Phase 2 statistics library with zero legacy test fixture coupling, while golden-evidence agreement tests guarantee exact numerical continuity across Wilson intervals, McNemar tests, bootstrap intervals, and MEC estimators (`pass_hat_k`, `naive_p_k`).

**Reversal cost.** Low; the public API in `faultline_p2.stats` is frozen and verified against committed Day 14 golden fixtures and property tests.

---

### 2026-08-31 · D-002 · Link layer documents, opaque IDs, traversal sources, and bounded reuse

**Decision.**
1. Introduce Phase-2-owned link layer documents with content-addressed opaque IDs (`link-{hashlib.sha256(text)[:12]}`) composed on top of frozen `build_env` to map intermediate answer tokens to subsequent entity names without metadata leakage (no scenario IDs or hop positions in document IDs or titles).
2. Maintain `traversal_sources` listing all required fact and link documents in exact sequential traversal order (1 for T1, 5 for T2, 9 for T3) for retrieval failure attribution (P12).
3. Preserve `required_sources` (fact documents: 1 for T1, 3 for T2, 5 for T3) and `required_source` (final hop fact document) so the oracle ground-truth condition remains unambiguous.
4. Scale entity universe to 300 entities (150 standard pool, 150 reserved hard pool) to enforce a strict any-hop document reuse bound $\le 5$ across all 1,348 fact hop-slots.

**Why.** `build_env` generates isolated fact documents with unique coined tokens and no cross-entity references. Without a link layer, intermediate prompts are forced to either name the next entity or leak its unique attributes (short-circuiting the retrieval chain). Link documents provide the bridge: hop $N$'s prompt refers only to hop $N-1$'s answer token, requiring the model to retrieve the link document to discover the next entity's identity, then retrieve that entity's fact document. Opaque IDs prevent models from bypassing traversal via ID pattern matching. Scaling entities to 300 guarantees low scenario correlation across hops while staying within deterministic bounds.

**Reversal cost.** Low; link documents and traversal structures are deterministically generated and self-contained within Phase 2.

## D-003 · Search Snippet Bound
**Date:** 2026-09-01
**Context:** AMENDMENTS.md A-002 requires search to return a snippet to reduce steps, but bounded so it cannot dump the corpus.
**Decision:** Snippets are 500 characters. If the match is in the text, it centers a 500-char window on the first occurrence of the query. Otherwise, it returns the first 500 chars of the text.
**Consequences:** One search surfaces the required fact for single-hop scenarios or immediate link records, reducing token volume and steps, but 500 chars is <10% of typical document sizes so it prevents full corpus dumping via generic searches.

### D-004: Tokenizer as Estimator
We added `tiktoken` to `pyproject.toml` as a dependency. The `cl100k_base` tokenizer is used as an ESTIMATOR for token counts. For non-OpenAI models, this provides a rough approximation rather than an exact count.

---

### 2026-09-12 · D-005 · Step Cap 24 (MEC v1.3) & P6 Pass^k Decay Validation
**Decision.** Formally adopt Amendment A-003 raising agent step cap $12 \to 24$ for Phase 2 multi-hop sweeps under MEC v1.3. Seal Project P6 empirical results evaluating joint reliability ($\text{pass}^k$) across R2 (`glm-5.3-flash`), R4 (`gpt-5.6-luna`), and R6 (`deepseek-v4-pro`) on 150 reserved hard Tier 3 scenarios ($k=3$, 1,350 agent runs).

**Why.** Tier 3 5-hop scenarios require a minimum of 10 steps (9 retrievals + 1 answer). A 12-step cap left an unworkable 2-step margin causing 49% cap saturation and artificial floor collapse. With `step_cap=24`, R2 achieved 63.11% pass@1 (only 4.0% cap saturation) and 22.67% pass$^3$, and R4 demonstrated a $6.06\times$ failure concentration ratio, providing an unfloored empirical basis for Publication #1 and Projects P7/P8.

**Reversal cost.** Low; governed by pre-registered trigger in Amendment A-002 and verified against empirical step distributions.

