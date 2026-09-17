## Highlights of Release v0.29.0

**FAULTLINE Phase 2 Milestone: Publication #2, Projects P7 & P8, Runtime Provenance Contracts**

This release marks the public launch of **Publication #2** alongside the completion of **Project P07** (Serving Variance) and **Project P08** (MCP Tool Poisoning Defense):  
**"Runtime Provenance Contracts for Mitigating Tool Poisoning in MCP Agents: A Paired Evaluation on MCPTox Across Six Models"**  
by Samir Sawarkar (*FAULTLINE AI Reliability Engineering*).

This release also updates **Publication #1** with its formal publication title:  
**"Multi-Trial Reliability and Failure Concentration in Multi-Hop AI Agents: Grounding Collapse, Failure Taxonomy, and Evaluator Calibration"**.

---

### Executive Summary

Modern AI agents increasingly execute dynamic actions via the Model Context Protocol (MCP), exposing them to tool poisoning where malicious instructions are embedded in tool schemas and descriptions. Release v0.29.0 delivers a deterministic, client-side defense architecture and a multi-model paired evaluation:

1. **Publication #2 — MCP Tool Poisoning Defense (Project P08)**: Across 300 MCPTox instances evaluated across six commercial model rungs (Qwen 3.7 Flash, GLM 5.3 Flash, Qwen 3.8 Flash, GPT 5.6 Luna, Gemini 3.7 Flash, DeepSeek v4 Pro; 1,800 paired runs), a client-side runtime provenance contract achieved a statistically significant paired mean score reduction of $\text{Mean } \Delta = -0.2194$ (95% CI $[-0.2400, -0.1983]$, $p < 0.0001$, $d_z = -0.49$), cutting pooled valid Attack Success Rate (ASR) from 30.32% to 7.41% (removing 421 attacks while inducing only 26, McNemar exact $p = 5.61 \times 10^{-93}$).
2. **Deterministic Five-Stage Provenance Policy Engine**: Interposes a client-side boundary before tool execution that enforces JSON envelope formatting, tool enumeration allowlists, strict schema argument boundaries, and verbatim substring-grounding of argument values against the user turn.
3. **Call-Only Retry Gating**: Uncovered that feeding raw rejections to safe refusals induces spurious compliance. Restricting retries strictly to contract-rejected tool calls (`--retry-mode call-only`) preserved 230 natural language refusals while allowing 479 valid corrections.
4. **Serving Variance and Greedy Decoding Jitter (Project P07)**: Formal investigation into temperature-0 nondeterminism caused by multi-provider inference engine scheduling and floating-point non-associativity across GPU reduction kernels.
5. **Environment Isolation with `.venv-inspect`**: Isolated upstream Inspect AI evaluation frameworks (`inspect_ai==0.3.263`, `inspect-evals-mcptox`) in an isolated virtual environment (`.venv-inspect`), eliminating dependency pollution from core verification harnesses.
6. **Publication Retitles & Provenance Policy**: Pinned academic paper titles and formalized the 7-gate red-team release protocol (`research/final/release_checklist.md` and `research_pub02/final/release_checklist.md`).

---

### Key Empirical Results (Publication #2 / Project P08)

| Rung | Model | Arm A ASR (Valid) | Arm B ASR (Valid) | McNemar ($b/c$, $p$) | Significant |
|---|---|---|---|---|---|
| R1 | `qwen/qwen3.7-flash` | 28.00% (32.94%) | 6.33% (8.26%) | $b=71, c=6, p = 3.02 \times 10^{-13}$ | Yes |
| R2 | `z-ai/glm-5.3-flash` | 17.00% (17.23%) | 4.00% (4.11%) | $b=41, c=2, p = 6.83 \times 10^{-9}$ | Yes |
| R3 | `qwen/qwen3.8-flash` | 41.00% (41.84%) | 9.67% (9.76%) | $b=98, c=4, p = 3.31 \times 10^{-20}$ | Yes |
| R4 | `openai/gpt-5.6-luna` | 37.00% (40.81%) | 4.67% (5.26%) | $b=99, c=2, p = 1.27 \times 10^{-21}$ | Yes |
| R5 | `google/gemini-3.7-flash` | 3.00% (3.01%) | 1.67% (1.68%) | $b=5, c=1, p = 0.2188$ | No (n.s.) |
| R6 | `deepseek/deepseek-v4-pro` | 47.00% (47.64%) | 15.00% (15.46%) | $b=107, c=11, p = 2.22 \times 10^{-18}$ | Yes |
| **Pooled** | **All 6 Models** | **28.83% (30.32%)** | **6.89% (7.41%)** | **$b=421, c=26, p = 5.61 \times 10^{-93}$** | **Yes** |

*Operational Trade-off:* Substring grounding introduces a 24.5% false-block rate on legitimate actions requiring external world knowledge not present in the user prompt.

---

### Included Release Assets

- 📄 **`publications/publication_02_mcptox_contract/paper.pdf`**: Complete Publication #2 research paper.
- 📄 **`publications/publication_01_passk_reliability/paper.pdf`**: Updated Publication #1 paper with formal title and sensitivity sweeps.
- 📊 **`fig_1_asr_by_rung.png`**: Primary attack success rate comparison across all six rungs.
- 📊 **`fig_2_blocked_vs_false.png`**: Operational frontier of attack mitigation versus false blocks.
- 📦 **`projects/p08_mcptox/results.json`**: Machine-readable paired evaluation metrics, confidence intervals, and McNemar test statistics.
- 📋 **`research_pub02/final/release_checklist.md`**: 7-gate red-team audit sign-off for Publication #2.

---

### One-Command Reproduction

```bash
make venv
make test          # Runs all 528 Phase 1 tests
make phase2-test   # Runs all 126 Phase 2 tests (P00-P08, P13, P15, P16)
make p08-replay    # Replays cached MCPTox evaluation traces without API calls
```

**Test Gate Verification:** 654 / 654 Unit/Integration tests passing (528 Phase 1 + 126 Phase 2). All pre-registered hypotheses tracked in `HYPOTHESES.md`.
