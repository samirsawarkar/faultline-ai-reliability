# DECISIONS — Day 28 publication argument

Append-only. Date · id · decision · why · reversal cost.

---

### 2026-07-30 · D28-001 · Findings precede method

**Decision.** Publish the Q1–Q5 result chain before experimental mechanics.

**Why.** A cold reader should learn the conclusion and its boundary before
deciding whether to inspect the method.

**Reversal cost.** Low; section order is editorial, while claim identifiers stay
stable.

### 2026-07-30 · D28-002 · A claim is a registered prose paragraph

**Decision.** Every substantive paragraph before the reproduction appendix must
carry one `CLAIM:Cxx` marker and an exact entry in `claims.json`.

**Why.** Auditing only bold headlines would let unsupported interpretation enter
between supported numbers.

**Reversal cost.** Medium; splitting or combining prose requires an intentional
claim-ledger migration.

### 2026-07-30 · D28-003 · Bind rendered tokens, not copied summaries

**Decision.** Each quantitative claim stores its source artifact, RFC-6901 JSON
pointer, and display format.

**Why.** The audit should prove that the visible token is the committed result,
not merely that a nearby file exists.

**Reversal cost.** Low; a result schema change produces a precise failing pointer.

### 2026-07-30 · D28-004 · Source figures from result JSON

**Decision.** Generate one coherent SVG for each research question and embed its
source paths in accessible metadata.

**Why.** A hand-maintained chart can disagree with correct prose. Regeneration and
byte-determinism make figure drift testable.

**Reversal cost.** Low; visual style can change without changing result sources.

### 2026-07-30 · D28-005 · Captions must stand alone

**Decision.** Every caption names the population, comparison, result, uncertainty
where applicable, and the caveat needed to avoid overclaiming.

**Why.** Figures travel independently in reviews and social publication.

**Reversal cost.** Low; caption drift is checked in both the article and caption
sheet.

### 2026-07-30 · D28-006 · Do not pool Q1–Q5

**Decision.** Synthesize mechanisms and decision rules, not a common effect size.

**Why.** The experiments use different populations, outcomes, and units. A pooled
number would be false precision.

**Reversal cost.** None unless a future preregistered common population exists.

### 2026-07-30 · D28-007 · Publish P4 as an upper bound

**Decision.** Keep the perfect retryability signal and strict simulator-oracle
guard in every P4 recommendation and caption.

**Why.** Omitting either would silently substitute the known-limited Day 16 judge
for simulator truth.

**Reversal cost.** Medium; a deployable recommendation needs measured routing and
guard error, cost, and latency.

### 2026-07-30 · D28-008 · Preserve Day 26 and Day 27 release evidence

**Decision.** Add Day 28 to the live repository test and reproduction commands,
while leaving the pinned `v0.27.0-rc1` test count and cold-reader transcript
unchanged.

**Why.** Historical release evidence must remain truthful to the revision it
attests; Day 28 has its own checkpoint.

**Reversal cost.** Low when a new release candidate and cold reproduction are
cut.
