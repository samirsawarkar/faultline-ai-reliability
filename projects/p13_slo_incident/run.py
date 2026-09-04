"""P13 SLO Monitoring and Incident Response Runner.

Simulates production traffic:
1. Nominal Healthy Traffic (SLO verified green, 0% budget burned).
2. Injected Degradation Incident (Upstream tool regression causing 75% error rate, triggering 15.0x Fast-Burn Page).
3. Post-Fix Verification (Traffic recovers to 100% pass rate, burn rate resets to 0.0x).
Outputs results.json, figure.svg, and populates trace.db.
"""
from __future__ import annotations

import argparse
import json
import random
from pathlib import Path
from typing import Any, Dict, List

from faultline_p2.env.corpus import build_corpus
from faultline_p2.agent.model import StubModel
from faultline_p2.agent.agent import run_agent
from faultline_p2.agent.contracts import ScenarioTask
from faultline_p2.trace.store import TraceStore
from faultline_p2.oracle._day01_oracle import oracle_check
from faultline_p2.slo.evaluator import evaluate_slos_from_trace


def run_phase_sweep(
    tasks: List[ScenarioTask],
    corpus_scenarios: List[Any],
    env: Dict[str, Any],
    trace_store: TraceStore,
    phase_name: str,
    failure_fraction: float = 0.0
) -> str:
    """Run a batch of scenarios with a given injected failure fraction."""
    run_id = trace_store.start_run()
    solver_model = StubModel(behavior="solver")
    failing_model = StubModel(behavior="hard_failure")

    for i, task in enumerate(tasks):
        # Deterministic failure injection based on index and failure fraction
        if failure_fraction > 0.0 and (i / len(tasks)) < failure_fraction:
            model = failing_model
        else:
            model = solver_model

        outcome = run_agent(task, env, model, step_cap=12, trace_store=trace_store, run_id=run_id)

        sc = next(s for s in corpus_scenarios if s.scenario_id == task.task_id)
        ans = outcome.answer if outcome.answer else ""
        verdict = oracle_check(
            {"id": sc.scenario_id, "answer": sc.final_answer, "required_source": sc.required_source},
            {"answer": ans, "cited_sources": outcome.cited_sources}
        )
        trace_store.record_verdict(run_id, task.task_id, verdict["passed"])

    trace_store.end_run(run_id, "completed")
    return run_id


def generate_svg(results: Dict[str, Any], output_path: Path):
    """Hand-crafted SVG depicting the SLO burn-rate incident and recovery."""
    healthy_burn = results["phases"]["healthy"]["slos"]["grounded_pass_rate"]["burn_rate"]
    incident_burn = results["phases"]["incident"]["slos"]["grounded_pass_rate"]["burn_rate"]
    recovery_burn = results["phases"]["recovery"]["slos"]["grounded_pass_rate"]["burn_rate"]

    healthy_pass = results["phases"]["healthy"]["slos"]["grounded_pass_rate"]["sli_metrics"]["pass_rate"] * 100
    incident_pass = results["phases"]["incident"]["slos"]["grounded_pass_rate"]["sli_metrics"]["pass_rate"] * 100
    recovery_pass = results["phases"]["recovery"]["slos"]["grounded_pass_rate"]["sli_metrics"]["pass_rate"] * 100

    svg = f"""<svg width="720" height="480" xmlns="http://www.w3.org/2000/svg" font-family="system-ui, -apple-system, sans-serif">
  <defs>
    <linearGradient id="bg" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#0f172a" />
      <stop offset="100%" stop-color="#1e293b" />
    </linearGradient>
    <filter id="shadow" x="-5%" y="-5%" width="110%" height="115%">
      <feDropShadow dx="0" dy="4" stdDeviation="4" flood-color="#000" flood-opacity="0.3"/>
    </filter>
  </defs>

  <rect width="100%" height="100%" fill="url(#bg)" rx="12"/>

  <!-- Title & Header -->
  <text x="360" y="38" font-size="20" font-weight="700" fill="#f8fafc" text-anchor="middle">P13: Multiwindow Multi-Burn-Rate Incident &amp; SLO Recovery</text>
  <text x="360" y="60" font-size="13" fill="#94a3b8" text-anchor="middle">SLO: 95% Grounded Pass Rate (5% Budget) | Fast-Burn Threshold: 14.4x Page</text>

  <!-- Grounded Pass Rate Panels -->
  <g transform="translate(40, 90)">
    <!-- Baseline Panel -->
    <rect x="0" y="0" width="200" height="230" rx="8" fill="#1e293b" stroke="#334155" stroke-width="1" filter="url(#shadow)"/>
    <text x="100" y="28" font-size="14" font-weight="600" fill="#38bdf8" text-anchor="middle">Phase 1: Healthy</text>
    <text x="100" y="55" font-size="32" font-weight="700" fill="#4ade80" text-anchor="middle">{healthy_pass:.0f}%</text>
    <text x="100" y="75" font-size="12" fill="#94a3b8" text-anchor="middle">Grounded Pass Rate</text>
    <line x1="20" y1="90" x2="180" y2="90" stroke="#334155" stroke-width="1"/>
    <text x="25" y="115" font-size="12" fill="#94a3b8">Burn Rate:</text>
    <text x="175" y="115" font-size="13" font-weight="700" fill="#4ade80" text-anchor="end">{healthy_burn:.1f}x</text>
    <text x="25" y="145" font-size="12" fill="#94a3b8">Alert Status:</text>
    <rect x="110" y="132" width="65" height="20" rx="10" fill="#166534"/>
    <text x="142" y="146" font-size="11" font-weight="700" fill="#86efac" text-anchor="middle">OK</text>
    <text x="100" y="195" font-size="11" fill="#64748b" text-anchor="middle">Budget Burn: 0.0% / 1h</text>
  </g>

  <g transform="translate(260, 90)">
    <!-- Incident Panel -->
    <rect x="0" y="0" width="200" height="230" rx="8" fill="#1e293b" stroke="#dc2626" stroke-width="2" filter="url(#shadow)"/>
    <text x="100" y="28" font-size="14" font-weight="600" fill="#f87171" text-anchor="middle">Phase 2: Incident</text>
    <text x="100" y="55" font-size="32" font-weight="700" fill="#ef4444" text-anchor="middle">{incident_pass:.0f}%</text>
    <text x="100" y="75" font-size="12" fill="#94a3b8" text-anchor="middle">Grounded Pass Rate</text>
    <line x1="20" y1="90" x2="180" y2="90" stroke="#334155" stroke-width="1"/>
    <text x="25" y="115" font-size="12" fill="#94a3b8">Burn Rate:</text>
    <text x="175" y="115" font-size="13" font-weight="700" fill="#ef4444" text-anchor="end">{incident_burn:.1f}x</text>
    <text x="25" y="145" font-size="12" fill="#94a3b8">Alert Status:</text>
    <rect x="105" y="132" width="70" height="20" rx="10" fill="#991b1b"/>
    <text x="140" y="146" font-size="11" font-weight="700" fill="#fca5a5" text-anchor="middle">PAGE</text>
    <text x="100" y="195" font-size="11" fill="#f87171" text-anchor="middle">Fast-Burn: 2.1% / 1h burned</text>
  </g>

  <g transform="translate(480, 90)">
    <!-- Recovery Panel -->
    <rect x="0" y="0" width="200" height="230" rx="8" fill="#1e293b" stroke="#334155" stroke-width="1" filter="url(#shadow)"/>
    <text x="100" y="28" font-size="14" font-weight="600" fill="#38bdf8" text-anchor="middle">Phase 3: Recovered</text>
    <text x="100" y="55" font-size="32" font-weight="700" fill="#4ade80" text-anchor="middle">{recovery_pass:.0f}%</text>
    <text x="100" y="75" font-size="12" fill="#94a3b8" text-anchor="middle">Grounded Pass Rate</text>
    <line x1="20" y1="90" x2="180" y2="90" stroke="#334155" stroke-width="1"/>
    <text x="25" y="115" font-size="12" fill="#94a3b8">Burn Rate:</text>
    <text x="175" y="115" font-size="13" font-weight="700" fill="#4ade80" text-anchor="end">{recovery_burn:.1f}x</text>
    <text x="25" y="145" font-size="12" fill="#94a3b8">Alert Status:</text>
    <rect x="110" y="132" width="65" height="20" rx="10" fill="#166534"/>
    <text x="142" y="146" font-size="11" font-weight="700" fill="#86efac" text-anchor="middle">OK</text>
    <text x="100" y="195" font-size="11" fill="#64748b" text-anchor="middle">Burn Rate Normalized</text>
  </g>

  <!-- Bottom Timeline & Takeaway -->
  <rect x="40" y="345" width="640" height="100" rx="8" fill="#0b1329" stroke="#1e293b" stroke-width="1"/>
  <text x="60" y="375" font-size="13" font-weight="600" fill="#f8fafc">Google SRE Burn-Rate Alerting Summary</text>
  <text x="60" y="400" font-size="12" fill="#94a3b8">• Healthy Traffic (0% error) maintains burn rate 0.0x: No false alerts.</text>
  <text x="60" y="420" font-size="12" fill="#fca5a5">• Degraded Incident (75% error) consumes budget at 15.0x (>14.4x threshold): Fires on-call PAGE immediately.</text>
  <text x="60" y="440" font-size="12" fill="#86efac">• Post-Mitigation Traffic verifies bug fix before resolving the incident.</text>
</svg>"""
    with open(output_path, "w") as f:
        f.write(svg)


def main():
    parser = argparse.ArgumentParser(description="P13 SLO Monitoring and Incident Demonstration")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for deterministic sampling")
    args = parser.parse_args()

    db_path = Path("projects/p13_slo_incident/trace.db")
    trace_store = TraceStore(str(db_path))

    corpus = build_corpus()
    env = {"documents": corpus.documents}

    std_scenarios = [s for s in corpus.scenarios if s.pool == "standard"]
    sampled = random.Random(args.seed).sample(std_scenarios, 40)
    tasks = [ScenarioTask(task_id=s.scenario_id, prompt=s.prompt, tier=s.tier) for s in sampled]

    print("Running Phase 1: Healthy Nominal Traffic...")
    healthy_run_id = run_phase_sweep(tasks, corpus.scenarios, env, trace_store, "healthy", failure_fraction=0.0)

    print("Running Phase 2: Injected Degradation Incident (75% failure)...")
    incident_run_id = run_phase_sweep(tasks, corpus.scenarios, env, trace_store, "incident", failure_fraction=0.75)

    print("Running Phase 3: Post-Fix Recovered Traffic...")
    recovery_run_id = run_phase_sweep(tasks, corpus.scenarios, env, trace_store, "recovery", failure_fraction=0.0)

    # Evaluate SLOs for all 3 phases
    slo_yaml = Path("projects/p13_slo_incident/slo.yaml")
    healthy_eval = evaluate_slos_from_trace(trace_store.conn, slo_yaml, healthy_run_id)
    incident_eval = evaluate_slos_from_trace(trace_store.conn, slo_yaml, incident_run_id)
    recovery_eval = evaluate_slos_from_trace(trace_store.conn, slo_yaml, recovery_run_id)

    results = {
        "metadata": {
            "project": "p13_slo_incident",
            "seed": args.seed,
            "compliance_period_days": 30,
            "target_slo": 0.95,
            "error_budget": 0.05
        },
        "phases": {
            "healthy": healthy_eval,
            "incident": incident_eval,
            "recovery": recovery_eval
        }
    }

    results_path = Path("projects/p13_slo_incident/results.json")
    with open(results_path, "w") as f:
        json.dump(results, f, indent=2)

    svg_path = Path("projects/p13_slo_incident/figure.svg")
    generate_svg(results, svg_path)

    print("Done. Generated:")
    print(f"  - {results_path}")
    print(f"  - {svg_path}")
    trace_store.close()


if __name__ == "__main__":
    main()
