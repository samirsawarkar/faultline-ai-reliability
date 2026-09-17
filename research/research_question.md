# Research question

**Question (one sentence, falsifiable):**
For LLM tool-use agents on a fixed set of 5-hop grounded-retrieval tasks, does the
joint reliability over k repeated executions equal the independence prediction
pass^k = (pass@1)^k, and if not, in which direction and by how much?

**Unit of analysis:** the scenario (task instance). 150 held-out Tier-3 scenarios
(`r-0201`..`r-0350`, manifest sha256 `7e0a1b79…`), each executed k=3 times per model.
Trials within a scenario are the repeated measurements; scenarios are the sampling units
for every CI, bootstrap, and paired test.

**Ground truth / how a correct answer is known:** deterministic dual-condition oracle —
normalised answer string equals the corpus answer AND the required source document id
appears in the agent's cited sources (`faultline_p2/oracle`, pinned by sha256 in MEC.md).
No LLM judge is in the success path.

**Baseline / comparison:** the independence prediction (pass@1)^k computed from the same
runs. Secondary: paired comparison of two models on identical scenarios (McNemar).

**Scope — in:** P6 data only (`projects/p06_passk/trace.db`, `ledger.jsonl`,
`analysis.json`, `results.json`); R2 `z-ai/glm-5.3-flash` and R4 `openai/gpt-5.6-luna`;
k ∈ {2,3}; scenario-level bootstrap; exact test of the successes-per-scenario
distribution against Binomial(3, pass@1); ICC; effect sizes; Holm over the tested family.
Mechanism evidence from P4 human trace coding (n=200) and P5 judge calibration (n=60),
presented as supporting, not as contributions.

**Scope — out:** R6 `deepseek/deepseek-v4-pro` for any capability claim — 900 spans /
450 runs / 0 verdicts = infrastructure failure at step 1; reported as invalid.
No new runs, no new models, no new environments ($0 constraint, CEO decision 2026-09-16).
No claim of generality beyond this environment / these two models / k ≤ 3.

**Constraints (time, data, compute, venue):** $0; existing data only; target arXiv +
GitHub, then MLSys 2027 (deadline 2026-10-30, ≤10 pages + appendices). Single author.

**What result would falsify the working hypothesis:** the working hypothesis (H4,
pre-registered) was pass^3 > (pass@1)^3 on ≥4 of 6 rungs. It is already FALSIFIED on the
data (1 of 2 valid rungs). The paper reports the falsification and the narrower observed
pattern: R2 consistent with independence (exact p=0.59, ICC −0.03); R4 excess of
always-pass scenarios (3 observed vs 0.50 expected, exact p≈0.012–0.014) with the ratio
C_3 unresolved (bootstrap CI [0.0, 12.7]).

## AI-reliability checklist (references/ai_reliability_checklist.md)
| Question | Answer |
|---|---|
| Unit of analysis | scenario; 150 per model; trials nested in scenarios |
| Ground truth | deterministic oracle (answer ∧ citation); no judge |
| Baseline | (pass@1)^k from the same runs; not a tuned method |
| Comparison | paired on identical scenario ids (R2 vs R4) |
| Leakage | corpus is coined pseudowords (contamination-resistant); prompts frozen (A-001); judge not in the loop |
| Confounds | **temperature 0.0, max_tokens 2048 for all runs** — between-trial variation is provider nondeterminism, not sampling; runs dated 2026-09 via one gateway (AI Credits); model snapshots as named by the gateway; step cap 24 (A-003) |
| Repeated measurements | resamples of the same 150 instances; NOT independent — hence scenario-level bootstrap and ICC |
| Metric | pass^k (all-k-pass), not pass@k (any-of-k); both defined in the paper |
| Benchmark | synthetic 300-entity graph, unsaturated at T3 (7.6–63%), label-clean by construction |
| Alternative explanations | provider nondeterminism; gateway rate-limits (P3 history); step-cap truncation; scenario difficulty heterogeneity — to be addressed in Limitations and by Reviewer #2 |
| Evidence vs strength | see research_decisions.md D-002 |

## Inclusion / exclusion criteria for sources
- Include: peer-reviewed or arXiv papers defining pass@k / pass^k; agent benchmarks
  reporting repeated-trial consistency; LLM-judge calibration; nondeterminism of LLM
  inference at temperature 0; statistics references actually used (Wilson, McNemar,
  Rogan–Gladen, ICC, bootstrap, Holm).
- Exclude: blog posts as evidence; anything not read (abstract or full text) before citing.
- Recency cutoff (if the field moves fast): none for statistics; 2021+ for pass@k and agents.

## Decision log pointer
Material changes to this question are recorded in `research_decisions.md`.
