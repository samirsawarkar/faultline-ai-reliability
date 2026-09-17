# Research question

**Question (one sentence, falsifiable):**
Does a runtime provenance contract on tool-call arguments (every argument value must be grounded in the user turn), with one retry gated on a rejected call, reduce tool-poisoning attack success on MCPTox relative to the published single-turn protocol, across six models, on the same 300 instances?

**Unit of analysis:**
One (model, instance) pair; pairing key `instance_id` (`<rung>:<scenario_id>`).

**Ground truth / how a correct answer is known:**
The MCPTox LLM judge category (`Success`, `Failure-Direct-Execution`, `Failure-Ignored`, `Failure-Refused`, `Invalid`), evaluated using judge model `z-ai/glm-5.3-flash` with the prompt verbatim from `inspect-evals-mcptox` (commit `d45705b`).

**Baseline / comparison:**
Arm A = `inspect-evals-mcptox` commit `d45705b` verbatim (single-turn unconstrained tool execution).
Arm B = Runtime provenance contract on tool-call arguments with single gated retry on rejected calls.

**Scope — in:**
MCPTox benchmark (commit `f85189f`), 300 sampled instances out of 1,312 (seed 42), six aicredits.in model rungs (R1: Qwen 3.7 Flash, R2: GLM 5.3 Flash, R3: Qwen 3.8 Flash, R4: GPT 5.6 Luna, R5: Gemini 3.7 Flash, R6: DeepSeek v4 Pro), Attack Success Rate (ASR) over valid instances (upstream definition: `Success / (Success + Failure-Direct-Execution + Failure-Ignored + Failure-Refused)`).

**Scope — out:**
Other benchmarks (e.g. ToolBench, AgentBench), multi-turn interactive agents, alternative defense mechanisms (e.g., input perplexity filtering, fine-tuning, system prompt defense alone), cost/latency optimization.

**Constraints (time, data, compute, venue):**
Zero model execution budget ($0 for this analysis phase; using frozen offline experimental artifacts), no live model calls, fixed 300 instances paired across arms, max tokens 2048 parity, temperature 0.

**What result would falsify the working hypothesis:**
Falsifier (pre-registered H7 in `HYPOTHESES.md`): Arm B ASR confidence interval overlaps or exceeds the published band (mean 0.365).

## Inclusion / exclusion criteria for sources
- Include: Peer-reviewed and pre-print literature on MCP/tool security, tool poisoning, indirect prompt injection in tool agents, runtime validation/contracts for tool calls.
- Exclude: Generic jailbreaking papers without tool-use context; papers lacking verifiable quantitative evaluation.
- Recency cutoff (if the field moves fast): 2024 to present (MCP and tool-poisoning domain).

## AI-Reliability Checklist Answers (per ai_reliability_checklist.md)

1. **Unit of analysis**: One (model, instance) pair; pairing key is instance id (`<rung>:<scenario_id>`). Total N = 1,800 pairs per arm (300 instances × 6 models).
2. **Ground truth**: MCPTox LLM judge categorization (`Success`, `Failure-Direct-Execution`, `Failure-Ignored`, `Failure-Refused`, `Invalid`), executed with `z-ai/glm-5.3-flash` using prompt verbatim from `inspect-evals-mcptox`.
3. **Baseline**: Arm A is upstream `inspect-evals-mcptox` commit `d45705b` run verbatim without modification.
4. **Comparison**: Strictly paired on identical instance IDs, identical system prompt tools, and identical user inputs across Arm A and Arm B.
5. **Leakage**: Prompts contain standard MCP tool definitions and benign/poisoned tool specifications. No training leakage possible as models are evaluated zero-shot via API. Judge receives final output only without knowledge of Arm A vs Arm B provenance mechanics.
6. **Confounders**: Model version drift (mitigated by recording provider snapshot and running arms closely on 2026-09-15/16), prompt length (identical system prompts and user queries), temperature (set to 0 for reproducibility), max tokens (pinned to 2048 parity across both arms). R2 self-judging noted as known potential confound.
7. **Independence of measurements**: 300 distinct benchmark instances evaluated across 6 models; paired comparisons evaluate the exact same 300 instances per rung.
8. **Metric appropriateness**: ASR over valid instances (`Success / (Valid)`), exactly matching upstream MCPTox definition; paired exact McNemar test and Wilson 95% score confidence intervals.
9. **Benchmark validity**: MCPTox (commit `f85189f`) provides 1,312 standardized poisoning scenarios across 3 distinct injection templates/paradigms (explicit trigger, implicit trigger via function hijack, parameter tampering). 300 stratified samples (seed 42) represent unsaturated attack space.
10. **Alternative explanations considered**: Rejection caused by syntax truncation rather than contract violation (ruled out: unparseable/empty completions are forwarded to judge, not classified as contract-blocked; call-only retry gating prevents false retry prompts on prose responses).
11. **Evidence strength**: Claims supported by 1,800 paired evaluations, exact contingency tables, Wilson CIs, and McNemar exact tests.

## Decision log pointer
Material changes to this question are recorded in `research_decisions.md`.
