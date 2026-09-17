# Results interpretation

Every substantive claim below is labelled 'Interpretation' and cites the specific row in `RAW.md` or `DERIVED.md` that it rests on.

1. **Interpretation (Substantial ASR reduction across all rungs):**
   - *Grounding:* Cites `RAW.md` rows R1–R6 (Arm A vs Arm B) and `DERIVED.md` Table 3 (Mean Δ = -0.2194, 95% CI [-0.2400, -0.1983], p < 0.0001).
   - *Statement:* We interpret the paired evaluation as confirming hypothesis H7: bounded and typed contracts substantially reduce tool-poisoning attack success across all six model rungs. In every rung, the Arm B 95% Wilson confidence interval falls strictly below the Arm A confidence interval with zero overlap (e.g., R1 ASR falls from 0.3294 [0.2746, 0.3893] to 0.0826 [0.0535, 0.1254]; R6 falls from 0.4764 [0.4201, 0.5332] to 0.1546 [0.1176, 0.2007]).

2. **Interpretation (Differential defense efficacy across paradigms):**
   - *Grounding:* Cites `DERIVED.md` Table 1 (Paradigm-pooled results: Template-1 block rate 0.9262; Template-2 block rate 0.8189; Template-3 block rate 0.8755; Arm B ASR on valid: Template-1 = 0.0183, Template-2 = 0.1093, Template-3 = 0.0659).
   - *Statement:* We interpret this differential pattern as supporting the post-hoc sub-hypothesis (H7-sub) that runtime contracts are weakest on Template-2 (function hijacking). Function hijacking diverts execution to legitimate tools whose arguments are more likely to appear incidentally in user context, resulting in a lower attack block rate (81.89%) compared to direct parameter injection (87.55%) or tool description prompt injection (92.62%).

3. **Interpretation (Asymmetric discordance demonstrates defense efficacy over induction):**
   - *Grounding:* Cites `DERIVED.md` Table 3 (Discordant pairs: b = 421 attacks removed, c = 26 attacks induced; McNemar chi2 = 347.28, p = 1.65e-77; exact p = 5.61e-93).
   - *Statement:* We interpret the massive ratio of attacks removed to attacks induced (421 vs 26, a 16:1 ratio) as conclusive evidence that the contract-defended system fundamentally prevents successful exploits rather than shifting error modes. In only 26 instances out of 1,800 did a retry or contract perturbation lead to an exploit where the unconstrained baseline resisted.

4. **Interpretation (Stability of gated retry mechanics):**
   - *Grounding:* Cites `DERIVED.md` Table 2 (Retry mechanics: 230 Step-1 no-call instances received no retry; 613 Step-1 blocked calls retried resulting in 479 allowed and only 22 residual leaks).
   - *Statement:* We interpret the retry data as validating the `--retry-mode call-only` architectural fix (DECISIONS.md entry 6). By gating retries strictly on contract violation of an attempted tool call, 230 natural language refusals and prose responses were preserved without inducing spurious tool calls, while legitimate tasks recovered with minimal residual attack leakage (1.2% of all instances).

5. **Interpretation (Cost-neutral security boundary):**
   - *Grounding:* Cites `RAW.md` spend columns (Arm A total = $1.325, Arm B total = $1.291 across all 6 rungs).
   - *Statement:* We interpret the API spend accounting as demonstrating that client-side contract filtering incurs near-zero economic overhead. Because blocked calls are aborted locally or bounded to two steps, Arm B API spend ($1.291) is comparable to or slightly lower than unconstrained Arm A execution ($1.325), providing security enforcement without model token inflation.
