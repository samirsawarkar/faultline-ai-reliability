import argparse
import sys
import sqlite3
import json
from pathlib import Path
from typing import Optional
from faultline_p2.env.corpus import build_corpus
from faultline_p2.agent.model import StubModel, LiteLLMModel
from faultline_p2.agent.agent import run_agent
from faultline_p2.agent.contracts import ScenarioTask, OutcomeStatus
from faultline_p2.trace.store import TraceStore
from faultline_p2.cost.ledger import CostLedger, PriceTable, RungPricing
from faultline_p2.sweep.runner import SweepRunner, CallUsage, SweepItemResult
from faultline_p2.oracle._day01_oracle import oracle_check
from faultline_p2.stats.intervals import wilson_interval

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--confirm", action="store_true")
    parser.add_argument("--real", action="store_true", help="Use LiteLLMModel (real spend)")
    args = parser.parse_args()

    # Setup environment
    corpus = build_corpus()
    env = {"documents": corpus.documents}
    
    # 100 scenarios from standard pool
    import random
    std_scenarios = [s for s in corpus.scenarios if s.pool == "standard"]
    sampled = random.Random(42).sample(std_scenarios, 100)
    tasks = [ScenarioTask(task_id=s.scenario_id, prompt=s.prompt, tier=s.tier) for s in sampled]
    
    # Cost Ledger & Pricing
    ledger = CostLedger(Path("projects/p01_baseline/ledger.jsonl"))
    price_table = PriceTable(rungs={
        "R2": RungPricing(model_name="deepseek-v4-flash", input_price_per_m=0.14, output_price_per_m=0.28)
    })
    
    # Model selection
    if args.real:
        model = LiteLLMModel("deepseek-v4-flash", "deepseek", "v4")
        model_name = "deepseek-v4-flash"
    else:
        model = StubModel(behavior="solver")
        model_name = "stub"
        
    in_tokens_est = 8565
    out_tokens_est = 183

    runner = SweepRunner(
        project="p01_baseline",
        price_table=price_table,
        ledger=ledger,
        confirmed=args.confirm
    )

    if not args.confirm:
        runner.dry_run(
            n_runs=len(tasks),
            in_tokens=in_tokens_est,
            out_tokens=out_tokens_est,
            rung="R2"
        )
        return

    db_path = Path("projects/p01_baseline/trace.db")
    trace_store = TraceStore(str(db_path))
    sweep_run_id = trace_store.start_run()

    def call_fn(task: ScenarioTask):
        outcome = run_agent(task, env, model, step_cap=12, trace_store=trace_store, run_id=sweep_run_id)
        
        spans = trace_store.conn.execute(
            "SELECT sum(prompt_tokens) as p, sum(completion_tokens) as c FROM spans WHERE run_id = ? AND scenario_id = ?",
            (sweep_run_id, task.task_id)
        ).fetchone()
        p, c = spans["p"] or 0, spans["c"] or 0
        
        usage = CallUsage(input_tokens=p, output_tokens=c, usd=0.0 if not args.real else None)
        
        sc = next(s for s in corpus.scenarios if s.scenario_id == task.task_id)
        ans = outcome.answer if outcome.answer else ""
        verdict = oracle_check({"id": sc.scenario_id, "answer": sc.final_answer, "required_source": sc.required_source},
                               {"answer": ans, "cited_sources": outcome.cited_sources})
        success = verdict["passed"]
        trace_store.record_verdict(sweep_run_id, task.task_id, success)
        
        return outcome, success, usage

    print("Starting sweep...")
    output = runner.execute_sweep(
        tasks=tasks,
        get_task_id=lambda t: t.task_id,
        call_fn=call_fn,
        in_tokens_est=in_tokens_est,
        out_tokens_est=out_tokens_est,
        rung="R2",
        partial_output_path=Path("projects/p01_baseline/sweep_output.json")
    )
    trace_store.end_run(sweep_run_id, "completed")
    
    final_results = build_results_from_trace(trace_store, run_id=sweep_run_id)
    with open("projects/p01_baseline/results.json", "w") as f:
        json.dump(final_results, f, indent=2)
        
    print("Results written to results.json")
    
    # Generate SVG
    svg = f"""<svg width="600" height="400" xmlns="http://www.w3.org/2000/svg">
      <rect width="100%" height="100%" fill="white"/>
      <text x="300" y="30" font-family="sans-serif" font-size="20" text-anchor="middle">P1 Baseline Grounded Pass Rate</text>
    """
    
    colors = {"T1": "#4daf4a", "T2": "#377eb8", "T3": "#e41a1c"}
    x_positions = {"T1": 150, "T2": 300, "T3": 450}
    
    for t in ["T1", "T2", "T3"]:
        if t in final_results["tiers"]:
            rate = final_results["tiers"][t]["pass_rate"]
            ci = final_results["tiers"][t]["wilson_ci"]
            bar_height = rate * 250
            y = 350 - bar_height
            x = x_positions[t]
            svg += f'<rect x="{x-40}" y="{y}" width="80" height="{bar_height}" fill="{colors[t]}"/>\n'
            svg += f'<text x="{x}" y="{y-10}" font-family="sans-serif" font-size="14" text-anchor="middle">{rate:.0%}</text>\n'
            svg += f'<text x="{x}" y="370" font-family="sans-serif" font-size="16" text-anchor="middle">{t}</text>\n'
            # Error bars
            err_y1 = 350 - ci[1]*250
            err_y2 = 350 - ci[0]*250
            svg += f'<line x1="{x}" y1="{err_y1}" x2="{x}" y2="{err_y2}" stroke="black" stroke-width="2"/>\n'
            svg += f'<line x1="{x-5}" y1="{err_y1}" x2="{x+5}" y2="{err_y1}" stroke="black" stroke-width="2"/>\n'
            svg += f'<line x1="{x-5}" y1="{err_y2}" x2="{x+5}" y2="{err_y2}" stroke="black" stroke-width="2"/>\n'
            
    svg += "</svg>"
    with open("projects/p01_baseline/figure.svg", "w") as f:
        f.write(svg)
        
    print("Figure written to figure.svg")
    trace_store.close()

def build_results_from_trace(trace_store_or_path, run_id: Optional[str] = None) -> dict:
    """Rebuild results.json structure completely from trace.db without in-memory sweep objects."""
    if isinstance(trace_store_or_path, (str, Path)):
        conn = sqlite3.connect(str(trace_store_or_path))
        conn.row_factory = sqlite3.Row
        should_close = True
    elif hasattr(trace_store_or_path, "conn"):
        conn = trace_store_or_path.conn
        should_close = False
    else:
        conn = trace_store_or_path
        should_close = False

    try:
        if run_id is None:
            row = conn.execute("SELECT run_id FROM runs ORDER BY start_time DESC, rowid DESC LIMIT 1").fetchone()
            if row is None:
                row = conn.execute("SELECT run_id FROM spans ORDER BY rowid DESC LIMIT 1").fetchone()
            if row is None:
                raise ValueError("No runs found in trace store")
            run_id = row["run_id"]

        model_row = conn.execute("SELECT model_name FROM spans WHERE run_id = ? LIMIT 1", (run_id,)).fetchone()
        model_name = model_row["model_name"] if model_row and model_row["model_name"] else "stub"

        scenarios = conn.execute("""
            SELECT scenario_id, tier, 
                   MAX(step_index) as steps, 
                   SUM(prompt_tokens) as p, 
                   SUM(completion_tokens) as c,
                   MAX(COALESCE(verdict, 0)) as passed
            FROM spans
            WHERE run_id = ?
            GROUP BY scenario_id, tier
        """, (run_id,)).fetchall()

        total_pass = sum(1 for s in scenarios if s["passed"] == 1)
        total_n = len(scenarios)

        final_results = {
            "metadata": {
                "model": model_name,
                "corpus_hash": "84e6ff590704aa94d10912f8002716b14c7436080e1a3270b53f9385dc728efc",
                "reference": "MEC v1.0 + A-001/A-002"
            },
            "pass@1": {
                "score": total_pass / total_n if total_n > 0 else 0,
                "wilson_ci": list(wilson_interval(total_pass, total_n)) if total_n > 0 else [0.0, 0.0]
            },
            "tiers": {}
        }

        for t in ["T1", "T2", "T3"]:
            tier_scenarios = [s for s in scenarios if s["tier"] == t]
            n = len(tier_scenarios)
            p = sum(1 for s in tier_scenarios if s["passed"] == 1)
            if n > 0:
                avg_steps = sum(s["steps"] for s in tier_scenarios) / n
                avg_p = sum(s["p"] for s in tier_scenarios) / n
                avg_c = sum(s["c"] for s in tier_scenarios) / n
                ci = list(wilson_interval(p, n))
                final_results["tiers"][t] = {
                    "n": n,
                    "pass_rate": p / n,
                    "wilson_ci": ci,
                    "avg_steps": round(avg_steps, 2),
                    "avg_tokens": {"prompt": int(avg_p), "completion": int(avg_c)}
                }

        return final_results
    finally:
        if should_close:
            conn.close()

if __name__ == "__main__":
    main()
