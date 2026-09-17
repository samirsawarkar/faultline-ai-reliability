# Statistical review (recomputed from `research_pub02/experiments/raw/per_instance.csv`)

Baseline: `arm_A`; alpha = 0.05; Holm correction over 1 comparisons; bootstrap 10k; permutation 20k; seed 0

| System | n instances | mean score |
|---|---|---|
| arm_A | 1800 | 0.2883 |
| arm_B | 1800 | 0.0689 |

Compare every number in the draft against this table — a headline figure that does not match is a HIGH finding (wrong number or wrong file).

| System | n paired |  mean Δ | 95% CI | p (sign-flip) | p (signed-rank) | p Holm | d_z | ties | unpaired dropped |
|---|---|---|---|---|---|---|---|---|---|
| arm_B | 1800 | -0.2194 | [-0.2400, -0.1983] | 0.0001 | 0.0001 | 0.0001 | -0.49 | 1353 | 0 |

Notes: sign-flip permutation on the paired mean is exact under exchangeability and needs no normality assumption. d_z is paired Cohen's d (mean diff / SD of diffs). Do not infer significance from bar-chart gaps.

---

## Reviewed by: independent automated critic pass (separate context), 2026-09-17

### Independent Recomputation Summary (python3 stdlib)

- **12 ASR-over-valid values & Wilson 95% CIs:**
  - R1 Arm A: 84 / 255 = 0.3294, 95% CI [0.2746, 0.3893] (Agrees with Table 1)
  - R1 Arm B: 19 / 230 = 0.0826, 95% CI [0.0535, 0.1254] (Agrees with Table 1)
  - R2 Arm A: 51 / 296 = 0.1723, 95% CI [0.1335, 0.2194] (Agrees with Table 1)
  - R2 Arm B: 12 / 292 = 0.0411, 95% CI [0.0237, 0.0704] (Agrees with Table 1)
  - R3 Arm A: 123 / 294 = 0.4184, 95% CI [0.3634, 0.4755] (Agrees with Table 1)
  - R3 Arm B: 29 / 297 = 0.0976, 95% CI [0.0688, 0.1367] (Agrees with Table 1)
  - R4 Arm A: 111 / 272 = 0.4081, 95% CI [0.3514, 0.4674] (Agrees with Table 1)
  - R4 Arm B: 14 / 266 = 0.0526, 95% CI [0.0316, 0.0864] (Agrees with Table 1)
  - R5 Arm A: 9 / 299 = 0.0301, 95% CI [0.0159, 0.0562] (Agrees with Table 1)
  - R5 Arm B: 5 / 298 = 0.0168, 95% CI [0.0072, 0.0387] (Agrees with Table 1)
  - R6 Arm A: 141 / 296 = 0.4764, 95% CI [0.4201, 0.5332] (Agrees with Table 1)
  - R6 Arm B: 45 / 291 = 0.1546, 95% CI [0.1176, 0.2007] (Agrees with Table 1)

- **Six Per-Rung Discordant Pairs & Exact Binomial McNemar p:**
  - R1: $b=71, c=6$, exact binomial $p = 3.42 \times 10^{-15}$ (Agrees with line 219)
  - R2: $b=41, c=2$, exact binomial $p = 2.15 \times 10^{-10}$ (Agrees with line 220)
  - R3: $b=98, c=4$, exact binomial $p = 1.75 \times 10^{-24}$ (Agrees with line 221)
  - R4: $b=99, c=2$, exact binomial $p = 4.06 \times 10^{-27}$ (Agrees with line 222)
  - R5: $b=5, c=1$, exact binomial $p = 0.2188$ (Agrees with line 223)
  - R6: $b=107, c=11$, exact binomial $p = 6.40 \times 10^{-21}$ (Agrees with line 224)

- **Pooled Discordant Pairs & Exact Binomial McNemar p:**
  - Pooled: $b=421, c=26$, exact binomial $p = 5.61 \times 10^{-93}$ (Agrees with line 263)

- **Paradigm Rates:**
  - Template-1: Arm A 67/272 = 0.2463 [0.1989, 0.3008]; Arm B 5/273 = 0.0183 [0.0078, 0.0421] (Agrees with Table 2)
  - Template-2: Arm A 151/625 = 0.2416 [0.2097, 0.2767]; Arm B 67/613 = 0.1093 [0.0870, 0.1365] (Agrees with Table 2)
  - Template-3: Arm A 301/815 = 0.3693 [0.3369, 0.4030] (Agrees with Table 2)
  - Template-3 Arm B: Raw data in `per_instance.csv` has $n=864$, $n_{\text{valid}}=788$ (excluding 75 Invalid and 1 Error), yielding $\text{ASR}_{\text{valid}} = 52 / 788 = 0.0660$ [0.0507, 0.0855]. Table 2 reports $n_{\text{valid}}=789$ and $\text{ASR}=0.0659$ [0.0506, 0.0854] due to forgetting to exclude the 1 Error row (Discrepancy: STAT-102).

- **Pooled Valid ASR:**
  - Pooled Arm A valid: 519 / 1,712 = 0.3032 (30.32%)
  - Pooled Arm B valid: 124 / 1,674 = 0.0741 (7.41%)
  - Draft line 33 reports "cutting valid ASR from 28.83% to 6.89% pooled", which are actually the overall rates ($519/1800 = 28.83\%$ and $124/1800 = 6.89\%$), not valid rates (Metric Mislabeling: STAT-101).

---

FAILURE_ID: STAT-101
CATEGORY: Statistical validity
SEVERITY: HIGH

CLAIM: "cutting valid ASR from 28.83% to 6.89% pooled, removing 421 attacks while inducing 26 ($p = 5.61 \times 10^{-93}$) [C034, C035]."
LOCATION: research_pub02/paper/draft.md:Section 1 (line 33), Section 5.3 (line 248)
PROBLEM: The draft mislabels overall rates ($\text{ASR}_{\text{all}}$) as valid rates ($\text{ASR}_{\text{valid}}$). In the pooled sample of 1,800 pairs, 519 / 1,800 is 28.83% and 124 / 1,800 is 6.89%. However, valid instances across the six rungs sum to $n_{\text{valid}} = 1,712$ for Arm A and $n_{\text{valid}} = 1,674$ for Arm B. The true pooled valid ASR values are 30.32% (519/1,712) for Arm A and 7.41% (124/1,674) for Arm B. The draft text in Section 1 explicitly calls 28.83% and 6.89% "valid ASR".
EVIDENCE: Recomputed sums of $n_{\text{valid}}$ and successes from `research_pub02/experiments/raw/results.json` and `research_pub02/experiments/raw/per_instance.csv`. Arm A valid: 255 + 296 + 294 + 272 + 299 + 296 = 1,712; Arm B valid: 230 + 292 + 297 + 266 + 298 + 291 = 1,674.
WHY_IT_MATTERS: Directly violates Section 3.2's core definition distinguishing $\text{ASR}_{\text{valid}}$ from $\text{ASR}_{\text{all}}$, reporting $\text{ASR}_{\text{all}}$ numbers under the $\text{ASR}_{\text{valid}}$ label in the paper's central contribution list.
REQUIRED_FIX: Change line 33 to either "cutting overall ASR from 28.83% to 6.89% (valid ASR from 30.32% to 7.41%) pooled" or report both explicitly.
VERIFICATION_METHOD: Check line 33 in `draft.md` against recomputed valid rates.
STATUS: RESOLVED

FAILURE_ID: STAT-102
CATEGORY: Statistical validity
SEVERITY: MEDIUM

CLAIM: "| **Template-3** (Parameter Injection) | Arm B | 864 | 789 | 52 | 0.0659 | [0.0506, 0.0854] | 0.8755 | 0.3199 |"
LOCATION: research_pub02/paper/draft.md:Section 5.4 (Table 2, line 278)
PROBLEM: Table 2 reports $n_{\text{valid}} = 789$ and $\text{ASR}_{\text{valid}} = 0.0659$ for Template-3 Arm B. Recomputation from `research_pub02/experiments/raw/per_instance.csv` reveals $n_{\text{valid}} = 788$, yielding $\text{ASR}_{\text{valid}} = 52 / 788 = 0.065990 \approx 0.0660$ (95% Wilson CI [0.0507, 0.0855]). The discrepancy arises because `analysis.json` subtracted only the 75 `Invalid` instances from 864 ($864 - 75 = 789$), overlooking instance `R6:mcptox_efc4ba94` which has `category: Error, valid: 0`.
EVIDENCE: Cross-checked `research_pub02/experiments/raw/per_instance.csv` row `R6:mcptox_efc4ba94` against `research_pub02/experiments/raw/analysis.json` lines 3381-3389.
WHY_IT_MATTERS: Numerical mismatch between raw instance CSV and reported table values creates reproducibility audit failures.
REQUIRED_FIX: Update Table 2 row for Template-3 Arm B to $n_{\text{valid}} = 788$, $\text{ASR}_{\text{valid}} = 0.0660$, 95% Wilson CI [0.0507, 0.0855], or document that the single runtime Error is treated as valid.
VERIFICATION_METHOD: Verify $n_{\text{valid}}$ and CI match `per_instance.csv` filtering.
STATUS: RESOLVED

FAILURE_ID: STAT-103
CATEGORY: Statistical validity
SEVERITY: MEDIUM

CLAIM: "paired Cohen's $d_z = -0.49$ (medium-to-large effect) [C034]"
LOCATION: research_pub02/paper/draft.md:Abstract (line 10), Section 1 (line 33), Section 5.3 (lines 253, 265)
PROBLEM: Cohen's $d_z$ is formulated for continuous, normally distributed paired differences. Here, the underlying observations are binary ($Y_i \in \{0, 1\}$), so paired differences $D_i = Y_{B, i} - Y_{A, i} \in \{-1, 0, 1\}$ follow a discrete ternary distribution dominated by ties (1,353 zeros out of 1,800 pairs, or 75.2%). Applying standard continuous Gaussian heuristics ("medium-to-large effect") to $d_z$ in binary paired data is methodologically inappropriate.
EVIDENCE: Recomputed standard deviation of paired difference $s_D = 0.4497$ and mean difference $\bar{D} = -0.2194$, giving $d_z = -0.4879$. For binary data, standard effect sizes are the odds ratio ($b/c = 421/26 = 16.19$), Cohen's $g = |421/447 - 0.5| = 0.4418$, or risk difference ($\Delta = -0.2194$).
WHY_IT_MATTERS: Misinterprets a binary contingency table effect using continuous Gaussian benchmarks, which can mislead readers regarding the nature of the distribution.
REQUIRED_FIX: Qualify the reporting of $d_z$ by stating that the distribution is discrete ternary, or lead with the binary effect sizes: odds ratio ($\text{OR} = 16.19$), discordant ratio ($16:1$), and paired risk difference ($\text{Mean } \Delta = -21.94\%$).
VERIFICATION_METHOD: Check Section 5.3 text discussing effect size interpretation.
STATUS: RESOLVED

FAILURE_ID: STAT-104
CATEGORY: Statistical validity
SEVERITY: HIGH

CLAIM: "Section 5.1 Per-Rung Attack Success Rates (lines 218-224) and Section 5.4 Paradigm Breakdown (lines 271-279)"
LOCATION: research_pub02/paper/draft.md:Section 5.1 (lines 218-224), Section 5.4 (lines 271-279)
PROBLEM: Section 5.1 reports six separate paired McNemar tests for rungs R1..R6, and Section 5.4 evaluates three attack paradigms, without reporting any family-wise error rate or false discovery rate corrections (such as Holm-Bonferroni). Although `protocol.md` (lines 75) explicitly pre-registered "Holm-Bonferroni correction over rung-level comparisons", the per-rung p-values in Section 5.1 are unadjusted raw values. Section 5.3 mentions "Holm-Bonferroni Corrected Value: $p = 0.0001$", but that was computed on the single pooled test (1 comparison, where Holm is trivial).
EVIDENCE: Inspected `research_pub02/method/protocol.md` line 75, `research_pub02/redteam/statistics_review.md` line 3, and `draft.md` lines 218-224.
WHY_IT_MATTERS: Performing multiple statistical comparisons without multiplicity adjustment inflates family-wise Type I error rates and violates the pre-registered protocol.
REQUIRED_FIX: Apply Holm-Bonferroni adjustment across the six per-rung McNemar tests and report the adjusted p-values alongside raw p-values in Section 5.1 (all five significant rungs remain significant under Holm since $p_{\text{raw}} < 10^{-9}$).
VERIFICATION_METHOD: Verify Holm-adjusted p-values are reported for R1..R6 in Section 5.1.
STATUS: RESOLVED

FAILURE_ID: STAT-105
CATEGORY: Statistical validity
SEVERITY: LOW

CLAIM: "Sign-Flip Permutation Test (20k iterations): $p = 0.0001$" and "McNemar exact binomial $p$-value: $5.61 \times 10^{-93}$"
LOCATION: research_pub02/paper/draft.md:Section 5.3 (lines 250, 263)
PROBLEM: For an empirical permutation test of 20,000 iterations in which 0 resamples exceed the observed statistic, the p-value is bounded by $p < 1/20,000$ (or $p < 0.0001$), not an exact equality $p = 0.0001$. Reporting exact equality conveys false simulation precision. Furthermore, reporting an exact binomial p-value of $5.61 \times 10^{-93}$ to three significant figures on a sample of $N=1,800$ reflects floating-point precision on a mathematical model rather than meaningful statistical discrimination, and standard convention is to report $p < 10^{-15}$ or $p < 10^{-4}$.
EVIDENCE: Recomputed exact binomial probability on $b=421, c=26$ ($n=447$); the tail probability is $\approx 5.605 \times 10^{-93}$.
WHY_IT_MATTERS: False precision in statistical reporting detracts from paper rigor.
REQUIRED_FIX: Report permutation test as $p < 0.0001$ and extreme binomial tail as $p < 10^{-15}$ or $p < 10^{-4}$ (with the exact calculation noted as an operational detail).
VERIFICATION_METHOD: Check Section 5.3 for $p < 0.0001$ bound notation.
STATUS: RESOLVED

---

### Verdict
We recomputed all 12 ASR-over-valid proportions, Wilson score 95% confidence intervals, six per-rung discordant pairs with exact binomial McNemar p-values, pooled McNemar test ($b=421, c=26$), and paradigm breakdown statistics directly from `research_pub02/experiments/raw/per_instance.csv`, `analysis.json`, and `results.json` using Python standard library scripts. All point estimates and confidence intervals in Table 1 match to four decimal places. However, we identified five statistical defects: (1) pooled $\text{ASR}_{\text{all}}$ (28.83% and 6.89%) is mislabeled as "valid ASR" in Section 1, (2) Template-3 Arm B valid sample size has a 1-instance discrepancy due to an unhandled runtime Error, (3) continuous Cohen's $d_z$ is applied to discrete binary paired data without qualification, (4) pre-registered Holm-Bonferroni correction is omitted from the per-rung comparisons, and (5) permutation p-values are reported with false equality precision. Overall confidence in the statistical calculations is high once these reporting corrections are implemented.
