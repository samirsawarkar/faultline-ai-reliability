# Evidence table

CLAIM → SOURCE → EVIDENCE → INTERPRETATION. Direction is relative to the claim ID.

| ID | Claim | Source (bib key or data file) | Finding (numbers, conditions) | Direction |
|---|---|---|---|---|
| E001 | C001 | wang2025mcptox | Evaluation across 45 MCP servers, 353 tools, 1312 test cases: o1-mini achieves 72.8% ASR; refusal rate <3% across 20 agent settings. | supports |
| E002 | C001 | research_pub02/redteam/statistics_review.md | Arm A evaluation on 300 MCPTox instances across 6 models yields mean ASR 28.83% (R1: 28.0%, R2: 17.0%, R3: 41.0%, R4: 37.0%, R5: 3.0%, R6: 47.0%), confirming widespread susceptibility to tool poisoning. | supports |
| E003 | C002 | zhan2024injecagent | 1054 test cases across 17 user tools and 62 attacker tools: ReAct GPT-4 achieves 24% ASR, doubling under enhanced hacking prompts. | supports |
| E004 | C003 | debenedetti2024agentdojo | Dynamic evaluation on 97 tasks and 629 security test cases shows state-of-the-art models fail many tasks unattacked and attacks breach subsets of properties. | supports |
| E005 | C004 | debenedetti2025defeating | CaMeL solves 77% of AgentDojo tasks with provable security and 0% security violations compared to 84% utility in undefended baseline. | supports |
| E006 | C004 | research_pub02/redteam/statistics_review.md | On 300 MCPTox poisoning instances across 6 models, runtime provenance contracts reduce mean ASR from 28.83% to 6.89% (Δ -21.94%, p=0.0001), but leave a model-dependent residual ASR between 1.67% and 15.00% (R1: 6.33%, R2: 4.00%, R3: 9.67%, R4: 4.67%, R5: 1.67%, R6: 15.00%), showing that provenance gating does not achieve zero residual vulnerability. | contradicts |
| E007 | C005 | hines2024spotlighting | Spotlighting input transformation reduces indirect prompt injection ASR from >50% to <2% across GPT models with minimal task performance loss. | supports |
| E008 | C005 | research_pub02/redteam/statistics_review.md | Under tool poisoning where malicious instructions are embedded in MCP tool metadata, provenance gating reduces ASR but retains residual vulnerability (6.89% mean ASR; up to 15.00% on DeepSeek v4 Pro), contradicting near-total attack elimination (<2%). | contradicts |
| E009 | C006 | wang2026aligning | AuthGraph dual-graph alignment cuts AgentDojo ASR from 40% to 1% (GPT-4o) and AgentDyn ASR from 39% to 2% with 76% and 51% utility retention. | supports |
| E010 | C006 | research_pub02/redteam/statistics_review.md | Arm B runtime provenance contract reduces mean ASR by -21.94% (p=0.0001, d_z=-0.49), but exhibits higher residual ASR on certain models (9.67% R3, 15.00% R6) than the 1%–2% reported under dual-graph alignment on AgentDojo. | mixed |
| E011 | C007 | kim2026dualview | DualView isolates untrusted data via AgentView/HumanView, blocking 100% of tested direct and stored IPI attacks with 1.8–6.4 point utility penalty on PinchBench. | supports |
| E012 | C007 | research_pub02/redteam/statistics_review.md | While environmental dual-view mechanisms block tested stored IPI, MCP tool schema poisoning operates prior to data storage; runtime argument provenance gating reduces ASR from 28.83% to 6.89% but leaves 6.89% residual. | mixed |
| E013 | C008 | souza2025provagent | PROV-AGENT extends W3C PROV via MCP to capture multi-agent interactions and metadata across edge, cloud, and HPC workflows. | supports |
| E014 | C009 | narisetty2026adaptive | Out-of-band defense Progent reduces ASR from 25.8% to 4.2% on Qwen2.5-7B in AgentDojo; authors caution that static benchmarks risk overstating defense robustness against adaptive attacks. | supports |
| E015 | C009 | research_pub02/redteam/statistics_review.md | Our empirical residual ASR band (1.67% on Gemini 3.7 Flash to 15.00% on DeepSeek v4 Pro; mean 6.89%) corroborates Narisetty et al.'s finding that out-of-band deterministic defenses leave non-zero residual attack surfaces on tool-using agents. | supports |
| E016 | C010 | maloyan2026sleeper | Identifies sleeper channels in persistent agents and proves D2 provenance gate sound against 7 deployment invariants, verified with 42 test suite. | supports |
| E017 | C011 | an2025ipiguard | IPIGuard decouples action planning from untrusted data traversal over Tool Dependency Graphs, suppressing injected tool invocations on AgentDojo. | supports |
| E018 | C012 | greshake2023compromised | Empirically validates indirect prompt injection across Bing Chat and synthetic apps, demonstrating arbitrary code execution via untrusted retrieved content. | supports |
| E019 | C013 | perez2022ignore | Demonstrates goal hijacking and prompt leaking vulnerabilities in GPT-3 via adversarial prompt composition. | supports |

Direction ∈ supports | contradicts | mixed. A claim with both `supports` and `contradicts` rows must be marked `Contested` in the ledger and discussed under "Where findings disagree".
