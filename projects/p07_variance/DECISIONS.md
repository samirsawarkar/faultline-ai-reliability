# Decisions — Project P7: Provider Variance

### 2026-09-14 — Drop primary/failover endpoints
- **Decision**: Dropped the primary/failover 'endpoints'.
- **Why**: Both were the AI Credits gateway under two labels and scored identically; comparing a gateway to itself is not provider variance.
- **What was rejected**: Retaining artificial E1 vs E2 gateway aliases in provider variance reporting.

### 2026-09-14 — Model-string guard
- **Decision**: Added a model-string guard: H6 is only evaluated if both endpoints' returned model strings match after prefix normalisation; otherwise results.json says NOT EVALUABLE.
- **Why**: Ensures genuine architectural identity when testing provider and gateway variance.
- **What was rejected**: Comparing gemini-3.7-flash to gemini-3.7-flash-low as if they were one model.

### 2026-09-14 — Report McNemar alongside disjoint-CI criterion
- **Decision**: Report McNemar alongside the disjoint-CI criterion.
- **Why**: The pre-registered criterion is CI overlap, which is conservative; the MEC names McNemar for paired comparisons. Both are reported; neither is dropped.
- **What was rejected**: Dropping McNemar or omitting the pre-registered Wilson overlap test.

### 2026-09-14 — Refuse stub traces in results
- **Decision**: The writer now refuses stub traces and --confirm implies real, with the mode printed at startup.
- **Why**: A stub run was once labelled as real endpoints in results.json.
- **What was rejected**: Silent fallback to synthetic or stub runs during production results aggregation.

### 2026-09-14 — Raise sample size to n=150 paired
- **Decision**: n raised from 30 to 150 paired.
- **Why**: Wilson at 29/30 is too wide to see a 5-point gap.
- **What was rejected**: Continuing evaluation with underpowered n=30 sample size.

### 2026-09-14 — Database store as single source of truth
- **Decision**: Verdicts are written to trace.db and results.json is rebuilt from the store (finalize.py); the in-memory path was removed.
- **Why**: Prevents state drift between trace persistence and reporting artifacts, guaranteeing auditability.
- **What was rejected**: Maintaining in-memory results accumulators alongside SQLite span recording.
