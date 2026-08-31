# FAULTLINE Phase 2 — Build Plan

**Companion to:** [PHASE2-PLAN.md](PHASE2-PLAN.md) (the research contract)
**This document:** how the work gets built, in what order, by whom
**Status:** approved 2026-08-31
**Audience:** the implementing agent

The plan says *what to measure and why*. This says *what to build and when to stop*.
Where the two disagree, the plan wins — and the disagreement gets logged.

---

## 0. Scope boundary — read first

**`day01/` … `day30/` are frozen.** They are not edited, not moved, not renamed, not
imported, and not deleted. Nothing under `arc/` is created; the days stay where they are.
They are read-only reference material. Read them freely. Change nothing.

The existing `Makefile`, `pytest.ini`, and the 30 day-level test suites keep passing
untouched for the whole of Phase 2. If a Phase 2 change makes `make test` fail, the
Phase 2 change is wrong.

**Phase 2 is a new tree, built fresh:**

```
faultline_p2/       new importable package — the instruments (see D5)
projects/p01..p12/  the experiments
reports/            the deliverables
MEC.md HYPOTHESES.md AMENDMENTS.md
day01/ … day30/     UNTOUCHED
```

### What the implementing agent does
Writes `faultline/`, writes `projects/pNN/`, writes tests, runs tests, reports results.

### What the implementing agent never does
- Edit, move, or delete anything under `day01/`…`day30/`
- Edit `MEC.md` or `HYPOTHESES.md` after they are committed — those are contracts
- Choose the hard-subset selection criteria (P3) — that is an owner decision
- Do the P4 open coding — the entire value of P4 is that a human did it
- Spend money. Every run that hits a paid endpoint requires an explicit `--confirm`
  from the owner. A sweep started without one is a bug.

---

## 1. Build decisions

**D1 · Hash-pinned oracle instead of import.**
The MEC requires `day01 oracle_check, UNMODIFIED`. Days are frozen, so the oracle and
the corpus generator are **copied byte-for-byte** into the new package. A test asserts
sha256 equality between the copy and the day01 original. "Unmodified" becomes a test
that fails loudly, not a promise in a README. If someone edits the copy, CI stops them.

**D2 · Week 0 comes before Project 1.**
A pre-flight probe hits all six rungs once and records, per rung: model version string,
measured input/output price, latency, and whether `temperature=0` is actually honored on
a repeated identical call. Its output is pasted into `MEC.md`. Then `MEC.md` and
`HYPOTHESES.md` are committed in one commit. That commit is the pre-registration
timestamp. No project starts before it exists.

**D3 · P2 moves after Publication #1.**
The OTel exporter blocks nothing — P1 already lands traces in a store. Spending weeks 1–2
on it leaves P4, the named biggest risk, with two weeks. §0 of the plan makes ordering
within a phase amendable. Weeks 1–2 become P1 → P3, with P4 open coding starting in
week 2. P2 fills the slack around Publication #1.
*If MEC v1.0 is already frozen when this is executed, log it as `A-001`.*

**D4 · The budget ceiling is enforced in code.**
Every paid call goes through one runner. It reads the per-project cap from `MEC.md`,
estimates total cost from pre-flight prices, prints the estimate, and refuses to start
without `--confirm`. It appends every call to an append-only ledger and hard-stops the
sweep the moment the project cap is reached. The stop rule stops being discipline and
becomes an exception.

**D5 · The Phase 2 import package is `faultline_p2`, not `faultline`.**
`day01/faultline/` already exists, and `day01/tests/test_oracle.py` does
`sys.path.insert(0, day01)` then `import faultline`. A second root-level package
named `faultline` would shadow it — in either direction, depending on which test
ran first and what landed in `sys.modules`. Days would go red, or worse, Phase 2
would silently import the day01 module and nobody would notice. The distribution
installs as `faultline-phase2`; the import name is `faultline_p2`, matching the
repo's existing `faultline_agent` / `faultline_stats` / `faultline_store`
convention. This overrides the `faultline/` layout sketched in plan §8, which §0
leaves amendable.

**D6 · The Phase 2 corpus builder is new code, not a copy.**
`build_env(seed, n_entities, n_distractors)` has no hop concept — multi-hop tiers
live in day03's `TierSpec` (EASY 1-3 / MEDIUM 4-6 / HARD 6-8) and day07's
`faultline_hops`. The MEC defines different tiers again: T1=1 hop, T2=3, T3=5. So
`build_env` and `oracle_check` are copied verbatim and hash-pinned, and the
300-scenario T1/T2/T3 corpus is **composed on top of them** as new code.
`build_env` itself is never modified — its determinism contract is the foundation
everything else stands on.

---

## 2. Week 0 — freeze the contract

Three tasks. Nothing else runs until all three are done.

| # | Task | Deliverable |
|---|---|---|
| W0.1 | Package skeleton: `pyproject.toml`, `faultline/` dirs, `pip install -e .` works, CI runs both the new tests and the untouched `make test` | repo installs clean |
| W0.2 | Copy oracle + corpus generator from `day01/`, with sha256 equality tests. `make phase2-corpus` regenerates the 300-scenario corpus from the pinned seed and prints its content hash | corpus hash, reproducible |
| W0.3 | Pre-flight probe across R1–R6: version, measured price, latency, temp-0 determinism | `preflight.json` |

**GATE:** `MEC.md` filled in with the real corpus hash, real prices, real model versions,
real system-prompt hash. `HYPOTHESES.md` written. Both committed together.
**Owner writes both files. The agent does not.**

If the pre-flight shows a rung is dead or repriced, fix the ladder *now*, before the
freeze. After the freeze it costs an amendment.

---

## 3. Package layout

One module, one job. Each is independently testable with no network.

| Module | Owns | Notes |
|---|---|---|
| `faultline_p2/env/` | corpus generation, scenario tiers, dataset manifests | `build_env` copied + hash-pinned; the T1/T2/T3 corpus is new code on top (D6) |
| `faultline_p2/oracle/` | `oracle_check` — the pass condition | copied from day01, hash-pinned, **pure function, never an LLM** |
| `faultline_p2/agent/` | bounded reason→tool→observe loop, step cap 8, 3 typed tools, LiteLLM call | Pydantic v2 `extra="forbid"` at every boundary |
| `faultline_p2/trace/` | span emission and the run store | P2 adds an OTel sink here later |
| `faultline_p2/stats/` | Wilson, McNemar, seeded bootstrap, pass^k | pure, no I/O, property-tested |
| `faultline_p2/cost/` | price table, estimator, append-only ledger, cap enforcement | D4 lives here |
| `faultline_p2/sweep/` | the one runner every project calls | `--dry-run` / `--confirm` |
| `faultline_p2/judge/` | binary evaluators, added at P5 | frozen after P5 |
| `faultline_p2/attribute/` | retriever-vs-generator ablation, added at P12 | |

`faultline/stats/` gets built and tested in week 0 alongside the skeleton — it is pure
and free, and every project depends on it.

---

## 4. Project briefs

Each project is one working session. Ship its five artifacts before starting the next:
`README.md`, `DECISIONS.md`, `results.json` (referencing `MEC v1.0`), one figure, one
`make` target, plus raw traces.

---

### P1 · real-agent-baseline — 8h, $2 · rung R2

**In:** frozen corpus, `faultline/agent`, `faultline/oracle`, `preflight.json`
**Build:** wire the real agent to the corpus and run 100 scenarios through it.
**Gate:** 100 real runs complete; traces land in the store; the oracle grades them with
zero modification to the oracle.
**Forbidden:** touching the oracle. If real traces don't grade cleanly, the *harness*
is wrong, not the oracle. That distinction is the whole point of P1.

---

### P3 · grounding-zero-point — 5h, $5 · R2 + R6

**In:** P1's working harness
**Build:** n=200 across both rungs, Wilson CIs per tier (T1/T2/T3).
**Also, and this is the part that matters:** select the 150-scenario hard subset for P6
and hash it into the dataset manifest **before any comparison result is read**. The
selection criteria are an owner decision, written down in `DECISIONS.md` before selection
runs. Once hashed, frozen.
**Gate:** `results.json` committed with a content-addressed dataset version. H1 resolved.
**Also do here:** README surgery — headline number and figure above the fold,
`pip install -e .` plus one reproducing command, Phase 1 / Phase 2 framing in two
sentences. Do it at P3, not week 10.

---

### P4 · failure-taxonomy — 14h, $0 · **owner-only, no agent**

**In:** 150 real P3 traces
**Do:** open coding — read the whole trace, write the first failure in plain language.
Then axial coding into 5–8 binary modes with definitions, examples, boundary cases.
Check saturation. Compare against the F1–F6 injected catalog **only afterward**.
**Gate:** ≥2 modes absent from F1–F6 (H2), or an honest writeup of why the catalog was
complete.
**Agent's only role:** a trace-viewing helper if one is asked for. It does not read the
traces and it does not propose modes. A model-generated taxonomy is worth nothing here.
**Kill switch:** if two weeks pass with <40 traces coded, cut to 80 traces and 4 modes
and ship. A small shipped taxonomy beats a large unshipped one.

---

### P5 · judge-validation — 12h, $10

**In:** P4 taxonomy
**Build:** one binary evaluator per mode. Code assertion wherever the mode is objective;
LLM judge only where interpretation is genuinely required — and say which is which.
Content-addressed train/dev/test split. TPR, TNR, Cohen's κ per judge. Prevalence
corrected using measured judge error rates. Benchmark against Ragas faithfulness and
DeepEval on the same set.
**Gate:** judges frozen, **test set read exactly once**, number committed. H3 resolved.
**Forbidden:** reading the test set twice. If you need another look, you need another
split, and you say so in `DECISIONS.md`.

> **PHASE GATE — hard.** P6 does not start until P5 has reported κ and the prevalence
> correction. An unvalidated judge makes every number downstream unfalsifiable.

---

### P6 · passk-decay — 10h + compute, $45 · all six rungs

**In:** the P3-hashed 150 hard scenarios, validated judges, the cost runner
**Build:** 150 × k=3 × 6 rungs = 2,700 runs. One axis varies: the model. Same prompt,
same tools, same harness, same suite. Off-peak. Prefix caching on.
**Primary:** per-rung measured pass³ vs naive (pass@1)³, Wilson CIs, disjointness test.
**Secondary:** between-model pass@1 with McNemar, **labelled underpowered below 10 pp**.
**Also emit:** cost per successful grounded answer, per rung.
**Gate:** H4 and H5 resolved either way. Raw traces committed.
**Run it once.** It is 30% of the budget. Dry-run the estimate first, confirm the number
against the cap, then go.
**If it returns a clean null:** publish it. "Failures are closer to i.i.d. than assumed"
is a real and rarely-reported result. That is not a failed experiment.

---

### PUBLICATION #1 — 8h

Question · pre-registration git hash · method · frozen config · raw data · result with
intervals · limitations · one reproducible command · negative results included.

Blog, HN, r/MachineLearning, the eval Discord, LinkedIn, X. **Then email it to three
people whose work you cite.** That last step is the one everybody skips and the one that
works.

> **HARD GATE: P7 does not start until Publication #1 is live.**
> The plan fails at exactly this step or nowhere.

---

### P2 · otel-genai-exporter — 10h, $0 *(moved here by D3)*

**Build:** emit existing spans as OTel GenAI semconv — `invoke_agent` → `chat` →
`execute_tool`, with `gen_ai.request.model`, `gen_ai.usage.*`, `gen_ai.operation.name`.
Langfuse and Phoenix sinks. A **conformance test** asserting spans validate against the
registry.
**Gate:** one trace, three backends, identical waterfall.
**Why it survives the cut:** `gen_ai.*` attributes still carry Development stability
badges, so a conformance-tested dual-emit exporter is a genuine OSS gap — and it makes a
custom SQLite tracer legible to people who have never heard of it.

---

### P7 · provider-variance — 6h, $5

One model name, three endpoints, everything else identical. Grounded rate, latency, cost,
with CIs. Provider, model version, and quantization logged in **every** span.
**Gate:** H6 resolved.
**Bonus finding:** any rung that failed the week-0 temperature-0 determinism check
belongs in this writeup.

---

### P8 · mcptox-bounded — 10h, $10

**Do not rebuild the harness.** Use `inspect-evals-mcptox` (MIT), dataset SHA256-verified
from a pinned upstream commit. Subsample ~300 of the 1,312 valid instances via
`-T servers` or `-T security_risks`.
**Your contribution is the second arm:** MCPTox runs a single-turn protocol — one system
prompt, one benign query, one JSON tool call. A bounded, step-capped, `extra="forbid"`
agent is a structurally different threat surface. Run both arms, report the delta.
**Baseline to beat:** mean ASR 36.5% across 45 servers, peak 72.8% — with more capable
models often *more* susceptible, because better instruction-following means better
compliance with malicious metadata.
**Gate:** H7 resolved. Cite arXiv 2508.14925 and the Inspect implementation properly.

---

### PUBLICATION #2 — 6h

Same discipline as #1. Send it directly to the MCPTox authors and the Inspect maintainers.

---

### P12 · failure-attribution — 10h, $6

Ablate retriever vs generator. For each P4 mode, which subsystem owns it? Report with CIs.
**Runs before P10, as a precondition:** if grounding failures are retriever-owned,
escalating to a frontier model cannot fix them, and a cascade calibrated on the wrong
variable is worse than no cascade.
**Gate:** H8 resolved.
**The deliverable sentence:** "Don't change the model. Fix chunking."

---

### P10 · calibrated-cascade — 12h, $8

Cheap → frontier router. Escalation threshold fit on P5-labelled data, not vibes. Plot
the Pareto frontier and keep multiple points on it. Reuses P6 runs heavily.
**Gate:** frontier plotted, threshold's fitting procedure documented and reproducible.

---

### P9 · redteam-regression — 8h, $6

Promptfoo attack suite against the live endpoint, 40+ adversarial plugin categories.
Every successful attack becomes a failing pytest.
**Assert separately:** authorization holds even when the model is fully compromised.
That assertion is independent of any detector, and it is the one that matters.
Independent of P12 — parallelize if convenient.

---

### P11 · release-gate — 10h, $5

GitHub Actions gate with **tolerance bands, not exact thresholds**, a pinned judge, and a
stable golden set — the three things that stop flaky eval CI. Then the upgrade drill:
every model stored as config, full suite re-runnable when a new model ships.
**Gate:** a real model upgrade run end-to-end producing a PASS/FAIL and a redrawn frontier.

---

## 5. Working rules for the implementing agent

1. **One project per session.** Ship its five artifacts before starting the next.
2. **Gates are not suggestions.** A project is done when its gate is met, not when the
   code runs.
3. **Never spend without `--confirm`.** Print the dry-run estimate first, every time.
4. **A cap is a stop, not a budget to borrow against.** Hit it, log it, stop.
5. **Report failures with the output.** A sweep that half-completed is reported as a
   sweep that half-completed.
6. **Days 1–30 are read-only.** If `make test` breaks, revert.
7. **Contract files are read-only once committed.** `MEC.md` and `HYPOTHESES.md` change
   only through `AMENDMENTS.md`, and only by the owner.

---

## 6. Revised schedule

| Week | Work | Cumulative |
|---|---|---|
| 0 | skeleton · oracle copy · stats · pre-flight · **MEC + HYPOTHESES frozen** | $0 |
| 1 | P1 · P3 start | $2 |
| 2 | P3 finish · README surgery · **P4 open coding starts** | $7 |
| 3 | P4 open coding | $7 |
| 4 | P4 axial · P5 start | $7 |
| 5 | P5 finish · **PHASE GATE** · P6 | $62 |
| 6 | **PUBLICATION #1** · P2 | $62 |
| 7 | P7 · P8 | $77 |
| 8 | **PUBLICATION #2** · P12 | $83 |
| 9 | P10 · P9 | $97 |
| 10 | P11 · final report | $102 |

Slack: 3 weeks. The likely consumer is P4.

**Cut order if forced:** P11 → P9 → P10 → P12. **Never cut a publication.**
