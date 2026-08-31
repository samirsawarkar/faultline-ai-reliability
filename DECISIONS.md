# FAULTLINE Phase 2 — Decision Log

Append-only. Date · id · decision · why · reversal cost.

> **Note on numbering:** This log uses `D-0NN` for tactical and engineering implementation decisions. Program-level decisions `D1`–`D7` are defined in `planning/cto/PHASE2-BUILD.md`.

---

### 2026-08-31 · D-001 · Phase 2 clean-room stats implementation and validation strategy

**Decision.** Implement `faultline_p2.stats` with clean-room, self-contained standard library modules (`intervals.py`, `paired.py`, `mathfns.py`, `passk.py`) validated directly against committed Day 14 evidence fixtures (`stats_verification.json` and `paired_comparison.json`).

**Why.** While Day 14's core modules (`intervals.py`, `paired.py`, `mathfns.py`) are self-contained, Day 14's test suite and packaging depend on test fixtures (`day14/tests/conftest.py`) and legacy experiment harness code. A clean-room implementation in `faultline_p2.stats` provides a minimal, typed Phase 2 statistics library with zero legacy test fixture coupling, while golden-evidence agreement tests guarantee exact numerical continuity across Wilson intervals, McNemar tests, bootstrap intervals, and MEC estimators (`pass_hat_k`, `naive_p_k`).

**Reversal cost.** Low; the public API in `faultline_p2.stats` is frozen and verified against committed Day 14 golden fixtures and property tests.

---

### 2026-08-31 · D-002 · Link layer documents for genuine multi-hop sequential traversal

**Decision.** Introduce Phase-2-owned link layer documents (`link-{scenario_id}-hop{N}`) composed on top of frozen `build_env` to map intermediate answer tokens to subsequent entity names. In `Scenario`, `required_sources` lists the 5 distinct fact documents in traversal order, with `required_source` set to the final hop's fact document.

**Why.** `build_env` generates isolated fact documents with unique coined tokens and no cross-entity references. Without a link layer, intermediate prompts are forced to either name the next entity or leak its unique attributes (short-circuiting the retrieval chain). Link documents provide the bridge: hop $N$'s prompt refers only to hop $N-1$'s answer token, requiring the model to retrieve the link document to discover the next entity's identity, then retrieve that entity's fact document. This ensures genuine sequential retrieval depth while keeping the oracle ground-truth condition well-defined on the final fact document.

**Reversal cost.** Low; link documents are deterministically generated and self-contained within Phase 2.
