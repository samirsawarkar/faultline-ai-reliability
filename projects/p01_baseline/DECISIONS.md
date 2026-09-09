# Decisions for P1 Baseline

- **Live Spend Execution**: Executed against live endpoint `z-ai/glm-5.3-flash` via AICredits API (`AICREDITS_BASE_URL` with OpenAI compatibility). Real token usage and spend ($0.144 USD total across 100 scenarios) were recorded to `ledger.jsonl`.
- **Cost Estimation vs Actual**: `run.py` uses dynamic pricing from `.env` and `MODEL_R2`. Real runs calculate and charge exact token-based USD costs to the ledger, well within the $2.00 cap.
- **Standard Pool Subset**: Seeded sample of 100 standard pool scenarios (33 T1, 34 T2, 33 T3) evaluated under bounded 12-step budget.
- **Trace DB**: Real-time spans containing step-level tool calls, prompt/completion tokens, and latencies are recorded in `projects/p01_baseline/trace.db`.
