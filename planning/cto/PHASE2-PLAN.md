# FAULTLINE Phase 2 — Execution Plan

**Owner:** Samir Sawarkar
**Status:** Frozen v1.0 · 2026-08-31
**Scope:** 12 projects, real models, real traces, real cost
**Predecessor:** FAULTLINE Days 1–30 (simulator track, scope capped, no additions)

---

## 0. How this document works

This plan is frozen in the parts that must not drift and amendable in the parts that must.

**Frozen (changing these invalidates all prior results):**
- The Master Experiment Contract in §2
- Primary metrics and their definitions
- The pre-registered hypotheses in §5
- The budget ceiling

**Amendable (log it, date it, keep going):**
- Ordering within a phase
- Model roster, if a provider dies or reprices
- Anything an experiment teaches you

Amendments go in `AMENDMENTS.md` at repo root, numbered `A-001…`, each with date, what changed, why, and what prior results it affects. An amendment that would break comparability with an already-published result is not an amendment — it is a new experiment with a new contract.

**One rule that overrides everything else:** a plan you cannot revise is a plan that will lie to you the first time reality disagrees. The discipline is not "never change" — it is "never change silently."

---

## 1. The bet, stated plainly

FAULTLINE Days 1–30 built a reliability laboratory: deterministic environment, required-source oracle, typed contracts, tracing that survives failure, verified intervals, paired tests. Every number is reproducible because nothing in it is real.

Phase 2 makes it real and asks whether the methodology survives.

**Why the split is the strong story, not a weakness:** you cannot measure a detector's precision against reality, only against known ground truth. The simulator exists so the instruments can be validated. Phase 2 points validated instruments at real models. Say it exactly that way in every writeup.

**What success looks like in 10 weeks:**
1. Two published findings with defensible statistics
2. A `pip install`-able package a stranger can run
3. Enough distribution that someone who does not know you has read it

**What failure looks like:** twelve completed projects, zero readers. This has happened to better work than yours. Distribution is a deliverable, not an afterthought.

---

## 2. Master Experiment Contract (MEC)

Write this as `MEC.md` at repo root and freeze it **before spending the first dollar**. This is the Day-3 `BaselineConfig` promoted to program level. Every project references `MEC v1.0` in its results file.

```
FAULTLINE PHASE 2 — MASTER EXPERIMENT CONTRACT v1.0
Frozen: 2026-XX-XX
────────────────────────────────────────────────────
CORPUS
  source              day01 seeded generator, seed=<PIN>
  content hash        <sha256 of generated corpus>
  scenario count      300 (200 standard + 100 reserved hard pool)
  tiers               T1 (1 hop) / T2 (3 hops) / T3 (5 hops)
  regeneration cmd    make phase2-corpus

AGENT
  architecture        bounded reason->tool->observe, step cap = 8
  contracts           Pydantic v2, extra="forbid" at every boundary
  tools               3 typed tools, identical to day02 signatures
  harness             LiteLLM, pinned version <X.Y.Z>
  temperature         0.0 (see AMENDMENT policy if any model ignores this)
  max_tokens          2048
  system prompt hash  <sha256>  [FROZEN — any edit = new contract version]

ORACLE
  implementation      day01 oracle_check, UNMODIFIED
  pass condition      answer correct AND cites the one source holding the fact
  authority           pure function; never an LLM; never overridden

MODEL LADDER (6 rungs, cheapest to most expensive)
  R1  gemini-2.5-flash-lite     $0.10 / $0.40
  R2  deepseek-v4-flash         $0.14 / $0.28   [VERIFY: Aug-16 repricing]
  R3  deepseek-v4-pro           $0.435 / $0.87
  R4  minimax-m3                $0.60 / $2.40
  R5  glm-5.2                   $1.40 / $4.40
  R6  <sonnet-class anchor>     ~$3 / ~$15      [frontier anchor]
  Prices per 1M tokens, verified 2026-08-31. Re-verify before each sweep.

PROVIDERS
  Each model pinned to ONE named endpoint. Provider, model version, and
  quantization logged in every span. Routing marketplaces (OpenRouter et al.)
  are NOT used for the ladder — they are the subject of P7, not the substrate.

SCHEDULING
  All sweeps run OFF-PEAK. DeepSeek peak = 01:00-04:00 and 06:00-10:00 UTC.
  Peak rates are ~2x. This is a real line item, not a detail.

METRICS
  PRIMARY    grounded_pass_rate  (oracle-verified, correct AND grounded)
  PRIMARY    pass^k              (all k i.i.d. trials succeed, averaged over
                                  scenarios; Yao et al. 2024, tau-bench)
  SECONDARY  pass@1, cost/run, tokens/run, latency p50/p95, steps/run
  SECONDARY  judge TPR, TNR, Cohen's kappa, corrected prevalence

STATISTICS
  intervals           Wilson 95% on every proportion, no exceptions
  paired comparison   McNemar (exact for n<25 discordant, chi-square above)
  bootstrap           10,000 resamples, seeded
  DECLARED POWER      n=200 paired detects ~10pp differences at 80% power.
                      Differences below 10pp are reported as INCONCLUSIVE,
                      never as "no difference."

JUDGE
  role                secondary instrument; never overrides the oracle
  pinned model        <name+version>, frozen at P5
  splits              train / dev / test, content-addressed
  discipline          freeze judge, read test set ONCE

ARTIFACTS
  every project ships  results.json, figure.svg, DECISIONS.md, README.md
  reproducibility      one make target per project, deterministic given seed
  raw traces           committed or hash-manifested; never summarized-only

BUDGET
  hard ceiling         USD 150  (~INR 13,500)
  per-project caps     see §4
  stop rule            hitting a project cap = stop, log it, do not borrow

PUBLICATION CRITERIA
  A result publishes if: pre-registered, powered or explicitly declared
  underpowered, reproducible by command, and honest about limitations.
  A NULL result meeting these criteria publishes. No exceptions.
```

---

## 3. Correction to the P6 design (read this before anything else)

I ran the power analysis before writing this plan. **My earlier P6 design was underpowered and I am replacing it.** Here is the arithmetic that forced the change.

**Problem 1 — the between-model test is weak.** McNemar on n=200 paired scenarios, assuming ~20% discordance:

| Difference to detect | n needed | Verdict at n=200 |
|---|---|---|
| 3 pp | 1,740 | underpowered |
| 5 pp | 625 | underpowered |
| 8 pp | 243 | underpowered |
| 10 pp | 154 | OK |

If cheap and frontier differ by 3–5 pp — the realistic case in 2026 — n=200 cannot see it. Running it anyway and reporting "no significant difference" would be a false null.

**Problem 2 — pass^k does not amplify the gap the way intuition says.** Two models 3 pp apart at pass@1:

| k | Model A | Model B | Absolute gap |
|---|---|---|---|
| 1 | 70.0% | 73.0% | 3.0 pp |
| 2 | 49.0% | 53.3% | 4.3 pp |
| 3 | 34.3% | 38.9% | **4.6 pp** ← peak |
| 5 | 16.8% | 20.7% | 3.9 pp |
| 8 | 5.8% | 8.1% | 2.3 pp |

The absolute gap peaks near k=3 then shrinks as both models decay toward zero. My "use k=5" instinct was wrong. And at n=60 × k=5, the Wilson CI on a pass^5 point estimate of 0.168 is ±9.4 pp — useless.

**The fix — change the primary question from between-model to within-model.**

> **Does measured pass^k equal (pass@1)^k?**

If trials were i.i.d., pass^k = p^k exactly. Deviation measures whether failures are *concentrated* on specific scenarios (deterministic hard cases) or *scattered* (stochastic noise). That distinction is what a production team actually needs: scattered failures mean retry; concentrated failures mean the scenario is broken and retrying is theatre.

This is the same methodological move as your Day 7 "naive compounding is wrong" result, applied to trials instead of hops. It reuses machinery you already own and already defended.

Simulation at n=150, k=3, true p=0.70:

| Failure clustering | pass@1 | naive p³ | measured pass³ | Wilson CI | Disjoint? |
|---|---|---|---|---|---|
| none (i.i.d.) | 0.707 | 0.353 | 0.353 | [0.281, 0.433] | no |
| moderate | 0.664 | 0.293 | 0.373 | [0.300, 0.453] | **YES** |
| total (deterministic) | 0.667 | 0.296 | 0.667 | [0.588, 0.737] | **YES** |

Well-powered, cheap, and it produces a finding under every outcome — including the i.i.d. one, which would itself be publishable.

**Locked P6 design:**
- 150 hard-tier scenarios × k=3 trials = 450 runs per model
- Primary: per-model deviation of measured pass³ from naive p³, Wilson CIs
- Secondary: between-model pass@1 comparison, McNemar, **declared powered only for ≥10 pp**
- The hard subset is selected and hashed into the dataset manifest **at P3, before any model sees it**

---

## 4. Budget

Verified pricing, 2026-08-31. Per agent run assumed 10k input / 2.5k output.

**Per-run cost by rung:**

| Rung | Model | Raw | With 60% cached prefix |
|---|---|---|---|
| R1 | gemini-2.5-flash-lite | $0.0020 | $0.0015 |
| R2 | deepseek-v4-flash | $0.0021 | $0.0013 |
| R3 | deepseek-v4-pro | $0.0065 | $0.0042 |
| R4 | minimax-m3 | $0.0120 | $0.0088 |
| R5 | glm-5.2 | $0.0250 | $0.0174 |
| R6 | sonnet-class anchor | $0.0675 | $0.0513 |

**Note on your model picks:** GLM-5.2 at $1.40/$4.40 is **10× DeepSeek V4 Flash**. It is a mid-ladder model, not a cheap one. Keeping it is fine; calling it cheap is not.

**Project allocation (hard caps):**

| Project | Runs | Cap | Notes |
|---|---|---|---|
| P1 real-agent-baseline | ~100 | $2 | R2 only |
| P2 otel-genai-exporter | 0 | $0 | no LLM calls |
| P3 grounding-zero-point | 400 | $5 | R2 + R6 |
| P4 failure-taxonomy | 0 | $0 | reuses P3 traces |
| P5 judge-validation | ~900 | $10 | judge calls + baselines |
| **P6 passk-decay** | **2,700** | **$45** | 450 × 6 rungs, cached, off-peak |
| P7 provider-variance | 600 | $5 | one model, 3 endpoints |
| P8 mcptox-bounded | 1,800 | $10 | subsample 300 × 6 |
| P9 redteam-regression | ~500 | $6 | |
| P10 calibrated-cascade | ~400 | $8 | reuses P6 data heavily |
| P11 release-gate | ~300 | $5 | smoke suite × several runs |
| P12 failure-attribution | ~500 | $6 | retriever ablations |
| **Reserve** | — | **$48** | reruns, mistakes, price moves |
| **CEILING** | | **$150** | ~₹13,500 |

P6 is 30% of spend. Run it **once**, after P5 has validated the judges, off-peak, with caching on.

**MCPTox note:** the full benchmark is 1,312 valid attack instances. Full run across 6 models ≈ $30. Subsampled to 300 via `-T servers` or `-T security_risks` ≈ $7 with CIs still usable. Take the subsample.

---

## 5. Pre-registered hypotheses

Write these to `HYPOTHESES.md` and commit **before** the relevant project runs. Git timestamp is your pre-registration.

| ID | Project | Hypothesis | Falsifiable how |
|---|---|---|---|
| H1 | P3 | Real-model grounded pass rate on T3 is below the simulator baseline | Wilson CIs disjoint |
| H2 | P4 | ≥2 discovered failure modes are absent from the injected F1–F6 catalog | modes fail to map onto catalog |
| H3 | P5 | A cheap judge (R2) reaches κ ≥ 0.7 against human labels on ≥3 of 5 modes | measured κ |
| H4 | **P6** | **Measured pass³ exceeds naive (pass@1)³ for ≥4 of 6 rungs** | Wilson CI of measured excludes naive point |
| H5 | P6 | Deviation from naive is larger for cheap rungs than frontier | rank correlation across ladder |
| H6 | P7 | Same model, 2+ endpoints, grounded rates with disjoint CIs | Wilson CIs disjoint |
| H7 | P8 | Bounded + typed contracts reduce ASR vs MCPTox published rates | ASR CI below published band |
| H8 | P12 | Retrieval owns >50% of grounding failures | attribution split with CIs |

**H4 is the headline.** If it holds, the claim is: *retry does not help as much as independence assumes, because failures concentrate.* If it fails, the claim is: *agent failures on grounded QA are closer to i.i.d. than the field assumes, and retry budgets are being under-spent.* **Both are publishable.** Commit to shipping whichever you get.

---

## 6. The twelve projects

Each project ships: `README.md`, `DECISIONS.md`, `results.json`, one figure, one `make` target, and raw traces.

### Phase 1 — Build the measurement foundation

**P1 · real-agent-baseline** — 8h, $2

Swap the simulator for a real agent. LiteLLM + R2 against the frozen corpus. `oracle_check` untouched — measurement authority stays fixed while the system under test becomes real.

*Gate:* 100 real runs complete, traces land in the Day-5 store, oracle grades them without modification.

**P2 · otel-genai-exporter** — 10h, $0

Emit Day-4 spans as OTel GenAI semconv: `invoke_agent` → `chat` → `execute_tool`, with `gen_ai.request.model`, `gen_ai.usage.*`, `gen_ai.operation.name`. Ship Langfuse and Phoenix sinks. Write a **conformance test** asserting your spans validate against the registry.

*Why this is worth 10 hours:* nearly all `gen_ai.*` attributes still carry Development stability badges — names can change without a major version bump. A conformance-tested exporter with dual-emit is a real gap and a genuinely useful OSS artifact. It also makes your custom SQLite tracer searchable to recruiters who have never heard of it.

*Gate:* one trace, three backends, identical waterfall.

**P3 · grounding-zero-point** — 5h, $5

n=200, R2 and R6, Wilson CIs, per tier. **Select and hash the 150-scenario hard subset for P6 here, before any comparison runs.** Freeze.

*Gate:* `results.json` committed with content-addressed dataset version. This is the first number you can defend cold.

**P4 · failure-taxonomy** — 14h, $0

Open coding on 150 real P3 traces: read the whole trace, write the first failure in plain language. Then axial coding into 5–8 binary modes with definitions, examples, and boundary cases. Check saturation. Compare to your F1–F6 injected catalog **only afterward**.

*This is the hardest project to actually do* — it is manual, boring, and has no dopamine. It is also the single biggest gap in your current work and the most-asked-about skill in eval interviews. Budget two full weekends. Do not let a model do the coding for you; the entire value is that a human found modes nobody predicted.

*Gate:* taxonomy with ≥2 modes not present in F1–F6 (H2), or an honest writeup of why the injected catalog was complete.

**P5 · judge-validation** — 12h, $10

One binary evaluator per P4 mode. Code assertion where objective, LLM judge only where interpretation is genuinely required. Train/dev/test split. Report TPR, TNR, Cohen's κ per judge. Correct prevalence using measured judge error rates. Benchmark against Ragas faithfulness and DeepEval on the same set.

*Gate:* freeze judges, read test set **once**, commit the number. Judges are now instruments with known error bars.

> **PHASE GATE:** Do not start P6 until P5 reports κ and prevalence correction. An unvalidated judge makes every downstream number unfalsifiable.

### Phase 2 — The headline experiment

**P6 · passk-decay** — 10h + compute, $45

150 hard scenarios × k=3 × 6 rungs = 2,700 runs. Same prompt, same tools, same harness, same workload, same suite. Vary one axis: the model.

Primary: per-rung measured pass³ vs naive (pass@1)³, Wilson CIs, disjointness test.
Secondary: between-model pass@1 with McNemar, **explicitly labelled underpowered below 10 pp**.
Also emit: cost per successful grounded answer, per rung. That number is the seed of your Model Value Score.

*Gate:* H4 resolved either way. Raw traces committed.

### **PUBLICATION #1** — 8h

Title shape: *"Retry Doesn't Help The Way You Think: measured vs. i.i.d. pass^k across six models on a grounded QA task."*

Contains: question, pre-registration link (git hash), method, frozen config, raw data, result with intervals, limitations, one reproducible command, negative results included.

Post to: your blog, HN, r/MachineLearning, the eval Discord, LinkedIn, X. Email it to three people whose work you cite. That last step is the one everybody skips and it is the one that works.

> **HARD GATE: do not start P7 until Publication #1 is live.** The plan fails at exactly this step or nowhere.

### Phase 3 — Generalization

**P7 · provider-variance** — 6h, $5

One model name, three endpoints, everything else identical. Grounded rate, latency, cost, with CIs. Log provider, model version, and quantization in every span.

*Why:* a leaderboard row saying "Model X = 85%" is meaningless if the served artifact varies by endpoint. Almost nobody measures this.

**P8 · mcptox-bounded** — 10h, $10

Use the existing Inspect AI implementation of MCPTox (MIT, `inspect-evals-mcptox`), dataset SHA256-verified from a pinned upstream commit, 1,312 valid instances, judge-graded into Success / Failure-Direct-Execution / Failure-Ignored / Failure-Refused / Invalid. Subsample to ~300. **Do not rebuild the harness.**

Your contribution is the second arm: MCPTox reproduces a **single-turn** protocol — one system prompt, one benign query, one JSON tool call. Your bounded, step-capped, `extra="forbid"` agent is a structurally different threat surface. Run both arms, report the delta.

*Published baseline to beat:* average ASR 36.5% across 45 servers, peaking at 72.8%, with more capable models often *more* susceptible because superior instruction-following makes them more compliant with malicious metadata.

*Gate:* H7 resolved. Cite the paper (arXiv 2508.14925, AAAI 2026) and the Inspect implementation properly.

### **PUBLICATION #2** — 6h

Title shape: *"Do Typed Contracts and Step Caps Blunt Tool Poisoning? An independent MCPTox arm."*

Same discipline as #1. Send it to the MCPTox authors and the Inspect maintainers directly.

### Phase 4 — Findings into engineering

**P12 · failure-attribution** — 10h, $6

Ablate retriever vs generator. For each P4 failure mode, which subsystem owns it? Report with CIs.

*Runs before P10 because it is a precondition:* if grounding failures are retriever-owned, escalating to a frontier model cannot fix them, and a cascade calibrated on the wrong variable is worse than no cascade. Also reuses P4/P6 traces while they are warm.

*Deliverable sentence:* "Don't change the model. Fix chunking." That is what a reliability engineer gets paid to say.

**P10 · calibrated-cascade** — 12h, $8

Cheap → frontier router. Escalation threshold fit on P5-labelled data, not vibes. Plot the Pareto frontier; keep multiple points on it. Reuses P6 runs.

*This is the methodology layer of your Model Value Score.* Naive score/cost ratio is exactly what this replaces: reliability-per-dollar with intervals, measured on one workload, attributed to a subsystem.

**P9 · redteam-regression** — 8h, $6

Promptfoo attack suite against the live endpoint — 40+ adversarial plugin categories. Every successful attack becomes a failing pytest. Authorization must hold even when the model is fully compromised; assert that separately from any detector.

*Independent of P12 — parallelize if convenient.*

**P11 · release-gate** — 10h, $5

GitHub Actions gate with **tolerance bands, not exact thresholds**, a pinned judge, and a stable golden set — the three things that stop flaky eval CI. Then the upgrade drill: every model stored as a config, full suite re-runnable on demand when a new model ships.

*Gate:* a real model upgrade run end-to-end, producing a PASS/FAIL and a redrawn frontier.

---

## 7. Schedule

Assumes ~16 h/week. Total ≈ 129 h.

| Week | Work | Cumulative spend |
|---|---|---|
| 1 | MEC + HYPOTHESES frozen · P1 · P2 start | $2 |
| 2 | P2 finish · P3 | $7 |
| 3 | P4 (open coding) | $7 |
| 4 | P4 (axial) · P5 start | $12 |
| 5 | P5 finish · **PHASE GATE** · P6 | $57 |
| 6 | **PUBLICATION #1** | $57 |
| 7 | P7 · P8 | $72 |
| 8 | **PUBLICATION #2** · P12 | $78 |
| 9 | P10 · P9 | $92 |
| 10 | P11 · repo surgery · final report | $97 |

Slack: 3 weeks. Something will break — likely P4 taking longer than budgeted, or a provider deprecating a model mid-sweep.

---

## 8. Repo structure

```
faultline/                    importable package — the instruments
  env/ oracle/ agent/ trace/ stats/ judge/ sweep/ attribute/
arc/day01..day30/             Phase 1, simulator, scope frozen
projects/p01..p12/            Phase 2, real models
reports/                      the deliverables
MEC.md                        master experiment contract
HYPOTHESES.md                 pre-registrations
AMENDMENTS.md                 A-001…
SCOPE.md                      what is capped and why
DECISIONS.md                  D-001… (existing, continued)
```

**README surgery, do it at P3 not week 10:**
- Headline number and one figure above the fold
- `pip install -e .` then one command that reproduces it
- "50-day arc" deleted; no 🔜 rows in the top section
- `dayNN/` demoted under `arc/`
- Phase 1 / Phase 2 framing stated in two sentences

---

## 9. Success criteria

Not "did I finish 12."

**Engineering** — can a stranger reproduce it from the README alone? Does CI catch a regression you deliberately introduce? Can you explain every measurement without notes?

**Research** — was the question pre-registered? Could the result have gone either way? Is the methodology defensible to someone hostile? Are limitations stated before someone else finds them?

**Hiring** — can you explain the headline experiment in 5 minutes to a non-specialist? Can you defend the statistics under pressure? Can you narrate a failed experiment without flinching?

**Distribution** — did anyone who does not know you read it? Did an engineer reply? Did a researcher engage? Did it start a conversation that led anywhere?

That last block is the one you will be tempted to skip. It is the one that converts the work into a job.

---

## 10. Failure modes and kill switches

| Risk | Signal | Action |
|---|---|---|
| P4 never gets done | Two weeks pass, <40 traces coded | Cut to 80 traces, 4 modes. Shipping a smaller taxonomy beats an unshipped one. |
| P6 returns a clean null | Measured pass³ ≈ naive p³ everywhere | **Publish it.** "Failures are closer to i.i.d. than assumed" is a real, useful, rarely-reported result. This is not a failure of the plan. |
| Provider deprecates a rung mid-sweep | 404 or silent version change | Log amendment, substitute nearest rung, re-run that rung only. Never mix versions inside one sweep. |
| Budget hits $150 | Ceiling reached | Stop. P9–P11 are cuttable. P1–P8 plus two publications is the complete story. |
| Time runs out at week 10 | | Ship P1–P8 + 2 publications + clean repo. **Do not** grind out P9–P11 to say "12 of 12" while nobody has read the work. |
| Temperature 0 not honored by a provider | Non-deterministic repeats at t=0 | Document it as a finding — it belongs in P7. |

**The cut order, if forced:** P11 → P9 → P10 → P12. Never cut a publication.

---

## 11. What I got wrong in earlier drafts

Recorded so you can see the reasoning, and so future-you does not re-derive it:

1. **P6 was underpowered.** n=200 paired detects only ~10 pp. Fixed by changing the primary question to within-model pass^k deviation.
2. **k=5 was wrong.** The absolute gap between two models peaks near k=3 and shrinks after. Fixed: k=3, n=150.
3. **P8 cost was understated** — $8 → ~$30 at full scale. Fixed by subsampling to ~300 and by using the existing Inspect implementation instead of building one.
4. **"GLM is cheap" is false.** It is 10× DeepSeek V4 Flash. Repositioned to R5.
5. **Distribution was missing entirely** from the first version of this plan. It is now two hard gates.

---

## 12. Sources

- τ-bench / pass^k: Yao et al., arXiv 2406.12045 (ICLR 2025). pass^k = chance all k i.i.d. trials succeed, averaged across tasks.
- MCPTox: arXiv 2508.14925 (AAAI 2026); Inspect implementation `stefanoamorelli/inspect-evals-mcptox` (MIT).
- OTel GenAI semantic conventions — Development status; `invoke_agent` / `chat` / `execute_tool`; MCP conventions merged into the GenAI repo at v1.42.0.
- Pricing verified 2026-08-31. DeepSeek peak/off-peak split introduced 2026-08-16 — **re-verify before each sweep.**

---

*Frozen v1.0 · amendments in `AMENDMENTS.md` · this document is a research contract, not a promise about outcomes.*
