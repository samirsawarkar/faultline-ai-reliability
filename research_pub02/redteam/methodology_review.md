# Methodology Review

## Reviewed by: Antigravity worker (critic context), 2026-09-17

FAILURE_ID: METH-101
CATEGORY: Overclaiming
SEVERITY: HIGH

CLAIM: "# Do Typed Contracts and Step Caps Blunt Tool Poisoning? An Independent MCPTox Arm with a Provenance Contract"
LOCATION: research_pub02/paper/draft.md:1
PROBLEM: The title frames "step caps" as a tested independent variable alongside typed contracts. However, the step cap was held constant at 2 across both Arm A (unconstrained baseline, step cap 2) and Arm B (contract-defended, step 1 + 1 retry = max 2 steps). No ablation or variation of step caps (e.g., 1 vs. 2 vs. 5 steps) was evaluated. Posing step caps as a causal factor in the title is an overclaim not supported by the experimental design.
EVIDENCE: Checked `research_pub02/method/protocol.md` (Arm A unconstrained step cap 2, Arm B single retry), `research_pub02/research_question.md` (only questions provenance contract and gated retry, not step caps), and `research_pub02/paper/draft.md` Section 4.1.
WHY_IT_MATTERS: Readers and reviewers will expect an ablation or experimental treatment of step caps as an intervention, whereas it was merely a fixed environment parameter.
REQUIRED_FIX: Remove "and Step Caps" from the title, e.g., "Do Typed Provenance Contracts Blunt Tool Poisoning? An Independent MCPTox Arm with a Gated Retry Contract".
VERIFICATION_METHOD: Verify title and abstract reflect only variables experimentally manipulated.
STATUS: RESOLVED

FAILURE_ID: METH-102
CATEGORY: Methodology
SEVERITY: HIGH

CLAIM: "$\text{ASR}_{\text{valid}} = \frac{\text{Success}}{\text{Success} + \text{Failure-Ignored} + \text{Failure-Direct-Execution} + \text{Failure-Refused}} = \frac{\text{Success}}{\text{Valid}}$"
LOCATION: research_pub02/paper/draft.md:Section 3.2 (lines 90-95), Section 5.1 (lines 187-202)
PROBLEM: The mathematical definition of $\text{ASR}_{\text{valid}}$ in Section 3.2 contradicts the actual calculation in Table 1 and `results.json`. Section 3.2 lists four categories in the denominator, omitting `Contract-Blocked`. In Table 1 and `results.json`, Arm B's $n_{\text{valid}}$ includes `Contract-Blocked` (e.g. R1: 19+168+30+13 = 230; R6: 45+186+37+1+22 = 291). Including `Contract-Blocked` in Arm B's denominator inflates the denominator and depresses Arm B ASR. Conversely, 65 step-2 empty completions on R1 are classified as `Invalid` and removed from the denominator, reducing $n_{\text{valid}}$ from 255 to 230.
EVIDENCE: Recomputed valid denominators from `research_pub02/experiments/raw/results.json`. Arm B $n_{\text{valid}}$ sum equals Success + Failure-Ignored + Failure-Direct-Execution + Failure-Refused + Contract-Blocked.
WHY_IT_MATTERS: Discrepancy between stated formula and reported data undermines metric transparency; selective denominator inclusion/exclusion can be seen as flattering defense metrics.
REQUIRED_FIX: Update equation in Section 3.2 to explicitly include `Contract-Blocked` in the valid denominator for defended arms: $\text{Valid} = \text{Success} + \text{Failure-Ignored} + \text{Failure-Direct-Execution} + \text{Failure-Refused} + \text{Contract-Blocked}$. State $\text{ASR}_{\text{all}}$ alongside $\text{ASR}_{\text{valid}}$ in all text and tables.
VERIFICATION_METHOD: Check formula in Section 3.2 against column sums in Table 1 and Table A1.
STATUS: RESOLVED

FAILURE_ID: METH-103
CATEGORY: Statistical validity
SEVERITY: MEDIUM

CLAIM: "R1 (Qwen 3.7 Flash): $b = 71, c = 6$, discordant $= 77$. Continuity-corrected $\chi^2 = 53.19$ ($p = 3.02 \times 10^{-13}$), exact binomial $p = 3.42 \times 10^{-15}$. Significant [C028]. False-block proxy $= 6$."
LOCATION: research_pub02/paper/draft.md:Section 5.1 (lines 219-224)
PROBLEM: Section 5.1 reports "False-block proxy" for each rung without defining the metric, stating its denominator, or explaining how it was computed. In data, `false_block_proxy` measures only the narrow transition where Arm A was `Failure-Ignored` and Arm B was `Contract-Blocked`. It ignores all instances where Arm B blocked a benign execution that subsequently collapsed into `Invalid` (empty completion) or `Failure-Direct-Execution`. This severely understates operational false blocks compared to the 24.50% false block rate identified in Section 5.6.
EVIDENCE: Cross-checked `research_pub02/experiments/raw/results.json` and `research_pub02/experiments/raw/per_instance.csv`. R1 has 27 instances where Arm A was `Failure-Ignored` and Arm B was not, but only 6 ended as `Contract-Blocked`.
WHY_IT_MATTERS: Reporting an undefined, ad-hoc proxy in the primary results table misleads readers into thinking live false blocks were negligible (3 to 16 instances), masking the real 24.5% utility cost documented in replay.
REQUIRED_FIX: Define `false_block_proxy` explicitly in Section 3.2 and Section 5.1, provide its denominator (relative to Arm A `Failure-Ignored`), or replace it with a comprehensive utility degradation metric.
VERIFICATION_METHOD: Verify definition of `false_block_proxy` in Section 3.2 and Section 5.1.
STATUS: RESOLVED

FAILURE_ID: METH-104
CATEGORY: Methodology
SEVERITY: HIGH

CLAIM: "Evaluation is conducted by an automated LLM judge using `inspect_evals_mcptox.prompts.MCPTOX_JUDGE_PROMPT` verbatim: Judge Model: `z-ai/glm-5.3-flash` (R2)."
LOCATION: research_pub02/paper/draft.md:Section 4.4 (lines 144-146), Section 6 (lines 355-357)
PROBLEM: Ground truth labels across all 1,800 evaluations are produced by a single LLM judge (`z-ai/glm-5.3-flash`), which is also one of the evaluated models (R2). The judge has never been validated or calibrated against human expert annotator agreement on this 300-instance sample. Furthermore, in R2, the model acts as its own judge, introducing potential self-preference or systematic evaluation blindness.
EVIDENCE: Checked `research_pub02/method/protocol.md` lines 55, 90 ("Judge validity vs humans not measured") and `research_pub02/research_decisions.md` line 9.
WHY_IT_MATTERS: If the single LLM judge exhibits systematic error on contract retry formatting (e.g. `[EMPTY COMPLETION]`), all conclusions regarding attack suppression could reflect judge bias rather than agent safety.
REQUIRED_FIX: Explicitly mark human validation as an open gap, recommend multi-judge ensemble evaluation for future work, and state that R2 results must be interpreted with caution due to the self-evaluation confound.
VERIFICATION_METHOD: Verify disclosure in Section 4.4 and Section 6.
STATUS: RESOLVED

FAILURE_ID: METH-105
CATEGORY: Methodology
SEVERITY: HIGH

CLAIM: "Across 1,800 paired evaluations on 300 stratified benchmark instances... removing 421 attacks while inducing only 26 (McNemar exact $p = 5.61 \times 10^{-93}$) [C034, C035]."
LOCATION: research_pub02/paper/draft.md:Abstract (line 10), Section 5.3 (lines 248-265)
PROBLEM: The pooled analysis combines 1,800 paired evaluations into a single 2x2 contingency table ($b=421, c=26$) and computes McNemar's exact test ($p = 5.61 \times 10^{-93}$) and sign-flip permutation test ($p = 0.0001$) under the assumption of observational independence. However, the 1,800 evaluations consist of the same 300 benchmark instances evaluated 6 times (once per model). Observations sharing the same benchmark instance are correlated, violating the fundamental independence assumption and creating massive pseudo-replication that produces astronomically inflated p-values.
EVIDENCE: Checked `research_pub02/method/protocol.md` (300 stratified instances evaluated across 6 models = 1,800 pairs).
WHY_IT_MATTERS: Pooling clustered/repeated-measures data as independent pairs invalidates standard McNemar and permutation test statistics.
REQUIRED_FIX: Explicitly state that the pooled McNemar test is an exploratory meta-summary and subject to pseudo-replication; emphasize the per-rung tests (where instances are strictly independent within each rung) as the primary confirmatory evidence.
VERIFICATION_METHOD: Check Section 5.3 for explicit disclosure of clustered instance structure in the pooled analysis.
STATUS: RESOLVED

FAILURE_ID: METH-106
CATEGORY: Methodology
SEVERITY: MEDIUM

CLAIM: "We execute FAULTLINE's runtime defense agent... applying a single retry gated under `--retry-mode call-only`."
LOCATION: research_pub02/paper/draft.md:Section 4.1 (line 117), Section 4.3 (lines 136-141)
PROBLEM: Section 4 presents `--retry-mode call-only` as the fixed experimental protocol without disclosing in Section 4 that this mechanism was adopted adaptively after pilot evaluation on R4 revealed that unconstrained retry prompts coerced benign prose refusals into malicious tool calls. While disclosed in Section 3.3, Section 5.5, and Appendix B, presenting it in Section 4 without stating it was a post-pilot modification obscures the adaptive research timeline.
EVIDENCE: Checked `research_pub02/experiments/raw/DECISIONS.md` (entry 6 and 7 on 2026-09-16) and `research_pub02/research_decisions.md` (decision on 2026-09-16).
WHY_IT_MATTERS: Methodological transparency requires protocol adjustments resulting from exploratory/pilot failures to be clearly identified in the Methodology section as protocol revisions.
REQUIRED_FIX: Add a sentence in Section 4.1 or 4.3 explicitly cross-referencing Appendix B and stating that `--retry-mode call-only` was adopted as a protocol correction following pilot evaluation on R4.
VERIFICATION_METHOD: Verify Section 4.1/4.3 contains cross-reference to pilot protocol refinement.
STATUS: RESOLVED

FAILURE_ID: METH-107
CATEGORY: Claim integrity
SEVERITY: LOW

CLAIM: "Across all six rungs ($n = 300$ per rung, total $N = 1,800$ paired instances)... confirmatory sweeps cost $1.3247 for Arm A and $1.2907 for Arm B across all six rungs, totaling $2.6154 [C048]."
LOCATION: research_pub02/paper/draft.md:Section 4.5 (lines 160-167), Section 6 (lines 354, 358)
PROBLEM: All 1,800 live evaluations were conducted through a single third-party proxy gateway (`aicredits.in` / OpenRouter) during a single 24-hour window (2026-09-15 to 2026-09-16). Model provider backends, quantization levels, load-balancing routing, and potential caching are unobservable. The draft acknowledges this in Section 6, but broader claims in the Abstract and Conclusion should avoid implying longitudinal stability across arbitrary deployment environments.
EVIDENCE: `research_pub02/method/protocol.md` explicit unknowns 2 and 4.
WHY_IT_MATTERS: API endpoints on aggregators are subject to provider-side updates and quantization drift.
REQUIRED_FIX: Maintain the scope of claims in the Abstract and Conclusion strictly within the tested gateway snapshot.
VERIFICATION_METHOD: Check Section 8 to ensure generalizability claims are properly scoped.
STATUS: RESOLVED

---

### Verdict
We reviewed `research_pub02/paper/draft.md` against `research_pub02/method/protocol.md`, `research_pub02/method/hypothesis.md`, `research_pub02/research_question.md`, `research_pub02/research_decisions.md`, and `research_pub02/experiments/raw/DECISIONS.md`. We verified experimental design parity, protocol change disclosures, metric formulas, and validity threats. We could not verify ground truth correctness against human annotations or provider backend configurations due to the offline, budget-constrained nature of this evaluation. Overall confidence in the methodology is moderate-to-high: the paired design and stimulus parity are rigorous, but overclaiming "step caps" in the title, formula inconsistency regarding `Contract-Blocked`, undefined `false_block_proxy`, and pseudo-replication in pooled McNemar testing must be corrected.
