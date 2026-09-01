# Decisions for P1 Baseline

- **Cost Estimation vs Actual**: `run.py` assigns $0.0 to the ledger via `CallUsage(usd=0.0)` for the `StubModel` so that the ledger is not incorrectly decremented during the free test run, but estimates still print as if it's the `R2` tier (`deepseek-v4-flash`).
- **Standard Pool Subset**: The standard pool has 200 scenarios. To meet the 100 scenario requirement and keep an even mix of tiers, we simply took `[:100]` which preserves whatever interleaving `build_corpus` emitted.
- **Trace DB**: Traces are isolated per-project in `projects/p01_baseline/trace.db`.
