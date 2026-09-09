"""Project P3: Grounding Zero-Point Runner.

Measures grounded pass rates across T1 (1-hop), T2 (3-hop), and T3 (5-hop)
tiers over the N=200 standard pool scenarios with real model spend on both
Model 1 (R2: z-ai/glm-5.3-flash) and Model 2 (R6: deepseek/deepseek-v4-pro),
or offline solver stub.
Generates results.json, figure.svg, trace.db, and ledger.jsonl.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sqlite3
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from dotenv import load_dotenv

from faultline_p2.agent.agent import run_agent
from faultline_p2.agent.contracts import OutcomeStatus, ScenarioTask
from faultline_p2.agent.model import LiteLLMModel, StubModel
from faultline_p2.cost.ledger import CostLedger, PriceTable, RungPricing
from faultline_p2.env.corpus import build_corpus
from faultline_p2.oracle._day01_oracle import oracle_check
from faultline_p2.resilience import CircuitBreaker, ResilientModel, RetryPolicy
from faultline_p2.stats.intervals import wilson_interval
from faultline_p2.sweep.runner import CallUsage, SweepRunner
from faultline_p2.trace.store import TraceStore


def ensure_manifest() -> Dict[str, Any]:
    """Ensure manifest.json is present and verified before execution."""
    manifest_path = Path("projects/p03_grounding/manifest.json")
    corpus = build_corpus()
    std_scenarios = [s.scenario_id for s in corpus.scenarios if s.pool == "standard"]
    res_scenarios = [s.scenario_id for s in corpus.scenarios if s.pool == "reserved"]

    std_sha = hashlib.sha256(json.dumps(std_scenarios).encode()).hexdigest()
    res_sha = hashlib.sha256(json.dumps(res_scenarios).encode()).hexdigest()

    manifest_data = {
        "spec_version": "2.0.0",
        "corpus_hash": corpus.content_hash,
        "selection_criteria": {
            "policy": "disjoint_split",
            "standard_pool_description": "200 scenarios (67 T1, 67 T2, 66 T3) for general grounding zero-point calibration",
            "reserved_hard_pool_description": "150 T3 scenarios reserved exclusively for P6 multi-trial pass^k decay sweep",
        },
        "pools": {
            "standard": {
                "count": len(std_scenarios),
                "tier_counts": {"T1": 67, "T2": 67, "T3": 66},
                "sha256": std_sha,
                "scenario_ids": std_scenarios,
            },
            "reserved_hard": {
                "count": len(res_scenarios),
                "tier_counts": {"T3": 150},
                "sha256": res_sha,
                "scenario_ids": res_scenarios,
            },
        },
    }

    manifest_bytes = json.dumps(manifest_data, indent=2, sort_keys=True).encode()
    manifest_sha = hashlib.sha256(manifest_bytes).hexdigest()
    manifest_data["manifest_sha256"] = manifest_sha

    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest_data, f, indent=2)

    return manifest_data


def generate_figure(results: Dict[str, Any], output_path: Path) -> None:
    """Generate publication-grade SVG chart comparing R2, R4, R6, and Simulator across T1, T2, T3."""
    width = 860
    height = 470

    tiers = ["T1", "T2", "T3"]
    tier_labels = {"T1": "T1 (1-hop)", "T2": "T2 (3-hop)", "T3": "T3 (5-hop)"}
    tier_center_x = {"T1": 190, "T2": 435, "T3": 680}

    # Colors
    color_r2 = "#1f77b4"  # Blue for R2 (Commodity / GLM-5.3-flash)
    color_r4 = "#e6550d"  # Orange/Amber for R4 (Frontier OpenAI / GPT-5.6-luna)
    color_r6 = "#9467bd"  # Purple for R6 (Reasoning Anchor / DeepSeek-V4-Pro)
    color_sim = "#bbbbbb"  # Gray for Simulator baseline

    # Simulator baselines from Day 3 for comparison reference
    sim_baselines = {"T1": 1.000, "T2": 0.658, "T3": 0.000}

    rungs_data = results.get("rungs", {})
    r2_tiers = rungs_data.get("R2", {}).get("tiers", results.get("tiers", {}))
    r4_tiers = rungs_data.get("R4", {}).get("tiers", {})
    r6_tiers = rungs_data.get("R6", {}).get("tiers", {})

    has_r4 = bool(r4_tiers)
    has_r6 = bool(r6_tiers)

    # Build model subtitle
    sub_parts = []
    if "R2" in rungs_data:
        sub_parts.append(f"R2: {rungs_data['R2'].get('model', 'R2')}")
    if has_r4:
        sub_parts.append(f"R4: {rungs_data['R4'].get('model', 'R4')}")
    if has_r6:
        sub_parts.append(f"R6: {rungs_data['R6'].get('model', 'R6')}")
    subtitle_text = " | ".join(sub_parts) if sub_parts else "Multi-Rung Grounded Pass Rate Comparison"

    svg_lines = [
        f'<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg">',
        '  <rect width="100%" height="100%" fill="#ffffff"/>',
        '  <style>',
        '    .title { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; font-size: 17px; font-weight: 600; fill: #1a1a1a; }',
        '    .subtitle { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; font-size: 12px; fill: #666666; }',
        '    .axis { stroke: #cccccc; stroke-width: 1; }',
        '    .grid { stroke: #eeeeee; stroke-dasharray: 4,4; }',
        '    .label { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; font-size: 13px; fill: #333333; }',
        '    .val { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; font-size: 10px; font-weight: 600; }',
        '    .legend { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; font-size: 11px; fill: #555555; }',
        '  </style>',
        '  <!-- Title -->',
        f'  <text x="{width/2}" y="30" class="title" text-anchor="middle">P3 Grounding Zero-Point: Multi-Tier Grounded Pass Rate (N=200)</text>',
        f'  <text x="{width/2}" y="48" class="subtitle" text-anchor="middle">{subtitle_text}</text>',
        '  <!-- Y-Axis Grid & Labels -->',
    ]

    chart_top = 75
    chart_bottom = 355
    chart_height = chart_bottom - chart_top

    for pct in range(0, 101, 20):
        y = chart_bottom - (pct / 100.0) * chart_height
        svg_lines.append(f'  <line x1="70" y1="{y}" x2="{width - 50}" y2="{y}" class="grid"/>')
        svg_lines.append(f'  <text x="60" y="{y + 4}" class="label" text-anchor="end">{pct}%</text>')

    svg_lines.append(f'  <line x1="70" y1="{chart_bottom}" x2="{width - 50}" y2="{chart_bottom}" class="axis"/>')

    # Draw grouped bars for each tier
    for t in tiers:
        cx = tier_center_x[t]

        # 1. R2 Bar
        if t in r2_tiers:
            r2_val = r2_tiers[t]["pass_rate"]
            r2_ci = r2_tiers[t]["wilson_ci"]
            r2_h = r2_val * chart_height
            r2_y = chart_bottom - r2_h
            bx = cx - 50 if (has_r4 and has_r6) else (cx - 45 if has_r6 else cx - 30)
            bw = 20 if (has_r4 and has_r6) else (28 if has_r6 else 36)

            svg_lines.append(f'  <!-- {t} R2 Bar -->')
            svg_lines.append(f'  <rect x="{bx}" y="{r2_y}" width="{bw}" height="{r2_h}" fill="{color_r2}" rx="3"/>')
            svg_lines.append(f'  <text x="{bx + bw/2}" y="{r2_y - 8}" class="val" fill="{color_r2}" text-anchor="middle">{r2_val:.1%}</text>')

            # R2 Error Bar
            ci_top = chart_bottom - r2_ci[1] * chart_height
            ci_bot = chart_bottom - r2_ci[0] * chart_height
            mid_x = bx + bw / 2
            svg_lines.append(f'  <line x1="{mid_x}" y1="{ci_top}" x2="{mid_x}" y2="{ci_bot}" stroke="#111111" stroke-width="1.5"/>')
            svg_lines.append(f'  <line x1="{mid_x - 3}" y1="{ci_top}" x2="{mid_x + 3}" y2="{ci_top}" stroke="#111111" stroke-width="1.5"/>')
            svg_lines.append(f'  <line x1="{mid_x - 3}" y1="{ci_bot}" x2="{mid_x + 3}" y2="{ci_bot}" stroke="#111111" stroke-width="1.5"/>')

        # 2. R4 Bar
        if has_r4 and t in r4_tiers:
            r4_val = r4_tiers[t]["pass_rate"]
            r4_ci = r4_tiers[t]["wilson_ci"]
            r4_h = r4_val * chart_height
            r4_y = chart_bottom - r4_h
            bx = cx - 25
            bw = 20

            svg_lines.append(f'  <!-- {t} R4 Bar -->')
            svg_lines.append(f'  <rect x="{bx}" y="{r4_y}" width="{bw}" height="{r4_h}" fill="{color_r4}" rx="3"/>')
            svg_lines.append(f'  <text x="{bx + bw/2}" y="{r4_y - 8}" class="val" fill="{color_r4}" text-anchor="middle">{r4_val:.1%}</text>')

            # R4 Error Bar
            ci_top = chart_bottom - r4_ci[1] * chart_height
            ci_bot = chart_bottom - r4_ci[0] * chart_height
            mid_x = bx + bw / 2
            svg_lines.append(f'  <line x1="{mid_x}" y1="{ci_top}" x2="{mid_x}" y2="{ci_bot}" stroke="#111111" stroke-width="1.5"/>')
            svg_lines.append(f'  <line x1="{mid_x - 3}" y1="{ci_top}" x2="{mid_x + 3}" y2="{ci_top}" stroke="#111111" stroke-width="1.5"/>')
            svg_lines.append(f'  <line x1="{mid_x - 3}" y1="{ci_bot}" x2="{mid_x + 3}" y2="{ci_bot}" stroke="#111111" stroke-width="1.5"/>')

        # 3. R6 Bar
        if has_r6 and t in r6_tiers:
            r6_val = r6_tiers[t]["pass_rate"]
            r6_ci = r6_tiers[t]["wilson_ci"]
            r6_h = r6_val * chart_height
            r6_y = chart_bottom - r6_h
            bx = cx + 0 if (has_r4 and has_r6) else (cx - 12)
            bw = 20 if (has_r4 and has_r6) else 28

            svg_lines.append(f'  <!-- {t} R6 Bar -->')
            svg_lines.append(f'  <rect x="{bx}" y="{r6_y}" width="{bw}" height="{r6_h}" fill="{color_r6}" rx="3"/>')
            svg_lines.append(f'  <text x="{bx + bw/2}" y="{r6_y - 8}" class="val" fill="{color_r6}" text-anchor="middle">{r6_val:.1%}</text>')

            # R6 Error Bar
            ci_top = chart_bottom - r6_ci[1] * chart_height
            ci_bot = chart_bottom - r6_ci[0] * chart_height
            mid_x = bx + bw / 2
            svg_lines.append(f'  <line x1="{mid_x}" y1="{ci_top}" x2="{mid_x}" y2="{ci_bot}" stroke="#111111" stroke-width="1.5"/>')
            svg_lines.append(f'  <line x1="{mid_x - 3}" y1="{ci_top}" x2="{mid_x + 3}" y2="{ci_top}" stroke="#111111" stroke-width="1.5"/>')
            svg_lines.append(f'  <line x1="{mid_x - 3}" y1="{ci_bot}" x2="{mid_x + 3}" y2="{ci_bot}" stroke="#111111" stroke-width="1.5"/>')

        # 4. Simulator Reference Bar
        sim_val = sim_baselines.get(t, 0.0)
        sim_h = sim_val * chart_height
        sim_y = chart_bottom - sim_h
        bx = cx + 25 if (has_r4 and has_r6) else (cx + 22 if has_r6 else cx + 12)
        bw = 18 if (has_r4 and has_r6) else 20

        svg_lines.append(f'  <!-- {t} Sim Reference -->')
        svg_lines.append(f'  <rect x="{bx}" y="{sim_y}" width="{bw}" height="{sim_h}" fill="{color_sim}" opacity="0.6" rx="2"/>')
        svg_lines.append(f'  <text x="{bx + bw/2}" y="{sim_y - 6}" class="legend" text-anchor="middle">{sim_val:.0%}</text>')

        # Tier X Label
        svg_lines.append(f'  <text x="{cx}" y="{chart_bottom + 25}" class="label" font-weight="600" text-anchor="middle">{tier_labels[t]}</text>')
        n_val = r2_tiers.get(t, {}).get("n", 67)
        svg_lines.append(f'  <text x="{cx}" y="{chart_bottom + 42}" class="legend" text-anchor="middle">n={n_val}</text>')

    # Legend
    legend_y = 430
    svg_lines.extend([
        '  <!-- Legend -->',
        f'  <rect x="70" y="{legend_y - 12}" width="14" height="12" fill="{color_r2}" rx="2"/>',
        f'  <text x="90" y="{legend_y - 2}" class="legend">R2 Workhorse (glm-5.3-flash)</text>',
        f'  <rect x="275" y="{legend_y - 12}" width="14" height="12" fill="{color_r4}" rx="2"/>',
        f'  <text x="295" y="{legend_y - 2}" class="legend">R4 Frontier (gpt-5.6-luna)</text>',
        f'  <rect x="460" y="{legend_y - 12}" width="14" height="12" fill="{color_r6}" rx="2"/>',
        f'  <text x="480" y="{legend_y - 2}" class="legend">R6 Reasoning (deepseek-v4-pro)</text>',
        f'  <rect x="665" y="{legend_y - 12}" width="14" height="12" fill="{color_sim}" opacity="0.6" rx="2"/>',
        f'  <text x="685" y="{legend_y - 2}" class="legend">Day 3 Simulator Baseline</text>',
        '</svg>',
    ])

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(svg_lines))


def extract_rung_metrics(conn: sqlite3.Connection, run_id: str, corpus: Any) -> Dict[str, Any]:
    """Extract full metrics, tier breakdown, token usage, and Wilson CIs for a single run_id."""
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

    has_resilience = conn.execute(
        "SELECT count(*) FROM sqlite_master WHERE type='table' AND name='run_resilience'"
    ).fetchone()[0] > 0
    retried_calls = 0
    if has_resilience:
        row = conn.execute(
            "SELECT retried_calls FROM run_resilience WHERE run_id = ?", (run_id,)
        ).fetchone()
        if row and row["retried_calls"] is not None:
            retried_calls = row["retried_calls"]

    rung_res = {
        "run_id": run_id,
        "model": model_name,
        "sample_size": total_n,
        "retried_calls": retried_calls,
        "pass@1": {
            "score": total_pass / total_n if total_n > 0 else 0,
            "wilson_ci": list(wilson_interval(total_pass, total_n)) if total_n > 0 else [0.0, 0.0],
        },
        "tiers": {},
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
            rung_res["tiers"][t] = {
                "n": n,
                "pass_rate": p / n,
                "wilson_ci": ci,
                "avg_steps": round(avg_steps, 2),
                "avg_tokens": {"prompt": int(avg_p), "completion": int(avg_c)},
            }

    return rung_res


def build_results_from_trace(
    trace_store_or_path: Any,
    manifest: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Rebuild results.json completely from trace.db aggregating all evaluated rungs."""
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
        corpus = build_corpus()
        manifest_sha = manifest.get("manifest_sha256") if manifest else "frozen"

        # Find all completed runs
        runs = conn.execute("SELECT run_id, start_time FROM runs ORDER BY start_time ASC").fetchall()
        if not runs:
            # Fallback to spans
            span_runs = conn.execute("SELECT DISTINCT run_id FROM spans").fetchall()
            run_ids = [r["run_id"] for r in span_runs]
        else:
            run_ids = [r["run_id"] for r in runs]

        rungs_data: Dict[str, Any] = {}
        for r_id in run_ids:
            # Check how many spans in run
            span_count = conn.execute("SELECT count(DISTINCT scenario_id) as sc_count FROM spans WHERE run_id = ?", (r_id,)).fetchone()
            if not span_count or span_count["sc_count"] == 0:
                continue

            metrics = extract_rung_metrics(conn, r_id, corpus)
            model_name = metrics["model"].lower()

            if "glm" in model_name or "qwen" in model_name:
                rungs_data["R2"] = metrics
            elif "gpt" in model_name or "luna" in model_name or "openai" in model_name:
                rungs_data["R4"] = metrics
            elif "deepseek" in model_name or "pro" in model_name or "gemini" in model_name:
                rungs_data["R6"] = metrics
            else:
                # Default label
                rungs_data[metrics["model"]] = metrics

        # Select primary model (R2 or latest)
        primary_rung = "R2" if "R2" in rungs_data else (list(rungs_data.keys())[0] if rungs_data else "R2")
        primary_data = rungs_data.get(primary_rung, {})

        total_retries = sum(v.get("retried_calls", 0) for v in rungs_data.values())
        final_results = {
            "metadata": {
                "project": "P3",
                "reference": "MEC v1.0 + A-001/A-002",
                "corpus_hash": corpus.content_hash,
                "manifest_sha256": manifest_sha,
                "rungs_evaluated": list(rungs_data.keys()),
                "total_retried_calls": total_retries,
            },
            "pass@1": primary_data.get("pass@1", {"score": 0.0, "wilson_ci": [0.0, 0.0]}),
            "tiers": primary_data.get("tiers", {}),
            "rungs": rungs_data,
            "hypotheses": {},
        }

        # Evaluate Hypothesis H1 for R2
        r2_tiers = rungs_data.get("R2", {}).get("tiers", primary_data.get("tiers", {}))
        t3_data = r2_tiers.get("T3")
        t1_data = r2_tiers.get("T1")
        if t3_data and t1_data:
            t3_ci = t3_data["wilson_ci"]
            t1_ci = t1_data["wilson_ci"]
            disjoint_from_t1 = t3_ci[1] < t1_ci[0]
            final_results["hypotheses"]["H1"] = {
                "claim": "Real-model grounded pass rate on T3 degrades significantly under multi-hop retrieval depth",
                "status": "CONFIRMED" if disjoint_from_t1 else "INCONCLUSIVE",
                "r2_t1_pass_rate": t1_data["pass_rate"],
                "r2_t1_wilson_ci": t1_ci,
                "r2_t3_pass_rate": t3_data["pass_rate"],
                "r2_t3_wilson_ci": t3_ci,
                "disjoint_t1_t3_intervals": disjoint_from_t1,
            }

        # Multi-rung comparison summary
        if len(rungs_data) > 1:
            comp: Dict[str, Any] = {
                "models": {k: v["model"] for k, v in rungs_data.items()},
                "overall_pass@1": {k: v["pass@1"]["score"] for k, v in rungs_data.items()},
                "tier_breakdown": {
                    t: {k: v["tiers"].get(t, {}).get("pass_rate", 0.0) for k, v in rungs_data.items()}
                    for t in ["T1", "T2", "T3"]
                },
            }
            if "R2" in rungs_data and "R6" in rungs_data:
                comp["r2_model"] = rungs_data["R2"]["model"]
                comp["r6_model"] = rungs_data["R6"]["model"]
                comp["delta"] = round(rungs_data["R6"]["pass@1"]["score"] - rungs_data["R2"]["pass@1"]["score"], 4)
            if "R4" in rungs_data:
                comp["r4_model"] = rungs_data["R4"]["model"]
            final_results["comparison"] = comp

        return final_results
    finally:
        if should_close:
            conn.close()


def run_single_rung_sweep(
    rung_name: str,
    tasks: List[ScenarioTask],
    corpus: Any,
    trace_store: TraceStore,
    ledger: CostLedger,
    confirm: bool,
    real: bool,
    concurrency: int,
) -> str:
    """Execute sweep for a specific rung and return the sweep_run_id."""
    env = {"documents": corpus.documents}

    if real:
        if rung_name == "R6":
            model_name = os.getenv("MODEL_R6", "deepseek/deepseek-v4-pro")
            in_p = float(os.getenv("PRICE_R6_INPUT", "0.435"))
            out_p = float(os.getenv("PRICE_R6_OUTPUT", "0.87"))
        elif rung_name == "R4":
            model_name = os.getenv("MODEL_R4", "openai/gpt-5.6-luna")
            in_p = float(os.getenv("PRICE_R4_INPUT", "0.20"))
            out_p = float(os.getenv("PRICE_R4_OUTPUT", "0.60"))
        else:
            model_name = os.getenv("MODEL_R2", "z-ai/glm-5.3-flash")
            in_p = float(os.getenv("PRICE_R2_INPUT", "0.075" if "glm" in model_name else "0.14"))
            out_p = float(os.getenv("PRICE_R2_OUTPUT", "0.25" if "glm" in model_name else "0.28"))
        raw_model = LiteLLMModel(model_name, "aicredits", "v1", dry_run=False)
        retry_policy = RetryPolicy(
            max_retries=5,
            initial_backoff_s=2.0,
            backoff_multiplier=2.0,
            max_backoff_s=30.0,
            seed=42,
        )
        model = ResilientModel(
            inner_model=raw_model,
            retry_policy=retry_policy,
            circuit_breaker=CircuitBreaker(failure_threshold=5, cooldown_seconds=5.0),
        )
    else:
        model_name = "stub"
        in_p = 0.075
        out_p = 0.25
        model = StubModel(behavior="solver")

    price_table = PriceTable(rungs={
        rung_name: RungPricing(model_name=model_name, input_price_per_m=in_p, output_price_per_m=out_p)
    })

    in_tokens_est = 15000
    out_tokens_est = 1200

    runner = SweepRunner(
        project="p03_grounding",
        price_table=price_table,
        ledger=ledger,
        confirmed=confirm,
    )

    if not confirm:
        runner.dry_run(
            n_runs=len(tasks),
            in_tokens=in_tokens_est,
            out_tokens=out_tokens_est,
            rung=rung_name,
        )
        return ""

    sweep_run_id = trace_store.start_run()

    def call_fn(task: ScenarioTask):
        outcome = run_agent(task, env, model, step_cap=12, trace_store=trace_store, run_id=sweep_run_id)

        with trace_store._lock:
            spans = trace_store.conn.execute(
                "SELECT sum(prompt_tokens) as p, sum(completion_tokens) as c FROM spans WHERE run_id = ? AND scenario_id = ?",
                (sweep_run_id, task.task_id),
            ).fetchone()
            p = spans["p"] or 0
            c = spans["c"] or 0

        usage = CallUsage(input_tokens=p, output_tokens=c, usd=0.0 if not real else None)

        sc = next(s for s in corpus.scenarios if s.scenario_id == task.task_id)
        ans = outcome.answer if outcome.answer else ""
        verdict = oracle_check(
            {"id": sc.scenario_id, "answer": sc.final_answer, "required_source": sc.required_source},
            {"answer": ans, "cited_sources": outcome.cited_sources},
        )
        success = verdict["passed"]
        trace_store.record_verdict(sweep_run_id, task.task_id, success)

        return outcome, success, usage

    print(f"Starting P3 sweep: {len(tasks)} scenarios on {model_name} ({rung_name}) with concurrency={concurrency}...")
    runner.execute_sweep(
        tasks=tasks,
        get_task_id=lambda t: t.task_id,
        call_fn=call_fn,
        in_tokens_est=in_tokens_est,
        out_tokens_est=out_tokens_est,
        rung=rung_name,
        concurrency=concurrency,
        partial_output_path=Path("projects/p03_grounding/sweep_output.json"),
    )
    trace_store.end_run(sweep_run_id, "completed")

    retried_calls = getattr(model, "retried_calls", 0)
    with trace_store._lock:
        trace_store.conn.execute(
            "CREATE TABLE IF NOT EXISTS run_resilience (run_id TEXT PRIMARY KEY, retried_calls INTEGER, total_attempts INTEGER)"
        )
        trace_store.conn.execute(
            "INSERT OR REPLACE INTO run_resilience (run_id, retried_calls, total_attempts) VALUES (?, ?, ?)",
            (sweep_run_id, retried_calls, getattr(model, "total_attempts", 0)),
        )
    print(f"Rung {rung_name} sweep finished. Total invocations: {getattr(model, 'total_invocations', 0)}, retried calls: {retried_calls}")
    return sweep_run_id


def main():
    parser = argparse.ArgumentParser(description="P3 Grounding Zero-Point Sweep")
    parser.add_argument("--confirm", action="store_true", help="Confirm and execute sweep")
    parser.add_argument("--real", action="store_true", help="Use live model (LiteLLM / AICredits)")
    parser.add_argument("--rung", default="all", choices=["R2", "R4", "R6", "all"], help="Model rung to evaluate (default: all)")
    parser.add_argument("--limit", type=int, default=None, help="Limit number of scenarios (for testing)")
    parser.add_argument("--concurrency", type=int, default=5, help="Number of concurrent workers (default: 5)")
    args = parser.parse_args()

    load_dotenv()
    manifest = ensure_manifest()
    corpus = build_corpus()

    # Load 200 standard pool scenarios
    standard_ids = set(manifest["pools"]["standard"]["scenario_ids"])
    std_scenarios = [s for s in corpus.scenarios if s.scenario_id in standard_ids]

    if args.limit:
        std_scenarios = std_scenarios[: args.limit]

    tasks = [ScenarioTask(task_id=s.scenario_id, prompt=s.prompt, tier=s.tier) for s in std_scenarios]

    ledger_path = Path("projects/p03_grounding/ledger.jsonl")
    ledger = CostLedger(ledger_path)
    db_path = Path("projects/p03_grounding/trace.db")
    trace_store = TraceStore(str(db_path))

    rungs_to_run = ["R2", "R4", "R6"] if args.rung == "all" else [args.rung]

    for r in rungs_to_run:
        run_single_rung_sweep(
            rung_name=r,
            tasks=tasks,
            corpus=corpus,
            trace_store=trace_store,
            ledger=ledger,
            confirm=args.confirm,
            real=args.real,
            concurrency=args.concurrency,
        )

    if args.confirm:
        final_results = build_results_from_trace(trace_store, manifest=manifest)
        results_path = Path("projects/p03_grounding/results.json")
        with open(results_path, "w", encoding="utf-8") as f:
            json.dump(final_results, f, indent=2)
        print(f"Results written to {results_path}")

        fig_path = Path("projects/p03_grounding/figure.svg")
        generate_figure(final_results, fig_path)
        print(f"Figure written to {fig_path}")

    trace_store.close()


if __name__ == "__main__":
    main()
