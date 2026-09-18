# Decisions — Project P11: Release Gate

### D1: Tolerance Bands Instead of Static Thresholds
- **Decision**: Candidate model release readiness is evaluated against an empirical variance band $[min, max]$ derived from replicate baseline sweeps rather than a static pass rate cut-off.
- **Why**: Empirical measurements on identical deterministic prompts at temperature 0.0 with `z-ai/glm-5.3-flash` range between 60.0% and 86.7% across evaluation dates. A static threshold (e.g. 75%) would arbitrarily fail valid model deployments and cause CI flakiness.
- **What was rejected**: Fixed scalar thresholds or uncalibrated pass/fail targets.

### D2: Content-Addressed Golden Set Selection
- **Decision**: The 30 golden scenarios are selected deterministically by sorting scenario IDs by `sha256(scenario_id)` from the 150 reserved hard-pool tasks and freezing the list with a SHA-256 manifest hash (`e79897ea4212...`).
- **Why**: Eliminates manual cherry-picking and ensures stability across machines and environments without random seed dependencies.
- **What was rejected**: Sequential selection (e.g., first 30 corpus IDs, which clusters scenarios) or pseudo-random sampling with variable seeds.

### D3: Pinned Deterministic Oracle Judge
- **Decision**: Ground-truth answer and citation verification is executed strictly by the deterministic oracle check (`faultline_p2/oracle/_day01_oracle.py`), SHA-256 pinned in MEC.
- **Why**: Project P5 demonstrated Cohen's $\kappa \approx 0$ between LLM judges and ground truth on multi-hop entity grounding. LLM judges introduce subjective noise that makes gate decisions uncalibrated.
- **What was rejected**: LLM-as-a-judge evaluators.

### D4: Baseline Band Ingested from Existing Runs ($0 Spend)
- **Decision**: The initial 4-source baseline band was constructed by harvesting existing runs from P6 (`trace.db` trials k1, k2, k3) and P12 (`sweep_output_R2_A.json`) without making any new API calls ($0).
- **Why**: Phase 2 repositories already contained 4 independent R2 runs across the identical reserved scenarios. Re-using them saved budget while establishing authentic run-to-run variance.
- **What was rejected**: Spending budget on redundant baseline sweeps.

### D5: Centralized Model Ladder in models.json
- **Decision**: Created [`faultline_p2/models.json`](file:///Volumes/SamirDrive/Development/FAULTLINE/faultline_p2/models.json) as the single source of truth for ladder rungs R1–R6 (model endpoints, provider `aicredits`, token pricing), and refactored `faultline_p2/config.py` to load from it.
- **Why**: Divergence between central config and runner-specific tables caused pricing quote drift in prior projects.
- **What was rejected**: Modifying frozen project runners (`p06_passk/run.py`, `p12_attribution/run.py`); duplicate tables are retained and documented as technical debt.

### D6: Choice of Candidate Models (R1, R4, R2) for Gate Drills
- **Decision**: Swept R1 (`qwen/qwen3.7-flash`), R4 (`openai/gpt-5.6-luna`), and R2 fresh (`z-ai/glm-5.3-flash`) across the golden set.
- **Why**: Evaluates three distinct failure/success modes:
  - R1 tested whether a cheaper model could pass the gate (failed on syntax: 33.3% malformed rate).
  - R4 tested whether frontier models solve hard multi-hop chains (failed on looping: 60.0% step cap exhaustion).
  - R2 fresh verified workhorse regression safety (passed at 86.67% with 0 regressions).
- **What was rejected**: Testing only R2 or testing uncalibrated non-ladder endpoints.

### D7: Single-Threaded First Chain and Concurrency Addition
- **Decision**: The first live gate sweep was executed sequentially and required ~2 hours for 90 runs. Concurrency (`--concurrency 4` via `concurrent.futures.ThreadPoolExecutor`) and incremental trace persistence were added to `projects/p11_release_gate/run.py` for future runs.
- **Why**: Sequential execution was safe for initial validation but unnecessarily slow. 4-worker concurrency reduces 30-scenario sweep latency to ~6–8 minutes without exceeding provider rate limits.
- **What was rejected**: Unbounded worker pools or retaining strictly sequential execution for live sweeps.

### D8: Band v1 vs Band v2 Partitioning
- **Decision**: Archived the original 4-source band as `band_v1.json` and saved the 5-source band (ingesting `p11_r2_fresh`) as `band.json`. Candidate reports explicitly record `band_file: band_v1.json`.
- **Why**: Guarantees auditability: candidates R1, R4, and R2 were evaluated against Band v1. Adding the fresh R2 run increases the observed ceiling from 0.8000 to 0.8667 but leaves the PASS threshold ($\ge 0.5667$) and FAIL threshold ($< 0.5000$) unchanged since the historical minimum (0.6000) was unchanged.
- **What was rejected**: Overwriting Band v1 destructively or retroactively re-evaluating candidates without documenting band provenance.
