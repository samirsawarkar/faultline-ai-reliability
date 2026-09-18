# P10 — Calibrated Cheap-to-Frontier Cascade & Pareto Frontier

## Executive Summary
On this workload the cheap model is on the frontier and escalating to the frontier model buys one extra pass in thirty at twice the cost — consistent with P12, where failures were retriever-owned.

When evaluated across matched hard multi-hop scenarios:
- **R2 (`glm-5.3-flash`, Cheap Workhorse)**: Achieves **76.7%** pass rate at **$0.0078 / run** on the held-out test split.
- **R4 (`gpt-5.6-luna`, Frontier Anchor)**: Achieves only **20.0%** pass rate at **$0.0634 / run** on the held-out test split (severely sub-frontier and dominated).
- **Calibrated Cascade**: Escalate on deterministic runtime signals (`status != 'answered'` or `steps >= 23`) achieves **80.0%** pass rate at **$0.0159 / run** (16.7% escalation rate) — gaining exactly 1 scenario (+3.3pp) over R2-only at 2.0× mean cost.
- **Theoretical Router Ceiling**: Across the full 100 scenarios, R2 passes 75 and fails 25. R4 passes 24, rescuing exactly **7 of 25** R2 failures. Therefore, an omniscient router that perfectly chooses when to escalate has an upper bound of $(75 + 7) / 100 = \mathbf{82.0\%}$.

## Design
A two-tier model cascade without an LLM judge:
1. **Initial Tier**: Run R2 (`glm-5.3-flash`, $0.14 in / $0.28 out per M tokens).
2. **Runtime Escalation Signal**: Check deterministic fields of the completed R2 run trace:
   - `status != 'answered'` (e.g. `step_cap`, `malformed`, `model_failure`).
   - Empty `cited_sources` (model returned an answer without grounding citations).
   - High step count: `steps_used >= t` for $t \in [2..24]$.
   - Combined: `status != 'answered' or steps_used >= t`.
3. **Escalation Action**: If the signal fires, discard R2's response, execute R4 (`gpt-5.6-luna`, $0.60 in / $2.40 out per M tokens), and take R4's answer.
4. **Ground Truth**: Evaluated against deterministic oracle check verdict (`grounded`).

### Content-Addressed Train / Test Split
To prevent data leakage and overfitting:
- **Hashing**: SHA-256 hex digest computed for each scenario ID.
- **Sorting**: Scenario IDs sorted lexicographically by SHA-256 hash.
- **Partition**: First 70% (70 scenarios) assigned to train split; remaining 30% (30 scenarios) assigned to held-out test split. Completely disjoint and platform-deterministic.
- **Threshold Selection**: On train, optimal threshold $t$ selected by maximizing train pass rate, with ties broken by lowest mean cost. Headline numbers are reported exclusively on the held-out test split.

## Dataset
- **R2 Arm A**: 150 hard-pool multi-hop scenarios (`r-0201` to `r-0350`) from Project P12 (`projects/p12_attribution/sweep_output_R2_A.json`).
- **R4 Arm A**: First 100 matched hard-pool scenarios (`r-0201` to `r-0300`), comprising 10 scenarios from P12 pilot plus 90 newly executed runs under project key `p10_cascade` (`projects/p10_cascade/sweep_output_R4_A.json`).

## Results Table
Evaluated across 100 paired scenarios (Train $N=70$, Test $N=30$):

| Policy | Train Pass Rate (95% CI) | Train Mean Cost | Train Escalation | Test Pass Rate (95% CI) | Test Mean Cost | Test Escalation | Status |
|---|---|---|---|---|---|---|---|
| `r2_only` (Baseline) | 0.743 [0.630, 0.831] (52/70) | $0.0074 | 0.0% | **0.767 [0.591, 0.882]** (23/30) | **$0.0078** | 0.0% | **Frontier** |
| `r4_only` (Frontier Anchor) | 0.257 [0.169, 0.370] (18/70) | $0.0565 | 100.0% | **0.200 [0.095, 0.373]** (6/30) | **$0.0634** | 100.0% | Dominated |
| `escalate_if_not_answered` | 0.800 [0.692, 0.877] (56/70) | $0.0119 | 10.0% | **0.800 [0.627, 0.905]** (24/30) | **$0.0159** | 16.7% | **Frontier** |
| `escalate_if_no_citation` | 0.800 [0.692, 0.877] (56/70) | $0.0119 | 10.0% | **0.800 [0.627, 0.905]** (24/30) | **$0.0159** | 16.7% | **Frontier** |
| `escalate_if_steps_ge_23` (Fitted) | 0.800 [0.692, 0.877] (56/70) | $0.0119 | 10.0% | **0.800 [0.627, 0.905]** (24/30) | **$0.0159** | 16.7% | **Frontier** |
| `escalate_if_not_answered_or_steps_ge_23` | 0.800 [0.692, 0.877] (56/70) | $0.0119 | 10.0% | **0.800 [0.627, 0.905]** (24/30) | **$0.0159** | 16.7% | **Frontier** |

*Note: On both splits, every run that failed to produce an answer (`status != 'answered'`) had also cited no sources and consumed $\ge 23$ steps, rendering the four deterministic signals equivalent on this dataset.*

## Pareto Frontier
Across the 50 candidate policies evaluated on the held-out test split, the strictly non-dominated Pareto frontier consists of:
1. `r2_only`: Cost **$0.0078**, Pass Rate **76.7%** [0.591, 0.882], Escalation 0.0%.
2. `escalate_if_not_answered` / `steps_ge_23`: Cost **$0.0159**, Pass Rate **80.0%** [0.627, 0.905], Escalation 16.7%.
3. `escalate_if_steps_ge_21`: Cost **$0.0193**, Pass Rate **83.3%** [0.664, 0.927], Escalation 23.3%.

All other policies (including `r4_only`) are Pareto-dominated.

## The Theoretical Rescue Ceiling
Across the full $N=100$ scenarios:
- R2 alone passed **75** scenarios and failed **25**.
- R4 alone passed **24** scenarios.
- Looking at the 25 scenarios where R2 failed, R4 passed only **7** (`r-0206`, `r-0208`, `r-0209`, `r-0230`, `r-0257`, `r-0260`, `r-0281`).
- For the other 18 R2 failures, R4 also failed.
- Consequently, even a hypothetical **perfect oracle router** that knows beforehand whether R4 will succeed can achieve at most:
  $$\text{Ceiling} = \frac{75 + 7}{100} = \mathbf{82.0\%}$$
On the held-out test split, the theoretical ceiling is $(23 + 2) / 30 = 25/30 = 83.3\%$, against which the calibrated cascade achieves $24/30$ ($80.0\%$).

## Secondary Replicate: Project P6
Replicating the cascade simulation on Project P6 (`projects/p06_passk/trace.db`) across 450 matched runs (`p06_r2_7e0a1b79` vs `p06_r4_7e0a1b79`):
- **Infrastructure Incident**: 95 of 450 R4 runs suffered zero-token gateway timeout errors (`infra_dead`).

### Full-Set Metrics (Entire Dataset)
- **`as_run` ($n=450$)**:
  - `r2_only`: pass rate **0.6311** (63.1%), mean cost **$0.0093**
  - `r4_only`: pass rate **0.1489** (14.9%), mean cost **$0.0492**
- **`infra_excluded` ($n=355$)**:
  - `r2_only`: pass rate **0.6085** (60.8%), mean cost **$0.0092**
  - `r4_only`: pass rate **0.1887** (18.9%), mean cost **$0.0598**

### Held-Out Test Split Metrics (`infra_excluded`, $n=107$)
- `r2_only`: pass rate **0.579** (57.9%), mean cost **$0.0090**
- `r4_only`: pass rate **0.131** (13.1%), mean cost **$0.0621**
- `escalate_if_steps_ge_24`: pass rate **0.589** (58.9%), mean cost **$0.0124**
- `escalate_if_not_answered`: pass rate **0.617** (61.7%), mean cost **$0.0299**

In both the primary P10 dataset and the P6 replicate, R2 strongly dominates the Pareto frontier over R4.

## Economics & Spend
All spend recorded per-call to `ledger.jsonl` under the pre-registered $8.00 P10 budget ceiling:
- Newly executed runs: 90 scenarios on R4 (`gpt-5.6-luna`, $0.60 in / $2.40 out per M tokens).
- Total Input Tokens: 6,685,635 (~74,285 tokens/run) -> $4.0114 USD
- Total Output Tokens: 272,425 (~3,027 tokens/run) -> $0.6538 USD
- **Total Project Spend**: **$4.6652 USD** (58.3% of $8.00 cap; $3.3348 remaining).

## Limitations
1. **Deviation from Original Plan (No LLM Judge)**: The original Phase 2 plan envisioned training an escalation router on P5 judge-labelled data. However, Project P5 showed that the LLM judge had Cohen's $\kappa \approx 0$ (falsifying Hypothesis H3). Consequently, this project relies exclusively on deterministic runtime signals (`status`, `steps_used`, `cited_sources`).
2. **Model Accuracy Variance Disclosed**: R4 (`gpt-5.6-luna`) achieved a pass rate of $24.0\%$ (24/100) here, compared to $15\%$ in P6 and $70\%$ (7/10) in the P12 pilot. This same-model gateway drift across runs and dates is reported empirically without post-hoc rationalization.
3. **Test Sample Size ($n_{\text{test}} = 30$)**: Because 70 scenarios were held for train, the test split contains 30 scenarios. At $N=30$, Wilson 95% confidence intervals are approximately $\pm 15\text{pp}$ wide. The cascade's $+3.3\text{pp}$ improvement over R2-only represents exactly one additional passing scenario (24 vs 23).
4. **Single Trial ($k=1$)**: Each arm was run for a single trial ($k=1$) per scenario under a hard step cap of 24 (Amendment A-003).
5. **P6 Replicate Artifacts**: The P6 replicate suffered 95 gateway dropouts on R4, and P6 span traces did not record `cited_sources`, making `escalate_if_no_citation` degenerate on that replicate.
6. **Execution Pause and Resume**: The R4 sweep was paused at 46 new runs for budget verification and resumed. Four runs (`r-0256`, `r-0258`, `r-0259`, `r-0260`) were interrupted mid-flight and cleanly re-executed upon resumption. `trace.db` retains spans for both attempts for those four scenarios, while `sweep_output_R4_A.json` retains only the final completed attempt used by the simulation.

## Reproduce
```bash
# Dry-run cost estimation (zero spend, no network calls)
.venv/bin/python projects/p10_cascade/run.py --dry-run

# Run P10 simulation and regenerate results.json from sweep outputs
.venv/bin/python projects/p10_cascade/run.py --simulate \
  --r4-file projects/p10_cascade/sweep_output_R4_A.json \
  --output-dir projects/p10_cascade

# Generate Pareto frontier figure (figure.svg and figure.png)
.venv/bin/python projects/p10_cascade/make_figure.py

# Re-run full P12 runner sweep (requires --confirm and live API keys)
# .venv/bin/python projects/p12_attribution/run.py --rung R4 --arms A \
#   --scenarios 100 --pool hard --project p10_cascade \
#   --output-dir projects/p10_cascade --confirm --concurrency 4
```
