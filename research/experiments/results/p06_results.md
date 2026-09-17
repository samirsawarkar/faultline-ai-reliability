# Project P06 Results

## RAW RESULT

### R2 (z-ai/glm-5.3-flash, as-run)
- Passing trials: 284 out of 450 total trials (`rungs.R2.as_run.pass_at_1.passing_trials`, `rungs.R2.as_run.pass_at_1.total_trials`).
- Successes-per-scenario observed histogram: {0: 8, 1: 34, 2: 74, 3: 34} across 150 scenarios (`rungs.R2.as_run.independence_test.observed_histogram`).
- Concentration scenario counts: 3-of-3 pass = 34, mixed = 108, 0-of-3 pass = 8, total = 150 (`rungs.R2.as_run.concentration_counts`).
- Dead-trial counts: 0 dead trials, 0 touched scenarios, 0 all-3 dead scenarios (`rungs.R2.infra_dead_trials`, `rungs.R2.infra_dead_scenarios`, `rungs.R2.infra_dead_scenarios_all3`).
- Spend: $5.0994 USD final-pass spend ($5.1485 USD total across passes; `rungs.R2.as_run.cost_per_grounded_pass.total_spend_usd`).
- Terminal-state classification [C060]: answered_pass = 284, midrun_no_completion = 109, step_cap (>=24) = 14, dead_at_start = 23, answered_fail = 17, other = 3, step_cap_sub24 = 0 (`rungs.R2.terminal_state_classification`).
- Latency signature of midrun_no_completion [C061]: 104 > 60 s timeouts, 5 other.

### R4 (openai/gpt-5.6-luna, as-run)
- Passing trials: 67 out of 450 total trials (`rungs.R4.as_run.pass_at_1.passing_trials`, `rungs.R4.as_run.pass_at_1.total_trials`).
- Successes-per-scenario observed histogram: {0: 95, 1: 46, 2: 6, 3: 3} across 150 scenarios (`rungs.R4.as_run.independence_test.observed_histogram`).
- Concentration scenario counts: 3-of-3 pass = 3, mixed = 52, 0-of-3 pass = 95, total = 150 (`rungs.R4.as_run.concentration_counts`).
- Dead-trial counts: 95 dead trials, 33 touched scenarios, 31 all-3 dead scenarios (`rungs.R4.infra_dead_trials`, `rungs.R4.infra_dead_scenarios`, `rungs.R4.infra_dead_scenarios_all3`).
- Dead-trial per-trial split: k1 = 31, k2 = 32, k3 = 32 (`rungs.R4.per_trial_split`).
- Dead-trial time window: 2026-09-11T14:42:37.484499 to 2026-09-11T22:41:55.061108 (`rungs.R4.time_window`).
- Spend: $17.9725 USD final-pass spend ($18.3208 USD total across passes; `rungs.R4.as_run.cost_per_grounded_pass.total_spend_usd`).
- Terminal-state classification [C060]: step_cap (>=24) = 118, midrun_no_completion = 119, answered_pass = 67, dead_at_start = 114, answered_fail = 32, other = 0, step_cap_sub24 = 0 (`rungs.R4.terminal_state_classification`).
- Latency signatures [C061]: dead_at_start = 106 < 1 ms (breaker fast-fail), 2 > 60 s (timeouts tripping breaker), 6 other; midrun_no_completion = 100 > 60 s, 19 other.

### R4 (openai/gpt-5.6-luna, infra-excluded)
- Surviving trials: 67 passes out of 351 total trials across 117 scenarios (`rungs.R4.infra_excluded.pass_at_1.passing_trials`, `rungs.R4.infra_excluded.pass_at_1.total_trials`).
- Successes-per-scenario observed histogram: {0: 62, 1: 46, 2: 6, 3: 3} across 117 scenarios (`rungs.R4.infra_excluded.independence_test.observed_histogram`).
- Concentration scenario counts: 3-of-3 pass = 3, mixed = 52, 0-of-3 pass = 62, total = 117 (`rungs.R4.infra_excluded.concentration_counts`).
- Retained scenarios note [C064]: drops 33 scenarios (r-0305, r-0310, and r-0320..r-0350 all); r-0318 and r-0319 survived, so retained set consists of 115 from the first 117 plus r-0318 and r-0319.

### R6 (deepseek/deepseek-v4-pro)
- Spans and runs: 900 spans, 450 runs, 0 verdicts (`rungs.R6.evidence.spans_count`, `rungs.R6.evidence.runs_count`, `rungs.R6.evidence.verdicts_count`).
- Latency signature: 869 spans < 1 ms, 12 timeouts > 60 s, 19 other spans (`infra_signature.json (r6_infrastructure_signature)`).
- Spend: $0.07 USD recorded spend (`ledger.jsonl`).

### Sweep Cumulative Spend & Attempts Breakdown [C024, C067]
- Pass 1 (cap 12, discarded): 18,917,495 tokens, $0.3974 USD discarded spend across 900 runs (R2: 11,427,348 tokens, $0.0491; R4: 7,490,147 tokens, $0.3483).
- Pass 2 (cap 24, final): 35,401,507 tokens, $23.0719 USD final spend across 900 runs (R2: 16,839,794 tokens, $5.0994; R4: 18,561,713 tokens, $17.9725).
- Grand total: 54,319,002 tokens, $23.4693 USD spend across 1,800 runs (34.83% tokens discarded from pass 1).

## DERIVED RESULT

### R2 (as-run, n=150 scenarios, 450 trials)
- pass@1: 0.6311 (Wilson 95% CI [0.5856, 0.6744]; scenario-level bootstrap CI [0.5867, 0.6733]) [C009] (`rungs.R2.as_run.pass_at_1`).
- pass^2: 0.4200 (bootstrap CI [0.3400, 0.5000]); naive (pass@1)^2: 0.3983 (bootstrap CI [0.3442, 0.4534]); C_2: 1.0545 (bootstrap CI [0.9083, 1.1968]) (`rungs.R2.as_run.pass_k.k2`).
- pass^3: 0.2267 (Wilson 95% CI [0.1670, 0.3000]; bootstrap CI [0.1600, 0.2933]); naive (pass@1)^3: 0.2514 (bootstrap CI [0.2019, 0.3053]) [C010] (`rungs.R2.as_run.pass_k.k3`).
- Concentration ratio C_3: 0.9017 (scenario-level bootstrap CI [0.7161, 1.0793]; delta = -0.0247, bootstrap CI [-0.0712, 0.0201]) [C011] (`rungs.R2.as_run.pass_k.k3`).
- Goodness-of-fit test against independent Binomial(3, pass@1): Pearson chi2 = 1.8919, df = 2, asymptotic p = 0.3883, parametric bootstrap p = 0.3794, exact binomial upper-tail p = 0.7840 [C012] (`rungs.R2.as_run.independence_test`).
- Tarone's Z score test for binomial goodness-of-fit against beta-binomial overdispersion [C066]: S = 140.735, z = -0.655, p = 0.7438 (absence of overdispersion; consistent with homogeneous binomial null).
- Intra-scenario correlation: ICC(1,1) = -0.0287 (bootstrap CI [-0.1217, 0.0668]); Fleiss' kappa = -0.0309 (bootstrap CI [-0.1235, 0.0644]) [C013] (`rungs.R2.as_run.intra_scenario_correlation`).
- Beta-binomial compounding extrapolation [C068]: at ICC upper CI bound (0.0668), k=1 C_1=1.00; k=2 C_2=1.04; k=3 C_3=1.10; k=4 C_4=1.21; k=5 C_5=1.39; k=6 C_6=1.60; k=7 C_7=1.89; k=8 C_8=2.25 (pass^8=0.057 vs naive 0.025); k=9 C_9=2.74; k=10 C_10=3.36.
- Cost per grounded pass: $0.017955 USD (evaluated on final-pass spend $5.0994 / 284 passes; bootstrap CI [$0.016830, $0.019318]) [C024] (`rungs.R2.as_run.cost_per_grounded_pass`).
- Order effects [C064]: Spearman rho = 0.1984, Pearson r = 0.1896, permutation p = 0.0144; 9 all-3 passes in 1st half vs 25 in 2nd half (`rungs.R2.as_run.order_effects`).

### R4 (as-run, n=150 scenarios, 450 trials)
- pass@1: 0.1489 (Wilson 95% CI [0.1190, 0.1847]; scenario-level bootstrap CI [0.1133, 0.1867]) [C014] (`rungs.R4.as_run.pass_at_1`).
- pass^2: 0.0333 (bootstrap CI [0.0067, 0.0667]); naive (pass@1)^2: 0.0222 (bootstrap CI [0.0128, 0.0348]); C_2: 1.5037 (bootstrap CI [0.4155, 2.5952]) (`rungs.R4.as_run.pass_k.k2`).
- pass^3: 0.0200 (Wilson 95% CI [0.0068, 0.0571]; bootstrap CI [0.0000, 0.0467]); naive (pass@1)^3: 0.0033 (bootstrap CI [0.0015, 0.0065]) [C015] (`rungs.R4.as_run.pass_k.k3`).
- Concentration ratio C_3: 6.0596 (scenario-level bootstrap CI [0.0000, 12.7450], includes 1.0; delta = +0.0167, bootstrap CI [-0.0022, 0.0411]) [C016] (`rungs.R4.as_run.pass_k.k3`).
- Goodness-of-fit test: Pearson chi2 = 13.6052, df = 2, asymptotic p = 0.0011, parametric bootstrap p = 0.0053, exact binomial upper-tail p = 0.0138 (3 observed vs 0.50 expected) [C017] (`rungs.R4.as_run.independence_test`).
- Tarone's Z score test [C066]: S = 176.433, z = 1.869, p = 0.0308 (marginal overdispersion driven by outage dropouts).
- Intra-scenario correlation: ICC(1,1) = 0.0905 (bootstrap CI [-0.0499, 0.2347]); Fleiss' kappa = 0.0881 (bootstrap CI [-0.0520, 0.2322]) [C018] (`rungs.R4.as_run.intra_scenario_correlation`).
- Cost per grounded pass: $0.268246 USD (evaluated on final-pass spend $17.9725 / 67 passes; bootstrap CI [$0.213958, $0.352402]) [C024] (`rungs.R4.as_run.cost_per_grounded_pass`).
- Infrastructure dropout summary: 95/450 trials (21.1%) dropped out across two windows (first attempt 14:42:37–14:45:38 UTC, retry sweep 22:30–22:41 UTC; both spans completion_tokens=0); 87/95 first attempts had latency < 1 ms (client circuit breaker fast-fail inference) after 2 ~67s gateway timeouts, touching 33 base scenarios (31 all-3 dropped) [C026], [C061] (`rungs.R4.terminal_state_classification`).
- Order effects: Spearman rho = -0.2699, Pearson r = -0.2683, permutation p = 0.0009; 2 all-3 passes in 1st half vs 1 in 2nd half (`rungs.R4.as_run.order_effects`).

### R4 (infra-excluded sensitivity, n=117 scenarios, 351 trials)
- pass@1: 0.1909 (Wilson 95% CI [0.1532, 0.2353]; bootstrap CI [0.1481, 0.2336]); live-trial pass@1: 0.1887 (67/355) [C027] (`rungs.R4.infra_excluded.pass_at_1`, `rungs.R4.live_trial_pass_at_1`).
- pass^2: 0.0427 (bootstrap CI [0.0085, 0.0855]); naive (pass@1)^2: 0.0364 (bootstrap CI [0.0219, 0.0546]); C_2: 1.1729 (bootstrap CI [0.3241, 2.0147]) (`rungs.R4.infra_excluded.pass_k.k2`).
- pass^3: 0.0256 (Wilson 95% CI [0.0088, 0.0727]; bootstrap CI [0.0000, 0.0598]); naive (pass@1)^3: 0.0070 (bootstrap CI [0.0033, 0.0128]) [C028] (`rungs.R4.infra_excluded.pass_k.k3`).
- Concentration ratio C_3: 3.6867 (bootstrap CI [0.0000, 7.5772], includes 1.0; delta = +0.0187, bootstrap CI [-0.0051, 0.0478]) [C028] (`rungs.R4.infra_excluded.pass_k.k3`).
- Goodness-of-fit test: Pearson chi2 = 7.8047, df = 2, asymptotic p = 0.0202, parametric bootstrap p = 0.0243, exact binomial upper-tail p = 0.0488 (3 observed vs 0.81 expected) [C028] (`rungs.R4.infra_excluded.independence_test`).
- Tarone's Z score test [C066]: S = 126.543, z = 0.764, p = 0.2224 (overdispersion evaporates once outage dropouts are excluded).
- Intra-scenario correlation: ICC(1,1) = 0.0438 (bootstrap CI [-0.0978, 0.1907]); Fleiss' kappa = 0.0408 (bootstrap CI [-0.1004, 0.1875]) (`rungs.R4.infra_excluded.intra_scenario_correlation`).
- Order effects [C064]: Spearman rho = 0.0140, Pearson r = -0.0257, permutation p = 0.8765; 2 all-3 passes in 1st half vs 1 in 2nd half (`rungs.R4.infra_excluded.order_effects`).

### Strict Sensitivity Variant (infra_excluded_strict) [C062]
- R2 (n=49 scenarios, 147 trials): pass@1 = 0.8776 (Wilson CI [0.8142, 0.9219]); pass^3 = 0.6939 (Wilson CI [0.5547, 0.8048]); naive = 0.6758; C_3 = 1.0267 (bootstrap CI [0.8654, 1.1578]); delta = +0.0181; Pearson chi2 = 1.6083, df = 2, asymptotic p = 0.4475, parametric bootstrap p = 0.4475; exact tail p = 0.5367 (`rungs.R2.infra_excluded_strict`).
- R4 (n=24 scenarios, 72 trials): pass@1 = 0.3889 (Wilson CI [0.2842, 0.5048]); pass^3 = 0.1250 (Wilson CI [0.0434, 0.3100]); naive = 0.0588; C_3 = 2.1262 (bootstrap CI [0.0000, 4.4172]); delta = +0.0662; Pearson chi2 = 2.7667, df = 2, asymptotic p = 0.2507, parametric bootstrap p = 0.2787; exact tail p = 0.1873 (`rungs.R4.infra_excluded_strict`).

### Paired Comparisons (R2 vs R4)
- as-run (n=150 matched scenarios):
  - all-3-pass: 34 R2-only vs 3 R4-only discordant pairs (113 ties, paired d_z = 0.4561, risk difference +0.2067, bootstrap CI [0.1333, 0.2800]; exact McNemar p = 1.23e-07 [primary], chi2 cc p = 8.14e-07; as-run Holm p = 3.70e-07, 5-test family Holm p = 4.93e-07; odds ratio 11.3333, CI [3.4808, 36.9004]) [C019] (`paired_comparisons.R2_vs_R4.as_run.all_3_pass`).
  - trial-1 pass: 77 R2-only vs 10 R4-only discordant pairs (63 ties, paired d_z = 0.7217, risk difference +0.4467, bootstrap CI [0.3467, 0.5400]; exact McNemar p = 5.92e-14 [primary], chi2 cc p = 1.48e-12; as-run Holm p = 2.37e-13, 5-test family Holm p = 2.96e-13; odds ratio 7.7000, CI [3.9844, 14.8804]) [C020] (`paired_comparisons.R2_vs_R4.as_run.trial_1_pass`).
- infra-excluded (n=117 matched scenarios):
  - all-3-pass: 22 R2-only vs 3 R4-only discordant pairs (92 ties, paired d_z = 0.3736, risk difference +0.1624, bootstrap CI [0.0855, 0.2393]; exact McNemar p = 0.000157 [primary], chi2 cc p = 0.000318; infra-excluded Holm p = 0.00047; odds ratio 7.3333, CI [2.1949, 24.5013]) (`paired_comparisons.R2_vs_R4.infra_excluded.all_3_pass`).
  - trial-1 pass: 55 R2-only vs 10 R4-only discordant pairs (52 ties, paired d_z = 0.5998, risk difference +0.3846, bootstrap CI [0.2650, 0.5043]; exact McNemar p = 1.18e-08 [primary], chi2 cc p = 4.83e-08; infra-excluded Holm p = 4.70e-08; odds ratio 5.5000, CI [2.8037, 10.7892]) (`paired_comparisons.R2_vs_R4.infra_excluded.trial_1_pass`).
- infra-excluded-strict (n=14 matched scenarios) [C063]:
  - all-3-pass: 3 R2-only vs 0 R4-only discordant pairs (11 ties; exact McNemar p = 0.1250) (`paired_comparisons.R2_vs_R4.infra_excluded_strict.all_3_pass`).
  - trial-1 pass: 5 R2-only vs 0 R4-only discordant pairs (9 ties; exact McNemar p = 0.0312) (`paired_comparisons.R2_vs_R4.infra_excluded_strict.trial_1_pass`).

### Hypotheses and Sensitivity Verdicts
- Pre-registered hypothesis H4 is NOT_TESTABLE_AS_PREREGISTERED because only 2 of 6 rungs are valid (requires >= 4 of 6) [C021]. The per-rung criterion (Wilson CI of pass^3 excludes and exceeds naive) was met on R4 under both as-run and infra-excluded variants, but failed on R2 (`hypotheses.H4`).
- Pre-registered hypothesis H5 is NOT_TESTABLE_AS_PREREGISTERED (2 rungs) because evaluating monotonic ordering requires a multi-tier ladder across >= 4 rungs [C022]. With 2 valid rungs, observed point estimates show delta_R2 = -0.0247 vs delta_R4 = +0.0167, but the difference (+0.0414) has a 95% scenario bootstrap CI [-0.0080, 0.0922] that includes zero (`hypotheses.H5`).
- Family-wise error rate [C065]: Holm-Bonferroni correction across the primary declared family of 5 tests yields adjusted p = 2.96e-13 (trial-1 pass exact), 4.93e-7 (all-3 pass exact), 0.0159 (R4 as-run GoF), 0.0486 (R4 infra-excluded GoF), and 0.3794 (R2 GoF) (`hypotheses.family_of_tests`).

### R6 Infrastructure Invalidation
- R6 suffered 100% step-1 failure (450 runs, 900 spans, 0 verdicts) starting 14:47:33 UTC from a gateway incident amplified by the client circuit breaker (869/900 spans < 1 ms fast-fail, 12 timeouts > 60 s); traces lack exception text, so breaker trip is inferred from latency signatures; R6 is invalidated and excluded from capability comparisons [C023], [C031] (`rungs.R6.evidence`, `infra_signature.json (r6_infrastructure_signature)`).

## INTERPRETATION

R2 outcomes are not distinguishable from independent trials (C_3 95% CI [0.7161, 1.0793], parametric bootstrap GoF p = 0.3794, Tarone z = -0.655, p = 0.7438). R4 shows an apparent excess of always-pass scenarios (parametric bootstrap GoF p = 0.0053 as-run, p = 0.0243 infra-excluded, exact binomial upper-tail p = 0.0488), but the concentration ratio C_3 remains unresolved at n=150 / n=117 as its bootstrap CI includes 1.0 ([0.0000, 12.7450] and [0.0000, 7.5772]), and under strict exclusion of all soft-timeout trials (n=24) the departure attenuates (parametric bootstrap p = 0.2787) [C025], [C062].
