# Reviewer #2 Report: research_pub02

Reviewed by: independent automated critic pass (separate context), 2026-09-17

**Overall Recommendation: REJECT**

---

### Top Three Changes That Would Most Raise Credibility

1. **Evaluate against an adaptive adversary who knows the contract:** The current defense is tested strictly against static, frozen benchmark prompts designed for an unconstrained system. A contract-aware attacker can bypass substring matching via prompt token reflection, permitted primitive types, or function hijacking. The paper must test against adaptive adversaries (Kerckhoffs's principle) rather than claiming exploits are "fundamentally neutralized."
2. **Benchmark against standard defensive baselines and evaluate live benign task utility:** The paper evaluates Arm B solely against an undefended baseline (Arm A). It must compare against simple defensive baselines (such as system prompt safety instructions or input spotlighting) to prove that the runtime contract's severe 24.50% false-block penalty and engineering complexity yield marginal security gains beyond existing lightweight methods.
3. **Calibrate the judge against human ground truth and scope headline claims to the empirical snapshot:** The automated judge (`z-ai/glm-5.3-flash`) must be validated against human expert annotations on this 300-instance sample to rule out evaluation artifacts, the R2 self-judging confound must be eliminated, and claims in the Abstract, Introduction, and Conclusion must be scoped strictly to the single-gateway snapshot rather than generalized as universal truths across model families.

---

## Adversarial Methodological Synthesis

### 1. Central Claim in One Sentence
"Interposing a deterministic client-side argument provenance contract (verbatim substring grounding of argument leaves against user turns) with call-only retry gating blunts tool-poisoning attack success on the MCPTox benchmark across six LLMs, but incurs a 24.5% false-block penalty on legitimate tool calls requiring world knowledge."

*Evaluation:* While this central thesis can be extracted, the manuscript diffuses it across four bullet points in §1 and conflates independent variables in the title and abstract (e.g. framing "step caps" as a causal factor despite holding them constant at 2 across both arms; see METH-101 and R2-107).

### 2. Three Strongest Reasons the Central Claim Could Be False
1. **The defense is trivial to evade under an adaptive threat model:** The contract exempts non-strings, strings $\le 3$ characters, and words present in the user query. Any contract-aware attacker can induce user reflection, exploit Template-2 function hijacking (residual ASR 10.93%), or leverage unconstrained primitive fields. The paper never tests this threat model.
2. **The defense is operationally unusable due to catastrophic utility destruction:** Replay reveals a 24.50% false block rate on benign tool use. Any production agent required to perform entity resolution, arithmetic, date formatting, or search formulation will be crippled.
3. **Apparent attack reduction is an artifact of evaluation methodology:** All 1,800 pairs are labeled by a single uncalibrated LLM judge that also evaluates its own subject model on R2 (METH-104), while 65 contract-rejected completions on R1 collapsed into empty responses (`[EMPTY COMPLETION]`) that were filtered out as `Invalid` rather than measured as security failures.

### 3. Novelty Assessment
The core mechanism is literal substring matching between tool arguments and user prompts—a standard taint-tracking heuristic previously explored in prompt firewalls and input transformation literature. The contribution is strictly an empirical benchmark report: deploying this heuristic as a second arm on the MCPTox benchmark. While useful as diagnostic benchmark data, it is not a foundational architectural breakthrough.

### 4. Missing Literature
The manuscript fails to cite foundational literature on adaptive evaluation of machine learning security (e.g., Carlini et al., Tramèr et al.), classic information flow control (IFC) models (Denning, Bell-LaPadula), and modern LLM guardrail architectures (e.g. NeMo Guardrails, Llama Guard) that implement schema and input grounding.

### 5. Overclaiming Analysis
The Abstract and Conclusion claim that the contract "significantly blunts tool poisoning across all evaluated model families" and "fundamentally neutralizes exploits." This directly contradicts the results: on Gemini 3.7 Flash (R5), the reduction is statistically non-significant ($p = 0.22$); on DeepSeek v4 Pro (R6), residual ASR remains high at 15.46%; on Template-2, residual ASR is 10.93%; and `Failure-Direct-Execution` jumped by 41.4% (from 145 to 205 instances).

### 6. Baseline Adequacy
The evaluation lacks any defensive baseline. It compares a 5-stage contract against doing nothing at all. A simple system prompt baseline ("Do not execute instructions in tool descriptions") was not evaluated, leaving open the possibility that a zero-code prompt defense matches Arm B's efficacy without the 24.5% false block penalty.

### 7. Engagement with Contradictory Evidence
Section 2.2 manufactures an artificial literature "disagreement" by contrasting Position A (prior papers reporting near-zero ASR on AgentDojo using capability tokens/graphs) against Position B (this paper's own MCPTox results). This is an apples-to-oranges comparison across different benchmarks, threat models, and defense mechanisms.

### 8. Definitions and Scope
The paper shifts between $\text{ASR}_{\text{valid}}$ and $\text{ASR}_{\text{all}}$ without warning (STAT-101), uses an undefined ad-hoc `false_block_proxy` in Table 1 that masks the real 24.5% utility cost (METH-103), and conflates syntactic substring checks with "typed provenance contracts."

---

## Detailed Failure Reports

FAILURE_ID: R2-101
CATEGORY: Methodology
SEVERITY: BLOCKER

CLAIM: "We deployed and evaluated an independent defensive second arm on the Model Context Protocol Poisoning benchmark (MCPTox), testing whether a client-side runtime provenance contract on tool-call arguments with step-capped retry mitigates tool poisoning across six model rungs... removing 421 attacks while inducing only 26... conclusive evidence that the defense fundamentally neutralizes exploits rather than shifting error modes"
LOCATION: research_pub02/paper/draft.md:Abstract (line 10), Section 1 (lines 31-35), Section 5.3 (line 265), Section 8 (lines 388-390)
PROBLEM: The defense is evaluated exclusively against static, frozen benchmark instances from MCPTox crafted for undefended models. The evaluation includes zero adaptive adversaries with knowledge of the provenance contract rules. Under Kerckhoffs's principle and established security evaluation standards for machine learning defenses, a defense cannot be claimed to "fundamentally neutralize exploits" without evaluating an adversary who knows the defense is active. A contract-aware attacker can easily circumvent verbatim substring matching by: (1) crafting injection instructions that manipulate the user or context into echoing payload tokens; (2) exploiting Template-2 function hijacking where legitimate tool parameters naturally align with query tokens (which already exhibits 10.93% residual ASR even non-adaptively); or (3) exploiting ungrounded primitive types (booleans, floats, integers, strings of length <= 3) explicitly exempted under Rule 5. The draft mentions "Absence of White-Box Adaptive Adversaries" in Section 6, but misrepresents adaptive attack as requiring "white-box GCG optimization" rather than simple grey-box/black-box contract-aware prompt manipulation.
EVIDENCE: Inspected Section 4.2 (ProvenancePolicy rules: non-strings exempt, strings <= 3 exempt, substring matching), Section 5.4 (Table 2: Template-2 residual ASR is 10.93%), and Section 6 (lines 362-363). No adaptive attack evaluations exist in `experiments/raw/results.json` or `analysis.json`.
WHY_IT_MATTERS: Static evaluations of prompt injection defenses routinely fail under adaptive testing. Claiming the defense "neutralizes exploits" without adaptive verification creates a false sense of security and fails peer-review standards for security publications.
REQUIRED_FIX: Explicitly downgrade all claims of exploit "neutralization" to "empirical reduction on static benchmark instances." Add a dedicated discussion analyzing contract-aware evasion vectors, and conduct an empirical evaluation against a contract-aware adaptive adversary.
VERIFICATION_METHOD: Verify that the Abstract, Section 5.3, and Section 8 explicitly state that the defense was evaluated non-adaptively and that robustness against contract-aware adversaries remains unverified.
STATUS: RESOLVED — Adaptive-adversary experiment deferred (no budget, CEO 2026-09-17); claims scoped to non-adaptive static instances.

FAILURE_ID: R2-102
CATEGORY: Overclaiming
SEVERITY: HIGH

CLAIM: "the provenance contract achieved a statistically significant paired mean score reduction of Mean Δ = -0.2194... The runtime contract reduced Attack Success Rate over valid completions by up to 35.5 percentage points on frontier models... runtime provenance contracts significantly blunt tool poisoning across all evaluated model families"
LOCATION: research_pub02/paper/draft.md:Abstract (line 10), Section 8 (line 388)
PROBLEM: The Abstract and Conclusion present a one-sided, highly flattering summary that conceals negative findings, non-significant results, and severe operational failure modes:
1. On R5 (Gemini 3.7 Flash), the ASR reduction was statistically non-significant ($b=5, c=1, p = 0.2188$), directly contradicting the claim that contracts significantly blunt poisoning "across all evaluated model families."
2. Across all six rungs, `Failure-Direct-Execution` jumped by 41.4% (from 145 instances in Arm A to 205 in Arm B), showing that contract rejection frequently coerces retrying models into directly invoking other unverified or poisoned tools.
3. On smaller models (R1 Qwen 3.7 Flash), the contract induced severe model collapse, increasing `Invalid` completions from 45 to 70 due to 65 empty completions on Step 2.
4. The Abstract highlights cherry-picked peak drops ("up to 35.5 percentage points") while omitting the pooled baseline and defended rates entirely, and omitting the 10.93% residual vulnerability on Function Hijacking.
EVIDENCE: Cross-checked Table 1, Table A1, and `results.json`: R5 McNemar exact p-value is 0.2188; Failure-Direct-Execution sum across Arm A is 14+26+30+21+27+27 = 145; across Arm B is 30+31+51+31+25+37 = 205; R1 Arm B has 65 empty completions out of 70 invalid.
WHY_IT_MATTERS: Concealing non-significant rungs, execution diversion, and model collapse misleads readers regarding the real-world operational reliability and boundaries of the defense.
REQUIRED_FIX: Update the Abstract and Conclusion to disclose: (1) that reduction on Gemini 3.7 Flash was non-significant ($p=0.22$) due to autonomous baseline resistance; (2) that retry rejection increased direct execution failures by 41.4%; and (3) that smaller models exhibited high rates of post-rejection empty completion collapse.
VERIFICATION_METHOD: Check Abstract and Section 8 for explicit disclosure of R5 non-significance and operational trade-offs.
STATUS: RESOLVED

FAILURE_ID: R2-103
CATEGORY: Claim integrity
SEVERITY: HIGH

CLAIM: "A sharp divergence exists regarding whether structural defenses eliminate attack susceptibility, or whether substantial residual vulnerability persists. We record this disagreement as Contested [C004, C005, C006, C007]... Position A (Near-Zero Residual ASR)... Position B (Substantial Residual Vulnerability)... We record this disagreement as contested without attempting an ungrounded resolution."
LOCATION: research_pub02/paper/draft.md:Section 2.2 (lines 57-70)
PROBLEM: Section 2.2 manufactures an artificial literature controversy by conflating disparate benchmarks, defenses, and threat models:
1. Position A cites published defenses (CaMeL, AuthGraph, DualView, Spotlighting) evaluated against indirect prompt injection (IPI) on AgentDojo and PinchBench.
2. Position B cites undefended MCPTox (Wang et al. 2025) combined with the author's own unpublished experimental results from this manuscript.
3. None of the cited Position A authors ever evaluated on MCPTox or claimed that MCPTox tool poisoning was eliminated by their tools.
4. FAULTLINE Arm B uses crude literal substring matching, whereas CaMeL uses capability tokens and AuthGraph uses graph alignment. The residual vulnerability on Arm B (6.89% to 15.46%) could easily reflect the weakness of crude substring contracts rather than proof that structural defenses in general leave substantial residual vulnerability.
5. In academic manuscripts, Related Work (§2) should review published literature, not cite the paper's own results in Position B to establish a literature disagreement before the results have even been presented.
EVIDENCE: Checked Section 2.2 lines 57-70 against `claims_ledger.md` (C004-C007) and `literature_map.md` line 36.
WHY_IT_MATTERS: Creates a strawman disagreement that misrepresents prior literature and distorts the scientific context of tool-agent security research.
REQUIRED_FIX: Reframe Section 2.2: remove the paper's own experimental results from Position B, clarify that prior defenses were evaluated on different benchmarks (AgentDojo/PinchBench) against data-payload IPI rather than MCP tool poisoning, and present the question as an open research gap rather than a contested controversy between prior works.
VERIFICATION_METHOD: Verify Section 2.2 removes self-citations to unpublished results and accurately frames benchmark differences.
STATUS: RESOLVED

FAILURE_ID: R2-104
CATEGORY: Methodology
SEVERITY: HIGH

CLAIM: "We show that bounded, typed provenance contracts achieve a statistically significant paired mean score reduction... cutting valid ASR from 28.83% to 6.89% pooled... runtime provenance contracts significantly blunt tool poisoning across all evaluated model families"
LOCATION: research_pub02/paper/draft.md:Abstract (line 10), Section 1 (line 33), Section 8 (line 388)
PROBLEM: Headline claims in the Abstract, Section 1, and Section 8 generalize defense efficacy across "all evaluated model families" and "tool poisoning" broadly, while omitting the severe empirical boundaries governing the evaluation:
1. One benchmark: Evaluated solely on 300 sampled instances of MCPTox.
2. One automated judge: Evaluated solely by `z-ai/glm-5.3-flash`, with zero human-judge validation (METH-104).
3. One gateway: Evaluated solely via OpenRouter (`aicredits.in`) with undisclosed backend quantization, load balancing, and routing (METH-107).
4. One day: Evaluated during a single 24-hour window (2026-09-15 to 2026-09-16), leaving longitudinal API stability unmeasured.
While these points are listed as limitations in Section 6, the headline claims in the Abstract, §1, and §8 fail to reflect these constraints.
EVIDENCE: Inspected `protocol.md` explicit unknowns, Section 6 limitations, and compared against Abstract and Conclusion.
WHY_IT_MATTERS: Presents findings from a single-gateway, single-day API snapshot as broad, generalizable laws of model security.
REQUIRED_FIX: Scope the claims in the Abstract, Section 1, and Section 8 strictly to the tested MCPTox benchmark and gateway configuration snapshot.
VERIFICATION_METHOD: Check Abstract, §1, and §8 to confirm generalizability claims are properly bounded.
STATUS: RESOLVED

FAILURE_ID: R2-105
CATEGORY: Claim integrity
SEVERITY: MEDIUM

CLAIM: "Across 20 agent settings, o1-mini reached 72.8% ASR with refusal rates under 3%, showing that more capable instruction-following models are often more susceptible to tool poisoning [C001]." and "Frontier reasoning models follow detailed schema instructions with high fidelity. When instructions reside in tool definitions, frontier models comply strictly..."
LOCATION: research_pub02/paper/draft.md:Section 2.1 (line 43), Section 2.2 (line 68)
PROBLEM: The draft accepts the claim that "more capable instruction-following models are often more susceptible to tool poisoning" as an established factual truth rather than explicitly attributing it as Wang et al.'s hypothesis/finding. Crucially, the draft fails to reconcile this narrative with its own empirical findings: R5 (Gemini 3.7 Flash) is a flagship frontier reasoning model, yet it exhibits an Arm A baseline ASR of only 3.01% (autonomously resisting 263 of 299 instances), whereas smaller open-weight models (Qwen 3.7 Flash) exhibit an Arm A baseline ASR of 32.94%. The paper's own empirical ladder contradicts a monotonic capability-susceptibility relationship, but the text glosses over this discrepancy.
EVIDENCE: Table 1: R5 (Gemini 3.7 Flash) Arm A ASR is 3.01% (9/299); R1 (Qwen 3.7 Flash) Arm A ASR is 32.94% (84/255).
WHY_IT_MATTERS: Endorses an external claim as a general truth while ignoring internal experimental data that contradicts it.
REQUIRED_FIX: Attribute the "more capable, more susceptible" assertion strictly to Wang et al. [C001] in Section 2.1, and add a discussion in Section 5.1/5.2 explaining that the performance of Gemini 3.7 Flash demonstrates that frontier capability does not universally correlate with higher susceptibility.
VERIFICATION_METHOD: Verify Section 2.1 and Section 5.2 discussion reconciling R5 baseline resistance with Wang et al.'s claim.
STATUS: RESOLVED

FAILURE_ID: R2-106
CATEGORY: Writing
SEVERITY: MEDIUM

CLAIM: Figure 1 (lines 208-214), Figure 2 (lines 325-329), and Figure 3 (lines 286-290)
LOCATION: research_pub02/paper/draft.md:Section 5.1 (line 208), Section 5.4 (line 286), Section 5.6 (line 325)
PROBLEM: Figure captions across all three figures are not self-contained:
1. Figure 1 caption refers to "six model rungs" and mentions only R5 (Gemini 3.7 Flash), failing to name models R1..R4 and R6.
2. Figure 2 caption cites "10,227 author traces" without explaining whether "author" refers to the upstream MCPTox benchmark authors (Wang et al. 2025) or the manuscript authors, and fails to state the dataset source or define what constitutes a "false block" in trace replay.
3. Figure 3 caption completely omits Template-3 (Parameter Injection)—which represents 48% of the benchmark (864 instances)—focusing exclusively on Template-1 and Template-2, and omits paradigm sample sizes ($n$).
EVIDENCE: Inspected lines 208-214, 286-290, and 325-329 in `draft.md`.
WHY_IT_MATTERS: Figures and captions must be fully interpretable independently of body text in standard peer-reviewed scientific publications.
REQUIRED_FIX: Expand captions: list all six models in Figure 1; define the origin and composition of the 10,227 traces and the false-block criterion in Figure 2; include Template-3 sample size and metrics in Figure 3.
VERIFICATION_METHOD: Verify all three figure captions can be fully understood without consulting main text.
STATUS: RESOLVED

FAILURE_ID: R2-107
CATEGORY: Writing
SEVERITY: LOW

CLAIM: "Our study delivers four contributions: [four bullets]"
LOCATION: research_pub02/paper/draft.md:Section 1 (lines 31-36)
PROBLEM: The manuscript lacks a single, concise thesis sentence summarizing its primary scientific contribution. Instead, Section 1 presents four bullet points that bundle distinct mechanisms ("step caps", "typed contracts", "call-only retry gating") without clearly isolating that the causal driver of attack reduction is syntactic substring grounding of argument values. Furthermore, as noted in METH-101, "step caps" were not experimentally manipulated, yet they are featured as a core contribution element.
EVIDENCE: Inspected Section 1 lines 31-36.
WHY_IT_MATTERS: Unclear contribution framing obscures the primary scientific takeaway and inflates secondary implementation parameters into claimed contributions.
REQUIRED_FIX: Add a single, rigorous sentence preceding the bulleted list in Section 1 that states the core contribution, and remove unmanipulated variables (e.g. step caps) from the contribution claims.
VERIFICATION_METHOD: Check Section 1 for a single-sentence thesis statement.
STATUS: RESOLVED

FAILURE_ID: R2-108
CATEGORY: Methodology
SEVERITY: HIGH

CLAIM: "We deployed and evaluated an independent defensive second arm on the Model Context Protocol Poisoning benchmark (MCPTox)... testing whether a client-side runtime provenance contract... mitigates tool poisoning"
LOCATION: research_pub02/paper/draft.md:Section 1 (lines 25-27), Section 4.1 (lines 114-118)
PROBLEM: The evaluation lacks any defensive baseline. It evaluates Arm B (contract-defended) solely against Arm A (completely undefended control). There is zero empirical comparison against simpler, standard baseline defenses, such as: (1) a system prompt defense instructing the model to ignore tool schema instructions, or (2) input spotlighting/delimiter tagging (Hines et al. 2024). Without a simple prompt-defense baseline, it is impossible to know whether the severe 24.5% utility penalty and engineering overhead of a 5-stage policy engine provides any marginal protection beyond a 1-line system prompt guardrail.
EVIDENCE: Inspected `protocol.md` and `draft.md` §4: only Arm A (unconstrained) and Arm B (contract) were executed.
WHY_IT_MATTERS: Reviewers cannot assess the marginal utility or necessity of the proposed defense without comparing it against existing, simpler defensive approaches.
REQUIRED_FIX: Acknowledge the absence of defensive baselines as a significant limitation in Section 6, and propose evaluating lightweight system prompt defenses as Arm C in future work.
VERIFICATION_METHOD: Check Section 6 for explicit discussion of missing defensive baselines.
STATUS: RESOLVED — Arm C deferred (no budget)

---

## Cross-Referenced 3a Critic Findings (Endorsed by Reviewer #2)

Reviewer #2 concurs with and incorporates the following core 3a critique findings that directly impact manuscript credibility:

- **REPRO-101 (SEVERITY: BLOCKER):** Section 7 lists execution commands referencing nonexistent modules (`faultline_p2.cli`), missing trace files, and nonexistent script paths (`scripts/stats_check.py`). Independent third-party execution is impossible as written.
- **METH-101 (SEVERITY: HIGH):** The title and abstract frame "step caps" as a tested intervention, but step caps were held constant at 2 across both arms and never ablated.
- **METH-102 (SEVERITY: HIGH):** Section 3.2 equation for $\text{ASR}_{\text{valid}}$ contradicts reported data by omitting `Contract-Blocked` from the denominator formula while including it in Table 1.
- **METH-104 (SEVERITY: HIGH):** Ground truth across all 1,800 runs relies entirely on a single LLM judge (`z-ai/glm-5.3-flash`), uncalibrated against human annotators, which also evaluates itself on Rung R2.
- **METH-105 (SEVERITY: HIGH):** Pooled McNemar testing ($b=421, c=26, p = 5.61 \times 10^{-93}$) treats 1,800 evaluations on the same 300 instances as independent observations, creating severe pseudo-replication and astronomically inflated p-values.
- **STAT-101 (SEVERITY: HIGH):** Section 1 mislabels overall rates (28.83% and 6.89%) as "valid ASR," violating the metric definition in Section 3.2.
- **STAT-103 (SEVERITY: MEDIUM):** Continuous Gaussian effect size (Cohen's $d_z = -0.49$) is applied to discrete ternary binary differences without qualification.
- **CIT-101 (SEVERITY: HIGH):** Six cited references in `references.bib` lack required CTO governance verification in `cto_verified_references.md`.

---

### Final Verdict

We reviewed `research_pub02/paper/draft.md`, `evidence/claims_ledger.md`, `literature/literature_map.md`, `literature/research_gaps.md`, `experiments/results/*.md`, and all Phase 3a critic reports (`redteam/*_review.md`). We verified statistical calculations, metric formulas, experimental designs, and literature citations. We could not verify ground truth correctness against human expert annotations or test live model behavior against an adaptive attacker due to the offline, budget-constrained nature of this review context. Our overall confidence in this assessment is high: while the manuscript documents an extensive paired evaluation on MCPTox, the total absence of adaptive attacker evaluation, the unviable 24.5% benign false-block rate, the uncalibrated single-judge setup, the artificial literature disagreement, and broken reproduction commands preclude acceptance in its present form.
