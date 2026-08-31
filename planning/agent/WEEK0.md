# Week 0 — build the foundation

**Read first:** `planning/agent/AGENT-RULES.md`, then `planning/cto/PHASE2-BUILD.md`
§0 and §1.
**Budget:** $0 for W0.1–W0.5. W0.6 spends roughly $0.05 and still needs `--confirm`.
**Ends when:** the owner commits `MEC.md` and `HYPOTHESES.md`. Not before.

Nothing in Phase 2 runs until Week 0 is done. This is the week that makes every
later number defensible, and it is the week where a shortcut is most expensive —
a corpus that isn't reproducible or an oracle that drifted invalidates everything
built on top of it, silently, months later.

Six tasks. Do them in order. Each one has an acceptance check you run and paste
the output of. "It should work" is not an acceptance check.

---

## W0.1 · Package skeleton

**Build**

| Path | Purpose |
|---|---|
| `pyproject.toml` | distribution `faultline-phase2`, import package `faultline_p2`, `requires-python = ">=3.11"` |
| `faultline_p2/__init__.py` | version string only |
| `faultline_p2/{env,oracle,agent,trace,stats,cost,sweep}/__init__.py` | empty packages, filled by later tasks |
| `tests/phase2/` | all Phase 2 tests live here |

Dependencies: `pydantic>=2.13`, `litellm` (pin the exact version you install —
the MEC records it), `pytest`. Nothing else. If you want a fourth dependency,
ask first.

**Do not create** `faultline_p2/judge/` or `faultline_p2/attribute/`. Those are
built at P5 and P12, when there is something to put in them.

**Do not edit** `requirements.txt` or `pytest.ini` — the day-1-to-30 gate depends
on both. Append new targets to the `Makefile`; never modify an existing target.

New Makefile targets, appended:

```
phase2-install    pip install -e .
phase2-test       pytest tests/phase2
phase2-corpus     regenerate the corpus, print its content hash
phase2-preflight  probe the model ladder (costs money, needs --confirm)
```

**Why the name is `faultline_p2` and not `faultline`:** read D5 in
`planning/cto/PHASE2-BUILD.md`. `day01/faultline/` already exists and
`day01/tests/test_oracle.py` puts `day01/` on `sys.path` before importing it. A
second package named `faultline` shadows it in one direction or the other
depending on test order. Do not "fix" this by renaming anything in day01.

**Acceptance**
1. `pip install -e .` succeeds in a clean venv
2. `python -c "import faultline_p2; print(faultline_p2.__version__)"` works
3. `make test` is green — the full 30-day gate, unchanged
4. `pytest` at the repo root is green — days and `tests/phase2` in one process

Check 4 is the one that catches the shadowing problem. Do not skip it.

---

## W0.2 · Hash-pinned copies of the oracle and the environment

The MEC requires `day01 oracle_check, UNMODIFIED`. Days are frozen, so this is a
copy plus a test that proves the copy never drifted.

**Build**

| Path | Source | Rule |
|---|---|---|
| `faultline_p2/oracle/_day01_oracle.py` | `day01/faultline/oracle.py` | byte-for-byte copy |
| `faultline_p2/env/_day01_env.py` | `day01/faultline/env.py` | byte-for-byte copy |

Re-export the public surface so callers never touch the underscore modules:
`faultline_p2.oracle` exports `oracle_check` and `normalize`;
`faultline_p2.env` exports `build_env`.

Put a header comment at the top of each copy — **outside** the byte-compared
region is impossible, so instead: do not add a header. The files are byte-identical
or the test fails. Document their provenance in `faultline_p2/oracle/__init__.py`
and `faultline_p2/env/__init__.py` instead.

**Build `tests/phase2/test_frozen_copies.py`:** reads both the copy and the day01
original as bytes, compares sha256, fails with a message naming both absolute
paths and both hashes.

**Acceptance**
1. `pytest tests/phase2/test_frozen_copies.py` passes
2. Change one byte in a copy → the test fails, and its message tells you which
   file and which pair of hashes. Paste that failure output, then revert.

Check 2 is the whole point. A test that has never been seen failing is not
evidence of anything.

---

## W0.3 · The Phase 2 corpus

**This is new code, not a copy.** `build_env(seed, n_entities=12, n_distractors=6)`
returns a single-hop environment — it has no notion of hops. Day 3 defines tiers
as EASY 1-3 / MEDIUM 4-6 / HARD 6-8 hops; day 7 has the hop machinery. The MEC
defines tiers differently again: **T1 = 1 hop, T2 = 3 hops, T3 = 5 hops.**

So: compose multi-hop scenarios on top of `build_env`. **Never modify
`build_env`.** Its determinism contract is what everything else stands on.

**Build `faultline_p2/env/corpus.py`**

- `build_corpus(seed) -> Corpus` producing **300 scenarios**: 200 standard,
  plus a 100-scenario reserved hard pool that is marked and kept separate
- tiers T1 / T2 / T3 at 1 / 3 / 5 hops
- each scenario carries: `scenario_id`, `tier`, `hops`, the question chain, the
  final answer, and the `required_source` for each hop
- pure function of `seed` — no clock, no environment, no filesystem reads
- canonical serialization: `sort_keys=True`, ASCII, fixed indent, LF, one
  trailing newline
- `content_hash` = sha256 of those canonical bytes

Typed with Pydantic, `extra="forbid"`. The hard pool is *reserved* — it is not
the P6 hard subset. P6's 150 are selected at P3 by the owner, from this pool,
against written criteria.

`make phase2-corpus` writes the corpus to a path you choose under
`projects/_corpus/` and prints the content hash to stdout.

**Acceptance**
1. Two runs, two separate processes, different `PYTHONHASHSEED` → identical
   content hash. Paste both hashes.
2. Scenario counts assert exactly: 300 total, 200 standard, 100 reserved,
   and the hop count of every scenario matches its declared tier.
3. Every scenario's `required_source` is resolvable and unique — the oracle's
   pass condition is meaningless otherwise.

Report the content hash. It goes into `MEC.md`.

---

## W0.4 · Statistics

Pure functions, no I/O, no network. Every project depends on these, so they are
built before anything produces a number.

**Build `faultline_p2/stats/`**

- `wilson(successes, n, z=1.96) -> (lo, hi)`
- `mcnemar(b, c)` — exact binomial when `b + c < 25`, chi-square above.
  The threshold is in the MEC; it is not yours to tune.
- `bootstrap(data, statistic, n_resamples=10_000, seed)` — seeded, reproducible
- `pass_hat_k(per_scenario_trials, k)` — measured: the fraction of scenarios
  where all k trials passed, averaged over scenarios
- `naive_p_k(p, k)` — simply `p ** k`, the i.i.d. prediction

`pass_hat_k` and `naive_p_k` are the two numbers H4 compares. Keep them
separate, name them unmistakably, and never let one call the other.

**Reuse decision, yours to make after reading:** day 14 has
`faultline_stats/intervals.py` and `paired.py`. If they import nothing outside
their own package, copy them hash-pinned exactly as in W0.2. If they are coupled
to day 8/9/10 (day 14's conftest puts those on the path — check), reimplement
cleanly instead. Either way, write a test asserting your results agree with the
committed numbers in `day14/evidence/stats_verification.json` and
`paired_comparison.json`. Say in `DECISIONS.md` which route you took and why.

**Acceptance**
1. Agreement test against day 14's committed evidence passes
2. Property test: Wilson bounds stay in [0, 1] and always contain the point
   estimate, across a grid including the ends (k=0 and k=n)
3. `bootstrap` with the same seed returns identical output across processes

---

## W0.5 · Cost ledger and the budget stop

Decision D4: the $150 ceiling is enforced in code. This is the module that does it.

**Build `faultline_p2/cost/`**

- a price table loaded from `preflight.json` (W0.6) — never hardcoded prices
- `estimate(n_runs, in_tokens, out_tokens, rung) -> usd`, with an optional
  cached-prefix fraction
- an append-only JSONL ledger: one line per call — `run_id`, `project`, `rung`,
  input tokens, output tokens, usd, UTC timestamp. Append-only means append-only:
  no rewriting, no compaction, no deletion.
- `check_cap(project) -> remaining_usd`, reading the per-project cap
- a `BudgetExceeded` exception raised the moment a cap is reached mid-sweep

**Build `faultline_p2/sweep/`** — the single runner every project calls:

- always prints the dry-run estimate before doing anything
- refuses to start without `--confirm`
- writes to the ledger after every call, not in a batch at the end (a crashed
  sweep must still have an accurate ledger)
- halts on `BudgetExceeded`, writes what completed, exits non-zero

**Acceptance**
1. Unit test: a ledger driven past its cap raises `BudgetExceeded` and the
   partial results are still on disk and still readable
2. `estimate` matches a hand-computed figure — put the arithmetic in the test
3. A sweep invoked without `--confirm` performs zero paid calls. Prove it with
   a fake endpoint that raises if called.

---

## W0.6 · Model ladder pre-flight

**This spends money — about $0.05 — and still requires `--confirm`.**

**Build `projects/p00_preflight/`**

For each rung R1–R6, make one minimal call, then **repeat the identical call a
second time at `temperature=0`**. Record:

- the endpoint actually used (one named endpoint per model; no routing marketplaces)
- the model version string the provider returns
- prompt and completion tokens
- measured USD — from the provider's response where it reports cost, otherwise
  computed from configured price, and say which
- latency
- **determinism: were the two responses byte-identical?**

Write `preflight.json`, plus a markdown table the owner pastes into `MEC.md`.

**A rung that fails is recorded as failed.** Never silently skip one. Six rungs
in, six rungs out — some may be error entries.

**Acceptance**
1. `preflight.json` has exactly six entries
2. The markdown table renders and contains real version strings, not placeholders
3. Report clearly: which rungs are live, which failed, and **which ones did not
   honour temperature 0**

That last one is free evidence. Any rung that fails determinism here becomes a
finding in P7 — flag it, don't fix it.

---

## Week 0 gate

Report to the owner, in one message:

1. The corpus content hash
2. `preflight.json` — live rungs, dead rungs, measured prices, model versions,
   temperature-0 results
3. The exact `litellm` version installed
4. The system prompt sha256, once the P1 prompt exists — **if it does not exist
   yet, say so** rather than inventing one
5. Confirmation that `make test` and root `pytest` are both green

**Then stop.** The owner writes `MEC.md` and `HYPOTHESES.md` and commits them.
That commit is the pre-registration timestamp, and P1 starts after it — not before.

If the pre-flight shows a rung is dead or repriced, that is fixed **now**, before
the freeze. After the freeze it costs an amendment.
