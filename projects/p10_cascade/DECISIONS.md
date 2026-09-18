# Decisions — Project P10: Calibrated Cascade

### D1: Scope Adjustment (Option 2: 140 Planned → 90 Run, CEO Budget ₹400)
- **Decision**: Scaled R4 execution to 90 new scenarios (+ 10 previously completed in P12 = 100 total matched scenarios), rather than executing all 140 remaining hard-pool scenarios.
- **Why**: Running 140 scenarios was estimated at $5.59 USD (~₹465 INR). The CEO approved an active budget allocation of ₹400 (~$4.80 USD). Executing 90 scenarios cost $4.6652 USD (within the ₹400 limit and well under the $8.00 P10 project cap), providing a robust $N=100$ sample ($70$ train, $30$ test) with clear statistical convergence.
- **What was rejected**: Running the full 140 scenarios and exceeding the approved ₹400 spend window, or running a minimal $\le 50$ scenario sweep that would have yielded an underpowered test split.

### D2: Deterministic Signals Instead of LLM Judge
- **Decision**: Built the cascade router entirely on deterministic runtime metadata fields from R2's execution trace:
  - `status != 'answered'` (e.g. `step_cap`, `malformed`, `model_failure`)
  - `not cited_sources` (empty citations)
  - `steps_used >= t` for $t \in [2..24]$
- **Why**: The original Phase 2 plan proposed training an escalation judge on P5-labelled data. However, Project P5 demonstrated that the LLM judge achieved Cohen's $\kappa \approx 0$ (falsifying Hypothesis H3). Replacing a noisy $\kappa \approx 0$ judge with deterministic runtime execution signals costs $0 in inference, introduces zero additional latency, and eliminates judge hallucinations.
- **What was rejected**: Invoking an LLM judge to decide whether to escalate.

### D3: Content-Addressed Split and Threshold Fitting Rule
- **Decision**: Partitioned the 100 scenarios into 70 train / 30 test using deterministic SHA-256 hashing of scenario IDs sorted lexicographically. Thresholds for parameterized policy families were fit on train by maximizing pass rate, with ties broken by lowest mean cost (and then lowest $t$). Headline findings and Pareto frontiers are reported strictly on the held-out test split.
- **Why**: Prevents threshold overfitting and data leakage. Content-addressed hashing is completely deterministic across operating systems and execution environments.
- **What was rejected**: Random unseeded splitting or evaluating policies on the training split.

### D4: Reuse of P12 R2 Arm A and Runner Invocation with `--project`
- **Decision**: Reused the 150 hard-pool R2 Arm A runs from Project P12 (`sweep_output_R2_A.json`) and added `--project` to `projects/p12_attribution/run.py` so that R4 Arm A runs were executed directly into `projects/p10_cascade/` and billed against P10's CostLedger.
- **Why**: R2 Arm A data was already completed on the identical hard scenario pool under identical temperature and step cap settings. Reusing R2 saved $1.47 USD of budget and eliminated duplicate computation.
- **What was rejected**: Re-running R2 Arm A from scratch or manually editing ledger files after execution.

### D5: P6 as Secondary Replicate with Caveats
- **Decision**: Replicated the simulation across Project P6's 450 matched runs (`p06_r2_7e0a1b79` vs `p06_r4_7e0a1b79`) from `projects/p06_passk/trace.db`, reporting both `as_run` and `infra_excluded` partitions.
- **Why**: Validates that the cascade dynamics generalize beyond the single P10 test pool. P6 confirmed that R2 dominates the frontier (R2 57.9% @ $0.0090 vs R4 18.9% @ $0.0598 on test). Caveats are documented: 95 R4 runs suffered zero-token gateway incident failures (`infra_dead`), and P6 span traces omitted `cited_sources`.
- **What was rejected**: Ignoring historical multi-trial data or concealing the P6 gateway incident.

### D6: Pause/Resume Handling and the Four Double-Attempt Runs
- **Decision**: The R4 sweep was paused at 46 new runs for budget confirmation and resumed. Four runs (`r-0256`, `r-0258`, `r-0259`, `r-0260`) were interrupted mid-flight during the pause. The runner cleanly resumed and completed those four. `trace.db` records spans for both attempts for those four scenarios, while `sweep_output_R4_A.json` contains only the final completed run used by the simulation.
- **Why**: The incremental save mechanism in `projects/p12_attribution/run.py` appends to `sweep_output` only upon scenario completion. Resumption skipped already-persisted scenario IDs and re-ran in-flight scenarios cleanly to completion.
- **What was rejected**: Discarding the partial sweep or manually scrubbing `trace.db`.

### D7: Deletion of One-Arm `results_R4.json`
- **Decision**: Deleted `results_R4.json` and `manifest_R4.json` emitted by the P12 runner in `projects/p10_cascade/`.
- **Why**: The P12 runner was designed as a two-arm (Arm A vs Arm B) failure attribution harness testing Hypothesis H8. When invoked in P10 with `--arms A` only, the P12 runner's automatic calculation marked H8 as "FALSIFIED" because Arm B had 0 runs. This was a meaningless artifact of reusing the runner for a single arm. The authoritative results for Project P10 are encapsulated in `results.json`.
- **What was rejected**: Retaining confusing and contradictory P12 attribution artifacts in the P10 cascade directory.
