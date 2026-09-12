> [!IMPORTANT]
> **OPERATIONAL DRILL NOTICE — NOT A LIVE PRODUCTION OUTAGE**
>
> This document is an incident response **DRILL** conducted against a deliberately injected degradation using the `StubModel` test harness. The service name (`faultline-fact-finding-agent`), deployment versions (`v2.4.1-rc1`), and on-call responder designations are fictional narrative scaffolding for drill fidelity; no live production system existed or was impacted.
>
> **What is real:** The SLI measurements collected in `trace.db`, the Google SRE multiwindow multi-burn-rate arithmetic (15.0x fast-burn rate), the 30-day error budget consumption calculations (2.08% / 10.42%), and the automated alert firing and clearing logic.
>
> **What is narrative scaffolding:** The canary promotion event, the human responder timeline, the rollback commands, and the external ticketing references.

# Post-Incident Report: INC-20260904-01
## High Burn-Rate Degradation on Agent Grounded Pass Rate & Infrastructure Availability

| Metadata | Details |
| :--- | :--- |
| **Incident Date** | 2026-09-04 |
| **Severity** | SEV-1 (Critical Availability & Accuracy Loss) |
| **Service Impacted** | `faultline-fact-finding-agent` |
| **Lead Responder / Incident Commander** | Staff SRE On-Call |
| **Detection Method** | SRE Multiwindow Multi-Burn-Rate Alert (`FastBurn-GroundedPassRate-Page`) |
| **Total Duration** | 24 minutes (14:18 UTC – 14:42 UTC) |
| **Status** | Resolved & Verified |

---

### 1. Executive Summary

At 14:24 UTC on 2026-09-04, the Google SRE multi-burn-rate alerting engine fired a **PAGE** alert against the `faultline-fact-finding-agent` service. The Grounded Pass Rate SLI collapsed from its nominal 100.0% to 25.0% (75.0% error rate), triggering a **15.0x fast-burn rate** over a 1-hour window (exceeding the 14.4x emergency threshold). Concurrently, the Agent Infrastructure Error Rate spiked to 75.0% (burn rate 75.0x against a 1.0% error budget).

The root cause was traced to an unhandled upstream tool interface regression deployed in prompt version `v2.4.1-rc1` that caused tool payload validation crashes (`MODEL_FAILURE`). Within 18 minutes of page notification, the on-call engineer rolled back the active prompt and model configuration to the pinned `v2.4.0` release. Post-rollback synthetic verification confirmed 100% grounded accuracy and immediate normalization of error burn rates to 0.0x. Total 30-day error budget consumed during the window was **2.08%** of the pass rate budget and **10.42%** of the agent availability budget.

---

### 2. SLO & Error Budget Impact

| SLO Metric | Target | Nominal Error Rate | Incident Error Rate | Burn Rate | 1h Budget Consumed | Total 30-day Budget Consumed | Alert Triggered |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Grounded Pass Rate** | 95.0% | 0.0% | **75.0%** | **15.0x** | **2.08%** | 2.08% | `FastBurn-GroundedPassRate-Page` (14.4x) |
| **Agent Error Rate** | 99.0% | 0.0% | **75.0%** | **75.0x** | **10.42%** | 10.42% | `FastBurn-AgentErrorRate-Page` (14.4x) |
| **Step Latency (P95)** | 95.0% < 1000ms | 0.0% | 0.0% | 0.0x | 0.0% | 0.0% | None (steps failed fast at ~25ms) |

- **Total 30-Day Budget Remaining (Pass Rate):** 97.92% (4.896% absolute headroom remaining).
- **Total 30-Day Budget Remaining (Availability):** 89.58% (0.896% absolute headroom remaining).
- **Customer Impact:** Callers requesting fact verification experienced high failure rates. Queries failed explicitly rather than hallucinating wrong facts (safety invariant held).

---

### 3. Detailed Incident Timeline (UTC)

- **14:18:00** — Automated canary deployment `v2.4.1-rc1` promoted to production cluster serving standard query traffic.
- **14:20:12** — Upstream model serialization protocol mismatched tool arguments; agents began throwing unhandled exceptions at step 1 (`MODEL_FAILURE`).
- **14:24:05** — **ALERT FIRED**: SRE Multiwindow Burn-Rate Monitor evaluates `trace.db` window.
  - Calculated 1-hour burn rate: **15.0x** on `grounded_pass_rate` (threshold 14.4x).
  - Calculated 1-hour burn rate: **75.0x** on `agent_error_rate` (threshold 14.4x).
  - PagerDuty notification dispatches to primary on-call engineer.
- **14:26:15** — On-call acknowledges page. Pulls latest `trace.db` queries:
  ```sql
  SELECT termination_reason, COUNT(*) FROM spans 
  WHERE timestamp >= datetime('now', '-15 minutes') 
  GROUP BY termination_reason;
  ```
  Found 30 of 40 recent scenario runs aborted with `termination_reason = 'MODEL_FAILURE'`.
- **14:29:30** — Correlated failure onset with `v2.4.1-rc1` canary release timestamp (14:18).
- **14:32:00** — Incident Commander issues rollback order: execute zero-downtime rollback to `v2.4.0` pinned configuration.
- **14:36:45** — Rollback completes. Routing switched 100% of live traffic back to stable `v2.4.0` agent runtime.
- **14:38:10** — Post-fix synthetic verification sweep initiated across 40 standard multi-hop scenarios.
- **14:41:30** — Sweep completes with 40/40 passed (100.0% pass rate, 0% errors, P95 latency 0.08ms).
- **14:42:00** — Multi-burn-rate evaluator evaluates new window: burn rate drops to **0.0x**. Alerts resolve automatically. Incident declared MITIGATED.

---

### 4. Root Cause Analysis

The incident was triggered by a breaking change in tool argument envelope serialization introduced in `v2.4.1-rc1`. When the agent attempted to dispatch search queries, the response format omitted required tool delimiter keys, triggering `RuntimeError` during response parsing. Because `run_agent` correctly traps model exceptions into `OutcomeStatus.MODEL_FAILURE` and records them durable into `trace.db`, the failure was transparently observable in the trace store without silent data corruption.

The Google SRE multi-burn-rate monitor caught the failure in under 6 minutes because it monitors *rate of budget consumption* rather than a naive 24-hour moving average (which would have required hours of sustained degradation to trigger an alert, burning 50%+ of monthly budget).

---

### 5. Verification & Recovery Evidence

The mitigation was proven through deterministic offline replay against `projects/p13_slo_incident/trace.db`:
1. **Healthy Run (`da17c995...`):**
   - 40 scenarios, 40 passed.
   - Grounded pass rate: 100.0%. Burn rate: 0.0x. Status: **OK**.
2. **Degraded Incident Run (`fe6871ec...`):**
   - 40 scenarios, 10 passed, 30 failed (`MODEL_FAILURE`).
   - Grounded pass rate: 25.0%. Burn rate: **15.0x** (Consumed 2.08% of 30-day budget).
   - Fast-burn alert: **PAGE** fired.
3. **Recovery Run (`ce2549a1...`):**
   - 40 scenarios, 40 passed.
   - Grounded pass rate: 100.0%. Burn rate: **0.0x**. Status: **OK**.

---

### 6. Corrective Actions & Action Items

| Action Item | Type | Owner | Target Date |
| :--- | :---: | :---: | :---: |
| Add pre-promotion contract test checking tool envelope serialization compatibility | Preventative | Agent Platform | 2026-09-08 |
| Configure automated circuit breaker to trip canary when 1h burn rate exceeds 10.0x | Mitigative | SRE Team | 2026-09-10 |
| Extend slow-burn ticketing integration to auto-file Jira tickets for 6h > 6.0x burns | Observability | SRE Team | 2026-09-15 |
| Document on-call runbook for prompt and runtime rollback procedures | Documentation | On-Call Team | 2026-09-05 |
