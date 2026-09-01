import argparse
import sys
import sqlite3
import json
from pathlib import Path
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

    db_path = Path("projects/p01_baseline/trace.db")
    if db_path.exists():
        db_path.unlink()
    trace_store = TraceStore(str(db_path))

    def call_fn(task: ScenarioTask):
        run_id = trace_store.start_run()
        outcome = run_agent(task, env, model, step_cap=12, trace_store=trace_store, run_id=run_id)
        
        spans = trace_store.conn.execute("SELECT sum(prompt_tokens) as p, sum(completion_tokens) as c FROM spans WHERE run_id = ?", (run_id,)).fetchone()
        p, c = spans["p"] or 0, spans["c"] or 0
        
        usage = CallUsage(input_tokens=p, output_tokens=c, usd=0.0 if not args.real else None)
        
        sc = next(s for s in corpus.scenarios if s.scenario_id == task.task_id)
        ans = outcome.answer if outcome.answer else ""
        verdict = oracle_check({"id": sc.scenario_id, "answer": sc.final_answer, "required_source": sc.required_source},
                               {"answer": ans, "cited_sources": outcome.cited_sources})
        success = verdict["passed"]
        
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
    
    runs_query = trace_store.conn.execute("""
        SELECT scenario_id, tier, 
               MAX(step_index) as steps, 
               SUM(prompt_tokens) as p, 
               SUM(completion_tokens) as c,
               SUM(CASE WHEN termination_reason = 'ANSWERED' THEN 1 ELSE 0 END) as is_answered
        FROM spans
        GROUP BY scenario_id
    """).fetchall()
    
    tier_stats = {"T1": {"pass": 0, "n": 0, "steps": [], "p": [], "c": []},
                  "T2": {"pass": 0, "n": 0, "steps": [], "p": [], "c": []},
                  "T3": {"pass": 0, "n": 0, "steps": [], "p": [], "c": []}}
                  
    total_pass = 0
    total_n = 0
    
    for result in output.results:
        tier = next(t.tier for t in tasks if t.task_id == result.task_id)
        stats = tier_stats[tier]
        stats["n"] += 1
        total_n += 1
        if result.success:
            stats["pass"] += 1
            total_pass += 1
        
        row = next((r for r in runs_query if r["scenario_id"] == result.task_id), None)
        if row:
            stats["steps"].append(row["steps"])
            stats["p"].append(row["p"])
            stats["c"].append(row["c"])
            
    final_results = {
        "metadata": {
            "model": model_name,
            "corpus_hash": "84e6ff590704aa94d10912f8002716b14c7436080e1a3270b53f9385dc728efc",
            "reference": "MEC v1.0 + A-001/A-002"
        },
        "pass@1": {
            "score": total_pass / total_n if total_n > 0 else 0,
            "wilson_ci": wilson_interval(total_pass, total_n) if total_n > 0 else (0,0)
        },
        "tiers": {}
    }
    
    for t in ["T1", "T2", "T3"]:
        stats = tier_stats[t]
        n = stats["n"]
        p = stats["pass"]
        if n > 0:
            avg_steps = sum(stats["steps"]) / n
            avg_p = sum(stats["p"]) / n
            avg_c = sum(stats["c"]) / n
            ci = wilson_interval(p, n)
            final_results["tiers"][t] = {
                "n": n,
                "pass_rate": p / n,
                "wilson_ci": ci,
                "avg_steps": round(avg_steps, 2),
                "avg_tokens": {"prompt": int(avg_p), "completion": int(avg_c)}
            }
            
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

if __name__ == "__main__":
    main()
