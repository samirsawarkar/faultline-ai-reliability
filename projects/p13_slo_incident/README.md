# P13: SLO Monitoring, Multi-Burn-Rate Alerting & Incident Response

Implements production-grade SLO tracking and incident response for the FAULTLINE fact-finding agent based on the Google SRE multiwindow multi-burn-rate alerting framework. Note: all incident response documentation in `INCIDENT.md` represents an operational drill conducted against a deliberately injected failure using the `StubModel` test harness with real SLI telemetry measured from `trace.db`.

## Core Components
- `slo.yaml`: Full SLO definitions (Grounded Pass Rate, Agent Infrastructure Errors, P95 Step Latency) with window durations, target thresholds, error budgets, and architectural rationales.
- `faultline_p2/slo/`: Evaluation engine reading directly from `trace.db` to compute SLIs, error budgets, and multi-burn-rate alerts (Fast-Burn 14.4x Page, Slow-Burn 6.0x Ticket).
- `INCIDENT.md`: SRE post-incident review (INC-20260904-01) documenting detection, budget burn, timeline, root cause, mitigation, and post-fix validation.
- `results.json` & `figure.svg`: Audit logs and visualization demonstrating nominal health, fast-burn paging during degradation, and post-fix recovery.

## Reproduction
To reproduce the full incident simulation and generate artifacts deterministically ($0 spend):
```bash
make p13
# or directly:
.venv/bin/python projects/p13_slo_incident/run.py
```
