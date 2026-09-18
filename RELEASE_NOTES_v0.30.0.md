## Highlights of Release v0.30.0

**FAULTLINE Phase 2 Milestone: Projects P12 & P10 — Failure Attribution and the Calibrated Cascade**

This release marks the completion of **Project P12** (Failure Attribution: Retriever vs Generator under Hypothesis H8) and **Project P10** (Calibrated Cheap-to-Frontier Cascade and Empirical Pareto Frontier) by Samir Sawarkar (*FAULTLINE AI Reliability Engineering*).

Release v0.30.0 resolves the root cause of multi-hop grounding failures in autonomous agents through oracle retrieval ablations, establishes an empirical Pareto frontier for model cascades using deterministic runtime signals without subjective LLM judges, and completes the Phase 2 empirical roadmap under strict cost governance ($36.67 cumulative Phase 2 spend across all experimental sweeps).

---

### Executive Summary

1. **P12 Failure Attribution (H8 Supported on R2)**: Evaluated 150 matched hard 5-hop scenarios under normal retrieval (Arm A) versus oracle retrieval (Arm B). Pre-registered Hypothesis H8 (*"Retrieval owns >50% of grounding failures"*) is **SUPPORTED** on R2 (`glm-5.3-flash`), where the retriever owns $32/34 = 0.9412$ (94.1%) of failures (Wilson 95% CI $[0.8091, 0.9837]$), strictly bounded above 50%. The paired McNemar test confirms the oracle retrieval advantage is statistically significant (exact binomial $p = 1.94 \times 10^{-6}$, continuity-corrected $\chi^2 = 20.25, p = 6.80 \times 10^{-6}$). On R4 (`gpt-5.6-luna`, $n=10$ pilot), retriever share is $3/3 = 1.0000$ (Wilson 95% CI $[0.4385, 1.0000]$, exact $p = 0.250$), resulting in an **UNDECIDED** verdict solely due to pilot sample size.
2. **Failure Mechanism Analysis**: Auditing step traces revealed that 29 of 32 retriever-owned R2 failures (90.6%) and 3 of 3 R4 failures (100.0%) never surfaced at least one required chain document in search results; only 3 of 32 R2 failures surfaced all required documents yet failed to synthesize the answer. Oracle retrieval cut mean prompt tokens from 47,852 to 15,349 (3.1× reduction) and mean spans from 17.43 to 5.35 (3.3× reduction) because required chain facts were available on initial search.
3. **P10 Calibrated Cheap-to-Frontier Cascade**: Implemented a two-tier cascade executing R2 (`glm-5.3-flash`, $0.14 in / $0.28 out per M tokens) and escalating to R4 (`gpt-5.6-luna`, $0.60 in / $2.40 out per M tokens) upon deterministic runtime signals (`status != 'answered'` or `steps_used >= 23`) fit on a 70-scenario SHA-256 content-addressed training split. On the held-out test split ($n=30$), the cascade achieved **80.0%** pass rate [0.627, 0.905] at **$0.0159 / run** (16.7% escalation rate, 5/30), gaining 1 scenario (+3.3pp) over the R2-only baseline (**76.7%** [0.591, 0.882] at **$0.0078 / run**) at 2.0× mean cost. R4 alone achieved only **20.0%** [0.095, 0.373] at **$0.0634 / run** (Pareto-dominated).
4. **Theoretical Rescue Ceiling**: Across all 100 paired scenarios, R2 passed 75 and failed 25; R4 passed 24, rescuing exactly 7 of 25 R2 failures (and failing on the other 18). An omniscient router perfectly selecting when to escalate achieves an upper bound of $(75 + 7)/100 = \mathbf{82.0\%}$ (held-out test split ceiling $(23 + 2)/30 = 25/30 = \mathbf{83.3\%}$).
5. **Rigorous Budget Discipline and Operational Corrections**: The P12 dry-run estimator was corrected from a guessed 35,000 in / 2,000 out tokens per run to P6-measured final-pass tokens (R2 59,452 / 3,364; R4 55,002 / 2,891), and the CTO's own $1.35 quote for P12 was corrected to a $3.58 ceiling before any spend; actual P12 spend was $1.9258 ($1.4683 R2 + $0.4575 R4) of the $6.00 cap. P10's planned 140-scenario R4 sweep was cut to 90 by the owner's budget; the sweep was paused after 46 new runs at the owner's request, resumed with zero re-spend from the incrementally saved sweep file, and finished 100 paired scenarios at $4.6652 (58.3% of the $8.00 cap); four runs interrupted at the pause (r-0256, r-0258, r-0259, r-0260) were re-executed and trace.db keeps both attempts. The P12 runner's one-arm artifacts results_R4.json and manifest_R4.json written into projects/p10_cascade/ were deleted because their 'H8 FALSIFIED' verdict is meaningless without an oracle arm. Total Phase 2 spend across all sweeps is $36.67 of the $150.00 ceiling.

---

### Key Empirical Results: Failure Attribution (Project P12)

| Rung | Role | Model | $n$ | Both Pass | Retriever Owned | Generator Owned | Reverse | Retriever Share | Wilson 95% CI | McNemar $p$ | H8 Verdict | Spend |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **R2** | Cheap Workhorse | `z-ai/glm-5.3-flash` | 150 | 112 (74.7%) | 32 (21.3%) | 2 (1.3%) | 4 (2.7%) | **0.9412** (32/34) | [0.8091, 0.9837] | exact $p = 1.94 \times 10^{-6}$ / $\chi^2$ $p = 6.80 \times 10^{-6}$ | **SUPPORTED** | $1.4683 |
| **R4** | Frontier Anchor | `openai/gpt-5.6-luna` | 10 | 7 (70.0%) | 3 (30.0%) | 0 (0.0%) | 0 (0.0%) | **1.0000** (3/3) | [0.4385, 1.0000] | exact $p = 0.250$ | **UNDECIDED** (pilot) | $0.4575 |

---

### Key Empirical Results: Calibrated Cascade (Project P10)

Evaluated across 100 paired scenarios (Train $N=70$, Held-Out Test $N=30$):

| Policy | Train Pass Rate (95% CI) | Train Mean Cost | Train Escalation | Test Pass Rate (95% CI) | Test Mean Cost | Test Escalation | Status |
|---|---|---|---|---|---|---|---|
| `r2_only` (Baseline) | 0.743 [0.630, 0.831] (52/70) | $0.0074 | 0.0% | **0.767 [0.591, 0.882]** (23/30) | **$0.0078** | 0.0% | **Frontier** |
| `r4_only` (Frontier Anchor) | 0.257 [0.169, 0.370] (18/70) | $0.0565 | 100.0% | **0.200 [0.095, 0.373]** (6/30) | **$0.0634** | 100.0% | Dominated |
| `escalate_if_not_answered` | 0.800 [0.692, 0.877] (56/70) | $0.0119 | 10.0% | **0.800 [0.627, 0.905]** (24/30) | **$0.0159** | 16.7% | **Frontier** |
| `escalate_if_no_citation` | 0.800 [0.692, 0.877] (56/70) | $0.0119 | 10.0% | **0.800 [0.627, 0.905]** (24/30) | **$0.0159** | 16.7% | **Frontier** |
| `escalate_if_steps_ge_23` (Fitted) | 0.800 [0.692, 0.877] (56/70) | $0.0119 | 10.0% | **0.800 [0.627, 0.905]** (24/30) | **$0.0159** | 16.7% | **Frontier** |
| `escalate_if_not_answered_or_steps_ge_23` | 0.800 [0.692, 0.877] (56/70) | $0.0119 | 10.0% | **0.800 [0.627, 0.905]** (24/30) | **$0.0159** | 16.7% | **Frontier** |

---

### Included Release Assets

- 📊 **`projects/p12_attribution/figure.png`**: Failure attribution waterfall and mechanism analysis across R2 and R4.
- 📊 **`projects/p10_cascade/figure.png`**: Calibrated cascade Pareto frontier and cost-versus-accuracy trade-offs.
- 📦 **`projects/p12_attribution/results_R2.json`** & **`results_R4.json`**: Machine-readable attribution counts, Wilson CIs, McNemar statistics, and token metrics.
- 📦 **`projects/p10_cascade/results.json`**: Full simulation metrics for 50 candidate policies across train/test splits and P6 replicate.
- 📋 **`projects/p10_cascade/DECISIONS.md`**: Architectural decision record documenting budget calibration, pause/resume procedure, and artifact hygiene.
- 📋 **`projects/p12_attribution/README.md`** & **`projects/p10_cascade/README.md`**: Detailed technical specifications and reproduction instructions.

---

### One-Command Reproduction

```bash
make venv
make test          # Runs all 528 Phase 1 tests
make phase2-test   # Runs all 136 Phase 2 tests (P00-P08, P10, P12, P13, P15, P16)
make p12 ARGS=--dry-run   # P12 cost estimation dry-run ($0 spend)
make p10-simulate         # Replays P10 cascade simulation from cached traces ($0 spend)
```

**Test Gate Verification:** 664 / 664 Unit/Integration tests passing (528 Phase 1 + 136 Phase 2). All pre-registered hypotheses tracked in `HYPOTHESES.md`.

---

### Limitations

1. **Deterministic Substring Retriever**: The retrieval component evaluated in P12 and P10 is a deterministic case-insensitive substring search over corpus titles and texts, returning top-5 candidates with 500-character snippets. Results reflect the dynamics of exact lexical matching rather than chunked vector embeddings, dense rerankers, or hybrid RAG pipelines.
2. **Model Gateway Drift Across Sweeps**: R4 (`gpt-5.6-luna`) exhibited substantial accuracy drift across experimental campaigns: $24.0\%$ (24/100) in P10 vs $14.9\%$ (67/450 as-run) / $18.9\%$ (67/355 infra-excluded) in P6 vs $70.0\%$ (7/10) in the P12 pilot. This same-model cloud gateway variance is disclosed empirically.
3. **Held-Out Test Sample Size ($n_{\text{test}} = 30$)**: Holding out 70 scenarios for policy parameter fitting leaves 30 scenarios for out-of-sample testing. At $N=30$, Wilson 95% confidence intervals are approximately $\pm 15\text{pp}$ wide, and the cascade's $+3.3\text{pp}$ pass rate gain over R2-only represents exactly one additional passing scenario (24 vs 23).
4. **Single Trial ($k=1$) Execution**: Sweeps were conducted at $k=1$ trial per scenario under a hard 24-step cap (Amendment A-003). Multi-trial failure clustering and variance across runs were not ablated for the cascade policies.
5. **Project P6 Secondary Replicate Gateway Incident**: In the P6 replicate dataset, 95 of 450 R4 runs suffered zero-token infrastructure gateway timeouts (`infra_dead`), and P6 span traces did not record `cited_sources`.
6. **Pending Phase 2 Projects**: Projects P09 (Evaluator Ablation) and P11 (Active Failure Detection) remain unexecuted on the roadmap.
