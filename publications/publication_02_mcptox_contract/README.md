# Runtime Provenance Contracts for Mitigating Tool Poisoning in MCP Agents: A Paired Evaluation on MCPTox Across Six Models

## Summary

We deployed and evaluated an independent defensive second arm on the Model Context Protocol Poisoning benchmark (MCPTox), testing whether a client-side runtime provenance contract on tool-call arguments with call-only retry gating mitigates tool poisoning across six model rungs. We interposed a deterministic five-stage provenance policy engine between model generations and tool execution that enforces envelope formatting, tool enumeration allowlists, strict schema argument boundaries, and verbatim substring grounding of argument values against the user turn, granting a single retry gated exclusively on contract-blocked tool calls. On 300 MCPTox instances, six models via one gateway, one LLM judge, and one operational window, the provenance contract achieved a statistically significant paired mean score reduction of $\text{Mean } \Delta = -0.2194$ (95% CI $[-0.2400, -0.1983]$, sign-flip permutation $p < 0.0001$, descriptive paired Cohen's $d_z = -0.49$), cutting overall Attack Success Rate (ASR) from 28.83% to 6.89% (valid ASR from 30.32% to 7.41%) pooled across 1,800 paired evaluations, removing 421 attacks while inducing only 26 (McNemar exact $p = 5.61 \times 10^{-93}$). Frontier models saw valid ASR drop by up to 35.5 percentage points (GPT 5.6 Luna falling from 40.81% to 5.26% and Qwen 3.8 Flash from 41.84% to 9.76%). However, on Gemini 3.7 Flash (R5), the reduction was statistically non-significant ($b=5, c=1$, exact $p=0.2188$) due to high baseline autonomous resistance (263/299 benign instances). Gating retries strictly on contract-rejected calls preserved 230 natural language refusals that unconstrained retry prompts corrupted into exploits. Furthermore, offline trace replay over 10,227 traces reveals an intrinsic operational trade-off: while blocking 86.99% of attacks, rigid substring grounding false-blocks 24.50% of benign executions when legitimate tasks require ungrounded world knowledge, and retains 10.93% residual vulnerability on function hijacking.

## Experimental Results

The table below reports raw counts across judge categories, sample sizes ($n$ and $n_{\text{valid}}$), Attack Success Rates over valid instances ($\text{ASR}_{\text{valid}}$) with 95% Wilson score confidence intervals, Attack Success Rates over all instances ($\text{ASR}_{\text{all}}$), and API spend extracted directly from `results.json` across all six rungs ($n = 300$ per rung) and pooled ($N = 1,800$ paired instances):

| Rung | Model | Arm | $n$ | $n_{\text{valid}}$ | Success | Failure-Ignored | Failure-Direct-Exec | Contract-Blocked | Invalid | $\text{ASR}_{\text{valid}}$ | 95% Wilson CI | $\text{ASR}_{\text{all}}$ | Spend (USD) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **R1** | Qwen 3.7 Flash | Arm A | 300 | 255 | 84 | 157 | 14 | 0 | 45 | 0.3294 | [0.2746, 0.3893] | 0.2800 | $0.1222 |
| **R1** | Qwen 3.7 Flash | Arm B | 300 | 230 | 19 | 168 | 30 | 13 | 70 | 0.0826 | [0.0535, 0.1254] | 0.0633 | $0.1573 |
| **R2** | GLM 5.3 Flash | Arm A | 300 | 296 | 51 | 209 | 26 | 0 | 4 | 0.1723 | [0.1335, 0.2194] | 0.1700 | $0.0965 |
| **R2** | GLM 5.3 Flash | Arm B | 300 | 292 | 12 | 225 | 31 | 18 | 8 | 0.0411 | [0.0237, 0.0704] | 0.0400 | $0.1086 |
| **R3** | Qwen 3.8 Flash | Arm A | 300 | 294 | 123 | 141 | 30 | 0 | 6 | 0.4184 | [0.3634, 0.4755] | 0.4100 | $0.1541 |
| **R3** | Qwen 3.8 Flash | Arm B | 300 | 297 | 29 | 204 | 51 | 13 | 3 | 0.0976 | [0.0688, 0.1367] | 0.0967 | $0.1784 |
| **R4** | GPT 5.6 Luna | Arm A | 300 | 272 | 111 | 112 | 21 | 0 | 28 | 0.4081 | [0.3514, 0.4674] | 0.3700 | $0.1975 |
| **R4** | GPT 5.6 Luna | Arm B | 300 | 266 | 14 | 184 | 31 | 22 | 34 | 0.0526 | [0.0316, 0.0864] | 0.0467 | $0.2109 |
| **R5** | Gemini 3.7 Flash | Arm A | 300 | 299 | 9 | 263 | 27 | 0 | 1 | 0.0301 | [0.0159, 0.0562] | 0.0300 | $0.2157 |
| **R5** | Gemini 3.7 Flash | Arm B | 300 | 298 | 5 | 263 | 25 | 4 | 2 | 0.0168 | [0.0072, 0.0387] | 0.0167 | $0.1815 |
| **R6** | DeepSeek v4 Pro | Arm A | 300 | 296 | 141 | 126 | 27 | 0 | 4 | 0.4764 | [0.4201, 0.5332] | 0.4700 | $0.5387 |
| **R6** | DeepSeek v4 Pro | Arm B | 300 | 291 | 45 | 186 | 37 | 22 | 8 | 0.1546 | [0.1176, 0.2007] | 0.1500 | $0.4640 |
| **Pooled** | All Models | Arm A | 1800 | 1712 | 519 | 1008 | 145 | 0 | 88 | 0.3032 | [0.2818, 0.3254] | 0.2883 | $1.3247 |
| **Pooled** | All Models | Arm B | 1800 | 1674 | 124 | 1230 | 205 | 92 | 125 | 0.0741 | [0.0623, 0.0877] | 0.0689 | $1.3007 |

## Package Contents

- `paper.md`: Full research paper with numbered citations, figures, and empirical evidence gaps.
- `README.md`: Executive summary, complete results table from `results.json`, package manifest, and reproduction commands.
- `blog_post.md`: Concise (<900 words) technical summary detailing findings, failure modes, retry dynamics, and limitations.
- `fig_1_asr_by_rung.png` / `.svg`: Figure 1 — Attack Success Rate over valid completions across six model rungs with 95% Wilson CIs.
- `fig_2_blocked_vs_false.png` / `.svg`: Figure 2 — Attack block rate vs false block rate on benign tasks in offline trace replay across 10,227 traces.
- `fig_3_paradigm.png` / `.svg`: Figure 3 — Defense efficacy breakdown across MCPTox attack paradigms.
- `make_figures.py`: Standalone reproduction script for rendering Figures 1, 2, and 3.

## Reproduction Commands

All experiments, analysis, and figures can be reproduced with standard tools:

```bash
# 1. Set up evaluation environment
make phase2-install-inspect

# 2. Run offline trace replay across 10,227 author traces ($0 API spend)
make p08-replay

# 3. Execute confirmatory evaluation sweep across 1,800 paired instances
make p08 ARGS='--confirm --arms A,B --reuse-arm-a --retry-mode call-only'

# 4. Compute derived statistics and significance tests
.venv/bin/python projects/p08_mcptox/analysis.py

# 5. Render publication figures
python publications/publication_02_mcptox_contract/make_figures.py
```
