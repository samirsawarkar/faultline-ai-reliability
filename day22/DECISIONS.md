# DECISIONS.md — Day 22 (recovery matrix) decision log

Append-only. Date · id · decision · why · reversal cost.

---

### 2026-08-01 · D22-001 · M5 checks step and cost bounds before execution
**Decision.** Refuse an action when the next step would cross either ceiling.
**Why.** A post-action check can overspend by one operation—the exact failure a
ceiling is supposed to prevent. The attack proves both bounds are strict.
**Reversal cost.** None; preflight checking is the contract.

### 2026-08-01 · D22-002 · M6 permits one replan, then terminates
**Decision.** A third identical consecutive action triggers one recovery plan; a
second repetition aborts inside shared step/cost bounds.
**Why.** Zero replans cannot recover a transient loop; unlimited replans recreate
the loop at the recovery layer. One makes both paths measurable.
**Reversal cost.** Low; `max_replans` is policy.

### 2026-08-01 · D22-003 · Every matrix cell uses 18 faults plus six clean controls
**Decision.** Pair mechanism and no-recovery on the same 24 seeds, including long
and legitimately repetitive controls.
**Why.** Fault-only evidence cannot expose false opens, premature ceilings, or
repetition false positives. Controls make induced failures observable.
**Reversal cost.** Medium; changing the population invalidates committed intervals.

### 2026-08-01 · D22-004 · Outcome separates correct, available, contained, and wrong
**Decision.** Never collapse those states into a single “recovered” bit.
**Why.** M4 can be available but wrong; M5 can contain a loop without answering.
One bit would reward the first or erase the second.
**Reversal cost.** None; the richer contract is additive.

### 2026-08-01 · D22-005 · Pair cost and latency per seed
**Decision.** Store paired deltas and bootstrap intervals in every cell.
**Why.** Mechanism and baseline see identical difficulty. Independent averages
would waste the pairing and could hide that low latency came from aborting work.
**Reversal cost.** Low; the raw outcomes already align.

### 2026-08-01 · D22-006 · M1–M6 remain narrow; F3/F5 have no forced winner
**Decision.** Report `none_of_M1_M6` when no mechanism improves correct success.
**Why.** Picking the cheapest tie for semantic drift would imply a recovery that
the evidence does not show. F3/F5 still need semantic rejection/re-grounding.
**Reversal cost.** Medium; a future semantic recovery needs its own paired evidence.

### 2026-08-01 · D22-007 · Every induced harm is a first-class artifact
**Decision.** Record harm type, fault, seed, variant, status, cost, and latency, then
reconcile per-cell and aggregate totals.
**Why.** The mission fails if recovery creates an unmeasured failure. A prose
limitations section is not enough; the 47 harms must be enumerable.
**Reversal cost.** None; this is the fail-condition guard.

### 2026-08-01 · D22-008 · Compose by order, not by enabling everything
**Decision.** M5 outer envelope → detector → narrow recovery → quality validation →
success/contain/escalate.
**Why.** Blind composition compounds each mechanism's measured failure mode.
Ordering preserves global bounds while keeping recovery conditional.
**Reversal cost.** Medium; orchestration code should follow this policy boundary.
