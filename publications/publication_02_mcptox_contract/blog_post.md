# Runtime Provenance Contracts for Mitigating Tool Poisoning in MCP Agents
*A Paired Evaluation on MCPTox Across Six Models*

Language model agents increasingly rely on dynamic tool protocols to discover and call external APIs. Under the Model Context Protocol (MCP), agents discover server tools dynamically, ingesting tool definitions and parameter schemas directly into their system context. However, this architectural coupling introduces a critical attack vector: tool poisoning. Unlike prompt injection embedded in user queries or retrieved text, tool poisoning places adversarial payloads inside tool schemas. When the agent inspects available tools, poisoned metadata enters its privileged context, turning instruction-following fidelity into an exploit mechanism.

Prior defenses—such as capability tokens, input spotlighting, and graph-based authorization monitors—focused primarily on data-payload prompt injection benchmarks like AgentDojo and PinchBench. Until now, no independent defensive architecture had been evaluated on the authentic multi-server MCPTox benchmark.

In this study, we implemented and evaluated FAULTLINE Arm B: a client-side runtime provenance contract intercepting tool calls before dispatch, paired with a call-only retry gating policy. We tested 1,800 paired evaluations across six model rungs on 300 stratified MCPTox instances under strict stimulus and judge parity.

## The Provenance Contract Architecture

Between the model generation and tool execution, FAULTLINE interposes a deterministic five-stage policy engine:
1. `multi_call`: Requires exactly one tool call per turn.
2. `envelope`: Enforces a valid dictionary structure containing only `'tool'` and `'arguments'`.
3. `unknown_tool`: Verifies that the requested tool exists on the active server.
4. `extra_argument`: Forbids undeclared schema parameters (`extra=forbid`).
5. `provenance`: Requires that every leaf string argument matches a normalized substring of the user's prompt (exempting primitives and short tokens $\le 3$ characters).

If Step 1 generates a tool call that violates any rule, the call is blocked, and the agent injects a standardized rejection message granting a single retry (Step 2). Crucially, retries are gated strictly on contract-rejected tool calls (`--retry-mode call-only`). If the model outputs natural language prose, a refusal, or an empty response on Step 1, no retry prompt is injected; the response proceeds directly to the judge.

## Key Empirical Findings

On 300 MCPTox instances, six models via one gateway, one LLM judge, and one day, the provenance contract achieved a statistically significant paired mean score reduction of $\text{Mean } \Delta = -0.2194$ (95% CI $[-0.2400, -0.1983]$, sign-flip permutation $p < 0.0001$, Cohen's $d_z = -0.49$).

Pooled across all six model rungs, the defense cut overall Attack Success Rate (ASR) from 28.83% to 6.89% (and valid ASR from 30.32% to 7.41%), removing 421 attacks while inducing only 26 (McNemar exact $p = 5.61 \times 10^{-93}$).

Frontier models demonstrated substantial vulnerability reductions on static MCPTox instances:
- GPT 5.6 Luna (R4): Valid ASR fell from 40.81% (Arm A) to 5.26% (Arm B), a 35.55 percentage point reduction ($p = 2.45 \times 10^{-24}$).
- Qwen 3.8 Flash (R3): Valid ASR dropped from 41.84% to 9.76%, a 32.08 percentage point reduction ($p = 7.76 \times 10^{-21}$).
- DeepSeek v4 Pro (R6): Valid ASR dropped from 47.64% to 15.46% ($p = 8.16 \times 10^{-19}$).

## The R5 Exception: Baseline Autonomous Resistance

The contract did not achieve significant gains on all models. On Gemini 3.7 Flash (R5), the baseline ASR was already near zero: 3.01% in Arm A (9 successes out of 299 valid instances) and 1.68% in Arm B (5 successes out of 298 valid instances). The paired reduction was statistically non-significant ($b=5, c=1$, exact binomial $p = 0.2188$). 

Gemini 3.7 Flash autonomously resisted tool poisoning in 263 of 299 instances without defensive mediation. On models with near-zero baseline susceptibility, runtime contract verification adds operational overhead without statistically meaningful security gain.

## Mechanics: The Importance of Call-Only Retry Gating

In pilot evaluations, injecting contract rejection prompts after any non-success output—including natural language refusals—backfired severely. When models appropriately refused malicious requests in prose on Step 1, receiving a prompt stating "Your tool call was rejected... Please revise" misled models into believing their refusal was an error, prompting them to generate unintended tool calls on Step 2. On GPT 5.6 Luna, unconstrained retries induced 27 additional direct execution failures and 7 successful exploits.

Standardizing on call-only retry gating (`--retry-mode call-only`) preserved 230 safe natural language refusals while permitting 479 legitimate corrections.

## Operational Costs and the World-Knowledge Penalty

Runtime contracts introduce real costs:
1. Rejection Feedback Shifts Error Distributions: Across all rungs, `Failure-Direct-Execution` rose 41.4% pooled from 145 instances in Arm A to 205 in Arm B. Smaller models collapsed into empty text under rejection: 65 empty completions on R1 accounted for 92.9% of its 70 invalid instances (21.7% of all 300 R1 instances).
2. The World-Knowledge False-Block Penalty: Through offline trace replay across 10,227 author traces, the contract blocked 86.99% of author-labelled attack successes (1,438/1,653). However, it also false-blocked 24.50% of author-labelled benign tasks (1,271/5,188 `Failure-Ignored` instances). Literal substring matching cannot distinguish malicious parameter tampering from legitimate entity resolution (such as converting a company name into a stock ticker).

## Limitations and Non-Adaptive Scope

Our evaluation tested static benchmark instances where adversaries had no knowledge of defense rules. Plausible contract-aware evasions—such as short exempt primitives ($\le 3$ characters), user-turn token reflection, and Template-2 function hijacking (which retained 10.93% residual ASR even non-adaptively)—remain untested. Future work must evaluate adaptive adversaries with full contract knowledge.
