# Decisions for Project P3: Grounding Zero-Point

## 1. Dataset Manifest & Hard Subset Freeze for P6
- **Pre-Selection & Partitioning**: The canonical 350-scenario corpus (`faultline_p2/env/corpus.py`, content hash `84e6ff590704aa94d10912f8002716b14c7436080e1a3270b53f9385dc728efc`) was partitioned into two strictly disjoint pools:
  - **Standard Pool (N=200)**: 67 T1 (1-hop), 67 T2 (3-hop), 66 T3 (5-hop) scenarios evaluated in P3 to establish the multi-tier grounding zero point across commodity and frontier rungs.
  - **Reserved Hard Pool (N=150)**: 150 T3 (5-hop) scenarios reserved exclusively for P6 multi-trial pass^k decay experiments.
- **Content-Addressed Manifest**: Serialized to `manifest.json` with SHA-256 hash `02180c04de27be7dd415f7f8959c8db9e92e5307e9e29934a065691618a11dbd` *before* comparison runs to guarantee zero data leakage.

---

## 2. Models Evaluated & Budget Controls

| Rung | Model | Role in P3 | Pricing ($/1M in / out) | Total Runs | Measured Spend |
|---|---|---|---|---|---|
| **R2** | `z-ai/glm-5.3-flash` | Cheap Workhorse (Baseline) | $0.075 / $0.25 | 200 | $0.2742 USD |
| **R4** | `openai/gpt-5.6-luna` | Frontier Lightweight Anchor | $0.200 / $0.60 | 200 | $0.4199 USD |
| **R6** | `deepseek/deepseek-v4-pro` | Frontier Reasoning Anchor (Ceiling) | $0.435 / $0.87 | 200 | $0.7346 USD |
| **Total** | — | — | — | **600** | **$1.4287 USD** |

- **Budget Ceiling**: P3 hard cap is **$5.00 USD**. Total actual spend across all three 200-scenario sweeps was **$1.4287 USD** (~28.6% of cap).
- **Append-Only Ledger**: 602 entries logged in `projects/p03_grounding/ledger.jsonl`.
- **Telemetry**: 4,400+ total execution spans streamed to SQLite database `projects/p03_grounding/trace.db`.

---

## 3. Empirical Grounding Zero-Point & Three-Model Comparison

### Grounded Pass Rates across Multi-Hop Tiers:

| Tier | Hops | Sample Size ($n$) | R2 (`glm-5.3-flash`) | R4 (`gpt-5.6-luna`) | R6 (`deepseek-v4-pro`) | Simulator Baseline |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Overall** | — | 200 | **56.5%** ($[49.6\%, 63.2\%]$) | **8.5%** ($[5.4\%, 13.2\%]$) | **34.0%** ($[27.8\%, 40.8\%]$) | — |
| **T1** | 1 hop | 67 | **100.0%** ($[94.6\%, 100.0\%]$) | **20.9%** ($[12.9\%, 32.1\%]$) | **73.1%** ($[61.5\%, 82.3\%]$) | 100.0% |
| **T2** | 3 hops | 67 | **61.2%** ($[49.2\%, 72.0\%]$) | **4.5%** ($[1.5\%, 12.4\%]$) | **26.9%** ($[17.7\%, 38.5\%]$) | 65.8% |
| **T3** | 5 hops | 66 | **7.6%** ($[3.3\%, 16.5\%]$) | **0.0%** ($[0.0\%, 5.5\%]$) | **1.5%** ($[0.3\%, 8.1\%]$) | 0.0% |

### Key Findings & Hypothesis H1:
1. **Hypothesis H1 (CONFIRMED)**: Grounded pass rates degrade precipitously with multi-hop retrieval depth across all three rungs. For R2, the Wilson 95% confidence intervals for T1 $[94.6\%, 100.0\%]$ and T3 $[3.3\%, 16.5\%]$ are completely disjoint.
2. **Tool Discipline & Schema Adherence Disparity**:
   - `z-ai/glm-5.3-flash` (R2) achieved the highest pass rate (56.5%) by strictly adhering to JSON tool invocation schemas and following linear document pointers.
   - `deepseek/deepseek-v4-pro` (R6) scored 34.0%, frequently generating speculative internal reasoning about entity relationships rather than issuing concrete retrieval tool calls.
   - `openai/gpt-5.6-luna` (R4) scored 8.5%, displaying high sensitivity to bounded step limits and frequently stopping prematurely or failing to emit structured citations.
3. **Severe T3 5-Hop Bottleneck**: All three models experience near-total collapse on T3 (7.6%, 0.0%, and 1.5%), empirically confirming that unstructured autonomous agents without active loop controls or self-healing mechanisms cannot reliably navigate 5-hop dependency chains under step caps.

---

## 4. Concurrency Architecture
- Parallel execution using `ThreadPoolExecutor` with thread-safe locks on `CostLedger` (atomic append) and `TraceStore` (SQLite WAL mode + mutex).
- Total sweep runtime for 600 calls executed in **< 30 minutes** total runtime without database locks or corruptions.
