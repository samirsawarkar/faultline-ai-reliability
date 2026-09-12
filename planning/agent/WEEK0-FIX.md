# Week 0 — corrective work order

**Read first:** `planning/agent/AGENT-RULES.md`, then this file.
**Status of Week 0:** W0.1, W0.2, W0.4, W0.5 accepted. **W0.3 rejected.** W0.6 held
(no live keys; the harness itself behaved correctly).
**Budget:** $0. Nothing here touches a paid endpoint.
**Do not freeze `MEC.md`.** The corpus hash `69e55ffa…` describes a corpus whose tier
definition is wrong. Freezing it would put a broken contract underneath every later
number.

The review found one defect that invalidates the corpus, one bookkeeping defect that
matters more than its size, and a handful of small things. Fix them in order.

---

## F0 · Restore days 29 and 30 *(owner task — not the agent's)*

The branch was cut from a stale local `main`, so `day29/` and `day30/` are absent from
this working tree. `make test` currently runs 28 days and reports green. The tripwire is
blind to two days.

```
git add -A && git commit -m "week0: package, frozen copies, stats, cost ledger, preflight"
git merge origin/main
make test
```

**No Phase 2 work continues until `make test` covers day01 through day30.**

---

## F1 · Rebuild the corpus with real multi-hop chaining · **BLOCKER**

**What is wrong.** `_generate_scenario` samples `hops` entities independently
(`rng.sample(fact_docs, k=hops)`) and emits one unrelated question per entity. Across all
300 scenarios, **zero** hop prompts reference any earlier hop's answer. A T3 scenario
reads:

```
Step 1: What is the internal codename of Juniper Foundry?
Step 2: What is the internal codename of Zephyr Union?
...
Step 5: What is the flagship product of Borel Collective?
Provide the final answer for Step 5.
```

`final_answer` is simply hop 5's answer, so a model can ignore steps 1–4 and still pass
the oracle. T3 is not harder than T1 — it is T1 with four decorative sentences in front.

This kills H1, and it poisons P6: a hard pool that is not hard makes measured pass³ vs
naive p³ a measurement of noise.

**What correct looks like.** Hop N's question must be *about the entity named by hop
N−1's answer*. The chain is only traversable in order:

```
Step 1: What is the internal codename of Juniper Foundry?      -> Prism-4014
Step 2: Who is the external auditor of <the firm from step 1>? -> ...
```

That requires the answer of hop N−1 to be an **entity reference**, not a coined token.
`build_env` currently makes every answer a globally unique coined value, which is exactly
what makes the oracle's required-source condition well defined — so do not break it.
Compose the linkage in `corpus.py`: pick a chain of entities first, then phrase hop N so
its subject is identified by hop N−1's answer, and verify the chain is genuinely ordered.

**Requirements**

- `build_env` is never modified. Compose on top of it.
- Every hop N>1 prompt must be unanswerable without hop N−1's answer.
- `final_answer` and `required_source` are the last hop's.
- `required_sources` lists every hop's source, in order — grounding is per hop.
- Keep the canonical serialization and the content hash.

**Acceptance — these are the checks that were missing the first time**

1. **Chain dependency test.** For every scenario, every hop N>1: the prompt for hop N
   references hop N−1's answer. Assert it across all scenarios, not a sample.
2. **Shortcut test.** For every T2 and T3 scenario, the final hop's prompt on its own
   does *not* identify the final entity. If it does, the chain can be skipped and the
   tier is decorative. This is the test whose absence caused the rebuild.
3. Hop counts still match tiers exactly: T1=1, T2=3, T3=5.
4. Cross-process determinism under two different `PYTHONHASHSEED` values.

Write test 2 first, watch it fail against the current `corpus.py`, paste that failure,
then build the fix. A test that has never failed proves nothing.

---

## F2 · Fix the seed derivation and prove uniqueness

`env_seed = seed % 1_000_000` truncates a derived seed into a space the generator can
collide in. It produced **2 duplicate `(prompt, final_answer)` scenarios** at n=300.
Paired statistics assume distinct scenarios.

Derive the per-scenario seed without truncation, and add an acceptance test asserting all
scenario `(prompt, final_answer)` pairs are unique and all `scenario_id`s are unique.

---

## F3 · Resize the pools · decision D7

**The arithmetic did not close.** The reserved hard pool held 100 scenarios; P6 needs
150. Filling the gap would have pulled ~90 scenarios out of the standard pool — the same
set P3 measures on — so the P6 subset would overlap the P3 baseline.

**Decision: the corpus is 350 scenarios.**

| Pool | Count | Composition |
|---|---|---|
| standard | 200 | 67 T1 / 67 T2 / 66 T3 |
| reserved hard | 150 | 150 T3 |

P3 keeps n=200. P6 keeps n=150. They are disjoint, which is what makes the P3 hard-subset
freeze meaningful. The corpus is free to generate; there is no reason to be short.

**Declare this and do not bury it:** per-tier n≈67 in the standard pool gives a Wilson
interval of roughly ±11 pp. H1 (real T3 below the simulator baseline) is therefore only
detectable if the gap is large. State that in P3's `results.json` as a declared power
limit — the MEC's rule is that small differences are reported INCONCLUSIVE, never as "no
difference."

Update the MEC draft's corpus block to 350 before the owner freezes it.

---

## F4 · Correct the decision log

`DECISIONS.md` D-001 says day 14's stats modules are "coupled to day08/day09/day10."
That is false. `intervals.py` imports `math`, `random`, `typing`, `.mathfns`.
`paired.py` imports `dataclasses`, `typing`, `.mathfns`. No cross-day imports exist. The
coupling is in `day14/tests/conftest.py`, which is a test fixture, not the modules.

The rewrite was still the right call and its agreement tests are good. **Rewrite the
entry so it records the true reason** — a clean-room implementation validated against
committed evidence, chosen deliberately — and delete the false claim.

A decision log that records a reason which is not true is the precise failure this
project exists to detect. It is not a small thing.

Also: renumber. The agent's `D-001` collides with `D1`–`D7` in
`planning/cto/PHASE2-BUILD.md`. Root `DECISIONS.md` uses `D-0NN` for implementation
decisions; the build plan's `DN` are program decisions. Say so at the top of the file.

---

## F5 · Remove the invented number from the cost model

`ledger.py` falls back to `input_price_per_m * 0.5` when no cached-prefix price is known.
Nothing measured that 50%. An unmeasured constant inside the module that enforces the
budget is exactly the wrong place for a guess.

Either take the cached rate from `preflight.json`, or raise when it is absent. Do not
default it.

Separately: `DEFAULT_PROJECT_CAPS` is hardcoded. Correct for now — `MEC.md` does not
exist. Add a TODO tied to the MEC freeze; once it exists, caps are read from it, or D4 is
theatre.

---

## F6 · Small cleanups

- Corpus embeds the full document set in all 300 scenarios (2.65 MB). Store documents
  once at corpus level; scenarios reference by id.
- `n_entities = max(12, hops + 4)` is always 12. Delete the expression.
- `projects/__init__.py` makes the experiment tree an importable package for no reason.
- The `assert answer in doc_by_id[...]["text"]` inside `_generate_scenario` is a data
  check, and asserts vanish under `-O`. Make it a real check or move it to a test.
- `pass_hat_k` takes `scenario_trials[:k]` and silently ignores extra trials. Fine at
  k=3 with 3 trials; add a note saying so, so nobody later assumes tau-bench's
  subset-averaging behaviour.

---

## Re-gate

Report, with pasted output:

1. `make test` green across **day01 … day30**
2. Root `pytest` green, days plus `tests/phase2`
3. The failing run of the shortcut test against the old corpus, then the passing run
   against the new one
4. The new corpus content hash, from two processes with different `PYTHONHASHSEED`
5. Scenario counts: 350 total, 200 standard (67/67/66), 150 reserved T3
6. Uniqueness test output — zero duplicate scenarios
7. The corrected `DECISIONS.md` entry

Then stop. `MEC.md` and `HYPOTHESES.md` remain the owner's to write.
