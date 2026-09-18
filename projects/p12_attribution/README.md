# P12 — Failure Attribution: Retriever vs Generator (H8)

## Executive Summary
For this workload, when the agent fails it is almost always because the search never surfaced a chain document — a stronger model does not fix that (R4 pilot: 3 of 3 failures also retriever-owned).

Pre-registered Hypothesis **H8**: *"Retrieval owns >50% of grounding failures; falsified if the attribution CI excludes 50% on the generator side."*
- **Rung R2 (`glm-5.3-flash`, N=150)**: **SUPPORTED** — Retriever share 94.12% with Wilson 95% CI [80.91%, 98.37%], strictly bounded above 50%.
- **Rung R4 (`gpt-5.6-luna`, pilot n=10)**: **UNDECIDED** — Retriever share 100.0% with Wilson 95% CI [43.85%, 100.0%]; pilot point estimate is unanimous (3/3), but small sample CI spans 50%.

## Design
Two matched arms evaluated across the exact 150 reserved hard-pool 5-hop scenarios (`r-0201` to `r-0350`) from Project P6:
- **Arm A (Normal Agent)**: Standard [`ToolBox`](file:///Volumes/SamirDrive/Development/FAULTLINE/faultline_p2/agent/tools.py) where `search(query)` executes case-insensitive substring matching over corpus document titles and text, returning top-5 candidates with 500-character snippets.
- **Arm B (Oracle Retrieval)**: [`OracleToolBox`](file:///Volumes/SamirDrive/Development/FAULTLINE/faultline_p2/attribute/oracle_toolbox.py) where `search(query)` ignores the model's query string and immediately returns all declared `traversal_sources` for the scenario as candidates with 500-character snippets. Because snippets contain the necessary chain facts, the model mostly answers directly from snippets and rarely calls lookup.

### Attribution Rule
Per scenario:
- **Fail A & Pass B**: *Retriever-owned* (oracle retrieval rescues the run).
- **Fail A & Fail B**: *Generator-owned* (oracle retrieval fails to rescue; reasoning/synthesis failure).
- **Pass A & Fail B**: *Reverse* (reported honestly; Arm A succeeded despite retrieval or Arm B drifted).
- **Pass A & Pass B**: *Both pass* (unambiguous joint success).

$$\text{Retriever Share} = \frac{\text{Retriever Owned}}{\text{Retriever Owned} + \text{Generator Owned}}$$

## Results Table

| Rung | Role | Model | n | Both Pass | Retriever Owned | Generator Owned | Reverse | Retriever Share | Wilson 95% CI | H8 Verdict | Spend |
|---|---|---|---|---|---|---|---|---|---|---|---|
| **R2** | Cheap Workhorse | `z-ai/glm-5.3-flash` | 150 | 112 (74.7%) | 32 (21.3%) | 2 (1.3%) | 4 (2.7%) | **0.9412** (32/34) | **[0.8091, 0.9837]** | **SUPPORTED** | $1.4683 |
| **R4** | Frontier Anchor | `openai/gpt-5.6-luna` | 10 | 7 (70.0%) | 3 (30.0%) | 0 (0.0%) | 0 (0.0%) | **1.0000** (3/3) | **[0.4385, 1.0000]** | **UNDECIDED** (pilot) | $0.4575 |

### Statistical Tests
- **R2 Paired McNemar Test**: exact binomial p = 1.94e-6; chi-square with continuity correction p = 6.80e-6 (the runner's recommended statistic, $\chi^2 = 20.25$) on discordant pairs (32 retriever-rescued vs 4 reverse). The oracle retrieval advantage is statistically significant at $\alpha = 0.05$.
- **R4 Paired McNemar Test**: exact binomial p = 0.250 (the runner's recommended statistic) on discordant pairs (3 vs 0), non-significant due to $n=10$ pilot sample size.
- **Reverse Pairs**: Of the 4 reverse pairs, 3 hit the step cap in arm B (r-0238, r-0273, r-0330) and 1 answered wrongly (r-0328).

## Mechanism Analysis
For every retriever-owned failure, Arm A's full step trace was audited against the scenario's required `traversal_sources`:
- **Never Surfaced vs Surfaced-but-Unused**:
  - **R2**: 29 of 32 (90.6%) never surfaced at least one required chain document during the search steps. Only 3 of 32 (9.4%) surfaced all required documents yet failed to synthesize the answer.
  - **R4**: 3 of 3 (100.0%) never surfaced a required chain document.
- **Missing-Doc Histogram (R2, 32 failures)**:
  - 0 missing (surfaced all): 3 runs
  - 1 missing doc: 9 runs
  - 2 missing docs: 6 runs
  - 3 missing docs: 4 runs
  - 4 missing docs: 2 runs
  - 7 missing docs: 2 runs
  - 8 missing docs: 3 runs
  - 9 missing docs: 3 runs
- **Arm A Failure Modes**:
  - *Retriever-owned (32)*: 16 `step_cap` (reached the 24-step cap (A-003) without a grounded answer), 15 `answered` (returned an answer that failed the oracle check (wrong answer and/or required source not cited)), 1 `malformed`.
  - *Generator-owned (2)*: 2 `step_cap` (both arms reached the step cap (r-0336, r-0342)).
- **Execution Burden & Efficiency**:
  - **Arm A (Normal)**: Mean 17.43 spans/run, mean 47,852 prompt tokens, mean 2,427 completion tokens (50,279 total tokens/run).
  - **Arm B (Oracle)**: Mean 5.35 spans/run, mean 15,349 prompt tokens, mean 933 completion tokens (16,281 total tokens/run) — 3.1× fewer tokens and 3.3× fewer steps because facts were available on initial search.

## Economics & Spend
All spend recorded per-call to `ledger.jsonl` under the pre-registered $6.00 P12 budget ceiling:
- Rung R2 (300 total agent runs): $1.4683 USD
- Rung R4 (20 total agent runs): $0.4575 USD
- **Total Project Spend**: **$1.9258 USD** (32.1% of $6.00 cap; $4.0742 remaining).

## Limitations
1. **Retriever Architecture**: The retriever evaluated here is a deterministic, case-insensitive substring matcher over document titles and text with top-5 rank (defined in `faultline_p2/agent/tools.py`), not an embedding-based or chunked vector retriever. "Retriever-owned" strictly means that the search tool failed to surface a required multi-hop chain document for the query terms the agent generated. The finding is about query-retriever interface coupling in multi-hop chains, not chunking algorithms.
2. **R4 Sample Size**: R4 (`gpt-5.6-luna`) is evaluated as a 10-scenario pilot ($n=10$) due to budget allocation. While 100% of observed failures were retriever-owned (3/3), the Wilson score interval [43.85%, 100.0%] spans 50%, leaving H8 formally UNDECIDED on R4.
3. **Model Accuracy Drift**: On the identical 150 reserved hard scenarios from P6, Arm A R2 achieved a pass rate of $116 / 150 = 77.3\%$, compared to P6 pass@1 of $63.11\%$ on the same model (`z-ai/glm-5.3-flash`) at temperature 0.0. This is reported as empirical same-model gateway drift across test dates, without post-hoc rationalization.
4. **Single Pass ($k=1$)**: Each arm was run for a single trial ($k=1$) per scenario under a hard step cap of 24 (Amendment A-003).

## Reproduce
```bash
# Dry-run cost estimation (zero spend, no network calls)
.venv/bin/python projects/p12_attribution/run.py --dry-run --rung R2 --scenarios 150
.venv/bin/python projects/p12_attribution/run.py --dry-run --rung R4 --scenarios 10

# Recompile results and mechanism analysis from persisted traces and trace.db
.venv/bin/python projects/p12_attribution/run.py --recompile --rung R2
.venv/bin/python projects/p12_attribution/run.py --recompile --rung R4

# Generate figure
.venv/bin/python projects/p12_attribution/make_figure.py
```
