# FAULTLINE PHASE 2 — PRE-REGISTERED HYPOTHESES

**Frozen:** 2026-09-01 · against `MEC v1.0`
**Pre-registration:** the git commit that adds this file is the timestamp.
**Change policy:** never edited. Revisions go in `AMENDMENTS.md`, by the owner only.

Each hypothesis states what would falsify it *before* the data exists. A hypothesis that
cannot fail is not registered here.

---

| ID | Project | Hypothesis | Falsified by |
|---|---|---|---|
| H1 | P3 | Real-model grounded pass rate on T3 is below the simulator baseline | Wilson CIs overlap, or real ≥ simulator |
| H2 | P4 | ≥2 discovered failure modes are absent from the injected F1–F6 catalog | every mode maps onto the catalog |
| H3 | P5 | A cheap judge (R2) reaches κ ≥ 0.7 against human labels on ≥3 of 5 modes | measured κ below threshold |
| H4 | **P6** | **Measured pass³ exceeds naive (pass@1)³ for ≥4 of 6 rungs** | Wilson CI of measured contains the naive point |
| H5 | P6 | Deviation from naive is larger for cheap rungs than frontier | rank correlation across the ladder is null or reversed |
| H6 | P7 | Same model, 2+ endpoints, grounded rates with disjoint CIs | CIs overlap across all endpoint pairs |
| H7 | P8 | Bounded + typed contracts reduce ASR vs published MCPTox rates | ASR CI overlaps or exceeds the published band |
| H8 | P12 | Retrieval owns >50% of grounding failures | attribution CI excludes 50% on the generator side |

---

## H1 — declared limitations, stated before the run

Two things constrain H1, and both are recorded now so neither can be presented later as
a discovery.

**Comparability.** The Phase 2 document store is 1,164 documents of which 804 (69.1%) are
link records introduced by Phase 2's own chaining design. The simulator baseline was
measured against a store with no link layer. Real T3 and simulator T3 are therefore not
matched environments, and any gap confounds model capability with retrieval difficulty.
H1 is a directional check, not a clean contrast, and must be reported as such.

**Power.** Per-tier n≈67 in the standard pool gives a Wilson interval near ±11 pp. H1 is
detectable only for large differences. Per MEC v1.0, anything smaller is INCONCLUSIVE,
never "no difference".

---

## H4 — the headline, and the commitment

If H4 holds: *retry helps less than independence assumes, because failures concentrate on
specific scenarios.*

If H4 fails: *agent failures on grounded QA are closer to i.i.d. than the field assumes,
and retry budgets are being under-spent.*

**Both publish.** Which one ships is decided by the data, and that decision is made here,
before any of it exists. A clean null on H4 is a result, not a failed experiment.

---

## Discipline

- No hypothesis is added, removed, or reworded after this commit.
- No hypothesis is tested twice on the same data.
- P5's test set is read once.
- The P6 hard subset is drawn from the reserved pool, which is disjoint from the standard
  pool P3 measures on.
