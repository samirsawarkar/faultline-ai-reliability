## Methodology critic — reviewed by independent automated critic pass (separate context)

Inputs read: `paper/draft.md`, `method/protocol.md`, `method/hypothesis.md`, `experiments/configs/example_run.json`, `experiments/configs/p06.json`, `experiments/processed/p06_all3pass.csv`, `experiments/processed/p06_long_trial.csv`, `experiments/results/p06_results.md`, `research_question.md`. No other files, no model APIs. Recomputations below were done from `p06_long_trial.csv` (900 rows: 150 scenarios x 3 trials x 2 models).

FAILURE_ID: METH-001
CATEGORY: Methodology
SEVERITY: HIGH
CLAIM: "Purging infrastructure dropouts renders failure clustering marginal ($p = 0.0488$ exact tail, $p = 0.0511$ uncollapsed Monte Carlo)" and "we interpret between-trial variation across our runs as inference engine and serving backend nondeterminism rather than stochastic sampling"
LOCATION: paper/draft.md:§4.4, §5.3 (finding 2), §4.1
PROBLEM: The exclusion rule catches only total dropouts (every span `completion_tokens==0` AND `max(step_index)<=1`). Any trial that got past step 1 and then hit a 429, a 5xx, a timeout, or a malformed gateway response is scored as a reasoning failure. Nothing in the inputs reports how many non-dead P6 trials contain HTTP errors or timeouts, even though the same pipeline on the same gateway recorded `INFRASTRUCTURE_RATE_LIMIT` as 62.3% of all P3 failures (Appendix C) and R4 ran inside a known gateway-incident window. Soft infrastructure failures deflate pass@1, which deflates the expected 3-of-3 count under Binomial(3, pass@1) (0.81 at n=117) and therefore inflates the significance of the 3 observed always-pass scenarios. The R4 "excess" can be produced by infrastructure depressing p-hat without any failure concentration in the model.
EVIDENCE: protocol.md D-008 exclusion rule; draft §4.4; Appendix C Table C1 (114/183 P3 failures are rate limits); p06_results.md reports dead-trial counts only, no per-trial error taxonomy for P6. Recomputed: with pass@1 = 67/351, expected 3-of-3 = 117 x (0.1909)^3 = 0.81; if only 10 of the 284 R4 non-passing live trials were soft infra failures, the expected count rises to ~1.1 and the exact tail p rises above 0.1.
WHY_IT_MATTERS: The paper's second core finding (R4 shows marginal failure concentration) and its attribution of all between-trial variance to serving nondeterminism both depend on every non-dead failure being a model failure. That is asserted, not shown.
REQUIRED_FIX: From `trace.db`, tabulate for every P6 trial (both models) the terminal reason: oracle-fail (answer mismatch vs citation missing), step-cap hit, HTTP/timeout error at any step, malformed tool call. Report the table in §5.1 and re-run the R4 tests with soft-infra trials either excluded or treated as missing. If the trace store cannot distinguish these, say so in Limitations and downgrade finding 2 to "cannot be separated from infrastructure".
VERIFICATION_METHOD: A reader can query `trace.db` spans for R4 live trials with status codes / latency > 60 s / completion_tokens = 0 at step_index > 1 and compare the count to the table.
STATUS: RESOLVED
RATIONALE: Implemented terminal state classification across Pass 2 (R2 pass 284, midrun 109, cap>=24 14, dead 23, fail 17; R4 cap>=24 118, midrun 119, pass 67, dead 114, fail 32), and strict sensitivity variant (infra_excluded_strict, n=49 R2, n=24 R4) shows R4 departure attenuates to p=0.2787.

FAILURE_ID: METH-002
CATEGORY: Methodology
SEVERITY: HIGH
CLAIM: "For R4, 33 scenarios are dropped, leaving $n=117$ valid scenarios (351 trials)" and "paired comparisons on identical scenario IDs isolate performance divergence across regimes"
LOCATION: paper/draft.md:§4.4, §5.2 Table 3, Appendix F.5
PROBLEM: The excluded scenarios are not a random subset. They are the contiguous ID block r-0318..r-0350 (the last 33 scenarios in manifest order). On R2, outcome is significantly correlated with manifest order, and the excluded block is where R2 performed best. So the infra-excluded R4 analysis is run on a subset that differs systematically from the pre-registered pool, and the paired R2-vs-R4 comparison at n=117 discards the block on which one arm's pass rate was highest. The paper never checks whether exclusion was ignorable with respect to scenario properties or time.
EVIDENCE: Recomputed from p06_long_trial.csv: R4 successes-per-scenario on the first 117 IDs (r-0201..r-0317) = {0:62, 1:46, 2:6, 3:3} and R2-only/R4-only all-3-pass discordant pairs = 22/3, which match the paper's infra-excluded numbers exactly; every R4 scenario from r-0320 onward has 0/3. R2 pass rate by 30-scenario ID block: 0.589, 0.567, 0.622, 0.667, 0.711; R2 all-3-pass count by block: 3, 4, 6, 10, 11 (9 in first half of IDs vs 25 in second half). Permutation test of Pearson r between ID rank and R2 successes: r = 0.19, p = 0.019 (20,000 permutations).
WHY_IT_MATTERS: Either scenario difficulty is ordered by manifest ID (then the exclusion changed the difficulty mix and the two analyses are not comparable) or R2's performance drifted over its sweep (then a time/gateway-state confound exists that the paper attributes to model behaviour). Both readings undermine "we report both analyses side-by-side" as a sufficient answer to the post-hoc objection.
REQUIRED_FIX: State the execution order of scenarios and trials. Report the R2 ID-order trend. Test whether the excluded block differs from the retained block on R2 outcomes and on scenario features (chain structure, prompt length). If the trend is temporal, add a time/position covariate to the analysis or report the paired comparison restricted to a time window both models completed.
VERIFICATION_METHOD: Recompute R2 per-block pass rates and the ID-rank correlation from `p06_long_trial.csv` (script above reproduces r = 0.19); confirm from `trace.db` timestamps whether ID order equals execution order.
STATUS: RESOLVED
RATIONALE: Computed and reported order-effects permutation tests and rank correlations across sweeps in §4.4 and §5.1 (Spearman rho = 0.1984, p = 0.0144 on R2; rho = -0.2699 on R4 as-run; rho = 0.0140, p = 0.8765 on R4 infra-excluded); documented execution order and 30-scenario ID block distributions.

FAILURE_ID: METH-003
CATEGORY: Statistical validity
SEVERITY: HIGH
CLAIM: "Family-Wise Error Rate is controlled via Holm-Bonferroni step-down adjustment" (Table A1 lists `independence_goodness_of_fit_R4_collapsed`, p = 0.9030)
LOCATION: paper/draft.md:§4.3 item 6, Appendix A.3 Table A1, §5.2
PROBLEM: The tests that carry the R4 result (uncollapsed exact MC p = 0.0123 / 0.0511; exact tail p = 0.0140 / 0.0488) are not in the Holm family. The family contains instead the collapsed R4 test (p = 0.90), which the paper itself discards as uninformative. The switch from collapsed to uncollapsed testing is recorded as Decision D-004, made after the histogram was seen (the justification cites the observed 6-vs-8.49 deficit in the 2-of-3 cell). The headline R4 p-values are therefore both post-hoc-selected and uncorrected, while the pre-registered family is populated with a null result.
EVIDENCE: Table A1 rows; §A.1 rationale for D-004; §5.2 reports 0.0123 and 0.0488 without adjustment. With the two R4 primary tests added to a family of 4 (dropping the collapsed duplicate), Holm on 0.0123 gives >= 0.037 and on 0.0511 gives >= 0.10.
WHY_IT_MATTERS: The paper's "apparent excess... becomes marginal" narrative is built on unadjusted p-values from a test chosen after seeing the data. Corrected, the as-run R4 result is itself at best marginal and the infra-excluded result is null.
REQUIRED_FIX: Put the uncollapsed exact tests (or the exact tail tests, whichever is declared primary) into Table A1 and report Holm-adjusted values in §5.2 and the Abstract; state explicitly that D-004 was a post-hoc change of test and give the pre-registered test's result alongside.
VERIFICATION_METHOD: Table A1 contains the 0.0123/0.0511 rows with adjusted values; the Abstract quotes the adjusted values.
STATUS: RESOLVED
RATIONALE: Rebuilt primary family of 5 tests in Table A1 and analysis.json containing uncollapsed goodness-of-fit tests with re-estimated p and exact McNemar tests, reporting Holm-adjusted p-values throughout.

FAILURE_ID: METH-004
CATEGORY: Overclaiming
SEVERITY: HIGH
CLAIM: "Our pre-registered working hypotheses H4 ... and H5 ... are both **FALSIFIED**"
LOCATION: paper/draft.md:Abstract, §2.2, §5.2 Hypothesis Verdicts; method/hypothesis.md
PROBLEM: H4 was pre-registered over 6 rungs with decision rules "true if >= 4 of 6 rungs" / "false if >= 3 rungs contain or fall below naive". P06 ran 3 rungs; 1 was lost to infrastructure; 2 remain. Neither pre-registered decision rule can fire with 2 rungs. On the 2 rungs available, the per-rung criterion held on R4 (Wilson CI [0.0068, 0.0571] excludes and exceeds 0.0033; infra-excluded [0.0088, 0.0727] vs 0.0070) and failed on R2, i.e. 1 of 2. Calling this FALSIFIED is falsification by attrition, not by data. Nothing in the inputs explains why 3 of the 6 pre-registered rungs were never run. H5 is declared FALSIFIED on a point-estimate ordering (delta_R2 = -0.0247 vs delta_R4 = +0.0167) whose bootstrap intervals on C_3 ([0.72, 1.08] vs [0.0, 12.7]) overlap almost entirely; no test of the difference is reported.
EVIDENCE: hypothesis.md H4/H5 rows; research_question.md ("1 of 2 valid rungs"); protocol.md lists 3 rungs; Table 1 CIs.
WHY_IT_MATTERS: "Both hypotheses FALSIFIED" is the bolded headline of the Abstract. The evidentially accurate statement is: H4 could not be evaluated under its pre-registered rule; on the 2 evaluable rungs it held on one; H5's predicted ordering was not observed in point estimates but the difference is not resolved.
REQUIRED_FIX: Replace "FALSIFIED" for H4 with "not evaluable as pre-registered (2 of 6 rungs); held on 1 of 2"; for H5 report the ordering as observed with a CI on delta_R2 - delta_R4 (or C_3 ratio) and state it is not significant. Explain in §2.2 why only 3 rungs were run.
VERIFICATION_METHOD: Abstract and §5.2 verdict text match the pre-registered decision rules quoted in §2.2.
STATUS: RESOLVED
RATIONALE: Updated H4 status to NOT_TESTABLE_AS_PREREGISTERED in analysis.json, protocol.md, p06_results.md, and draft.md (§2.2, §5.2), explicitly stating the 2-rung design constraint and reporting per-rung criteria honestly.

FAILURE_ID: METH-005
CATEGORY: Overclaiming
SEVERITY: HIGH
CLAIM: "Regime-Dependent Independence: At higher single-trial accuracy ... multi-trial outcomes match independent Bernoulli compounding ... An agent with sufficient reasoning capability exhibits no task-level failure clustering on this benchmark" and Contribution 1: "showing that consistency cannot be universally assumed across model tiers"
LOCATION: paper/draft.md:§5.3 finding 1, §1 contributions 1-2, Abstract ("asymmetric behavior")
PROBLEM: A regime-dependence claim requires a test that the two regimes differ. None is performed. R2's C_3 CI [0.72, 1.08] and R4's [0.0, 7.58] (or [0.0, 12.7]) overlap; R2's ICC CI [-0.12, 0.07] and R4's [-0.10, 0.19] overlap. The paper's own finding 3 says C_3 is "unresolved" for R4, so the "asymmetry" is between a null result and an unresolved result. Further, "regime" is perfectly confounded with model identity (one model per regime) and with time of execution (R4 ran during the gateway incident, R2 did not), so even a demonstrated difference could not be attributed to accuracy level. The causal phrase "sufficient reasoning capability" has no support in the design.
EVIDENCE: Table 1 CIs; §5.3 finding 3; protocol.md timestamps (single sweep 12:15-22:42 UTC, R2 then R4 then R6).
WHY_IT_MATTERS: Contribution 1 and finding 1 are the paper's stated advance; both assert a between-model difference the data do not establish.
REQUIRED_FIX: Reword to what is supported: "On R2, no departure from independence was detected (C_3 CI [0.72, 1.08]); on R4 the question is unresolved." Delete "regime-dependent", "asymmetric", "cannot be universally assumed", and "sufficient reasoning capability", or add a between-model test on C_3 / ICC with its CI and note the model-identity and time confounds.
VERIFICATION_METHOD: Every between-regime statement in Abstract/§1/§5.3 is accompanied by a between-regime test or is removed.
STATUS: RESOLVED
RATIONALE: Adopted Reviewer #2 framing in Abstract, Intro, and §5.3; removed speculative claims of "regime-dependent independence" and "sufficient reasoning capability"; reported that naive formula is accurate to 2.5 pp across both models, R2 fits homogeneous binomial null, and R4 is marginal/unresolved with overlapping CIs.

FAILURE_ID: METH-006
CATEGORY: Overclaiming
SEVERITY: HIGH
CLAIM: "Abandon Naive $(\text{pass@1})^k$ Extrapolation: System designers must cease multiplying single-trial pass rates to predict operational multi-trial reliability"
LOCATION: paper/draft.md:§7 item 1
PROBLEM: The paper's own evidence points the other way. On the only rung with a resolved result, naive extrapolation was accurate to within the CI (pass^3 0.2267 vs 0.2514, C_3 CI includes 1). On R4 the paper says the ratio is unresolved. A recommendation to abandon a practice needs evidence that it fails; the paper found no such evidence in its own data and cites external work for the recommendation.
EVIDENCE: Table 1; §5.3 findings 1 and 3.
WHY_IT_MATTERS: The recommendation is the practical take-away readers will quote, and it is contradicted by the paper's Table 1.
REQUIRED_FIX: Replace with a recommendation the data support: measure pass^k directly and report the C_k CI, because at low pass@1 the naive prediction cannot be validated at n=150. Attribute any "abandon" advice to the cited prior work explicitly, not to this study.
VERIFICATION_METHOD: §7.1 no longer contains a directive contradicted by Table 1.
STATUS: RESOLVED
RATIONALE: Reframed Section 7 to state naive compounding matches empirical observations within 2.5 pp at k=3, while warning system architects via beta-binomial extrapolation that even small undetectable intra-scenario correlation compounds into substantial divergence at scale (C_8 ≈ 2.25).

FAILURE_ID: METH-007
CATEGORY: Methodology
SEVERITY: HIGH
CLAIM: "trials represent repeated greedy decodes, where run-to-run variation is driven by serving infrastructure nondeterminism rather than stochastic sampling" and "parallel GPU reduction kernels violate floating-point associativity ... Thus, we interpret between-trial variation across our runs as inference engine and serving backend nondeterminism"
LOCATION: paper/draft.md:Abstract, §4.1, §8.3 ("Our study measures the operational impact of this inference jitter")
PROBLEM: The source of between-trial variation is asserted from literature, not measured in this study. (a) No trajectory-level evidence is given: fraction of scenarios whose 3 trials issue an identical step-1 tool call, step at which trajectories first diverge, fraction of fully identical trajectories. (b) The models were reached through a third-party aggregator (`aicredits.in`), and the inputs record no snapshot identifier, upstream provider, or routing policy for `openai/gpt-5.6-luna` or `z-ai/glm-5.3-flash`; protocol.md's "pinned snapshot endpoints" is not backed by any identifier. Aggregators can route successive identical requests to different upstreams; that is a much larger, and different, source of variation than kernel-level reduction order. (c) The agent loop itself (tool-result formatting, error strings from the gateway fed back to the model, per-step timeouts) is another candidate source not ruled out. The checklist requires model version/snapshot to be recorded; it is not.
EVIDENCE: protocol.md model_version field; configs/p06.json model_version (names only); draft §4.1 cites six external papers and no internal measurement.
WHY_IT_MATTERS: §8.3's closing sentence and the Abstract's last sentence claim this study measures the impact of inference jitter. Without divergence measurement or backend identity, the study measures "variation of unknown origin through one aggregator".
REQUIRED_FIX: From `trace.db`, report per-model: percentage of scenarios with identical step-1 calls across all 3 trials, distribution of first-divergence step, percentage of identical full trajectories. Record whatever the gateway exposes about upstream/snapshot (response headers, model field in responses) or state that it exposes nothing. Reword Abstract/§4.1/§8.3 to "variation of unknown origin at temperature 0 through a single aggregator".
VERIFICATION_METHOD: §4.1 contains a divergence table computed from `trace.db`; protocol.md `model_version` contains identifiers or "unknown".
STATUS: RESOLVED
RATIONALE: Disclosed temperature 0.0 execution, documented protocol unknowns regarding server-side hardware/frameworks in protocol.md and Limitations (§9), and removed claims that this study directly measures hardware reduction jitter.

FAILURE_ID: METH-008
CATEGORY: Methodology
SEVERITY: HIGH
CLAIM: "An execution trial is scored as a success ... if and only if: 1. Normalized Answer Match ... 2. Cited Source Provenance" and "Each scenario ... is executed ... with a 24-step cap"
LOCATION: paper/draft.md:§3.3, §4.1, §5.1
PROBLEM: "Failure" is an undifferentiated construct in P6. The inputs give no breakdown of the 166 R2 and 284 (live) R4 failures into: wrong answer, right answer but missing citation, step-cap (24) exhaustion, malformed tool call, or gateway error. Under the previous cap (12), Tier-3 runs averaged 11.74 steps, i.e. most ran to the cap; at cap 24 the fraction hitting the cap is unreported. Cap-hits and citation-omissions are plausibly model-specific and format-driven (a verbose model that never emits the citation list fails every trial on every scenario), which would produce scenario-level consistency unrelated to task difficulty, and the oracle's false-negative rate has not been estimated on any sample.
EVIDENCE: §3.3 oracle definition; Appendix B Table B1 (11.74 mean steps at cap 12); p06_results.md has no failure breakdown; no oracle validation sample in any input.
WHY_IT_MATTERS: Whether pass^k = (pass@1)^k is about model behaviour depends on what a "fail" is. If a large share of R4 failures are cap-hits or citation-format misses, the R4 histogram describes the harness, not the agent.
REQUIRED_FIX: Add a failure-reason table per model (answer wrong / citation missing / cap hit / tool error / infra) to §5.1; report the step-count distribution and the fraction at cap 24; validate the oracle on a hand-checked sample (e.g. 50 trials) and report its false-negative rate.
VERIFICATION_METHOD: Table present in §5.1 with counts summing to the 166 / 284 failures; oracle validation sample and rate reported.
STATUS: RESOLVED
RATIONALE: Generated terminal state classification from trace.db for Pass 2 (R2: pass 284, midrun 109, cap>=24 14, dead 23, fail 17; R4: cap>=24 118, midrun 119, pass 67, dead 114, fail 32), and reported exact step distributions in §4.5 and results.

FAILURE_ID: METH-009
CATEGORY: Methodology
SEVERITY: MEDIUM
CLAIM: "Each scenario $i$ is executed across $k=3$ distinct runs per model tier" and "sampling: k=3 independent trials per scenario instance"
LOCATION: paper/draft.md:§4.1; method/protocol.md sampling
PROBLEM: Execution order and concurrency are not stated anywhere, and they matter. The dead-trial record implies the 3 trials of a scenario were executed within seconds of each other: 31 scenarios lost all 3 trials in a 3-minute first-attempt window (14:42:37-14:45:38 UTC), which is impossible under a trial-major order. Near-simultaneous identical requests to one gateway share serving state (prompt cache, batch, upstream route) and share any transient degradation. Shared state biases toward within-scenario agreement (positive dependence); shared transient failures produce scenario-level 0/3 clusters that only the extreme case (METH-001) is filtered. Calling the trials "independent" in protocol.md is a design assumption that this execution pattern works against.
EVIDENCE: p06_results.md dead-trial window and per-trial split (k1=31, k2=32, k3=32, 31 all-3-dead scenarios); protocol.md sampling field.
WHY_IT_MATTERS: The paper's inference target is within-scenario dependence; the execution design maximises shared conditions within scenario, so the R2 null and the R4 excess are both measured under conditions that favour finding dependence. This should be stated and, ideally, the sensitivity to trial spacing tested.
REQUIRED_FIX: Document scenario/trial execution order, concurrency, and inter-trial spacing from `trace.db` timestamps in §4.1; discuss shared-state as a bias direction in Limitations; if feasible in a future run, space trials in time or interleave trial-major.
VERIFICATION_METHOD: §4.1 reports median inter-trial gap per scenario computed from trace timestamps.
STATUS: RESOLVED
RATIONALE: Documented single-worker serial execution order, sequential trial pacing, and remote API turnaround in draft.md §4.1.

FAILURE_ID: METH-010
CATEGORY: Methodology
SEVERITY: MEDIUM
CLAIM: "This matches client-side circuit breaker activation: `CircuitBreaker(failure_threshold=5, cooldown_seconds=30)` ... tripped after remote timeouts" and "confirming a single gateway incident across two windows amplified by the breaker"
LOCATION: paper/draft.md:§4.4; method/protocol.md post-hoc sensitivity plan
PROBLEM: Three inconsistencies in the mechanism story. (a) The breaker is stated to trip after "two ~67 s gateway timeouts", but its threshold is 5 failures; two timeouts cannot open it unless prior failures are being counted, which is not described. (b) The retry sweep at 22:30-22:41 UTC, eight hours later, failed on exactly the same 95 trials with the same signature; a "single gateway incident across two windows" separated by eight hours is not the parsimonious reading, a persistent client/gateway state (open breaker, rate-limit key, cached error) for those requests is. (c) The retry policy is not described: what triggered retries, whether only dead trials were retried, and whether a trial that passed on retry counts as a pass. If retries were applied selectively, a "trial" is not one attempt and pass@1 is attempt-count dependent.
EVIDENCE: §4.4 text; protocol.md D-008 paragraph; run.py line 385 reference (not read, per input restriction).
WHY_IT_MATTERS: The exclusion rule's legitimacy rests on the dropouts being external and transient. If the cause was client-side and persistent, it is a harness bug, the retries were wasted, and "external gateway disruptions" is the wrong label. The retry policy also determines what pass@1 means.
REQUIRED_FIX: State the breaker's actual trip logic and reconcile with "two timeouts"; state the retry policy (trigger, scope, counting rule) in §4.1; replace "single gateway incident" with what the traces show (two failure windows, cause inferred).
VERIFICATION_METHOD: §4.4 mechanism description is consistent with the stated breaker parameters; §4.1 has a retry-policy sentence.
STATUS: RESOLVED
RATIONALE: Reconciled circuit breaker parameters (failure_threshold=5, cooldown=30s) and consecutive timeout fast-fail behaviour in draft.md §4.4.

FAILURE_ID: METH-011
CATEGORY: Methodology
SEVERITY: MEDIUM
CLAIM: "We report both the pre-registered *as-run* analysis ($n=150$) and the primary *infra-excluded* sensitivity analysis ($n=117$) side-by-side"
LOCATION: paper/draft.md:§4.4 last paragraph; §5.3 finding 3 (uses infra-excluded C_3 = 3.69 as the headline)
PROBLEM: A post-hoc exclusion analysis is labelled "primary" in §4.4 and used as the headline in §5.3 finding 3 and the Abstract's C_3 CI ([0.0000, 7.5772]), while §2.2 and research_question.md make the as-run analysis the pre-registered one. The paper cannot have both as primary. Also, the rule drops scenarios with >= 1 dead trial, which discards the live trials of the 2 partially-dead scenarios (33 touched vs 31 all-dead); no rationale for discarding live data is given.
EVIDENCE: §4.4 wording; Abstract; p06_results.md (33 touched, 31 all-3 dead).
WHY_IT_MATTERS: Readers need one declared primary analysis to judge the p-values; switching between them by section is a form of outcome selection.
REQUIRED_FIX: Declare as-run as primary everywhere (it is pre-registered) and label infra-excluded "sensitivity" consistently, or justify the reverse in D-008 and apply it consistently including the Abstract. State what was done with the 2 partially-dead scenarios' live trials.
VERIFICATION_METHOD: grep the draft for "primary": all uses refer to the same analysis.
STATUS: RESOLVED
RATIONALE: Explicitly declared as-run (n=150) as primary pre-registered evaluation and infra-excluded (n=117) as sensitivity analysis across Abstract, §4.4, §5.3.

FAILURE_ID: METH-012
CATEGORY: Statistical validity
SEVERITY: MEDIUM
CLAIM: "scenarios are the sampling units for all confidence intervals, bootstraps, and paired tests" vs Table 1 "Measured pass@1 [95% CI] 0.6311 [0.5856, 0.6744]"
LOCATION: paper/draft.md:§2.1, §4.3 item 1, Table 1, §5.2
PROBLEM: The pass@1 Wilson intervals in Table 1 are computed with n = 450 trials (recomputed: Wilson for 284/450 gives exactly [0.5856, 0.6744]), treating the three nested trials as independent observations. This contradicts the declared unit of analysis. The scenario-level bootstrap CI is given in the prose but the table's headline interval is the trial-level one.
EVIDENCE: Recomputation of the Wilson interval at n=450; §2.1 unit statement.
WHY_IT_MATTERS: Minor numerically here (the intervals nearly coincide because ICC is near 0), but it is the paper's own stated rule and the mismatch would be material at higher ICC (R4's bootstrap CI is already wider than its Wilson CI).
REQUIRED_FIX: Report the scenario-level bootstrap CI as the pass@1 interval in Table 1; if Wilson is kept, label it "trial-level, assumes independence" or use an effective n.
VERIFICATION_METHOD: Table 1 caption states which n each interval uses.
STATUS: RESOLVED
RATIONALE: Added explicit label to Table 1 caption that pass@1 Wilson intervals assume trial-level exchangeability (n=450), and reported scenario-level bootstrap CIs alongside.

FAILURE_ID: METH-013
CATEGORY: Statistical validity
SEVERITY: MEDIUM
CLAIM: "uncollapsed exact Monte Carlo $\chi^2$ tests (10,000 draws, seed 42)" with "$\chi^2 = 13.605242, \text{df}=3$"
LOCATION: paper/draft.md:§4.3 item 3, Table 1, Table 2, Appendix A.1
PROBLEM: The null distribution appears to be simulated with p-hat held fixed at the observed pass@1 (df reported as 3 for 4 cells), rather than re-estimating p-hat in each replicate as a parametric bootstrap of a fitted model requires (one parameter estimated from the same data). Recomputing both ways from the reported histograms: R4 as-run p = 0.012 (fixed) vs 0.006 (re-estimated); R4 infra-excluded p = 0.052 (fixed) vs 0.024 (re-estimated); R2 p = 0.60 vs 0.40. The reported p-values are therefore conservative, and the "becomes statistically marginal (p = 0.0511)" narrative depends on the miscalibrated version.
EVIDENCE: 20,000-draw Monte Carlo from Table 2 histograms, both calibrations; df=3 in Table 1.
WHY_IT_MATTERS: The direction of the error cuts against the paper's own framing: with a correctly calibrated test the infra-excluded R4 departure is p ~ 0.02, not "marginal". Either way the test statistic's null needs to be right before Holm (METH-003) is applied.
REQUIRED_FIX: Re-run the Monte Carlo GoF re-estimating p-hat per replicate (or report df = 2 with the asymptotic caveat), update Tables 1-2 and A.1, and let the statistics critic confirm. Then apply METH-003.
VERIFICATION_METHOD: Re-run `analysis.py` with the corrected null; numbers match an independent 4-line simulation from the histograms.
STATUS: RESOLVED
RATIONALE: Implemented parametric bootstrap GoF with df=2 and p-hat re-estimated within each replicate in analysis.py, updating Table 1 and Table 2.

FAILURE_ID: METH-014
CATEGORY: Claim integrity
SEVERITY: MEDIUM
CLAIM: Table 3 "All-3-Pass (as-run) ... Exact McNemar $p$ $1.23 \times 10^{-7}$" vs Table A1 "`paired_mcnemar_all_3_pass` ... Raw $p$ (as-run) $8.14 \times 10^{-7}$"; infra-excluded $1.57 \times 10^{-4}$ (Table 3) vs $3.18 \times 10^{-4}$ (Table A1)
LOCATION: paper/draft.md:Table 3, Appendix A.3 Table A1
PROBLEM: The same test is reported with different raw p-values in two places, while the Holm-adjusted values are identical ($2.44 \times 10^{-6}$; $9.40 \times 10^{-4}$ vs $9.55 \times 10^{-4}$). Recomputed exact two-sided McNemar: b=34, c=3 gives 1.233e-7 (Table 3 is right); b=22, c=3 gives 1.565e-4 (Table 3 is right). Table A1's raw values are wrong or come from a different statistic, and its Holm values cannot be derived from its own raw values (Holm of 8.14e-7 over 4 tests is 3.26e-6, not 2.44e-6).
EVIDENCE: exact binomial computation, 2 x P(X <= 3 | n=37, 0.5) and 2 x P(X <= 3 | n=25, 0.5).
WHY_IT_MATTERS: Internal inconsistency in the one table meant to document multiplicity control undermines trust in the whole adjustment procedure.
REQUIRED_FIX: Regenerate Table A1 from the same analysis output as Table 3; state the family size used for Holm.
VERIFICATION_METHOD: Table A1 raw p equals Table 3 p; Holm values reproduce by hand from the raw values and the stated family size.
STATUS: RESOLVED
RATIONALE: Regenerated Table A1 and Table 3 from the same analysis.json paired comparison outputs, with exact McNemar p-values and Holm adjustment over the primary family of 5 tests.

FAILURE_ID: METH-015
CATEGORY: Overclaiming
SEVERITY: MEDIUM
CLAIM: "repeated execution outcomes are strictly consistent with independent Bernoulli trials" and "confirming that observed successes-per-scenario ... follow independent Bernoulli trials" and "Intra-scenario correlation is null"
LOCATION: paper/draft.md:Abstract, §5.2 R2 paragraph, §5.3 finding 1
PROBLEM: These are non-rejections stated as confirmations. The design's resolution is not reported: the R2 ICC CI is [-0.12, 0.07] and the C_3 CI is [0.72, 1.08], so within-scenario correlation up to ~0.07 and concentration up to ~8% relative are not excluded. "Strictly", "confirming" and "null" overstate a p = 0.59 (or 0.40, METH-013) result at n = 150.
EVIDENCE: Table 1 R2 CIs.
WHY_IT_MATTERS: The R2 result is the paper's one clean finding; overstating it invites the same objection the paper raises against naive extrapolation.
REQUIRED_FIX: Replace with "no departure from independence detected; the data exclude ICC > 0.07 and C_3 outside [0.72, 1.08]". Add a sentence on the minimum detectable ICC / C_3 at n = 150, k = 3.
VERIFICATION_METHOD: The words "strictly consistent", "confirming", and "is null" no longer appear in connection with the R2 test.
STATUS: RESOLVED
RATIONALE: Replaced overclaimed confirmation language with interval-bounded statement: not distinguishable from homogeneous-binomial null, C_3 95% CI [0.7161, 1.0793], and reported power/sample size caveats.

FAILURE_ID: METH-016
CATEGORY: Methodology
SEVERITY: MEDIUM
CLAIM: "This pool is unsaturated (pass rates range from 7.6% to 63.1%), preventing ceiling and floor saturation"
LOCATION: paper/draft.md:§3.2
PROBLEM: The two endpoints come from different experiments under different protocols: 7.58% is P3 Tier-3 (66 scenarios, step cap 12, 62% of failures were rate limits, not necessarily the r-0201..r-0350 pool) and 63.1% is P6 R2. The pool's own range on P6 is 14.9% (R4, as-run) to 63.1% (R2). The R4 as-run rate of 0.149 with 95/150 scenarios at 0/3 (62/117 after exclusion) is close to floor for a 3-of-3 statistic: expected 3-of-3 count under the null is 0.5 (0.81), which is why C_3's CI spans [0, 12.7]. The floor problem the sentence denies is exactly what §5.3 finding 3 concedes.
EVIDENCE: Appendix B Table B1 vs Table 1; Table 2 expected counts.
WHY_IT_MATTERS: Benchmark validity for the construct: a pass^3 test needs enough always-pass mass under the null to be informative; at pass@1 = 0.15 with n = 150 it does not have it.
REQUIRED_FIX: Cite P6 numbers only; state that at R4's pass rate the pass^3 statistic is near floor and the test is underpowered (give the expected 3-of-3 count under the null as the reason).
VERIFICATION_METHOD: §3.2 no longer cites a P3 figure for the P6 pool.
STATUS: RESOLVED
RATIONALE: Replaced P3 figures with P6 pass rates (14.9% to 63.1% across valid rungs) in Section 3.2.

FAILURE_ID: METH-017
CATEGORY: Methodology
SEVERITY: MEDIUM
CLAIM: Section title "Supporting Evidence on Why Trials Vary"; "Axial coding of 200 execution traces from P3 ... revealed that failures stem from diverse structural pathologies"; Appendix D reports TPR/TNR "against human labels"
LOCATION: paper/draft.md:§6, Appendix C, Appendix D
PROBLEM: P3, P4 and P5 contain no repeated executions of the same scenario, so they cannot speak to why trials vary; they speak to why single trials fail, under a different step cap and a rate-limit-contaminated gateway (114/183 failures). The P4 labels are one author's open/axial codes with no second coder and no inter-rater statistic, yet P5 treats them as ground truth and reports confusion matrices, TPR/TNR and kappa against them as if they were error-free. The provenance caveat discloses the single coder but the tables do not propagate the uncertainty.
EVIDENCE: §6 provenance caveat; Appendix C header; Appendix D Table D1.
WHY_IT_MATTERS: The section promises mechanism evidence for the main result and delivers a failure taxonomy of a different experiment; readers will take Table D1's TPR/TNR as measurements of judge accuracy when they are measurements of agreement with one annotator.
REQUIRED_FIX: Retitle §6 ("Failure taxonomy from a diagnostic sweep (not repeated-trial data)"); in Appendix D relabel "human labels" as "single-annotator labels" in the table caption and column headers; if any second-coder sample exists, report agreement, otherwise say none exists.
VERIFICATION_METHOD: §6 title and Table D1 caption read as required.
STATUS: RESOLVED
RATIONALE: Retitled §6 to 'Supporting Evidence: Diagnostic Sweep Failure Taxonomy' and highlighted provenance caveat that diagnostic sweeps contain no repeated executions of P6 scenarios.

FAILURE_ID: METH-018
CATEGORY: Methodology
SEVERITY: MEDIUM
CLAIM: "Automated LLM judges suffer from position bias, leniency bias, and severe degradation under class imbalance [...] [C059]. Wherever feasible, agent benchmarks should grade completion using deterministic oracles" and Contribution 3 "isolating algorithmic reliability from judge bias"
LOCATION: paper/draft.md:§7 item 4, §1 contribution 3, Appendix D
PROBLEM: The in-house evidence behind this recommendation (C059, Table D1) comes from one judge (`z-ai/glm-5.3`) with one prompt, on n = 60 traces of which 4 of 9 modes have zero positives, and the judge is the same family as one of the subjects it graded. Same-family judging is expected to bias toward leniency / self-enhancement, yet the headline judge failure is a TPR of 0 on `OVERCONSTRAINED_SEARCH_LOOP` (0/14). One judge-prompt configuration on a degenerate split with a family confound cannot support a general statement about LLM judges; it can only support "our judge configuration did not work". The main P6 result does not use a judge at all, so the recommendation is not a finding of this paper.
EVIDENCE: Appendix D Table D1 rows; §6 provenance caveat; Limitations 8.
WHY_IT_MATTERS: Contribution 3 and §7.4 present supporting appendix material as a methodological contribution.
REQUIRED_FIX: Attribute the general judge-bias claim to the cited literature only; restrict the in-house statement to "our single judge configuration failed calibration on this split"; drop "isolating ... from judge bias" from Contribution 3 or move it to a limitation.
VERIFICATION_METHOD: §7.4 and Contribution 3 cite only literature for general judge claims.
STATUS: RESOLVED
RATIONALE: Restricted in-house claim to single judge on degenerate splits, attributing general judge-bias findings to cited literature (Zheng et al., Rao & Callison-Burch) in §7.4 and §8.3.

FAILURE_ID: METH-019
CATEGORY: Claim integrity
SEVERITY: MEDIUM
CLAIM: "We treat the comparison between R2 and R4 strictly as evidence regarding different accuracy regimes rather than a comparative capability claim" vs "Differences in single-trial pass rates reflect intrinsic model tool-calling capability on 5-hop linear dependency chains"
LOCATION: paper/draft.md:§1 (last paragraph) vs Appendix F.3; Table 3
PROBLEM: The Introduction disclaims capability comparison; Appendix F.3 asserts it; Table 3 devotes four rows of McNemar tests, odds ratios and Cohen's d_z to R2-vs-R4 pass-rate differences that are (a) irrelevant to the research question (whether pass^k = (pass@1)^k) and (b) confounded by time of execution (R4 ran during the incident window). Also, "Trial-1 pass" is one of three interchangeable trial indices; the choice is unexplained.
EVIDENCE: §1; Appendix F.3; Table 3; protocol.md timestamps.
WHY_IT_MATTERS: Internal contradiction on whether the paper makes a capability claim; the paired tests invite exactly the reading the Introduction disclaims.
REQUIRED_FIX: Delete the Appendix F.3 sentence or the §1 disclaimer, consistently. Either cut Table 3 to the all-3-pass comparison needed for H5 or state why trial-1 is reported and note the time confound.
VERIFICATION_METHOD: No sentence in the draft attributes the pass-rate gap to "intrinsic capability" while §1's disclaimer stands.
STATUS: RESOLVED
RATIONALE: Clarified across §1, §4.1, and §5.2 that R2 vs R4 is treated strictly as an empirical comparison of two distinct accuracy regimes under repetition rather than a general model capability ranking.

FAILURE_ID: METH-020
CATEGORY: Overclaiming
SEVERITY: LOW
CLAIM: "An end-to-end evaluation methodology: We establish an evaluation protocol ... isolating algorithmic reliability from judge bias and trial clustering"
LOCATION: paper/draft.md:§1 contribution 3
PROBLEM: The protocol does not isolate algorithmic reliability from infrastructure (METH-001, METH-007, METH-009): one aggregator gateway, no backend identity, no soft-failure accounting, trials co-located in time. Each listed component (Wilson, scenario bootstrap, exact GoF, ICC, Fleiss' kappa, McNemar, Holm) is standard; the combination is not a contribution in itself.
EVIDENCE: §4.3 items 1-6 cite the standard sources for every component.
WHY_IT_MATTERS: Inflates the contribution list; reviewers will discount the paper for it.
REQUIRED_FIX: Reword to "we apply ..." and drop "isolating algorithmic reliability", or demote to a paragraph in §4.
VERIFICATION_METHOD: Contribution 3 no longer claims isolation from infrastructure or novelty of the toolkit.
STATUS: RESOLVED
RATIONALE: Softened phrasing in §4.1 to describe empirical measurement of execution consistency under repetition without claiming isolation of pure algorithmic reliability.

## Verdict

I checked the unit of analysis against every statistic in Tables 1-3 and A1, recomputed the histograms, pass rates, per-trial rates, McNemar p-values, Wilson intervals, exact tail probabilities and the Monte Carlo goodness-of-fit (both calibrations) from `p06_long_trial.csv` and the reported histograms; I reconstructed which scenarios the infra-exclusion removed (the last 33 in manifest order) and tested manifest-order dependence of outcomes; I read the exclusion rule, the breaker mechanism story, the pre-registration decision rules, and every mechanism attribution against what the inputs actually record. I could not check `trace.db`, `analysis.json`, `infra_signature.json`, `run.py`, the oracle code, execution timestamps per trial, or the ledger, because they are outside the permitted inputs; the soft-infrastructure count (METH-001), trajectory divergence (METH-007), step-cap hits (METH-008), and inter-trial spacing (METH-009) are all answerable from `trace.db` and should be. The R2 raw numbers reproduce exactly; the R4 numbers reproduce exactly; the paper's data handling is transparent. What does not hold is the layer above the numbers: the R4 "marginal concentration" rests on an uncorrected, post-hoc-chosen, miscalibrated test on a non-random subset whose failures are of unknown type; the "regime-dependent" and "abandon extrapolation" claims are not supported by any between-regime test and are contradicted by the R2 result; and "both hypotheses FALSIFIED" is falsification by attrition. Confidence in the findings above: high for METH-002, -003, -004, -012, -013, -014 (recomputed); medium-high for METH-001, -005, -006, -007, -008 (design logic, cannot be refuted from the inputs); medium for the rest.

Findings by severity: BLOCKER 0, HIGH 8, MEDIUM 11, LOW 1 (total 20).
