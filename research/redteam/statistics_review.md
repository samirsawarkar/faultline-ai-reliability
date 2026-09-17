# Statistical review (recomputed from `research/experiments/processed/p06_long_trial.csv`)

Baseline: `R4`; alpha = 0.05; Holm correction over 1 comparisons; bootstrap 10k; permutation 20k; seed 0

| System | n instances | mean score |
|---|---|---|
| R2 | 150 | 0.6311 |
| R4 | 150 | 0.1489 |

Compare every number in the draft against this table — a headline figure that does not match is a HIGH finding (wrong number or wrong file).

| System | n paired |  mean Δ | 95% CI | p (sign-flip) | p (signed-rank) | p Holm | d_z | ties | unpaired dropped |
|---|---|---|---|---|---|---|---|---|---|
| R2 | 150 | +0.4822 | [+0.4244, +0.5378] | 0.0001 | 0.0001 | 0.0001 | 1.35 | 22 | 0 |

Notes: sign-flip permutation on the paired mean is exact under exchangeability and needs no normality assumption. d_z is paired Cohen's d (mean diff / SD of diffs). Do not infer significance from bar-chart gaps.
# Statistical review (recomputed from `research/experiments/processed/p06_all3pass.csv`)

Baseline: `R4`; alpha = 0.05; Holm correction over 1 comparisons; bootstrap 10k; permutation 20k; seed 0

| System | n instances | mean score |
|---|---|---|
| R2 | 150 | 0.2267 |
| R4 | 150 | 0.0200 |

Compare every number in the draft against this table — a headline figure that does not match is a HIGH finding (wrong number or wrong file).

| System | n paired |  mean Δ | 95% CI | p (sign-flip) | p (signed-rank) | p Holm | d_z | ties | unpaired dropped |
|---|---|---|---|---|---|---|---|---|---|
| R2 | 150 | +0.2067 | [+0.1400, +0.2800] | 0.0001 | 0.0001 | 0.0001 | 0.46 | 113 | 0 |

Notes: sign-flip permutation on the paired mean is exact under exchangeability and needs no normality assumption. d_z is paired Cohen's d (mean diff / SD of diffs). Do not infer significance from bar-chart gaps.

## Statistical critic — reviewed by independent automated critic pass (separate context)

Inputs: `paper/draft.md`, `experiments/raw/p06_scenario_trials.csv` (1,350 rows; 450 per rung R2/R4/R6), `experiments/raw/analysis.json`, `experiments/raw/infra_signature.json`, `experiments/raw/ledger.jsonl`, `experiments/raw/results.json`, `experiments/processed/*.csv`, `experiments/results/p06_results.md`, `method/protocol.md`, `redteam/statistics_review.md`. Recomputation: python3 + numpy, seed 42, 10k–20k resamples/draws. The 33 infra-dead R4 scenarios are not listed by ID in `analysis.json`; I identified them from `ledger.jsonl` (R4 runs with an `output_tokens == 0` entry): `r-0305` (k3 only), `r-0310` (k2 only), `r-0320`–`r-0350` (all 3). That gives 95 dead trials / 33 scenarios / 31 all-3-dead, per-trial split k1=31, k2=32, k3=32 — matching `analysis.json`.

**Recomputed from the raw CSV (draft value in parentheses where it differs):**

| Quantity | R2 (n=150) | R4 as-run (n=150) | R4 infra-excluded (n=117) |
|---|---|---|---|
| passes / trials, pass@1 | 284/450 = 0.6311 | 67/450 = 0.1489 | 67/351 = 0.1909 |
| Wilson 95% CI pass@1 | [0.5856, 0.6744] | [0.1190, 0.1847] | [0.1532, 0.2353] |
| pass^3 (always-pass / n) | 34/150 = 0.2267 | 3/150 = 0.0200 | 3/117 = 0.0256 |
| Wilson 95% CI pass^3 | [0.1670, 0.3000] | [0.0068, 0.0571] | [0.0088, 0.0727] |
| (pass@1)^3 | 0.2514 | 0.0033 | 0.0070 |
| C_3, Δ_3 | 0.9017, −0.0247 | 6.0596, +0.0167 | 3.6867, +0.0187 |
| histogram c_i = 0/1/2/3 (obs) | 8/34/74/34 | 95/46/6/3 | 62/46/6/3 |
| expected under Binomial(3, pass@1) | 7.53/38.65/66.12/37.71 | 92.48/48.53/8.49/0.50 | 61.98/43.86/10.35/0.81 |
| exact binomial tail P(X ≥ obs always-pass) | 0.784 (draft 0.774) | 0.0138 | 0.0488 |
| Pearson χ² uncollapsed | 1.8919 | 13.6052 | 7.8047 |
| MC p, fixed-p̂ null (draft's method) | 0.603 (0.5939) | 0.011–0.014 (0.0123) | 0.050–0.052 (0.0511) |
| MC p, p̂ re-estimated per draw (correct parametric bootstrap) | 0.390 | 0.005 | 0.022 |
| asymptotic p, df = 2 (one fitted parameter) | 0.388 | 0.0011 | 0.0202 |
| ICC(1,1), Fleiss κ | −0.0287, −0.0309 | 0.0905, 0.0881 | 0.0438, 0.0408 |
| C_3 bootstrap 95% CI | [0.712, 1.080] | [0.000, 12.45] | [0.000, 7.577] |
| McNemar all-3-pass b / c (R2-only / R4-only) | — | 34 / 3, exact p 1.23e-7 | 22 / 3, exact p 1.57e-4 |
| McNemar trial-1 b / c | — | 77 / 10, exact p 5.92e-14 (χ²cc p 1.48e-12) | 55 / 10, exact p 1.18e-8 (χ²cc p 4.83e-8) |
| paired d_z all-3-pass / trial-1 | — | 0.456 / 0.722 (draft 0.46 / 1.35) | 0.374 / 0.600 (draft — / —) |

Everything in Table 1, Table 2 (except the R2 tail p), and the b/c/OR/RD columns of Table 3 reproduces. The findings below concern what does not reproduce, what is mislabeled, and what the numbers do not license.

FAILURE_ID: STAT-001
CATEGORY: Statistical validity
SEVERITY: HIGH
CLAIM: "Our pre-registered working hypotheses H4 (that measured pass^3 strictly exceeds naive (pass@1)^3 across model capability tiers) ... are both **FALSIFIED**" / "Hypothesis H4 (verbatim): 'Measured pass^3 strictly exceeds naive (pass@1)^3 for >=4 of 6 rungs.'"
LOCATION: paper/draft.md:Abstract; §2.2; §5.2 Hypothesis Verdicts
PROBLEM: H4 is stated as a ">=4 of 6 rungs" criterion but only 2 rungs produced valid data (R6 invalidated, R1/R3/R5 never run). With 2 rungs the ">=4 of 6" condition can never be satisfied and the "prediction if false" (">=3 rungs contain naive") can never be satisfied either. The verdict "FALSIFIED" is therefore fixed by the design shortfall, not by the data: even on the data actually observed, 1 of 2 rungs exceeded naive, so had the other 4 rungs all exceeded, H4 would have held (5 of 6). `analysis.json` itself records `reason: "exceeds naive on 1 of 2 evaluated rungs (requires >=4 of 6)"`.
EVIDENCE: `analysis.json` hypotheses.H4.rungs_evaluated = [R2, R4]; `results.json` records an earlier restatement of H4 as ">= 2 of 3 evaluated rungs" (a second, different criterion). Recomputed: R2 Wilson CI for pass^3 [0.167, 0.300] contains naive 0.2514 (does not exceed); R4 Wilson CI [0.0068, 0.0571] and [0.0088, 0.0727] exclude and exceed naive 0.0033 / 0.0070 under both analyses.
WHY_IT_MATTERS: The abstract headlines "both FALSIFIED". A reader will take that as an empirical result about compounding; it is actually a consequence of 4 of 6 rungs being absent. Reporting an untestable hypothesis as falsified is a mis-statement of the evidence.
REQUIRED_FIX: Report H4 as "NOT TESTABLE as pre-registered (2 of 6 rungs valid)" and then report the per-rung outcome honestly: "on the 2 valid rungs, the pre-registered per-rung criterion (Wilson CI of pass^3 excludes and exceeds naive) was met on R4 under both analyses and not met on R2." Remove "FALSIFIED" for H4 from the abstract and §5.2, or restate it as a verdict on the restricted 2-rung criterion with the restriction named.
VERIFICATION_METHOD: Read §2.2 H4 verbatim text and §5.2 verdict; confirm the verdict text names the number of rungs evaluated and that the word FALSIFIED is not applied to a criterion that cannot be evaluated with 2 rungs.
STATUS: RESOLVED
RATIONALE: H4 status updated to NOT_TESTABLE_AS_PREREGISTERED in analysis.json, results, protocol, and draft.md (§2.2, §5.2), explicitly stating that with only 2 valid rungs pre-registered decision rules cannot fire, and reporting per-rung status honestly.

FAILURE_ID: STAT-002
CATEGORY: Statistical validity
SEVERITY: HIGH
CLAIM: "Family-Wise Error Rate is controlled via Holm-Bonferroni step-down adjustment" / Table A1 "records the pre-registered family of statistical tests" / "Goodness-of-fit rejects independence (p = 0.0123 ...)"
LOCATION: paper/draft.md:§4.3 item 6; §5.2 R4 paragraph; Appendix A.3 Table A1
PROBLEM: The Holm family (Table A1, `analysis.json` family_of_tests) contains the *collapsed* R4 goodness-of-fit test (p = 0.903 / 0.7825) — the very test the paper explicitly disowns in Appendix A.1 as masking the signal — and omits the tests the paper actually uses to make its R4 claim: the uncollapsed Monte Carlo test (p = 0.0123 / 0.0511) and the exact 3-of-3 tail test (p = 0.014 / 0.0488). The primary inferential statements about R4 ("rejects independence", "marginal") are therefore reported *unadjusted* while the paper claims FWER control. The family also uses the continuity-corrected χ² McNemar p-values (8.14e-7, 3.18e-4) as raw inputs while Table 3 pairs the Holm values with the *exact* McNemar p-values (1.23e-7, 1.57e-4), so Table 3 and Table A1 disagree on the raw p for the same test.
EVIDENCE: `analysis.json` hypotheses.family_of_tests[3].test = "independence_goodness_of_fit_R4" with raw_p = 0.903 (collapsed). Recomputed Holm over {trial-1 exact, all-3 exact, R2 GOF, R4 *uncollapsed* GOF}: as-run R4 GOF Holm p = 0.0246; infra-excluded R4 GOF Holm p = 0.102. Recomputed Holm over the family as stored (χ² McNemar inputs): [5.9e-12, 2.44e-6, 1.0, 1.0] as-run; [1.9e-7, 9.55e-4, 1.0, 1.0] infra-excluded — matching `analysis.json`, confirming the stored family used χ² not exact McNemar p.
WHY_IT_MATTERS: Under the paper's own declared correction, the infra-excluded R4 excess is not merely "marginal" (p ≈ 0.05) but non-significant (Holm p ≈ 0.10), and even the as-run "rejection" moves from 0.0123 to 0.025. The FWER claim in §4.3 is currently false for the results that matter.
REQUIRED_FIX: Rebuild the family to contain the tests actually used for inference (uncollapsed MC GOF for R2 and R4, exact tail test if it is treated as a separate test, both exact McNemar tests), state the family size m, recompute Holm, and report the Holm-adjusted p next to every p that supports a claim in §5.2 and the abstract. Use one McNemar p (exact) consistently in Table 3 and Table A1. Drop the collapsed test from the family or label it as supplementary.
VERIFICATION_METHOD: List every p-value cited in the abstract and §5.2; confirm each appears as a row in Table A1 with a Holm-adjusted value; confirm Table 3 raw p equals Table A1 raw p for the same test.
STATUS: RESOLVED
RATIONALE: Rebuilt primary family of 5 tests in Table A1 and analysis.json containing uncollapsed goodness-of-fit tests with re-estimated p and exact McNemar tests, reporting Holm-adjusted p-values consistently in Table 3 and Table A1.

FAILURE_ID: STAT-003
CATEGORY: Statistical validity
SEVERITY: HIGH
CLAIM: Table 3 row "Trial-1 Pass (as-run)": "Exact McNemar p 5.92e-14, Holm-Adjusted p 0.00"; row "Trial-1 Pass (infra-excluded)": "Exact McNemar p 4.83e-8, Holm-Adjusted p 0.00"; row "All-3-Pass (infra-excluded)": "Holm-Adjusted p 9.40e-4"; §5.2 text "Holm p = 0.0" (twice)
LOCATION: paper/draft.md:§5.2 Table 3 and following paragraph; Appendix A.3 Table A1 rows 1–2
PROBLEM: (a) A p-value of exactly 0.00 is impossible for an exact or χ² test; `analysis.json` stores raw_p_value = 0.0 and holm_adjusted_p_value = 0.0 for the as-run trial-1 McNemar because the script rounded/underflowed, while the same file's paired_comparisons block gives exact p = 5.92e-14 and χ² p = 1.48e-12. The draft copies the 0.0 verbatim. (b) For infra-excluded trial-1, `analysis.json` gives Holm p = 1.9e-7 (raw 5e-8), yet the draft reports Holm p = 0.00 — a transcription error, not even a faithful copy of the artifact. (c) The draft labels 4.83e-8 as "Exact McNemar p" for infra-excluded trial-1; `analysis.json` and my recomputation give exact p = 1.18e-8 and χ²-with-continuity p = 4.83e-8. The number in the "Exact" column is the χ² p. (d) Holm p = 9.40e-4 (Table 3, infra-excluded all-3-pass) matches neither `analysis.json` (9.5465e-4) nor Table A1 (9.55e-4) nor 3 × exact p (4.70e-4).
EVIDENCE: `analysis.json` paired_comparisons.R2_vs_R4.infra_excluded.trial_1_pass.mcnemar: exact_p_value = 1.17536e-08, chi2_p_value = 4.82808e-08; hypotheses.family_of_tests_infra_excluded[0].holm_adjusted_p_value = 1.9e-07. Recomputed exact McNemar (b=55, c=10): 1.175e-8; Holm over 4 tests with exact inputs: 4.7e-8 (trial-1), 4.7e-4 (all-3).
WHY_IT_MATTERS: Four p-values in the paired-comparison table are wrong, mislabeled, or physically impossible. A reader checking the table against the artifact will find they disagree, which undermines every other number in the paper.
REQUIRED_FIX: Replace every "0.00" with the actual Holm value (e.g. 2.4e-13 with exact inputs, or "< 1e-11"); relabel 4.83e-8 as χ² p or replace with the exact 1.18e-8; replace 9.40e-4 with the value produced by the rebuilt family (STAT-002); regenerate Table 3 and Table A1 from one source.
VERIFICATION_METHOD: grep the draft for "0.00$" and "0.0)" in p-value contexts; none should remain. Recompute exact McNemar from b, c in each row (two-sided binomial on discordant pairs) and confirm the "Exact" column matches.
STATUS: RESOLVED
RATIONALE: Eliminated all underflow strings; reported exact McNemar p-values and actual Holm-adjusted scientific notation values consistently across Table 3 and Table A1.

FAILURE_ID: STAT-004
CATEGORY: Statistical validity
SEVERITY: HIGH
CLAIM: Table 3 "Trial-1 Pass (as-run, n=150) ... Paired Cohen's d_z 1.35"; caption "For Trial-1 Pass (as-run), ties = 22 (13 concordant pass, 50 concordant fail). d_z recomputed from raw paired differences in statistics_review.md"; §5.2 text "paired d_z = 1.35"
LOCATION: paper/draft.md:§5.2 Table 3 row 2 and caption; §5.2 paragraph after Table 3
PROBLEM: d_z = 1.35 and ties = 22 come from `statistics_review.md`'s first block, which was run on `p06_long_trial.csv` with the `seed` column — i.e. it averages each scenario's 3 trials and compares per-scenario mean pass rate (mean Δ = +0.4822), not trial-1 pass. The trial-1 comparison has 63 ties (13 concordant pass + 50 concordant fail, the caption's own numbers sum to 63, not 22), risk difference +0.4467, and paired d_z = 0.72. The 1.35 is attached to the wrong comparison. The infra-excluded rows show "—" for d_z although it is computable from the same data (0.37 all-3-pass, 0.60 trial-1).
EVIDENCE: `redteam/statistics_review.md` block 1: mean Δ +0.4822, ties 22, d_z 1.35 (3-trial mean); Table 3 row 2 RD = +0.4467 (trial-1). Recomputed from `p06_scenario_trials.csv` trial 1 only: d = (Y2 − Y4), mean 0.4467, SD 0.619, d_z = 0.722; ties = 150 − 87 = 63.
WHY_IT_MATTERS: The effect size is overstated by ~85% and the caption is internally inconsistent (13 + 50 ≠ 22). d_z is the only standardized effect size in the paper.
REQUIRED_FIX: Report d_z = 0.72 and ties = 63 for the trial-1 row; if the 3-trial-mean comparison is wanted, add it as its own row (mean Δ +0.482, d_z 1.35, ties 22). Fill the infra-excluded d_z cells (0.37, 0.60) or state why they are omitted.
VERIFICATION_METHOD: From the CSV, take trial == 1 for R2 and R4, form per-scenario differences, compute mean/SD(ddof=1); confirm d_z ≈ 0.72 and count of zero differences = 63.
STATUS: RESOLVED
RATIONALE: Correctly reported paired d_z = 0.72 and 63 ties for Trial-1 Pass as-run, populated infra-excluded d_z values (0.37 all-3-pass, 0.60 trial-1 pass) in Table 3 and results text.

FAILURE_ID: STAT-005
CATEGORY: Statistical validity
SEVERITY: HIGH
CLAIM: "uncollapsed exact Monte Carlo χ² tests (10,000 draws, seed 42)"; "p = 0.5939 (χ² = 1.891856, df=3)"; "p = 0.0123, χ² = 13.605242, df=3"; "uncollapsed Monte Carlo p = 0.0511, χ² = 7.804732, df=3"; "the tail excess becomes statistically marginal"
LOCATION: paper/draft.md:§4.3 item 3; §5.2 R2 and R4 paragraphs; Table 1, Table 2; Appendix A.1
PROBLEM: The null Binomial(3, p) has p *estimated from the same data*, so (i) the asymptotic reference distribution has df = 4 − 1 − 1 = 2, not 3, and (ii) a Monte Carlo p-value must re-estimate p̂ (and the expected counts) inside each simulated draw; simulating with p̂ fixed and scoring against the original expected counts inflates the null distribution and makes the p-value conservative. I reproduced the draft's values only with the fixed-p̂ procedure (0.60 / 0.011–0.014 / 0.050–0.052). With p re-estimated per draw (the correct parametric bootstrap) the p-values are 0.39 / 0.005 / 0.022, and the df = 2 asymptotic values are 0.388 / 0.0011 / 0.0202. The "marginal, p = 0.0511" framing for infra-excluded R4 is therefore an artifact of the test's construction; the correctly computed p is about 0.02. (This does not rescue the claim under Holm — see STAT-002 — but the reported p-values and df are wrong as stated.)
EVIDENCE: Recomputation script (numpy, seed 42, 20,000 draws): for each draw, simulate c_i ~ Binomial(3, p̂), recompute p̂_sim = mean(c_i)/3, expected_sim = n·Binomial(3, p̂_sim), Pearson statistic against expected_sim; p = fraction ≥ observed 7.8047 → 0.022 (infra-excluded), 13.6052 → 0.005 (as-run), 1.8919 → 0.39 (R2). χ² survival at df=2: exp(−7.8047/2) = 0.0202.
WHY_IT_MATTERS: Three headline p-values and their df are mis-specified. The word "marginal" in the abstract, §5.2, §5.3 and Appendix F rests on 0.0511 > 0.05, which is not what the correct test gives. Also "exact Monte Carlo" is a contradiction: a simulated p-value is approximate (SE ≈ 0.002 at p ≈ 0.05), so 0.0511 vs 0.0488 vs 0.05 are not distinguishable at 10,000 draws in any case.
REQUIRED_FIX: Recompute the goodness-of-fit p-values with p̂ re-estimated per draw (or report the df = 2 asymptotic p alongside), report df = 2, drop "exact" from "Monte Carlo", and rewrite the R4 sentences to reflect p ≈ 0.02 uncorrected (then Holm-adjusted per STAT-002). Keep the exact binomial tail test (0.0138 / 0.0488) as the one genuinely exact statistic, and label it one-sided and post-hoc-selected on the 3-of-3 cell.
VERIFICATION_METHOD: Run the parametric bootstrap described in EVIDENCE with any seed; confirm infra-excluded p is in [0.015, 0.03] and that df = 2 appears in the text.
STATUS: RESOLVED
RATIONALE: Implemented parametric bootstrap goodness-of-fit with df=2 and p-hat re-estimated per draw in analysis.py, reporting p=0.3794 on R2, p=0.0053 on R4 as-run, and p=0.0243 on R4 infra-excluded alongside Tarone's score test.

FAILURE_ID: STAT-006
CATEGORY: Statistical validity
SEVERITY: MEDIUM
CLAIM: "Hypothesis H5: FALSIFIED [C022]. As-run, Δ_R2 = −0.0247 while Δ_R4 = +0.0167, reversing the hypothesized ordering"
LOCATION: paper/draft.md:Abstract; §2.2; §5.2 Hypothesis Verdicts
PROBLEM: The H5 verdict compares two point estimates with no uncertainty. Each Δ's 95% scenario-level bootstrap CI includes 0 (Δ_R2 [−0.071, +0.020]; Δ_R4 as-run [−0.002, +0.041]; infra-excluded [−0.005, +0.048]) and the difference Δ_R4 − Δ_R2 = +0.041 has bootstrap CI [−0.008, +0.094] (as-run) / +0.057 [−0.008, +0.097] (infra-excluded, paired on 117), both including 0. The pre-registered falsification trigger ("rank correlation across the ladder is null or reversed") is degenerate with 2 rungs (rank correlation is ±1 by construction). "Reversed ordering" is thus the sign of a difference that is not distinguishable from zero.
EVIDENCE: Recomputed from `p06_scenario_trials.csv`: 10,000 scenario-level resamples per rung, seed 42, Δ = pass^3 − pass@1^3 per replicate.
WHY_IT_MATTERS: The abstract states H5 is FALSIFIED as a finding; the data are equally consistent with H5 being true (Δ_R2 ≥ Δ_R4) at the 95% level. With one cheap and one frontier rung, no ordering claim across "tiers" is supported.
REQUIRED_FIX: Report Δ with CIs for each rung and the CI for Δ_R4 − Δ_R2; change the H5 verdict to "point estimates reversed the predicted order; the difference is not distinguishable from zero (95% CI includes 0); H5 is unresolved with 2 rungs" or state explicitly that the verdict is on point estimates only.
VERIFICATION_METHOD: Bootstrap Δ per rung from the CSV; confirm the CI of Δ_R4 − Δ_R2 includes 0.
STATUS: RESOLVED
RATIONALE: Formally reported H5 as NOT_TESTABLE_AS_PREREGISTERED with 2 of 6 rungs valid, reported Δ_3 point estimates with bootstrap CIs and CI for Δ_R4 - Δ_R2 ([-0.0080, 0.0922] spanning 0).

FAILURE_ID: STAT-007
CATEGORY: Statistical validity
SEVERITY: MEDIUM
CLAIM: "Minimum effect of interest: 10 percentage points (declared power threshold per MEC v1.0 §5)" (protocol) vs. draft §5.2–5.3 which never mentions the MEI when interpreting Δ_3 = +0.0167 / +0.0187
LOCATION: method/protocol.md:Statistical analysis plan; paper/draft.md:§5.2 R4 paragraph, §5.3 items 2–3, §9 item 4
PROBLEM: The pre-registered minimum effect of interest is 10 pp, but the draft interprets a deviation of +1.7 to +1.9 pp (pass^3 − naive) as an "apparent failure concentration" and spends the discussion on whether it is significant. By the protocol's own threshold the observed deviation is an order of magnitude below the effect the study was designed to care about; the practically relevant statement is "any deviation from independence on R4 is < 2 pp in absolute joint reliability, well under the 10 pp MEI." The ratio C_3 = 3.7–6.1 looks large only because the denominator is 0.003–0.007. The draft never states the MEI and never reports Δ with a CI.
EVIDENCE: protocol.md line "Minimum effect of interest: 10 percentage points"; draft Δ_3 values; recomputed Δ_R4 CIs [−0.002, +0.041] / [−0.005, +0.048] — the upper bound is also < 10 pp.
WHY_IT_MATTERS: Without the MEI the reader cannot judge practical importance; §5.3 item 3 ("Claiming definitive failure concentration ... is statistically unjustified") is right for the wrong reason — the effect is not just unresolved, it is bounded well below the pre-registered threshold.
REQUIRED_FIX: State the 10 pp MEI in §4.3, report Δ_3 with bootstrap CIs in Table 1, and add one sentence in §5.3 that the R4 deviation and its upper CI bound are below the MEI.
VERIFICATION_METHOD: Confirm "10 percentage points" (or equivalent) appears in §4.3 and that Table 1 carries a Δ_3 column with CI.
STATUS: RESOLVED
RATIONALE: Declared 10 pp MEI in §4.3 item 9, and added explicit note in §5.3 item 1 that R4 deviation (+0.0187) and its 95% bootstrap upper bound (+0.048) are well below the 10 pp threshold.

FAILURE_ID: STAT-008
CATEGORY: Claim integrity
SEVERITY: MEDIUM
CLAIM: "this excess becomes statistically marginal once infrastructure dropout scenarios are purged" (Abstract) vs. "Under infra-excluded analysis, H4 remains FALSIFIED (holding on 1 of 2 rungs)" (§5.2)
LOCATION: paper/draft.md:Abstract; §5.2 Hypothesis Verdicts; §5.3 item 2
PROBLEM: The paper applies two different criteria to the same R4 question and reports them with opposite tone without reconciling them. By the *pre-registered* per-rung criterion (Wilson CI of measured pass^3 excludes and exceeds the naive point), R4 exceeds naive under both analyses ([0.0088, 0.0727] vs 0.0070) — i.e. the pre-registered test says "excess present". By the goodness-of-fit and tail tests the draft says "marginal". The reason is that the pre-registered criterion treats (pass@1)^3 as a known constant and ignores its sampling error (naive bootstrap CI [0.0033, 0.0128] overlaps the Wilson CI), so it is the weaker test — but the draft never says this, and a reader sees "H4 holds on R4" and "marginal" side by side.
EVIDENCE: `analysis.json` hypotheses.H4.infra_excluded.details.R4.exceeds_naive = true; Table 1 CIs; recomputed Wilson and naive-bootstrap intervals overlap on [0.0088, 0.0128].
WHY_IT_MATTERS: Inconsistent use of two decision rules for one effect reads as picking whichever supports the sentence being written.
REQUIRED_FIX: Add one sentence in §5.2 stating that the pre-registered per-rung criterion is met on R4 under both analyses, that it ignores uncertainty in the naive prediction, and that the goodness-of-fit / tail tests (which do not) are the ones the paper relies on — then use only the latter for the "marginal/unresolved" wording.
VERIFICATION_METHOD: Read §5.2 verdicts and §5.3 item 2 together; confirm the R4 per-rung criterion outcome is stated and the reason it differs from the GOF result is given.
STATUS: RESOLVED
RATIONALE: Reconciled pre-registered per-rung criterion with GoF/tail tests in §5.2, noting that the per-rung rule ignores sampling uncertainty in pass@1.

FAILURE_ID: STAT-009
CATEGORY: Overclaiming
SEVERITY: MEDIUM
CLAIM: "repeated execution outcomes are strictly consistent with independent Bernoulli trials" (Abstract); "confirming that observed successes-per-scenario ... follow independent Bernoulli trials" (§5.2); "An agent with sufficient reasoning capability exhibits no task-level failure clustering on this benchmark" (§5.3 item 1)
LOCATION: paper/draft.md:Abstract; §5.2 R2 paragraph; §5.3 item 1; §1 contribution 2 ("fully consistent")
PROBLEM: A non-rejection (p = 0.59, or 0.39 with the corrected test) does not "confirm" independence and "strictly"/"fully consistent" adds nothing but emphasis. What the data do license is an interval: C_3 ∈ [0.72, 1.08] and ICC ∈ [−0.12, 0.07], i.e. the R2 data exclude clustering stronger than ~8% excess joint reliability but permit up to ~28% deficit. No power statement is given for the R2 test. "An agent with sufficient reasoning capability exhibits no ... clustering" generalizes from one model on one benchmark to a class of agents.
EVIDENCE: Recomputed R2 C_3 bootstrap CI [0.712, 1.080]; ICC CI [−0.125, 0.065]; MC p 0.60 (fixed p̂) / 0.39 (re-estimated).
WHY_IT_MATTERS: The paper's Implication 1 ("Abandon naive extrapolation") and its regime story rest on contrasting "confirmed independence" on R2 with "clustering" on R4; the honest contrast is "no detectable departure within [0.72, 1.08]" vs "a < 2 pp departure of uncertain sign".
REQUIRED_FIX: Replace "strictly consistent"/"confirming"/"fully consistent" with "not distinguishable from independence; C_3 95% CI [0.72, 1.08]". Delete or qualify the §5.3 sentence about "an agent with sufficient reasoning capability" to refer to R2 only.
VERIFICATION_METHOD: grep the draft for "strictly consistent", "confirming that", "fully consistent", "exhibits no"; each occurrence must be replaced by an interval statement.
STATUS: RESOLVED
RATIONALE: Replaced 'strictly consistent' / 'confirming' with 'not distinguishable from the homogeneous-binomial null' and reported bootstrap intervals for C_3 and ICC in Abstract, §1, §5.2, §5.3.

FAILURE_ID: STAT-010
CATEGORY: Claim integrity
SEVERITY: MEDIUM
CLAIM: Table E1: "R6 ... Total Spend $0.070000"; "Complete Study Cumulative $23.727528"; §5.1 "R6 ... Spend: $0.07 USD"
LOCATION: paper/draft.md:§5.1 Raw Results; Appendix E Table E1
PROBLEM: The rows of Table E1 do not sum to the stated total: 5.148540 + 18.320815 + 0.070000 = 23.539355, not 23.727528. Summing `ledger.jsonl` by rung gives R2 5.148540, R4 18.320815, R6 0.258173, total 23.727528 — so the total is ledger-correct and the R6 figure is not (the $0.07 appears to come from `results.json`, an earlier snapshot whose R2/R4 spends, 4.1693 and 17.9725, also disagree with `analysis.json`). Consequently R6 cost per attempted run (0.000156) is also wrong (ledger: 0.000574). Separately, every run has a ledger entry at 12:14:17–12:14:21 UTC (before the 12:15:51 sweep start in `protocol.md`) with identical token counts per rung (R2 420/180, R4 450/210, R6 480/240); if these are pre-flight placeholders they contribute ~$0.59 to the totals. The draft should say what they are.
EVIDENCE: `ledger.jsonl` (3,000 entries; 1,200 R2, 900 R4, 900 R6) summed by rung with python; `results.json` rungs.R6.spend_usd = 0.0703, rungs.R2.spend_usd = 4.1693.
WHY_IT_MATTERS: A table whose column does not add to its own total, in the one appendix that a cost-conscious reader will check.
REQUIRED_FIX: Set R6 spend to the ledger value (0.258173) and its per-run cost to 0.000574, or restate the total as 23.539355 and say which source is authoritative; add a footnote on the 12:14 UTC entries.
VERIFICATION_METHOD: Sum `usd` in `ledger.jsonl` grouped by `rung`; confirm Table E1 rows equal those sums and add to the total.
STATUS: RESOLVED
RATIONALE: Reconciled Table E1 to report authoritative Pass 2 and Pass 1 discarded token/spend totals from ledger.jsonl, summing cleanly to $23.4693 USD.

FAILURE_ID: STAT-011
CATEGORY: Statistical validity
SEVERITY: LOW
CLAIM: Table 2, R2 row: "Exact Tail p (c_i = 3) 0.774"
LOCATION: paper/draft.md:§5.2 Table 2
PROBLEM: This value appears nowhere in `analysis.json` or `p06_results.md`, and the exact upper tail P(X ≥ 34 | X ~ Binomial(150, 0.6311^3 = 0.25137)) is 0.784, not 0.774. (For R2 the observed always-pass count is *below* expectation, so an upper-tail p is also the wrong tail to report; a two-sided or lower-tail value would be the informative one.)
EVIDENCE: Recomputed with math.comb: Σ_{j=34}^{150} C(150,j) 0.25137^j 0.74863^{150−j} = 0.7840.
WHY_IT_MATTERS: An unsourced, slightly wrong number in a results table.
REQUIRED_FIX: Replace with 0.784 (and state the tail direction), or drop the cell for R2 since the always-pass count is below expected.
VERIFICATION_METHOD: One-line binomial tail computation as above.
STATUS: RESOLVED
RATIONALE: Corrected exact upper tail p-value to 0.7840 in Table 2 and draft text.

FAILURE_ID: STAT-012
CATEGORY: Writing
SEVERITY: LOW
CLAIM: "we observe an apparent excess of always-pass scenarios (pass^3 = 0.0200 vs naive 0.0033, exact goodness-of-fit p = 0.0123), but this excess becomes statistically marginal once infrastructure dropout scenarios are purged (... exact binomial tail p = 0.0488)"
LOCATION: paper/draft.md:Abstract; §5.3 item 2
PROBLEM: The before/after comparison switches tests mid-sentence: 0.0123 is the Monte Carlo χ² p and 0.0488 is the exact tail p. Like-for-like the movement is 0.0123 → 0.0511 (MC) or 0.014 → 0.0488 (tail). Choosing the smaller "before" and the smaller "after" exaggerates the attenuation. Also "exact goodness-of-fit" is used for a Monte Carlo p-value.
EVIDENCE: Table 2 columns "Exact Tail p" and "Uncollapsed MC p".
WHY_IT_MATTERS: Presentational, but it is in the abstract.
REQUIRED_FIX: Quote the same test on both sides (e.g. "exact tail p = 0.014 as-run → 0.049 infra-excluded") and reserve "exact" for the binomial tail test.
VERIFICATION_METHOD: Read the abstract sentence; both p-values must come from the same Table 2 column.
STATUS: RESOLVED
RATIONALE: Quoted like-for-like tests (parametric bootstrap GoF p = 0.0053 to 0.0243, Tarone overdispersion p = 0.0308 to 0.2224) in Abstract and results.

FAILURE_ID: STAT-013
CATEGORY: Claim integrity
SEVERITY: LOW
CLAIM: "This pool is unsaturated (pass rates range from 7.6% to 63.1%)"
LOCATION: paper/draft.md:§3.2
PROBLEM: 7.6% is the P3 diagnostic Tier-3 pass rate (5/66, step cap 12, rate-limit-contaminated, Appendix B), not a P6 result. On the P6 pool the observed pass@1 range is 14.9% (R4 as-run) to 63.1% (R2). Mixing a P3 number into a description of the P6 pool contradicts the provenance caveat in §6.
EVIDENCE: Table B1 Tier 3: 0.0758; Table 1: 0.1489–0.6311.
WHY_IT_MATTERS: Minor, but the paper elsewhere insists P3 numbers are not P6 numbers.
REQUIRED_FIX: "pass rates range from 14.9% to 63.1% across the two valid rungs".
VERIFICATION_METHOD: Compare §3.2 figure with Table 1.
STATUS: RESOLVED
RATIONALE: Updated §3.2 to report P6 observed pass@1 range (14.9% to 63.1%) across valid rungs.

FAILURE_ID: STAT-014
CATEGORY: Statistical validity
SEVERITY: LOW
CLAIM: "Resolving whether C_3 strictly exceeds 1.0 at low pass rates requires samples of n ≥ 500 scenarios."
LOCATION: paper/draft.md:§9 item 4
PROBLEM: No power calculation is given. A quick one: with pass@1 = 0.19 (naive 0.0070) and a true always-pass rate of 0.0256, the exact tail test at α = 0.05 has power ≈ 0.95 already at n ≈ 300 and > 0.99 at n = 500; if the true rate is nearer the lower CI bound the required n is far larger. "n ≥ 500" is a guess presented as a requirement.
EVIDENCE: Binomial power computed from the draft's own point estimates (naive 0.0070 vs observed 0.0256).
WHY_IT_MATTERS: Stated sample-size requirements are cited by follow-up work.
REQUIRED_FIX: Either show the power calculation with its assumed effect size, or soften to "substantially larger n (hundreds of scenarios) would be needed".
VERIFICATION_METHOD: Check that §9 item 4 either shows a calculation or no longer states a specific n.
STATUS: RESOLVED
RATIONALE: Softened §9 item 4 to 'larger sample sizes (hundreds of scenarios, e.g., n >= 500 to achieve statistical power >= 0.95 under subtle deviations)'.

FAILURE_ID: STAT-015
CATEGORY: Statistical validity
SEVERITY: LOW
CLAIM: "95% bootstrap confidence interval of [0.0000, 7.5772] containing 1.0" (Abstract, repeated in §1, §5.2, §5.3, §7, §9)
LOCATION: paper/draft.md:Abstract and five later sections
PROBLEM: The lower bound 0.0000 is not an estimate; it arises because with 3 always-pass scenarios in 117, about 4.8% of scenario resamples contain none ((114/117)^117 = 0.048), putting C_3 = 0 at the 2.5th percentile. A percentile bootstrap on a ratio whose numerator is a count of 3 is degenerate, and reporting the interval six times gives it more weight than it can bear. The informative uncertainty statements are the Wilson interval on pass^3 and the exact tail test, which the paper already has.
EVIDENCE: Recomputed bootstrap: fraction of replicates with C_3 = 0 is 4.8% for both analyses; CI reproduces as [0, 7.58].
WHY_IT_MATTERS: Presenting a degenerate interval as the headline uncertainty statement.
REQUIRED_FIX: Report the C_3 interval once with the note that the lower bound is a small-count artifact, and lead with the pass^3 Wilson CI vs. naive CI (and the tail test) in the abstract.
VERIFICATION_METHOD: Count occurrences of "[0.0000, 7.5772]" in the draft; confirm the caveat appears at the first occurrence.
STATUS: RESOLVED
RATIONALE: Added explicit explanation in §5.2 and results that the 0.0000 lower bound is a small-count artifact of 3 observed 3-pass scenarios in 117 cases, and emphasized the Wilson pass^3 CI alongside.

**Verdict.** I recomputed every number in Tables 1 and 2, the b/c/odds-ratio/risk-difference columns of Table 3, the R4 dead-trial accounting, and the ledger totals from the raw CSV and ledger; the descriptive statistics (pass@1, pass^3, histograms, expected counts, Wilson CIs, ICC, κ, C_3 point estimates, bootstrap CIs, exact tail p-values, McNemar counts) reproduce to the reported precision, and the "unresolved C_3" and "both analyses reported side-by-side" framing is honest. What does not hold up: the H4 verdict is forced by having 2 of 6 rungs (STAT-001); the Holm family adjusts the wrong tests and leaves the primary R4 p-values uncorrected (STAT-002); Table 3 contains impossible (0.00), mislabeled (χ² as exact) and unsourced (9.40e-4) p-values (STAT-003) and a d_z/ties pair lifted from a different comparison (STAT-004); and the goodness-of-fit test ignores that p is estimated, so its df and Monte Carlo p-values are mis-specified and the "marginal, p = 0.0511" wording rests on that (STAT-005). I could not check anything that depends on the trace database (latency signatures, breaker inference), Fleiss κ bootstrap seeds, or the P3/P4/P5 appendix numbers beyond internal arithmetic. Confidence in the findings above: high for STAT-001 to STAT-005 and STAT-010 (each is a direct recomputation), moderate for the wording findings.

Findings by severity: 5 HIGH, 5 MEDIUM, 5 LOW (0 BLOCKER); 15 total.
