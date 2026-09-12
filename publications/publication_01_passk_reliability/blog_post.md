# Failures Did Not Concentrate: A Pre-Registered Agent Hypothesis Failed in Public (And a Cheap Model Won by 48 Points)

**By Samir Sawarkar**  
*FAULTLINE (Independent Research)*  
*Full Paper:* [`paper.md`](./paper.md) · *Code & Data:* [`github.com/samirsawarkar/faultline-ai-reliability`](https://github.com/samirsawarkar/faultline-ai-reliability)

---

![Overview of the Experiment](./figure_overview.jpg)

In production AI engineering, retry loops are ubiquitous. When an autonomous tool-use agent fails, the standard prescription is simple: *just retry it three times ($k=3$)*.

Under basic probability, if failures are independent random events, multi-trial joint reliability decays exponentially:
$$\text{pass}^k_{\text{naive}} = (\text{pass@1})^k$$

However, practitioners and researchers routinely argue that real agent tasks are non-uniform: hard tasks fail consistently, while easy tasks succeed consistently. Under this **failure concentration** thesis, retries should compound far better than independent coin flips:
$$\text{pass}^k > (\text{pass@1})^k$$

On September 1, 2026, before generating a single token of test data, we pre-registered this claim as **Hypothesis H4** under Minimum Evaluation Contract (MEC) v1.0 in `HYPOTHESES.md`:
> *"Measured $\text{pass}^3$ strictly exceeds naive compounding $(\text{pass@1})^3$ (disjoint Wilson 95% score intervals) for $\ge 4$ of 6 rungs."*

The pre-registration explicitly bound us to publish regardless of outcome:
> *"Both publish. Which one ships is decided by the data, and that decision is made here, before any of it exists. A clean null on H4 is a result, not a failed experiment."*

Then we spent real money: **1,350 audited multi-hop agent executions** across 150 reserved Tier 3 scenarios (5-hop knowledge graph traversals requiring 9 specific source documents) $\times$ $k=3$ trials across 3 foundation models, audited to the cent in an append-only ledger ($23.73 total spend, 25,477 logged telemetry spans in SQLite).

**The result: Hypothesis H4 was FALSIFIED.**

Failures did not concentrate into an easy task cluster. On the primary workhorse model carrying statistical mass (R2, `z-ai/glm-5.3-flash`, with 34 scenarios passing all three trials), measured joint reliability was $\text{pass}^3 = 22.67\%$ (Wilson 95% CI $[16.70\%, 30.00\%]$) against naive compounding of $25.14\%$ ($0.6311^3$). The ratio was **$0.902\times$**—the model decayed *below* naive compounding, and the naive estimate sits safely inside the confidence interval.

Only one model exhibited concentration (R4, `openai/gpt-5.6-luna`), where measured $\text{pass}^3 = 2.00\%$ exceeded naive $0.33\%$ ($6.06\times$)—but that concentration rested on exactly **3 scenarios out of 150**. R6 (`deepseek/deepseek-v4-pro`) collapsed at the floor ($0.00\%$ everywhere; all 450 runs terminated at step 1 with `model_failure`).

Under both the original pre-registered threshold ($\ge 4$ of 6 rungs) and the evaluated threshold ($\ge 2$ of 3 rungs), **failure concentration failed to hold**.

While the data refused our pre-registered hypothesis, it revealed four unexpected operational findings.

---

## 1. The 48-Point Cost Upset: Budget Model Destroys Frontier Reasoning

The conventional playbook assumes that complex multi-hop tool use demands expensive frontier reasoning models. The empirical data showed the exact opposite:

| Model Rung | Architecture & Role | Single-Turn Pass@1 (Wilson 95% CI) | Joint Pass³ (3/3 Trials) | Total Spend | Cost per Grounded Answer |
|---|---|:---:|:---:|:---:|:---:|
| **R2 (`glm-5.3-flash`)** | Budget Workhorse | **63.11%** [58.56%, 67.44%] | **22.67%** (34/150) | $4.17 | **$0.01468** (~₹1.30) |
| **R4 (`gpt-5.6-luna`)** | Frontier OpenAI | **14.89%** [11.90%, 18.47%] | **2.00%** (3/150) | $17.97 | **$0.26825** (~₹23.60) |
| **R6 (`deepseek-v4-pro`)** | Frontier Anchor | **0.00%** [0.00%, 0.85%] | **0.00%** (0/150) | $0.07 | N/A *(Step 1 model failure)* |
| **Total** | | | | **$23.73** | |

### The Findings:
- **Descriptive Single-Turn Gap**: On single-turn accuracy ($\text{pass@1}$), R2 outperformed R4 by **48.22 percentage points** ($63.11\%$ vs $14.89\%$) with strictly disjoint Wilson 95% confidence intervals. This 48.22 pp difference is strictly **descriptive**: no hypothesis test was pre-registered or run on $\text{pass@1}$.
- **Statistically Significant Joint Reliability**: The pre-registered significance test was executed on **joint 3-trial reliability ($\text{pass}^3$)** across the **exact same 150 scenarios**. A paired McNemar test with continuity correction yielded:
  - Discordant pairs: $b = 34$ (R2 passed all 3, R4 failed), $c = 3$ (R4 passed all 3, R2 failed), both wrong: $113$.
  - Test statistic: $\chi^2 = 24.3243, p = 8.140458 \times 10^{-7}$ (exact binomial $p = 1.233129 \times 10^{-7}$).
  - Difference: **$+20.67\text{ percentage points}$**, declared `ADEQUATELY_POWERED` ($\ge 10\text{pp}$).
- **The Economic Inversion**: R4 cost **$18.3\times$ more per grounded answer** than R2 ($\$0.26825$ vs $\$0.01468$), while achieving less than one-fourth the single-turn accuracy and less than one-tenth the joint 3-trial reliability.

### Why did this happen?
`gpt-5.6-luna` fell into reasoning traps. When BM25 keyword search queries returned zero results, it attempted to "reason" by adding boolean quotes, synonyms, and multi-word filter syntax that BM25 rejected. This produced self-induced search loops that exhausted the 24-step budget in 28.0% of its runs. 

In contrast, `glm-5.3-flash` exhibited strict tool discipline: it issued simple single-token keyword queries, followed graph pointers methodically, and completed the 5-hop traversal in a median of 15 steps (hitting the step cap in only 4.0% of runs).

---

## 2. The Truth About Failure Concentration: Why 6.06× Was Misleading

An earlier draft circulated with the headline: *"6.06x Failure Concentration Ratio Confirmed!"* That framing was an artifact of selective emphasis.

Here is what actually happened:
- For **R4 (`gpt-5.6-luna`)**, single-turn accuracy was so low ($14.89\%$) that naive stochastic compounding predicted almost zero multi-trial passes: $(0.1489)^3 = \mathbf{0.33\%}$. Because 3 scenarios managed to pass all 3 trials ($2.00\%$, Wilson CI $[0.68\%, 5.71\%]$), the ratio was $2.00\% / 0.33\% = \mathbf{6.06\times}$. But that entire "concentration" finding rested on exactly **3 scenarios out of 150**.
- For **R2 (`glm-5.3-flash`)**, which had real statistical mass ($n=34$ scenarios passing all 3 trials), naive compounding predicted $25.14\%$, and the model achieved **$22.67\%$**. The concentration ratio was **$0.902\times$**—below naive independence.

Across the benchmark, concentration was observed on only **1 of 3 evaluated rungs**. The hypothesis that failures systematically concentrate was falsified. When an agent is genuinely competent at tool use, errors behave much closer to independent stochastic trials than the field assumes.

---

## 3. The 12-Step Trap: How Pre-Registration Saved the Benchmark

Our initial execution of Project P6 produced a shocking result: **0.00% pass rate across 1,350 runs**, with $\$0.59$ spent, 662 step-cap terminations, and 646 model failures.

In ad-hoc benchmarking, this is the moment where teams quietly tweak prompts, adjust parameters after the fact, or hide the initial run.

Because our methodology was governed by **Minimum Evaluation Contract (MEC)**, we had pre-registered an explicit trigger in **Amendment A-002**:
> *If $>10\%$ of Tier 3 runs terminate on the step cap, the step cap must be formally amended and the evaluation re-run.*

In Project P03, we had measured 44.4% step-cap saturation. A 5-hop knowledge graph traversal requires 9 document lookups and 1 answer step = 10 steps minimum. A cap of 12 steps gave the agent a margin of only 2 steps for search branching. Any backtracking hit the wall.

Under **Amendment A-003**, we transparently updated $T_{\max}$ from 12 to 24 steps (MEC v1.3), verified the fix with a single-scenario probe, and re-ran the full 1,350-run sweep. 

Without pre-registered protocol hygiene, a harness defect would have been published as a false model capability ceiling.

---

## 4. LLM Judges Are Fragile: $\kappa = -0.0321$ on Agent Loops

In Project P5, we evaluated automated LLM judges (`glm-5.3`) against 200 human-annotated failure traces:
- For deterministic, syntactic failure modes (HTTP 429 rate limits, step caps, JSON parse errors), code assertions achieved perfect agreement (**$\kappa = 1.0000$**).
- When an LLM judge was asked to detect subtle multi-turn search pathologies (`OVERCONSTRAINED_SEARCH_LOOP`), it achieved Cohen's **$\kappa = -0.0321$**—worse than random guessing.
- On test splits where an error class was absent ($TP=0, FP=0, FN=0, TN=60$), standard Cohen's kappa returned a deceptive **$\kappa = 1.0000$** (observed across 3 of 5 error classes).

**Takeaway:** Never deploy an uncalibrated LLM judge. Deterministic code assertions must run first, and any automated evaluator must be corrected using Rogan-Gladen prevalence estimation.

---

## Reproduce the Full Evaluation

All 1,350 raw execution traces, SQLite telemetry spans, spend ledgers, and 86 passing Phase 2 tests are fully open source:

```bash
# 1. Clone repository
git clone https://github.com/samirsawarkar/faultline-ai-reliability.git
cd faultline-ai-reliability
python -m venv .venv && source .venv/bin/activate
pip install -e .

# 2. Run the verified Phase 2 test suite (86 passing tests)
.venv/bin/pytest tests/phase2 -q

# 3. Verify sweep metrics and audit ledger ($23.73 total spend)
.venv/bin/python projects/p06_passk/run.py --verify-manifest
```

---

## Acknowledgements

The evaluation harness, synthetic graph generation, and statistical analysis pipelines were implemented with the assistance of an AI coding agent operating under the author's direction. All experimental designs, pre-registrations, hypotheses, manual trace taxonomy codings, and editorial interpretations are the author's sole responsibility.

---

### Social Share Snippet (LinkedIn / X)

> **Our pre-registered agent reliability hypothesis just failed in public.**
> 
> Across 1,350 audited multi-hop agent runs ($n=150$ hard tasks $\times$ $k=3$ trials, 25,477 logged spans, $23.73 spent), here is what the data showed:
> 
> 1. **Hypothesis H4 was FALSIFIED**: Agent failures did not concentrate into an easy task core. On our primary workhorse model (`glm-5.3-flash`, 34 passes), joint 3-trial reliability was 22.67% vs 25.14% naive compounding (0.902x ratio). The widely cited 6.06x concentration ratio on `gpt-5.6-luna` rested on exactly 3 scenarios out of 150.
> 2. **A 48-Point Cost Upset**: Budget model `glm-5.3-flash` beat `gpt-5.6-luna` by a descriptive 48.22 pp on single-turn pass rate (63.11% vs 14.89%, disjoint Wilson CIs). On joint 3-trial reliability, a paired McNemar test on the exact same 150 scenarios confirmed a +20.67 pp advantage ($p = 8.14 \times 10^{-7}$) at 18.3x lower cost per grounded answer ($0.0147 vs $0.2683).
> 3. **The 12-Step Trap**: An initial sweep collapsed to 0.00% across 1,350 runs. Pre-registered trigger Amendment A-002 caught the 12-step cap harness defect and raised it to 24, preventing a test-harness bug from being published as a model failure.
> 4. **LLM Judge Fragility**: Automated LLM judges scored Cohen's $\kappa = -0.0321$ on multi-hop search loops.
> 
> Full paper, raw SQLite traces, and 86 passing tests: https://github.com/samirsawarkar/faultline-ai-reliability
