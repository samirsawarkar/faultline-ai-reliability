# FAULTLINE Phase 2 — Decision Log

Append-only. Date · id · decision · why · reversal cost.

---

### 2026-08-31 · D-001 · Phase 2 stats implementation and reuse strategy

**Decision.** Implement `faultline_p2.stats` with clean, self-contained standard library modules (`intervals.py`, `paired.py`, `mathfns.py`, `passk.py`) rather than copying Day 14 package-level files, while asserting strict numerical agreement against Day 14 committed evidence (`stats_verification.json` and `paired_comparison.json`).

**Why.** `day14/faultline_stats` contains experiment runners coupled to Phase 1 simulator days (day08/day09/day10). The mathematical primitives (`norm_ppf`, `wilson`, `mcnemar`, `bootstrap`) and the new MEC metrics (`pass_hat_k`, `naive_p_k`) are pure functions of data with zero external dependencies. A clean implementation avoids legacy coupling while verified tests ensure exact statistical continuity.

**Reversal cost.** Low; the public API in `faultline_p2.stats` is frozen and verified by property and regression tests.
