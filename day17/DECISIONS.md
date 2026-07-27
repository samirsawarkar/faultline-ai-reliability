# DECISIONS.md — Day 17 (subgroup analysis + measurement gate) decision log

Append-only. Date · id · decision · why · reversal cost.

---

### 2026-07-27 · D17-001 · A contradiction means the interval excludes the headline — not mere point variation
**Decision.** A subgroup "contradicts" the headline only when its 95% Wilson
interval excludes the headline value. Point-estimate variation (rate ≠ headline) is
recorded but is not a contradiction.
**Why.** Every subgroup differs from the aggregate by chance; calling all of that
"contradiction" is noise. Requiring the interval to exclude the headline is the
honest bar — it means the subgroup's data is actually inconsistent with the claim.
**Reversal cost.** Low; the definition is one predicate.

### 2026-07-27 · D17-002 · Minimum sample size gates every conclusion
**Decision.** Subgroups with n < MIN_SAMPLES (5) are marked `insufficient`; their
interval is reported but no claim is drawn from them.
**Why.** Finely sliced (fault × severity) cells are n=2 here. Drawing conclusions
from them would manufacture findings from noise. Gating them is the difference
between "we don't know at this granularity" and a false claim.
**Reversal cost.** None; MIN_SAMPLES is a named constant.

### 2026-07-27 · D17-003 · Multiple-comparison correction (Holm-Bonferroni) on the reportable family
**Decision.** All reportable subgroup-vs-headline tests enter one Holm-Bonferroni
family; only survivors are called significant.
**Why.** Testing ~10 subgroups at α=0.05 expects a false positive by chance. Holm
controls the family-wise error rate while being uniformly more powerful than plain
Bonferroni. Without it, "we found a significant subgroup" is meaningless.
**Reversal cost.** Low; swap Holm for BH (FDR) if a less conservative rule is wanted.

### 2026-07-27 · D17-004 · Search for ordering reversals (Simpson), verified against a known paradox
**Decision.** `detect_ordering_reversal` compares the aggregate A-vs-B ordering to
each slice's ordering and flags reversals; it is verified against a hard-coded
kidney-stone-style Simpson's paradox.
**Why.** The mission's danger is a subgroup that reverses the headline. A detector
for it is only trustworthy if it fires on a paradox we already know is there — the
Day-14 verify-against-a-known-answer stance.
**Reversal cost.** None; additive.

### 2026-07-27 · D17-005 · Detection and hop-count axes are NOT pooled
**Decision.** Fault/severity subgroups come from the Day-13 detection dataset; the
hop-count axis comes from Day-7's reliability curve. They are reported side by side
but never merged into one table.
**Why.** They are different populations measuring different quantities (detection
correctness vs end-to-end reliability). Pooling them would itself be an aggregation
trap. Keeping them separate is the honest treatment of "slice by hops."
**Reversal cost.** None; a unified multi-hop detection dataset could be built later.

### 2026-07-27 · D17-006 · The audit independently re-derives contradictions and fails if any is ignored
**Decision.** `run_audit` recomputes the contradiction set from the analysis and
asserts the report acknowledged every one; the measurement gate fails on any
unacknowledged significant contradiction.
**Why.** This is the fail condition as a switch, not a promise. A report that quietly
dropped a contradicting subgroup is caught because the audit doesn't trust the
report's own list — it recomputes it.
**Reversal cost.** None; it is the deliverable's guarantee.

### 2026-07-27 · D17-007 · Commit the checkpoint WITH its known limitations
**Decision.** `known_limitations` is a first-class field (small n, under-powered
cells, the confounded severity-3 reversal, separate hop population, single dataset
version), rendered at the TOP of the findings doc.
**Why.** A subgroup analysis on n=44 is under-powered, and hiding that would be the
very sin the mission targets. Leading with limitations is how the checkpoint stays
defensible: the honest conclusion is "the spread is real but not yet significant."
**Reversal cost.** None; limitations shrink as the dataset grows.
