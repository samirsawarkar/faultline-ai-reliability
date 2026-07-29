# DECISIONS.md — Day 23 (seeded cascade) decision log

Append-only. Date · id · decision · why · reversal cost.

---

### 2026-08-02 · D23-001 · One seed and one full configuration are the replay key
**Decision.** No hidden environment variables, wall clock, or global random state
participate in the incident.
**Why.** The mission fails if the cascade needs undocumented state. The scenario
artifact serializes every policy field and its digest.
**Reversal cost.** None; this is the reproducibility contract.

### 2026-08-02 · D23-002 · F2 latency is the sole initiating fault
**Decision.** The canonical trigger is `F2:primary_latency_spike`; downstream
semantic drift is labelled propagated, not co-root.
**Why.** Multiple initiators would make the incident ambiguous and weaken the
causal graph. The secondary fault becomes reachable only through recovery routing.
**Reversal cost.** Medium; a multi-root incident needs a different graph contract.

### 2026-08-02 · D23-003 · Recovery mechanisms live inside the causal chain
**Decision.** M2/M3/M4/M6 are causal transitions or side effects; M5 is terminal
containment.
**Why.** Treating recovery as a footnote would erase the retry amplification,
fallback exposure, and re-entry that turn one timeout into a cascade.
**Reversal cost.** None; the labels reflect observed component actions.

### 2026-08-02 · D23-004 · Every graph node must cite trace spans
**Decision.** A causal event without at least one resolving `span_ref` fails the
audit.
**Why.** The narrative and graph must remain grounded in captured evidence rather
than retrospective prose.
**Reversal cost.** None; additional references are additive.

### 2026-08-02 · D23-005 · Stable replay includes labels, not only bytes
**Decision.** Compare incident digest, trace digest, and ordered label chain across
20 runs and four hash seeds.
**Why.** Identical bytes prove determinism; identical labels prove the same
incident explanation recurred.
**Reversal cost.** Low; a future schema version can migrate labels explicitly.

### 2026-08-02 · D23-006 · The ceiling abort is an error span but a contained incident
**Decision.** Raise inside the M5 span so the trace records a complete error, catch
at the incident root, and report terminal containment rather than success.
**Why.** The ceiling performed as designed, but the user still received no correct
answer. Trace status and product outcome answer different questions.
**Reversal cost.** None; both facts remain visible.

### 2026-08-02 · D23-007 · Causal claims carry an intervention caveat
**Decision.** State that the graph is intervention-informed in the deterministic
simulator, not proof that temporal order establishes production causality.
**Why.** A reproducible simulator controls confounders that production traces do
not. The evidence should not be marketed beyond that boundary.
**Reversal cost.** None; it protects claim integrity.
