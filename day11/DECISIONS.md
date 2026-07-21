# DECISIONS.md — Day 11 (F5/F6 + the deterministic-vs-semantic map) decision log

Append-only. Date · id · decision · why · reversal cost.

---

### 2026-07-21 · D11-001 · A crisp, defended definition of the deterministic/semantic split
**Decision.** A detector is DETERMINISTIC if its verdict is a function of
structure / counts / equality / explicit flags with no model of correctness;
SEMANTIC if it needs a correctness or meaning model (a value invariant, or the
oracle/judge). The definition is stated in the map, LEARN, and the cards.
**Why.** The fail condition is precisely "cannot separate deterministic from
semantic detection." A separation is only credible if the criterion is explicit
and then applied uniformly to all six faults.
**Reversal cost.** None; it's the organizing definition.

### 2026-07-21 · D11-002 · F5 has a coherent and an incoherent kind
**Decision.** `context_inconsistent` corrupts a context value but leaves the final
(breaking `final == sum(context)`); `context_drift` recomputes the final to match
(coherent). The consistency invariant catches the former, misses the latter.
**Why.** It shows precisely where the semantic floor is: an internal-consistency
check (cheap, no oracle) raises the floor but a coherent corruption sails through.
Only the oracle catches `context_drift`. This makes "requires semantic evaluation"
a demonstrated fact, not a label.
**Reversal cost.** None; both kinds are needed to locate the boundary.

### 2026-07-21 · D11-003 · F6 is modelled at the loop level with a step budget
**Decision.** A bounded loop completes in M steps or aborts at a STEP_BUDGET;
`repetition` repeats a step signature, `budget_exhaustion` burns the budget
without completing. Detectors are a repetition check and a budget check.
**Why.** Termination correctness is a counting property (Day 2's bounded loop,
Day 7's hop cap made a fault). Modelling it as counts/equality is what makes F6
the cleanest deterministic case: recall 1.0 with no correctness model.
**Reversal cost.** Low; a richer loop (partial progress, recovery) is additive.

### 2026-07-21 · D11-004 · Run-level faults, scored per run against the Day-8 truth log
**Decision.** F5/F6 are whole-run faults; a batch of runs is scored with each run
a sample (seq = run index), reusing Day 8's `GroundTruthLog` and Day 9's confusion.
**Why.** Context and termination are properties of a run, not a single call. Per-run
scoring keeps the mission's "score detectors against injection truth" discipline
intact while fitting the new granularity.
**Reversal cost.** None; the scorer is Day 9's, unchanged.

### 2026-07-21 · D11-005 · The map is backed by observed recalls, not assertions
**Decision.** `spectrum_map.build_map` pulls F1/F2 recalls from Day 9's report and
F3/F4 from Day 10's, and computes F5/F6 live, then classifies each fault.
**Why.** A map of claims is worthless; a map where each cell cites the day that
measured it is evidence. It also keeps the map honest if an upstream day changes.
**Reversal cost.** None; it re-derives from the source reports.

### 2026-07-21 · D11-006 · Semantic escapes are isolated with oracle evidence, never hidden
**Decision.** `semantic_escapes` returns the F5 `context_drift` runs that are
oracle-wrong but passed the consistency check, each with expected-vs-got context.
**Why.** Same discipline as Day 10's false-negative analysis: a fault that requires
semantic evaluation is reported as such, with proof, not silently counted as
detected. This is what "isolate faults requiring semantic evaluation" means.
**Reversal cost.** None; it is the deliverable.

### 2026-07-21 · D11-007 · Commit the Q2 split hypothesis as falsifiable, with a stated refuter
**Decision.** `q2_split_hypothesis.json` states the bifurcation, lists the two
fault sets, and names what would refute it (a deterministic detector that closes a
semantic escape without a correctness model).
**Why.** A hypothesis that cannot be refuted is not a hypothesis. Stating the
refuter up front (and noting it cannot exist by construction) is how the claim
earns the right to be tested in Q2 (Mission 15).
**Reversal cost.** Q2 may sharpen the numbers with intervals; the split itself is
structural and unlikely to move.
