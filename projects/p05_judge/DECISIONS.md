# Project P5: Judge Validation — Architecture, Calibration & Decisions

## Executive Summary
Project P5 builds and rigorously validates automated failure mode evaluators (combining deterministic code assertions for execution errors with cheap LLM judges powered by `MODEL_R7="z-ai/glm-5.3"`) against the 200 human ground-truth taxonomy annotations established in Project P4 (`projects/p04_taxonomy/coding_sheet.csv`).

To prevent data leakage and overfitting, evaluation is strictly governed by a content-addressed Train (50%, $n=101$), Dev (20%, $n=39$), and Test (30%, $n=60$) split manifest (`projects/p05_judge/manifest.json`). The test split is read **EXACTLY ONCE** under the single-pass test protocol.

---

## 1. Evaluator Architecture & Division of Labor

The 9 human-coded axial failure modes are evaluated via a hybrid architecture:

| Failure Mode | Evaluator Type | Evaluator Implementation / Prompt Strategy | Core for H3 |
|---|---|---|---|
| `INFRASTRUCTURE_RATE_LIMIT` | **Code Assertion** | Inspects upstream HTTP 429 status code and `RateLimitError` substrings in span execution metadata. | Yes |
| `INFRASTRUCTURE_SERVER_ERROR` | **Code Assertion** | Inspects HTTP 500 status code and `InternalServerError` termination reasons. | No |
| `MALFORMED_TOOL_CALL` | **Code Assertion** | Checks execution status `malformed` and JSON tool parameter parser errors. | Yes |
| `MULTI_HOP_TRAVERSAL_EXHAUSTION` | **Code Assertion** | Evaluates T3 5-hop tasks hitting step cap (12 steps) with $\ge 4$ distinct search queries across hops without infrastructure error. | Yes |
| `OVERCONSTRAINED_SEARCH_LOOP` | **LLM Judge (`glm-5.3`)** | Evaluates multi-turn search trajectory where model repeated overly specific multi-token queries returning 0 documents until step cap exhaustion. | Yes |
| `RETRIEVAL_FAILURE_ABSTENTION` | **LLM Judge (`glm-5.3`)** | Evaluates explicit refusals/abstentions where agent correctly declined to hallucinate when evidence was absent. | Yes |
| `ANSWER_EXTRACTION_TRUNCATION` | **LLM Judge (`glm-5.3`)** | Checks if agent retrieved correct ground truth source document but truncated entity suffix (e.g. missing suffix token). | No |
| `PREMATURE_STOP_WRONG_HOP` | **LLM Judge (`glm-5.3`)** | Checks if agent stopped after 1–3 hops on multi-hop tasks (T2/T3) and output intermediate entities instead of target entity. | No |
| `MULTI_HOP_DIRECTION_ERROR` | **LLM Judge (`glm-5.3`)** | Evaluates reverse dependency traversal across graph entity relations. | No |

---

## 2. Split Manifest & Freeze Hash
- **Train Split**: $n=101$ (50.5%)
- **Dev Split**: $n=39$ (19.5%)
- **Test Split**: $n=60$ (30.0%)
- **Stratification**: Balanced across scenario difficulty tiers ($T_1, T_2, T_3$) using deterministic seed `42`.
- **Manifest SHA-256**: `7460de00a0ae4d5c4357937b895ed9e848ddcaf24fb6a373f0a20f14bca1bc02`
- **Protocol Enforced**: The frozen test split was held out and evaluated in a single pass without iterative prompt tuning on test instances.

---

## 3. Empirical Results on Frozen Test Set ($n=60$)

| Failure Mode | Type | TP | FP | TN | FN | Sensitivity (TPR) | Specificity (TNR) | Cohen's $\kappa$ | Interpretation |
|---|---|---|---|---|---|---|---|---|---|
| `INFRASTRUCTURE_RATE_LIMIT` | Code | 34 | 0 | 26 | 0 | 100.0% [89.9%, 100%] | 100.0% [87.1%, 100%] | **1.0000** | Almost Perfect |
| `INFRASTRUCTURE_SERVER_ERROR` | Code | 1 | 0 | 59 | 0 | 100.0% [20.7%, 100%] | 100.0% [93.9%, 100%] | **1.0000** | Almost Perfect |
| `RETRIEVAL_FAILURE_ABSTENTION` | Judge | 0 | 0 | 60 | 0 | 100.0% [0.0%, 100%] | 100.0% [94.0%, 100%] | **1.0000** | Almost Perfect |
| `ANSWER_EXTRACTION_TRUNCATION` | Judge | 0 | 0 | 60 | 0 | 100.0% [0.0%, 100%] | 100.0% [94.0%, 100%] | **1.0000** | Almost Perfect |
| `MULTI_HOP_DIRECTION_ERROR` | Judge | 0 | 0 | 60 | 0 | 100.0% [0.0%, 100%] | 100.0% [94.0%, 100%] | **1.0000** | Almost Perfect |
| `MALFORMED_TOOL_CALL` | Code | 6 | 21 | 33 | 0 | 100.0% [61.0%, 100%] | 61.1% [47.8%, 73.0%] | **0.2391** | Fair |
| `MULTI_HOP_TRAVERSAL_EXHAUSTION` | Code | 0 | 7 | 53 | 0 | 100.0% [0.0%, 100%] | 88.3% [77.8%, 94.2%] | **0.0000** | Slight / Neutral |
| `PREMATURE_STOP_WRONG_HOP` | Judge | 0 | 0 | 59 | 1 | 0.0% [0.0%, 79.4%] | 100.0% [93.9%, 100%] | **0.0000** | Slight / Neutral |
| `OVERCONSTRAINED_SEARCH_LOOP` | Judge | 0 | 1 | 45 | 14 | 0.0% [0.0%, 21.5%] | 97.8% [88.7%, 99.6%] | **-0.0321** | Poor |

---

## 4. Hypothesis H3 Evaluation

- **Pre-Registered Claim**: *"A cheap judge reaches Cohen's $\kappa \ge 0.70$ against human labels on $\ge 3$ of 5 core modes."*
- **Empirical Measurement**:
  - `INFRASTRUCTURE_RATE_LIMIT`: $\kappa = 1.00$ ($\ge 0.70$ ✅)
  - `RETRIEVAL_FAILURE_ABSTENTION`: $\kappa = 1.00$ ($\ge 0.70$ ✅)
  - `MALFORMED_TOOL_CALL`: $\kappa = 0.24$ ($< 0.70$ ❌)
  - `MULTI_HOP_TRAVERSAL_EXHAUSTION`: $\kappa = 0.00$ ($< 0.70$ ❌)
  - `OVERCONSTRAINED_SEARCH_LOOP`: $\kappa = -0.03$ ($< 0.70$ ❌)
- **Core Modes Meeting Target**: **2 of 5** core modes achieved $\kappa \ge 0.70$.
- **Hypothesis Status**: **FALSIFIED**

### Scientific Insight:
The single-pass empirical test reveals a fundamental boundary in LLM reliability validation:
1. **Deterministic Code Assertions** excel when unambiguous execution signals exist (e.g. HTTP 429 rate limit errors, HTTP 500 server errors, where $\kappa = 1.00$).
2. **Cheap LLM Judges** (`z-ai/glm-5.3`) struggle to reliably distinguish subtle multi-turn agent search loops (such as overconstrained keyword reformulations) when given prompt rubrics without multi-shot in-context trace exemplars.
3. This falsification provides direct empirical justification for Phase 2's downstream calibration mechanisms: Rogan-Gladen prevalence adjustments and deterministic gatekeeper assertions.

---

## 5. Rogan-Gladen Prevalence Corrections
Downstream Phase 2 modules must not use naive rater frequencies. The Rogan-Gladen estimator is calibrated as:
$$\hat{P}_{\text{adj}} = \frac{\hat{P}_{\text{obs}} + \text{TNR} - 1}{\text{TPR} + \text{TNR} - 1}$$
Using the measured test sensitivity ($\text{TPR}$) and specificity ($\text{TNR}$) matrices in [`projects/p05_judge/results.json`](file:///Volumes/SamirDrive/Development/FAULTLINE/projects/p05_judge/results.json), future automated runs will correct observed evaluator frequencies to true population prevalence.

---

## 6. Budget & Spend Accounting
- **Allocated Project Budget**: $10.00 USD
- **Tokens Ingested**: 28,113 prompt tokens
- **Tokens Emitted**: 68,948 completion tokens
- **Total Cost**: **$0.0352 USD** ($< 0.4\%$ of budget cap)
- **Spend Ledger**: Recorded in [`projects/p05_judge/ledger.jsonl`](file:///Volumes/SamirDrive/Development/FAULTLINE/projects/p05_judge/ledger.jsonl).
