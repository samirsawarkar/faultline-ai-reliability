# FAULTLINE PHASE 2 — AMENDMENTS

Amendments to `MEC.md` and `HYPOTHESES.md`. Owner-written only. Each entry records the
date, what changed, why, and which prior results it affects.

An amendment that would break comparability with an already-published result is not an
amendment — it is a new experiment with a new contract version.

---

## A-001 · System prompt frozen · 2026-09-01 · MEC v1.0 → v1.1

**Changed.** The system prompt, left deliberately unset at freeze, is authored and frozen.

**Hash.** `87c7641e74964dcfe00c605051d7f5ddfade01f4019c95a00fd5dc3f1907c8df`

**Why.** MEC v1.0 shipped with `system prompt hash: NOT YET SET` rather than a fabricated
placeholder. It is the one field of the contract written after the freeze, once.

**Prior results affected.** None. No experiment has run.

---

## A-002 · Step cap 8 → 12; search returns snippets · 2026-09-01 · MEC v1.1 → v1.2

**Changed.**
1. Agent step cap: **8 → 12**.
2. The `search` tool returns a bounded text snippet alongside each candidate, so a
   document can be read in one step rather than two.
3. `lookup` resolves only documents surfaced by a prior `search` in the same run.

**Why.** The frozen corpus requires 9 document retrievals for a T3 scenario and 5 for a
T2 (`traversal_sources`). Under the day02 tool contract each document costs a `search`
plus a `lookup`, so a T3 needed roughly 19 steps and a T2 roughly 11 — against a cap of 8.
**283 of 350 scenarios, including the entire 150-scenario P6 reserved pool, were
unsolvable by construction at any price.**

This was an owner error. `step_cap = 8` was carried from the execution plan into MEC v1.0
without re-deriving it against the corpus approved in the same week. Day 3 used a cap of
12 for 6–8 hops; the Phase 2 link layer added four retrievals per T3 and the budget was
never recomputed.

Left unamended, every model would have scored near zero on T3 and H1 would have appeared
strongly confirmed by an artefact of the harness.

**Why 12 and not 20.** Snippet-returning search makes the minimum path 9 searches plus 1
answer = 10 steps for a T3, so 12 leaves a 2-step margin. Raising the cap instead of the
tool contract would have meant ~20 turns of accumulated context per run, multiplying the
token cost that the $45 P6 cap was sized against.

**Declared trigger, registered in advance.** The 2-step margin is thin. If more than 10%
of T3 runs in P1 terminate on the step cap, the cap is amended again and P1 is re-run
before P3. Deciding this now prevents choosing a cap after seeing which value flatters
the result.

**Why `lookup` is restricted.** Fact document IDs are `doc-0000`…`doc-0359` and therefore
enumerable. Restricting `lookup` to previously-surfaced documents enforces the MEC's
content-reachability requirement rather than relying on the step cap to make enumeration
impractical.

**Prior results affected.** None. No experiment has run and $0 has been spent.

**Open obligation.** The MEC's budget assumed 10k input / 2.5k output per run, costed
before any multi-step agent existed. Tokens per run must be measured in P1 and the P6
allocation re-checked before P6 runs.
