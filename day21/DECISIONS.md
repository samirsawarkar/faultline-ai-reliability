# DECISIONS.md — Day 21 (silent fallback degradation) decision log

Append-only. Date · id · decision · why · reversal cost.

---

### 2026-07-31 · D21-001 · Availability and quality share the same paired seeds
**Decision.** Primary-only and fallback-enabled configurations run the same 120
request seeds with the same primary outage.
**Why.** Different populations would confound fallback behavior with request
difficulty. Pairing makes each availability and service-quality difference
attributable to configuration.
**Reversal cost.** Low; the scenario generator owns population size and outage rule.

### 2026-07-31 · D21-002 · Report conditional quality and service quality separately
**Decision.** Report strict quality / answered and strict-quality passes / all
requests, never one without the other.
**Why.** Conditional quality exposes harm in delivered answers; service quality also
charges silence. In Q4 the first falls 0.25 while the second rises 0.0833. Either
alone tells an incomplete story.
**Reversal cost.** None; both are additive views of the same records.

### 2026-07-31 · D21-003 · Route provenance selects the slice but does not certify quality
**Decision.** Use `served_by` / `is_fallback` to identify fallback answers, then
measure their content independently.
**Why.** Provenance answers “where,” not “how good.” The attack preserves complete,
consistent provenance while 30 answers fail strict quality.
**Reversal cost.** None; this preserves the Day-20 contract.

### 2026-07-31 · D21-004 · The Day-16 judge is advisory, pointwise, and non-core
**Decision.** Require its validation report and core-scoring prohibition, use only
pointwise `accept`, and never write oracle or strict-quality truth from judge output.
**Why.** Day 16 measured κ=0.5, pairwise positional bias, and a token-order blind
spot. The judge can add signal without being promoted beyond its evidence.
**Reversal cost.** Medium; a new judge may replace it only after the same validation
harness passes on the target population.

### 2026-07-31 · D21-005 · Keep and publish the known detector misses
**Decision.** Do not patch the simulated judge's token-order blind spot in the
headline detector; commit every false-negative seed and slice.
**Why.** Q4 requires explicit judge caveats. A perfect score created by adding the
ground-truth check into the detector would be circular and would erase the evidence
needed to defend its limits.
**Reversal cost.** None; production can add a separate deterministic token check
without rewriting this benchmark.

### 2026-07-31 · D21-006 · The mission fail condition is executable
**Decision.** The report gate passes only when availability and fallback quality are
reported together, the judge stays outside core scoring, and every detector false
negative is surfaced.
**Why.** “Availability up” is the precise claim this mission forbids when quality is
absent. Encoding the rule prevents a future renderer from silently regressing to
the flattering metric.
**Reversal cost.** None; this is the mission contract.
