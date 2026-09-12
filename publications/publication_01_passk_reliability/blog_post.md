# Retry Doesn’t Help The Way You Think: We Ran 1,350 Multi-Hop Agent Trials with Real Money. Here’s What Broke.

**By Samir Sawarkar**  
*FAULTLINE AI Reliability Engineering · Antigravity Research*  
*Full Paper:* [`paper.md`](./paper.md) · *Code & Data:* [`github.com/samirsawarkar/faultline-ai-reliability`](https://github.com/samirsawarkar/faultline-ai-reliability)

---

![Overview of the Experiment](./figure_overview.jpg)

In production AI engineering, everyone repeats the same intuition:

> *"If an agent fails, just retry it 3 times ($k=3$). By basic probability, pass rate compounds as $	ext{pass}^k = 1 - (1 - p)^k$."*

We decided to test this assumption with real money, pre-registered hypotheses, and cryptographically sealed evaluation contracts. 

We ran **1,350 multi-turn agent runs** across **150 hard 5-hop knowledge graph scenarios** over 3 foundation model rungs:
- **R2:** `z-ai/glm-5.3-flash` (Cheap Workhorse)
- **R4:** `openai/gpt-5.6-luna` (OpenAI Frontier)
- **R6:** `deepseek/deepseek-v4-pro` (Frontier Anchor)

Every run was executed with real tool calls (BM25 search + document lookup), logged into SQLite traces (25,477 spans), and audited down to the cent in an append-only ledger ($23.73 total spend).

Here are the 3 counter-intuitive findings that surprised us.

---

## 1. The Cheap Workhorse Destroyed the Frontier Model (At 1/18th the Cost)

The common wisdom is that frontier reasoning models are required for complex multi-hop tool use. The data showed the exact opposite:

| Model | Role | Pass@1 (Single Try) | Pass³ (3/3 Consecutive Passes) | Cost per Grounded Answer |
|---|---|:---:|:---:|:---:|
| **`glm-5.3-flash`** (R2) | Cheap Workhorse | **63.11%** | **22.67%** | **$0.0147** (~₹1.30) |
| **`gpt-5.6-luna`** (R4) | Frontier OpenAI | **14.89%** | **2.00%** | **$0.2680** (~₹23.60) |
| **`deepseek-v4-pro`** (R6) | Frontier Anchor | 0.00% | 0.00% | N/A *(Provider Timeout)* |

- **Statistical Significance:** In a paired McNemar test on identical scenarios, `glm-5.3-flash` outperformed `gpt-5.6-luna` by **+20.67 percentage points** ($p = 8.14 	imes 10^{-7}$), formally declared `ADEQUATELY_POWERED` ($\ge 10	ext{pp}$).
- **Why did this happen?**  
  `gpt-5.6-luna` over-reasoned. When search queries returned 0 results, it added boolean quotes and complex multi-word filters, creating self-induced search loops that exhausted the 24-step budget (28% capped runs). In contrast, `glm-5.3-flash` adhered strictly to simple keyword queries, moving rapidly through the 5-hop chain in a median of 15 steps (only 4% capped runs).

---

## 2. Failure Concentration: The Retry Trap ($6.06	imes$)

Does retrying an agent 3 times actually improve reliability? **It depends entirely on model accuracy.**

- **For the High-Accuracy Model (`glm-5.3-flash` @ 63%):**  
  Errors behaved roughly like independent coin flips. Naive compounding predicted $0.6311^3 = 25.1\%$, and the model achieved **$22.7\%$**.
- **For the Weaker Model (`gpt-5.6-luna` @ 15%):**  
  Naive compounding predicted that passing 3 times in a row should be almost impossible: $0.1489^3 = \mathbf{0.33\%}$.  
  Yet in reality, the model achieved **$2.00\%$**—a **$6.06	imes$ concentration ratio**!

### What does this mean?
Weak agents do not make random errors. They make **correlated, systematic errors**.  
They succeed reliably on a narrow, "tractable" subset of tasks (passing all 3 trials easily), but fail catastrophically on the rest. **Retrying a struggling agent on hard tasks is pure waste—it hits the same wall in trial 2 and trial 3.**

---

## 3. The 12-Step Trap & Scientific Pre-Registration

Our initial run of this experiment produced an eerie result: **0.00% pass rate across all models**.

Rather than panicking or tweaking prompts in secret, our pre-registered contract (`MEC.md`) caught the problem. We had frozen a step cap of 12 steps. But solving a 5-hop graph requires 9 document lookups and 1 answer step = 10 steps minimum. A cap of 12 left only a 2-step margin for search branching, causing 49% of all runs to choke at step 12.

Under **Amendment A-003**, we transparently raised the cap to 24 steps, ran a $0.20 single-rung probe, and then executed the full 1,350-run sweep. 

**Lesson:** If your benchmark doesn't pre-register harness parameters, you are probably measuring harness artefacts instead of model intelligence.

---

## 4. LLM Judges Are Deceptive Without Code Assertions

In Project P5, before running the sweep, we calibrated automated LLM judges (`glm-5.3`) against 200 human-annotated failure traces.
- Where error signals were clear (HTTP 429 rate limits, step caps, JSON syntax errors), **deterministic Python code assertions achieved perfect agreement ($\kappa = 1.00$)**.
- When an LLM judge was asked to detect subtle agent looping behavior without code checks, it scored **$\kappa = -0.04$ (worse than random guessing)**.
- Furthermore, on test splits where an error class was absent ($0$ true positives), standard Cohen's kappa falsely reported $\kappa = 1.00$.

**Takeaway:** Never trust an uncalibrated LLM judge. Use deterministic assertions first, and apply Rogan-Gladen prevalence corrections to any LLM rater.

---

## Reproduce It in One Command

All 1,350 traces, SQLite telemetry, spend logs, and verification tests are completely open source:

```bash
git clone https://github.com/samirsawarkar/faultline-ai-reliability.git
cd faultline-ai-reliability
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Run the test suite (86/86 Phase 2 tests)
make phase2-test

# Verify manifest and reproduce sweep metrics
python projects/p06_passk/run.py --verify-manifest
```

---

### Social Share Snippet (LinkedIn / X)

> **We ran 1,350 multi-hop agent trials across 150 hard tasks with real money.**
> 
> Three counter-intuitive findings from our pre-registered study:
> 1. A cheap model (`glm-5.3-flash`) beat `gpt-5.6-luna` by +20.67 pp on 5-hop tool use at 1/18th the cost ($0.014 vs $0.268 per answer).
> 2. Failure concentration is real ($6.06x): retrying weaker agents on hard tasks is pure waste—they repeat the exact same search loop in all 3 trials.
> 3. LLM judges score worse than chance ($\kappa = -0.04$) on agent loops without code assertions.
> 
> Read the full open-source paper and reproducible traces: [github.com/samirsawarkar/faultline-ai-reliability](https://github.com/samirsawarkar/faultline-ai-reliability)
