# Decisions for P13 SLO Monitoring and Incident Response

- **SLO Engine over TraceStore**: In alignment with the MEC ARTIFACTS clause, all SLI calculations (grounded pass rate, agent error rate, step latency) are computed directly from `trace.db` without reliance on volatile in-memory objects or external monitoring SaaS.
- **Google SRE Multiwindow Multi-Burn-Rate Architecture**: Naive alerting thresholds (e.g. "error rate > 5% over 24h") are either too slow to prevent catastrophic budget exhaustion or suffer high false alarm rates during short traffic spikes. We adopted the Google SRE multi-burn-rate model:
  - **Fast-Burn (Page)**: 14.4x burn rate over 1 hour (burns 2.0% of 30-day budget).
  - **Slow-Burn (Ticket)**: 6.0x burn rate over 6 hours (burns 5.0% of 30-day budget).
- **Injected Degradation Model**: To demonstrate both positive and negative alerting states deterministically with $0 budget, `run.py` uses `StubModel` behaviors (`solver` for healthy, `hard_failure` for degraded). This simulates a realistic tool/model integration breakage without invoking external APIs or nondeterministic network latency.
- **Persistent Trace Store**: All phases (healthy, incident, recovery) write distinct `run_id` sweeps into `projects/p13_slo_incident/trace.db`. The SLO evaluator selects and isolates individual phases by `run_id`, preventing trace pollution while providing an auditable incident trail.
