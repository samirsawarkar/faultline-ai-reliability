# Decisions — Project P12: Failure Attribution

### D1: Scope and Cost Correction
- **Decision**: Evaluated 150 matched scenarios on Rung R2 (`glm-5.3-flash`) and a 10-scenario pilot on Rung R4 (`gpt-5.6-luna`).
- **Why**: Initial task planning informally estimated $1.35 USD total spend. Updating the dry-run estimator with P6-measured token counts (59k in / 3.4k out for R2, 55k in / 2.9k out for R4) revealed a theoretical ceiling estimate of $2.78 (R2) + $0.80 (R4) = $3.58 USD. Actual live spend came in at $1.4683 (R2) + $0.4575 (R4) = $1.9258 USD total, comfortably within the pre-registered $6.00 project budget cap.
- **What was rejected**: Running R4 across all 150 scenarios, which would have risked breaching the project cap ($0.60/in, $2.40/out pricing).

### D2: Oracle Arm Definition
- **Decision**: Arm B is implemented via `OracleToolBox(ToolBox)`, intercepting `search(query)` to return the scenario's declared `traversal_sources` directly with 500-character snippets at score 3.0, regardless of the model's query string.
- **Why**: Perfectly isolates retrieval quality from reasoning/generation. With all chain documents surfaced upfront in search candidates, the agent rarely needs `lookup` and answers directly from candidate snippets.
- **What was rejected**: Providing answers directly or bypassing the agent loop; the agent still executes full tool dispatch, prompt parsing, and answer formation.

### D3: Attribution Rule Including Reverse Cell
- **Decision**: Grounding failures are classified into four mutually exclusive quadrants per matched scenario:
  - Fail A & Pass B = *Retriever-owned*
  - Fail A & Fail B = *Generator-owned*
  - Pass A & Fail B = *Reverse*
  - Pass A & Pass B = *Both pass*
  Retriever share is calculated strictly as $\text{Retriever Owned} / (\text{Retriever Owned} + \text{Generator Owned})$. The 4 reverse cases on R2 are reported transparently.
- **Why**: H8 tests whether failure to ground originates primarily from the retrieval interface rather than the model's reasoning capabilities. Hiding or dropping the reverse cell would bias the attribution estimator.
- **What was rejected**: Re-attributing reverse trials to generator failure or dropping discordant pairs from reporting.

### D4: Per-Rung Artifact Partitioning
- **Decision**: Outputs are partitioned by rung as `manifest_{rung}.json` and `results_{rung}.json`, while `sweep_output_{rung}_{arm}.json` isolates traces by rung and arm. `trace.db` and `ledger.jsonl` remain unified project stores.
- **Why**: Running sequential rungs (R2 with 150 scenarios, R4 with 10) in the same directory previously caused the second rung's manifest and results to overwrite the first.
- **What was rejected**: Creating nested subdirectories that break uniform Phase 2 project structure.

### D5: Measured Tokens for Estimates
- **Decision**: Configured `RUNG_CONFIG` with empirical P6-measured final-pass token averages from `projects/p06_passk/results.json`: R2 at 59,452 in / 3,364 out; R4 at 55,002 in / 2,891 out, scaled by `step_cap / 24`.
- **Why**: The initial guess of 35,000/2,000 underestimated multi-hop token accumulation by 40%, distorting dry-run budget estimates.
- **What was rejected**: Uncalibrated hardcoded estimates.

### D6: R4 Designated as Labelled Pilot
- **Decision**: Rung R4 is explicitly labelled in all tables, results, and figures as `pilot, n=10`.
- **Why**: While 3 of 3 failures on R4 were retriever-owned (100.0% share), the 95% Wilson confidence interval [43.85%, 100.0%] spans the 50% boundary due to small sample size. Pre-registered H8 resolution rules mandate a verdict of **UNDECIDED**.
- **What was rejected**: Claiming H8 support on R4 based on the point estimate alone.

### D7: Precise Definition of 'Retriever'
- **Decision**: Documented in the README that the retriever in this evaluation is the Phase 2 substring title/text matching tool defined in `faultline_p2/agent/tools.py`.
- **Why**: "Retriever-owned" failure means the agent's generated queries failed to match entity keywords or content-addressed link titles in the top-5 candidate pool. It represents query-retrieval coupling failure in multi-hop chains, not semantic chunking failure or vector index degradation.
- **What was rejected**: Generalizing attribution results to dense embedding or hybrid BM25 retrieval without qualification.
