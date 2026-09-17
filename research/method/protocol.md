# Experimental protocol

Fill every field with the value actually used. "Unknown" is acceptable and must then appear in Limitations.

**dataset:** FAULTLINE Phase 2 synthetic pseudoword graph corpus (`build_corpus(42)`, content hash `84e6ff590704aa94d10912f8002716b14c7436080e1a3270b53f9385dc728efc`)
**data_split:** 150 reserved hard Tier-3 5-hop scenarios (`r-0201` to `r-0350`, manifest sha256 `7e0a1b79d6e756f712d27e29168fed8b3bc5c4cd7beba7f8fc21d50366d41b83`)
**model:** R2 `z-ai/glm-5.3-flash`, R4 `openai/gpt-5.6-luna`, R6 `deepseek/deepseek-v4-pro` (invalidated: 100% step-1 failure from gateway incident amplified by client circuit breaker; 869/900 spans < 1 ms, 12 timeouts > 60 s; breaker trip is inferred from latency signatures)
**model_version:** Pinned snapshot endpoints served via AI Credits gateway (`https://aicredits.in/v1`); specific underlying model snapshot strings and upstream provider routing Unknown
**prompt:** `faultline_p2/agent/prompt.py` (system prompt hash sha256 `87c7641e74964dcfe00c605051d7f5ddfade01f4019c95a00fd5dc3f1907c8df`, frozen in A-001)
**decoding:** temperature 0.0, top_p null, max_tokens 2048 (`faultline_p2/agent/model.py`)
**sampling:** k=3 independent trials per scenario instance
**seed:** master seed 42
**n_instances:** 150 scenarios (450 runs per model, 1350 runs total)
**metric:** pass^k (all-k-pass) and pass@1 under deterministic dual-condition oracle grading
**eval_protocol:** deterministic oracle (`faultline_p2/oracle/oracle_check`); requires normalized answer token match AND citation of ground-truth source document ID; step cap 24 (amendment A-003, MEC v1.3); no LLM judge in evaluation loop
**contamination_check:** synthetic 300-entity pseudoword graph generated with master seed 42; no real-world web data
**hardware:** Apple Silicon Mac client; inference executed across remote cloud providers via AI Credits gateway (exact physical GPU architectures, serving frameworks like vLLM/TensorRT-LLM, server CUDA driver versions, and instantaneous batch concurrency levels Unknown)
**environment:** Python 3.11, LiteLLM 1.98.0 pinned, sqlite3 trace store (`faultline_p2/trace/store.py`), Pydantic v2 (2.13.4), pure stdlib statistical analysis (seed 42, math)
**code_url:** https://github.com/samirsawarkar/faultline-ai-reliability
**timestamp:** 2026-09-11T12:15:51Z to 2026-09-11T22:42:16Z
**runtime / cost:** ~10.5 hours sweep wall-clock time; $23.4693 USD cumulative spend across 1,800 runs ($23.0719 final pass, $0.3974 discarded pass 1)

## Statistical analysis plan (written BEFORE looking at results; corrected 2026-09-16 after independent statistical review)
- Unit of analysis: the scenario instance (n=150); trials (k=3) nested within scenarios
- Pairing key: `scenario_id`
- Primary comparison: empirical pass^k vs naive independence compounding $(pass@1)^k$; paired model comparison R2 vs R4 via McNemar test
- Test (corrected 2026-09-16 per STAT-005, STAT-011, METH-013): Pearson chi-square goodness-of-fit against Binomial(3, pass@1) using asymptotic df = 2 (4 cells − 1 − 1 fitted parameter) and parametric bootstrap Monte Carlo (10,000 draws, seed 42) where pass@1* and expected counts are re-estimated inside each replicate; exact one-sided binomial upper-tail test on always-pass count (3-of-3); legacy fixed-p Monte Carlo and collapsed tests preserved under legacy keys
- Overdispersion score test (added 2026-09-16 per R2-001, R2-004): Tarone (1979) C(alpha) score test for binomial goodness-of-fit against beta-binomial overdispersion with analytic z statistic and one-sided p-value
- Beta-binomial compounding extrapolation (added 2026-09-16 per R2-003): analytical extrapolation across $k \in \{1 \dots 10\}$ evaluated at point estimate and ICC upper confidence bound with bootstrap CIs
- Paired comparison (corrected 2026-09-16 per STAT-003, STAT-004): exact two-sided binomial McNemar test as primary, continuity-corrected chi-square as secondary; paired Cohen's d_z from identical 0/1 vectors (mean difference / sample SD, ddof=1); ties count; scenario-level percentile bootstrap (10,000 resamples, seed 42) for risk difference; matched-pairs log-normal odds ratio CI
- Multiple-comparison correction (corrected 2026-09-16 per STAT-002, METH-003): Holm-Bonferroni step-down adjustment over the declared primary family of reported tests (R2 GoF parametric bootstrap, R4 GoF as-run parametric bootstrap, R4 GoF infra-excluded parametric bootstrap, R2-vs-R4 all-3-pass exact McNemar, R2-vs-R4 trial-1 exact McNemar); exact floats preserved without underflow to 0.0 ('<1e-15' on underflow); collapsed tests excluded from primary family
- Minimum effect of interest: 10 percentage points (declared power threshold per MEC v1.0 §5)
- Order effects check (added 2026-09-16 per METH-002): Spearman rho and Pearson r between manifest position and per-scenario success count with 10,000 seeded permutations; first vs second half comparison
- Attempt segmentation & terminal-state classification (added 2026-09-16 per D-010, METH-001, METH-008): chronological segmentation into Pass 1 (cap 12) and Pass 2 (cap 24); all span-level metrics, tokens, costs, and terminal-state classifications evaluated on Pass 2 final pass; classifications partitioned via latest span at run max step_index into answered_pass, answered_fail, step_cap (>=24), dead_at_start, midrun_no_completion, and other, with latency signatures (<1 ms / >60 s / other) for no-completion classes

## Post-hoc sensitivity analysis plan (registered 2026-09-16, Decision D-008; refined after independent review)
- **Motivation:** In run `p06_r4_7e0a1b79`, 95 of 450 trials dropped out across two distinct windows (first attempt 14:42:37–14:45:38 UTC, retry sweep 22:30–22:41 UTC), each with two step-1 spans having completion_tokens=0. 93 of 95 first attempts showed latency < 1 ms following two ~67 s gateway timeouts, consistent with the client-side circuit breaker (`CircuitBreaker(failure_threshold=5, cooldown_seconds=30)`) opening and fast-failing calls client-side (an inference from latency signatures, as traces do not record exception text). This artificially inflated the 0/3 failure cell across 33 touched base scenarios (31 completely dead). R6 (started 14:47:33 UTC) exhibited the same signature (869/900 spans < 1 ms, 12 timeouts > 60 s), confirming a single gateway incident across two windows amplified by the breaker; R6 lost every run, R4 its final 95.
- **Exclusion rules and variants:**
  1. *as_run* (pre-registered baseline, n=150 scenarios, 450 trials).
  2. *infra_excluded* (drops scenarios with >= 1 dead_at_start trial; R2 n=150, R4 n=117 scenarios). Retained R4 scenarios are 115 of the first 117 plus r-0318 and r-0319 (dead scenarios are r-0305 k3, r-0310 k2, and r-0320..r-0350 all).
  3. *infra_excluded_strict* (added 2026-09-16 per METH-001: drops scenarios with >= 1 dead_at_start OR midrun_no_completion trial in Pass 2; R2 n=49, R4 n=24 scenarios, paired n=14 scenarios).
- **Transparency:** Retained scenario IDs are explicitly recorded in `analysis.json` for every variant.

## Supporting experiments P3/P4/P5
- **Provenance caveat:** P3 was a DIAGNOSTIC sweep under MEC v1.2 (step cap 12, Amendment A-002), before A-003 raised the cap to 24 for P6; it was contaminated by gateway rate limits (see P4 INFRASTRUCTURE_RATE_LIMIT prevalence). P4 human open/axial coding was performed on P3 traces (n=200), by the single author. P5 judge calibration used judge z-ai/glm-5.3 on a frozen n=60 test split of P4-labelled traces; the judge is the same model family as rung R2 (confound: same-family judge and subject). None of P3/P4/P5 data is from the P6 runs the main result rests on. All P3/P4/P5 claims are marked as SUPPORTING (appendix-bound).
