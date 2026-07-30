# DECISIONS — Day 29 staff-engineer briefing

Append-only. Date · id · decision · why · reversal cost.

---

### 2026-07-30 · D29-001 · Demonstrate one incident, not the whole platform

**Decision.** Use the stale-fallback incident for the complete run → fault →
trace → recover → replay sequence.

**Why.** It contains availability, semantic quality, repetition, routing,
ceilings, trace causality, and a replay-verified fix in one controlled seed.

**Reversal cost.** Low; another incident can reuse the same five-beat contract.

### 2026-07-30 · D29-002 · Put the proof in the first screen

**Decision.** Open both the demo and case study with one sentence that states the
controlled comparison, outcome change, fix, and production boundary.

**Why.** A cold viewer should not have to infer the result from a chronology.

**Reversal cost.** Low; the comprehension rubric makes wording changes explicit.

### 2026-07-30 · D29-003 · Fix narrated duration at 165 seconds

**Decision.** Record five beats at a planned 2:45 pace while keeping the live
command immediate.

**Why.** The recording satisfies the staff-engineer attention budget; the compact
command keeps CI and reproduction fast.

**Reversal cost.** Low; frame timestamps and the cast-duration test change
together.

### 2026-07-30 · D29-004 · Use exactly five case-study numbers

**Decision.** Bind seed, legacy latency, fixed latency, fixed cost, and replay
count to Day 25 JSON pointers.

**Why.** These numbers establish identity, before/after outcome, resource
feasibility, and stability without turning the page into a dashboard.

**Reversal cost.** Medium; replacing a number requires both a decision and source
binding update.

### 2026-07-30 · D29-005 · Four case-study layers

**Decision.** Structure the page as decision, incident, evidence, and boundary.

**Why.** A staff engineer needs the conclusion, causal failure, verification, and
deployment limit—nothing else in the primary path.

**Reversal cost.** Low; the audit rejects missing or extra layers.

### 2026-07-30 · D29-006 · Attack verbosity with a cold-viewer proxy

**Decision.** Preserve a deliberately bloated attack fixture, score both
surfaces with the same rubric, and require baseline red → final green.

**Why.** “Concise” should be measured by proof extraction, concept coverage,
word budget, and reading-time proxy.

**Reversal cost.** Low; rubric changes are versioned in JSON.

### 2026-07-30 · D29-007 · Do not call the proxy a human study

**Decision.** Serialize `human_participant=false` and carry the caveat into the
README and checkpoint.

**Why.** Structural extractability is useful evidence, but it does not measure
real comprehension variance or time pressure.

**Reversal cost.** None; an actual peer attempt can be added without weakening
the proxy.

### 2026-07-30 · D29-008 · Publish four surfaces from one commit

**Decision.** Coordinate the repository entry point, Day 28 article, Day 29 demo,
and one-page case study in one publication bundle and push only after all gates
pass.

**Why.** A short claim without the deep evidence is marketing; deep evidence
without a short entry point is inaccessible.

**Reversal cost.** Low; future revisions can update all four bundle hashes.
