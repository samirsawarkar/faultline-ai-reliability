# Literature map

Not a paper-by-paper summary. Organise by the research problem.

## Problem being studied

Vulnerability of tool-using large language model (LLM) agents to indirect prompt injection (IPI) and tool poisoning, specifically where untrusted external data or malicious Model Context Protocol (MCP) tool metadata diverts agent execution into unauthorized, harmful, or data-exfiltrating tool calls.

## Approaches (families, not papers)
| Approach | Key papers (bib keys) | Core assumption | Datasets | Metrics |
|---|---|---|---|---|
| Unconstrained tool agents (Baseline threat model) | wang2025mcptox, zhan2024injecagent, debenedetti2024agentdojo, greshake2023compromised, perez2022ignore | Models can autonomously distinguish system instructions from untrusted data/metadata without structural mediation. | MCPTox (45 servers, 353 tools), InjecAgent (17 user tools, 62 attacker tools), AgentDojo (97 tasks, 629 security test cases) | Attack Success Rate (ASR), Task Utility / Completion Rate, Refusal Rate |
| Control/Data flow isolation & capabilities | debenedetti2025defeating, an2025ipiguard | Untrusted inputs can be isolated from program control flow; security policies can enforce capability tokens before dispatch. | AgentDojo | Provable security task rate (%), Utility retention (%) |
| Input transformation & data spotlighting | hines2024spotlighting | Transforming or delimiting untrusted inputs provides continuous provenance signals recognizable by the LLM. | Synthetic NLP benchmarks, prompt injection suites | ASR (%), Downstream NLP task accuracy |
| Graph-based provenance & authorization alignment | wang2026aligning, souza2025provagent, maloyan2026sleeper | Runtime execution traces can be captured as provenance graphs and aligned against clean-context authorization graphs or digest invariants. | AgentDojo, AgentDyn, synthetic multi-agent workflows, sleeper channel suites | ASR (%), Authorization deviation rate, Utility retention (%) |
| Dual-view environmental isolation | kim2026dualview | Hiding untrusted data from the agent's internal view (using symbolic identifiers) prevents both direct and stored injection. | PinchBench | ASR under direct/stored IPI (%), Utility drop (points) |
| Deterministic out-of-band policy enforcement | narisetty2026adaptive | Mediating agent actions via an out-of-band deterministic reference monitor outside model control prevents unintended tool execution. | AgentDojo (Qwen2.5-7B) | Static ASR (%), Adaptive ASR (%) |
| Runtime argument provenance contracts (FAULTLINE) | maloyan2026sleeper, souza2025provagent, wang2026aligning | Tool parameter values must be grounded as substrings or tokens of trusted user query context; rejected calls receive bounded retry. | MCPTox (300 stratified instances, 6 rungs) | ASR over valid (%), Wilson 95% CI, Replay Block Rate (%), Replay False Block Rate (%) |

## Reported results by approach
| Approach | Result | Conditions | Source (bib key) | Evidence ID |
|---|---|---|---|---|
| Unconstrained baseline (Tool poisoning) | 72.8% ASR on o1-mini; 36.5% published mean across 20 agent settings; refusal <3% | 45 MCP servers, 353 tools, 1,312 malicious test cases, single-turn execution | wang2025mcptox | E001 |
| Unconstrained baseline (IPI) | 24% ASR on ReAct GPT-4; doubles under enhanced hacking prompt | 1,054 test cases across 17 user tools and 62 attacker tools | zhan2024injecagent | E003 |
| Unconstrained baseline (Dynamic environment) | State-of-the-art LLMs fail many tasks unattacked; attacks break subsets of security invariants | 97 realistic tasks, 629 security test cases in dynamic agentic environment | debenedetti2024agentdojo | E004 |
| Control/Data flow isolation (CaMeL) | 77% tasks solved with provable security; 0% security violations (vs 84% undefended utility) | AgentDojo benchmark suite with fine-grained capability checks | debenedetti2025defeating | E005 |
| Input spotlighting | ASR reduced from >50% to <2% across GPT models with minimal NLP performance penalty | Multi-task prompt injection evaluations using delimiter/encoding transformations | hines2024spotlighting | E007 |
| Graph-based alignment (AuthGraph) | ASR reduced from 40% to 1% (AgentDojo) and 39% to 2% (AgentDyn); 76% and 51% utility | Dual-graph alignment comparing clean-context plan against execution trace | wang2026aligning | E009 |
| Dual-view isolation (DualView) | Blocked 100% of tested direct and stored IPI attacks; 1.8–6.4 points utility penalty | PinchBench personal assistant environment separating AgentView and HumanView | kim2026dualview | E011 |
| Out-of-band mediation (Progent) | ASR reduced from 25.8% to 4.2% on Qwen2.5-7B; 2.6% under black-box adaptive attack | AgentDojo out-of-band deterministic action policy enforcement | narisetty2026adaptive | E014 |
| Runtime provenance contracts (FAULTLINE Arm B) | Mean ASR reduced from 28.83% to 6.89% (Δ -21.94%, p=0.0001); residual ASR 1.67% to 15.00% | MCPTox 300 instances, 6 models (R1..R6), call-only retry gating, Wilson 95% CIs | wang2025mcptox, wilson1927probable, mcnemar1947note | E002, E006, E008, E010, E015 |

## Where findings disagree
| Topic | Position A (source) | Position B (source) | Plausible reason for the difference | Claim ID |
|---|---|---|---|---|
| Residual attack susceptibility under structural defenses | Near-zero residual ASR reported under structural/provenance defenses: CaMeL reports 0% violations on AgentDojo (debenedetti2025defeating); AuthGraph reports 1%–2% ASR (wang2026aligning); DualView reports 0% attacks successful (kim2026dualview); Spotlighting reports <2% ASR (hines2024spotlighting). | Significant residual vulnerability persists under tool poisoning: MCPTox unconstrained baseline averages 36.5% ASR with peak 72.8% on o1-mini (wang2025mcptox); runtime provenance contracts on MCPTox exhibit 6.89% pooled residual ASR and 1.67%–15.00% across models (R6 DeepSeek v4 Pro at 15.00%, R3 Qwen 3.8 Flash at 9.67%, R1 Qwen 3.7 Flash at 6.33%). | 1. **Benchmark structure**: MCPTox embeds attacks directly into server tool schemas and metadata across 45 live servers, whereas AgentDojo and PinchBench focus on retrieved user data payloads.<br>2. **Threat model (Single-turn tool selection vs agentic multi-turn)**: In tool poisoning, malicious schema instructions manipulate initial tool choice before external data flows occur, bypassing capability extraction that presumes uncorrupted tool definitions.<br>3. **Judge sensitivity and criteria**: Programmatic state invariants in AgentDojo vs automated LLM-as-a-judge classification (z-ai/glm-5.3-flash) assessing natural language intent fulfillment.<br>4. **Sample and model capability spectrum**: Frontier reasoning models (DeepSeek v4 Pro, o1-mini) adhere more strictly to tool schema instructions than smaller models, creating heterogeneous model-dependent compliance bands not visible on single-model evaluations.<br>*(The disagreement is recorded without resolution).* | C004, C005, C006, C007 |

## Recurring limitations

1. **Synthetic and toy environments**: Existing evaluations (AgentDojo, PinchBench) primarily employ mock environments and synthetic tools, leaving vulnerability on authentic multi-server protocols (e.g. MCP) untested.
2. **Unmeasured false-block cost**: Defensive studies emphasize attack reduction (ASR) while omitting quantitative evaluation of false blocks on valid entity-resolution or world-knowledge parameters (e.g., mapping company names to ticker symbols).
3. **Absence of retry and interaction modeling**: Defenses are largely evaluated on static single-step interactions, ignoring whether runtime failure messages or contract rejections induce spurious actions or bypasses.
4. **Single-model evaluations**: Most evaluations benchmark only one or two frontier models (e.g. GPT-4, GPT-4o), obscuring how defense efficacy varies across model scales and reasoning paradigms.

## What has not been tested

1. **Independent second arm on MCPTox**: No prior study has deployed and evaluated an independent defensive second arm on the MCPTox benchmark suite.
2. **Empirical false-block rate of runtime provenance contracts**: Quantitative measurement of false-positive contract rejections on legitimate user tool invocations under tool poisoning benchmarks.
3. **Behavioral dynamics of contract retry gating**: Whether providing rejection feedback to an agent induces successful tool execution following an initial benign prose refusal.
4. **Cross-model performance across a systematic model ladder**: Paired comparative defense evaluation across multiple model families spanning open-weight, proprietary, and reasoning-specialized architectures.

## Source register pointer
Every bib key above must appear in `evidence/source_register.md` with a read-status.
