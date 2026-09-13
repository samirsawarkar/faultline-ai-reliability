"""Project P5: Judge Validation Runner.

Validates automated binary evaluators (code assertions + LLM judges using MODEL_R7=z-ai/glm-5.3)
against human ground-truth taxonomy annotations from Project P4 across a content-addressed
Train/Dev/Test split. Evaluates TPR, TNR, Cohen's kappa, Rogan-Gladen prevalence corrections,
and verifies Pre-Registered Hypothesis H3.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import random
import sqlite3
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from dotenv import load_dotenv

from faultline_p2.cost.ledger import CostLedger, LedgerEntry, PriceTable, RungPricing
from faultline_p2.env.corpus import build_corpus
from faultline_p2.judge.contracts import EvaluatorMetrics, SplitManifest
from faultline_p2.judge.evaluators import EvaluatorRegistry
from faultline_p2.judge.metrics import calculate_evaluator_metrics


EVALUATOR_SPECS = {
    "INFRASTRUCTURE_RATE_LIMIT": {"type": "code_assertion", "core_for_h3": True},
    "OVERCONSTRAINED_SEARCH_LOOP": {"type": "llm_judge", "core_for_h3": True},
    "MALFORMED_TOOL_CALL": {"type": "code_assertion", "core_for_h3": True},
    "INFRASTRUCTURE_SERVER_ERROR": {"type": "code_assertion", "core_for_h3": False},
    "MULTI_HOP_TRAVERSAL_EXHAUSTION": {"type": "code_assertion", "core_for_h3": True},
    "RETRIEVAL_FAILURE_ABSTENTION": {"type": "llm_judge", "core_for_h3": True},
    "ANSWER_EXTRACTION_TRUNCATION": {"type": "llm_judge", "core_for_h3": False},
    "PREMATURE_STOP_WRONG_HOP": {"type": "llm_judge", "core_for_h3": False},
    "MULTI_HOP_DIRECTION_ERROR": {"type": "llm_judge", "core_for_h3": False},
}


def ensure_split_manifest(csv_path: Path, manifest_path: Path, seed: int = 42) -> SplitManifest:
    """Create deterministic content-addressed Train (50%), Dev (20%), Test (30%) split manifest."""
    with open(csv_path, "r", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    # Stratified split by tier
    by_tier: Dict[str, List[str]] = defaultdict(list)
    for r in rows:
        by_tier[r["tier"]].append(r["scenario_id"])

    rng = random.Random(seed)
    train_ids: List[str] = []
    dev_ids: List[str] = []
    test_ids: List[str] = []

    for t in sorted(by_tier.keys()):
        sids = sorted(by_tier[t])
        rng.shuffle(sids)
        n = len(sids)
        n_train = int(round(n * 0.50))
        n_dev = int(round(n * 0.20))
        train_ids.extend(sids[:n_train])
        dev_ids.extend(sids[n_train : n_train + n_dev])
        test_ids.extend(sids[n_train + n_dev :])

    train_ids.sort()
    dev_ids.sort()
    test_ids.sort()

    manifest_data = {
        "spec_version": "1.0.0",
        "total_scenarios": len(rows),
        "train_count": len(train_ids),
        "dev_count": len(dev_ids),
        "test_count": len(test_ids),
        "train_ids": train_ids,
        "dev_ids": dev_ids,
        "test_ids": test_ids,
    }

    manifest_bytes = json.dumps(manifest_data, indent=2, sort_keys=True).encode()
    manifest_sha = hashlib.sha256(manifest_bytes).hexdigest()
    manifest_data["manifest_sha256"] = manifest_sha

    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest_data, f, indent=2)

    return SplitManifest(**manifest_data)


def generate_figure(results: Dict[str, Any], output_path: Path) -> None:
    """Generate publication-grade SVG chart illustrating Cohen's kappa and diagnostic metrics."""
    width = 900
    height = 520

    chart_top = 75
    chart_bottom = 360
    chart_height = chart_bottom - chart_top

    evals = results.get("evaluators", {})
    sorted_modes = sorted(evals.keys(), key=lambda m: evals[m]["cohen_kappa"], reverse=True)
    judge_model_name = results.get("metadata", {}).get("judge_model", "z-ai/glm-5.3")

    color_code = "#2b6cb0"   # Deep Blue for Code Assertion
    color_judge = "#9467bd"  # Purple for LLM Judge
    color_pass = "#2e7d32"   # Green for Kappa >= 0.70
    color_sub = "#d97706"    # Amber for Kappa < 0.70

    svg_lines = [
        f'<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg">',
        '  <rect width="100%" height="100%" fill="#ffffff"/>',
        '  <style>',
        '    .title { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; font-size: 17px; font-weight: 600; fill: #1a1a1a; }',
        '    .subtitle { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; font-size: 12px; fill: #666666; }',
        '    .axis { stroke: #cccccc; stroke-width: 1; }',
        '    .grid { stroke: #eeeeee; stroke-dasharray: 4,4; }',
        '    .thresh { stroke: #d9534f; stroke-width: 1.5; stroke-dasharray: 6,4; }',
        '    .label { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; font-size: 11px; fill: #333333; }',
        '    .val { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; font-size: 11px; font-weight: 600; }',
        '    .legend { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; font-size: 11px; fill: #555555; }',
        '    .tag-thresh { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; font-size: 10px; font-weight: 700; fill: #d9534f; }',
        '  </style>',
        '  <!-- Title -->',
        f'  <text x="{width/2}" y="28" class="title" text-anchor="middle">P5 Judge Validation: Cohen\'s \u03ba Agreement on Frozen Test Split (n=60)</text>',
        f'  <text x="{width/2}" y="46" class="subtitle" text-anchor="middle">Evaluator Architecture: Code Assertions + LLM Judge ({judge_model_name}) vs Human Ground Truth</text>',
        '  <!-- Y-Axis Grid & Labels (Kappa -0.2 to 1.0) -->',
    ]

    # Y-axis from 0.0 to 1.0
    for pct in range(0, 101, 20):
        val = pct / 100.0
        y = chart_bottom - val * chart_height
        svg_lines.append(f'  <line x1="60" y1="{y}" x2="{width - 40}" y2="{y}" class="grid"/>')
        svg_lines.append(f'  <text x="50" y="{y + 4}" class="label" text-anchor="end">\u03ba = {val:.1f}</text>')

    # Threshold Line at kappa = 0.70 (Hypothesis H3 threshold)
    y_thresh = chart_bottom - 0.70 * chart_height
    svg_lines.append(f'  <!-- H3 Threshold kappa = 0.70 -->')
    svg_lines.append(f'  <line x1="60" y1="{y_thresh}" x2="{width - 40}" y2="{y_thresh}" class="thresh"/>')
    svg_lines.append(f'  <text x="{width - 45}" y="{y_thresh - 4}" class="tag-thresh" text-anchor="end">H3 Threshold (\u03ba \u2265 0.70)</text>')

    svg_lines.append(f'  <line x1="60" y1="{chart_bottom}" x2="{width - 40}" y2="{chart_bottom}" class="axis"/>')

    n_modes = len(sorted_modes)
    slot_width = (width - 120) / n_modes
    bar_width = min(slot_width * 0.65, 52)

    for i, m in enumerate(sorted_modes):
        cx = 70 + slot_width * i + slot_width / 2
        bx = cx - bar_width / 2
        data = evals[m]
        kappa = data["cohen_kappa"]
        etype = data["evaluator_type"]
        tpr = data["tpr"]
        tnr = data["tnr"]

        bh = max(0.0, kappa) * chart_height
        by = chart_bottom - bh
        col = color_code if etype == "code_assertion" else color_judge

        svg_lines.append(f'  <!-- Mode {m} Bar -->')
        svg_lines.append(f'  <rect x="{bx}" y="{by}" width="{bar_width}" height="{bh}" fill="{col}" rx="3"/>')
        svg_lines.append(f'  <text x="{cx}" y="{by - 6}" class="val" fill="{col}" text-anchor="middle">\u03ba={kappa:.2f}</text>')

        # Labels
        short_name = m.replace("_", " ").title()
        words = short_name.split()
        if len(words) >= 3:
            line1 = " ".join(words[:2])
            line2 = " ".join(words[2:])
            svg_lines.append(f'  <text x="{cx}" y="{chart_bottom + 18}" class="label" font-weight="600" text-anchor="middle">{line1}</text>')
            svg_lines.append(f'  <text x="{cx}" y="{chart_bottom + 32}" class="label" font-weight="600" text-anchor="middle">{line2}</text>')
            type_tag = "[Code]" if etype == "code_assertion" else "[Judge]"
            svg_lines.append(f'  <text x="{cx}" y="{chart_bottom + 46}" class="legend" text-anchor="middle">{type_tag} Sens={tpr:.0%}</text>')
        else:
            svg_lines.append(f'  <text x="{cx}" y="{chart_bottom + 20}" class="label" font-weight="600" text-anchor="middle">{short_name}</text>')
            type_tag = "[Code]" if etype == "code_assertion" else "[Judge]"
            svg_lines.append(f'  <text x="{cx}" y="{chart_bottom + 36}" class="legend" text-anchor="middle">{type_tag} Sens={tpr:.0%}</text>')

    # Legend
    legend_y = 475
    svg_lines.extend([
        '  <!-- Legend -->',
        f'  <rect x="110" y="{legend_y - 12}" width="14" height="12" fill="{color_code}" rx="2"/>',
        f'  <text x="130" y="{legend_y - 2}" class="legend">Deterministic Code Assertion Evaluator</text>',
        f'  <rect x="420" y="{legend_y - 12}" width="14" height="12" fill="{color_judge}" rx="2"/>',
        f'  <text x="440" y="{legend_y - 2}" class="legend">LLM Judge Evaluator ({judge_model_name})</text>',
        f'  <line x1="750" y1="{legend_y - 6}" x2="{780}" y2="{legend_y - 6}" class="thresh"/>',
        f'  <text x="790" y="{legend_y - 2}" class="legend">H3 Target (\u03ba \u2265 0.70)</text>',
        '</svg>',
    ])

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(svg_lines))


def run_judge_validation(
    csv_path: Path,
    trace_db_path: Path,
    sweep_output_path: Path,
    manifest_path: Path,
    results_path: Path,
    figure_path: Path,
    ledger_path: Path,
    confirm: bool = False,
    real: bool = False,
) -> Dict[str, Any]:
    load_dotenv()
    manifest = ensure_split_manifest(csv_path, manifest_path)
    corpus = build_corpus()
    scenario_map = {s.scenario_id: s for s in corpus.scenarios}

    # Load human annotations
    with open(csv_path, "r", encoding="utf-8") as f:
        human_rows = {r["scenario_id"]: r for r in csv.DictReader(f)}

    # Load sweep output
    sweep_data: Dict[str, Any] = {}
    if sweep_output_path.exists():
        with open(sweep_output_path, "r", encoding="utf-8") as f:
            for item in json.load(f).get("results", []):
                sweep_data[item["task_id"]] = item

    # Load spans from trace.db
    conn = sqlite3.connect(str(trace_db_path))
    conn.row_factory = sqlite3.Row
    spans_by_sc: Dict[str, List[sqlite3.Row]] = defaultdict(list)
    for s in conn.execute("SELECT * FROM spans ORDER BY scenario_id, step_index ASC").fetchall():
        spans_by_sc[s["scenario_id"]].append(s)
    conn.close()

    judge_model = os.getenv("MODEL_R7", "z-ai/glm-5.3")
    in_price = float(os.getenv("PRICE_R7_INPUT", "0.15"))
    out_price = float(os.getenv("PRICE_R7_OUTPUT", "0.45"))

    price_table = PriceTable(rungs={
        "R7": RungPricing(model_name=judge_model, input_price_per_m=in_price, output_price_per_m=out_price)
    })
    ledger = CostLedger(ledger_path)

    # Cost Estimation
    test_ids = manifest.test_ids
    n_llm_modes = sum(1 for spec in EVALUATOR_SPECS.values() if spec["type"] == "llm_judge")
    est_llm_calls = len(test_ids) * n_llm_modes
    est_in_tokens = est_llm_calls * 450
    est_out_tokens = est_llm_calls * 60
    est_cost = (est_in_tokens / 1e6) * in_price + (est_out_tokens / 1e6) * out_price

    if not confirm:
        print("============================================================")
        print(f"DRY-RUN COST ESTIMATE: Project [p05_judge] / Judge [{judge_model}]")
        print(f"  Test Scenarios:     {len(test_ids)} (read exactly once)")
        print(f"  LLM Evaluator Calls: {est_llm_calls}")
        print(f"  Est. Tokens:        in={est_in_tokens}, out={est_out_tokens}")
        print(f"  Est. Total Cost:    ${est_cost:.6f} USD")
        print(f"  Project Cap:        $10.00 USD (Spent so far: ${ledger.spent(project='p05_judge'):.4f})")
        print("============================================================")
        return {}

    print(f"Executing Judge Validation on frozen test set (n={len(test_ids)}) using {judge_model} (real={real})...")
    registry = EvaluatorRegistry(judge_model_name=judge_model, real=real)

    # Prepare all evaluation tasks across modes and test scenarios
    tasks = []
    for mode in EVALUATOR_SPECS.keys():
        for sid in test_ids:
            sc = scenario_map.get(sid)
            tier = sc.tier if sc else "T1"
            spans = spans_by_sc.get(sid, [])
            sweep_item = sweep_data.get(sid, {})
            tasks.append((mode, sid, tier, spans, sweep_item, sc))

    # Concurrently execute evaluator queries
    verdicts: Dict[Tuple[str, str], Any] = {}
    max_workers = 12 if real else 1
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_map = {
            executor.submit(registry.evaluate_mode, m, s, t, sp, sw, sc): (m, s)
            for m, s, t, sp, sw, sc in tasks
        }
        for fut in as_completed(future_map):
            m, s = future_map[fut]
            try:
                verdicts[(m, s)] = fut.result()
            except Exception as exc:
                print(f"Warning: Evaluator failed for {m}/{s}: {exc}")

    evaluator_results: Dict[str, Any] = {}
    total_tokens = {"prompt": 0, "completion": 0}
    core_modes_tested = 0
    core_modes_passing_h3 = 0

    for mode, spec in EVALUATOR_SPECS.items():
        preds: List[bool] = []
        gts: List[bool] = []

        for sid in test_ids:
            h_row = human_rows.get(sid, {})
            human_mode = h_row.get("axial_failure_mode", "")
            gt_bool = (human_mode == mode)

            v = verdicts.get((mode, sid))
            detected = v.detected if v else False
            preds.append(detected)
            gts.append(gt_bool)

            if v and v.tokens_used:
                total_tokens["prompt"] += v.tokens_used.get("prompt", 0)
                total_tokens["completion"] += v.tokens_used.get("completion", 0)

        # Calculate metrics
        metrics = calculate_evaluator_metrics(mode, spec["type"], preds, gts)
        evaluator_results[mode] = metrics.model_dump()

        if spec["core_for_h3"]:
            core_modes_tested += 1
            if metrics.cohen_kappa >= 0.70:
                core_modes_passing_h3 += 1

    # Record cost in ledger
    if real and (total_tokens["prompt"] > 0 or total_tokens["completion"] > 0):
        cost_usd = (total_tokens["prompt"] / 1e6) * in_price + (total_tokens["completion"] / 1e6) * out_price
        ledger.record(
            LedgerEntry(
                run_id=f"p05_{manifest.manifest_sha256[:8]}",
                project="p05_judge",
                rung="R7",
                input_tokens=total_tokens["prompt"],
                output_tokens=total_tokens["completion"],
                usd=cost_usd,
                timestamp_utc=datetime.now(timezone.utc).isoformat(),
            )
        )

    # Hypothesis H3
    h3_status = "CONFIRMED" if core_modes_passing_h3 >= 3 else "FALSIFIED"

    final_results = {
        "metadata": {
            "project": "P5",
            "reference": "MEC v1.0",
            "judge_model": judge_model,
            "manifest_sha256": manifest.manifest_sha256,
            "test_sample_size": len(test_ids),
            "total_evaluators": len(EVALUATOR_SPECS),
            "tokens_used": total_tokens,
            "spend_usd": ledger.spent(project="p05_judge"),
        },
        "split": {
            "train_count": manifest.train_count,
            "dev_count": manifest.dev_count,
            "test_count": manifest.test_count,
        },
        "evaluators": evaluator_results,
        "hypotheses": {
            "H3": {
                "claim": "A cheap judge reaches kappa >= 0.7 against human labels on >=3 of 5 modes",
                "status": h3_status,
                "core_modes_tested": core_modes_tested,
                "core_modes_meeting_threshold": core_modes_passing_h3,
                "threshold_kappa": 0.70,
                "evidence": (
                    f"Measured Cohen's kappa >= 0.70 on {core_modes_passing_h3} of {core_modes_tested} core evaluated modes "
                    f"against human labels on the frozen single-pass test set (n={len(test_ids)})."
                ),
            }
        },
    }

    results_path.parent.mkdir(parents=True, exist_ok=True)
    with open(results_path, "w", encoding="utf-8") as f:
        json.dump(final_results, f, indent=2)

    generate_figure(final_results, figure_path)
    print(f"P5 Results saved to {results_path}")
    print(f"P5 Figure saved to {figure_path}")
    print(f"Hypothesis H3: {h3_status} ({core_modes_passing_h3}/{core_modes_tested} core modes >= 0.70).")

    return final_results


def main():
    parser = argparse.ArgumentParser(description="P05 Judge Validation Runner")
    parser.add_argument("--confirm", action="store_true", help="Confirm and execute validation on test split")
    parser.add_argument("--real", action="store_true", help="Use live LiteLLM judge endpoint (AICredits)")
    parser.add_argument("--csv", default="projects/p04_taxonomy/coding_sheet.csv", help="Human coding sheet path")
    parser.add_argument("--db", default="projects/p03_grounding/trace.db", help="Trace DB path")
    parser.add_argument("--sweep-json", default="projects/p03_grounding/sweep_output.json", help="Sweep output JSON")
    parser.add_argument("--manifest-out", default="projects/p05_judge/manifest.json", help="Split manifest destination")
    parser.add_argument("--results-out", default="projects/p05_judge/results.json", help="Results destination")
    parser.add_argument("--figure-out", default="projects/p05_judge/figure.svg", help="Figure destination")
    parser.add_argument("--ledger", default="projects/p05_judge/ledger.jsonl", help="Ledger path")
    args = parser.parse_args()

    run_judge_validation(
        csv_path=Path(args.csv),
        trace_db_path=Path(args.db),
        sweep_output_path=Path(args.sweep_json),
        manifest_path=Path(args.manifest_out),
        results_path=Path(args.results_out),
        figure_path=Path(args.figure_out),
        ledger_path=Path(args.ledger),
        confirm=args.confirm,
        real=args.real,
    )


if __name__ == "__main__":
    main()
