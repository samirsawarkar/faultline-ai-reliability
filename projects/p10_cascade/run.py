"""Project P10: Calibrated Cheap->Frontier Cascade Simulation.

Simulates rule-based escalation from R2 (glm-5.3-flash) to R4 (gpt-5.6-luna)
without an LLM judge, fitting thresholds on train and evaluating on held-out test.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sqlite3
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

from faultline_p2.cascade.simulate import (
    evaluate,
    fit,
    get_all_candidate_policies,
    pareto_frontier,
    split_scenarios,
)
from faultline_p2.cost.ledger import CostLedger


def load_sweep_runs(sweep_path: Path) -> Dict[str, Dict[str, Any]]:
    """Load runs from a sweep JSON file, keyed by scenario_id."""
    if not sweep_path.exists():
        return {}
    try:
        data = json.loads(sweep_path.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"Warning: could not read {sweep_path}: {e}")
        return {}

    runs: Dict[str, Dict[str, Any]] = {}
    if isinstance(data, list):
        for item in data:
            sid = item.get("scenario_id") or item.get("task_id")
            if sid:
                runs[sid] = item
    elif isinstance(data, dict):
        runs = data
    return runs


def load_p6_pairs(db_path: Path) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Load paired runs from P6 trace.db for R2 and R4.

    Pricing per 1M tokens:
      R2 (glm-5.3-flash): in $0.14, out $0.28
      R4 (gpt-5.6-luna):   in $0.60, out $2.40

    Returns (as_run_pairs, infra_excluded_pairs).
    """
    if not db_path.exists():
        return [], []

    conn = sqlite3.connect(str(db_path))
    cur = conn.cursor()

    def _fetch_spans(run_id: str) -> Dict[str, List[Tuple[Any, ...]]]:
        cur.execute(
            """
            SELECT scenario_id, step_index, prompt_tokens, completion_tokens, termination_reason, verdict
            FROM spans
            WHERE run_id = ?
            ORDER BY scenario_id, step_index
            """,
            (run_id,),
        )
        grouped: Dict[str, List[Tuple[Any, ...]]] = defaultdict(list)
        for row in cur.fetchall():
            grouped[row[0]].append(row)
        return grouped

    r2_spans = _fetch_spans("p06_r2_7e0a1b79")
    r4_spans = _fetch_spans("p06_r4_7e0a1b79")
    conn.close()

    def _build_run_dict(spans: List[Tuple[Any, ...]], in_price: float, out_price: float) -> Dict[str, Any]:
        max_step = max(s[1] for s in spans) if spans else 0
        tot_prompt = sum(s[2] or 0 for s in spans)
        tot_comp = sum(s[3] or 0 for s in spans)
        cost = (tot_prompt * in_price + tot_comp * out_price) / 1e6
        verdict = bool(max(s[5] or 0 for s in spans)) if spans else False
        last_span = max(spans, key=lambda s: s[1]) if spans else (None, 0, 0, 0, "unknown", 0)
        status = last_span[4] or "unknown"
        all_zero_comp = all(s[3] is None or s[3] == 0 for s in spans)
        infra_dead = (max_step <= 1 and all_zero_comp)
        return {
            "grounded": verdict,
            "status": status,
            "steps_used": max_step,
            "cost_usd": cost,
            "cited_sources": [],
            "infra_dead": infra_dead,
        }

    common_ids = sorted(set(r2_spans.keys()) & set(r4_spans.keys()))
    as_run_pairs: List[Dict[str, Any]] = []
    infra_excluded_pairs: List[Dict[str, Any]] = []

    for sc in common_ids:
        r2_info = _build_run_dict(r2_spans[sc], 0.14, 0.28)
        r4_info = _build_run_dict(r4_spans[sc], 0.60, 2.40)
        pair = {
            "scenario_id": sc,
            "r2": r2_info,
            "r4": r4_info,
            "r2_grounded": r2_info["grounded"],
            "r4_grounded": r4_info["grounded"],
            "r2_cost": r2_info["cost_usd"],
            "r4_cost": r4_info["cost_usd"],
            "r4_infra_dead": r4_info["infra_dead"],
        }
        as_run_pairs.append(pair)
        if not r4_info["infra_dead"]:
            infra_excluded_pairs.append(pair)

    return as_run_pairs, infra_excluded_pairs


def simulate_cascade(
    r2_file: Path,
    r4_file: Path,
    p6_db: Path,
    output_dir: Path,
) -> Dict[str, Any]:
    """Run full calibrated cascade simulation and write results.json."""
    output_dir.mkdir(parents=True, exist_ok=True)

    r2_runs = load_sweep_runs(r2_file)
    r4_runs = load_sweep_runs(r4_file)

    common_ids = sorted(set(r2_runs.keys()) & set(r4_runs.keys()))
    if not common_ids:
        print(f"No common scenarios found between {r2_file} ({len(r2_runs)}) and {r4_file} ({len(r4_runs)})")

    pairs: List[Dict[str, Any]] = []
    for sid in common_ids:
        pairs.append({
            "scenario_id": sid,
            "r2": r2_runs[sid],
            "r4": r4_runs[sid],
            "r2_grounded": bool(r2_runs[sid].get("grounded", False)),
            "r4_grounded": bool(r4_runs[sid].get("grounded", False)),
            "r2_cost": float(r2_runs[sid].get("cost_usd", 0.0)),
            "r4_cost": float(r4_runs[sid].get("cost_usd", 0.0)),
        })

    train_ids, test_ids = split_scenarios(common_ids, train_frac=0.7)
    pair_map = {p["scenario_id"]: p for p in pairs}
    train_pairs = [pair_map[sid] for sid in train_ids]
    test_pairs = [pair_map[sid] for sid in test_ids]

    split_info = {
        "train_ids": train_ids,
        "test_ids": test_ids,
        "train_count": len(train_ids),
        "test_count": len(test_ids),
        "train_sha256": hashlib.sha256(",".join(train_ids).encode("utf-8")).hexdigest(),
        "test_sha256": hashlib.sha256(",".join(test_ids).encode("utf-8")).hexdigest(),
        "all_sha256": hashlib.sha256(",".join(common_ids).encode("utf-8")).hexdigest(),
    }

    # Fit thresholds on train, evaluate on test
    fit_res = fit(train_pairs, test_pairs)
    chosen_thresholds = fit_res["chosen_thresholds"]
    train_metrics = fit_res["train_metrics"]
    test_metrics = fit_res["test_metrics"]
    side_by_side = fit_res["side_by_side"]
    test_frontier = fit_res["test_frontier"]

    # Replicate on P6 trace.db
    p6_as_run, p6_infra_excluded = load_p6_pairs(p6_db)
    p6_replicate: Dict[str, Any] = {}

    if p6_as_run:
        p6_tr_ar, p6_te_ar = split_scenarios([p["scenario_id"] for p in p6_as_run], train_frac=0.7)
        p6_ar_map = {p["scenario_id"]: p for p in p6_as_run}
        p6_ar_train = [p6_ar_map[sid] for sid in p6_tr_ar]
        p6_ar_test = [p6_ar_map[sid] for sid in p6_te_ar]
        fit_p6_ar = fit(p6_ar_train, p6_ar_test)

        p6_replicate["as_run"] = {
            "n_pairs": len(p6_as_run),
            "r2_only": evaluate("r2_only", p6_as_run),
            "r4_only": evaluate("r4_only", p6_as_run),
            "chosen_thresholds": fit_p6_ar["chosen_thresholds"],
            "side_by_side": fit_p6_ar["side_by_side"],
            "test_frontier": fit_p6_ar["test_frontier"],
        }

    if p6_infra_excluded:
        p6_tr_ie, p6_te_ie = split_scenarios([p["scenario_id"] for p in p6_infra_excluded], train_frac=0.7)
        p6_ie_map = {p["scenario_id"]: p for p in p6_infra_excluded}
        p6_ie_train = [p6_ie_map[sid] for sid in p6_tr_ie]
        p6_ie_test = [p6_ie_map[sid] for sid in p6_te_ie]
        fit_p6_ie = fit(p6_ie_train, p6_ie_test)

        p6_replicate["infra_excluded"] = {
            "n_pairs": len(p6_infra_excluded),
            "infra_dead_count": len(p6_as_run) - len(p6_infra_excluded),
            "r2_only": evaluate("r2_only", p6_infra_excluded),
            "r4_only": evaluate("r4_only", p6_infra_excluded),
            "chosen_thresholds": fit_p6_ie["chosen_thresholds"],
            "side_by_side": fit_p6_ie["side_by_side"],
            "test_frontier": fit_p6_ie["test_frontier"],
        }

    # Spend from ledger
    ledger_path = output_dir / "ledger.jsonl"
    spend_usd = 0.0
    if ledger_path.exists():
        try:
            ledger = CostLedger(ledger_path=ledger_path)
            spend_usd = round(ledger.spent(project="p10_cascade"), 4)
        except Exception:
            pass

    results_data: Dict[str, Any] = {
        "spec_version": "2.0.0",
        "experiment": "p10_cascade",
        "n_pairs": len(common_ids),
        "split": split_info,
        "split_ids_sha256": split_info["all_sha256"],
        "chosen_thresholds": chosen_thresholds,
        "baselines": {
            "r2_only": side_by_side.get("r2_only"),
            "r4_only": side_by_side.get("r4_only"),
        },
        "train_metrics": train_metrics,
        "test_metrics": test_metrics,
        "side_by_side": side_by_side,
        "all_test_metrics": fit_res.get("all_test_metrics", {}),
        "frontier_points": test_frontier,
        "p6_replicate": p6_replicate,
        "spend_usd": spend_usd,
    }

    results_file = output_dir / "results.json"
    results_file.write_text(json.dumps(results_data, indent=2), encoding="utf-8")

    # Print summary
    print("\n" + "=" * 65)
    print(f"P10 Cascade Simulation Summary (N={len(common_ids)} pairs):")
    print(f"  Split: {len(train_ids)} train / {len(test_ids)} test (SHA-256: {split_info['all_sha256'][:12]}...)")
    print(f"  Chosen Thresholds (fit on train):")
    print(f"    - escalate_if_steps_ge_t: t={chosen_thresholds['escalate_if_steps_ge_t']}")
    print(f"    - escalate_if_not_answered_or_steps_ge_t: t={chosen_thresholds['escalate_if_not_answered_or_steps_ge_t']}")
    print(f"\n  Headline Results (Held-out Test Split, N={len(test_ids)}):")
    for pol, metric in side_by_side.items():
        if metric and metric.get("test"):
            t_m = metric["test"]
            print(f"    * {pol:<40}: pass={t_m['pass_rate']*100:5.1f}% [CI: {t_m['wilson_ci'][0]:.3f}, {t_m['wilson_ci'][1]:.3f}]  cost=${t_m['mean_cost']:.4f}  esc={t_m['escalation_rate']*100:4.1f}%")
    print(f"\n  Pareto Frontier: {len(test_frontier)} non-dominated policies found")
    if p6_replicate:
        print(f"  P6 Replicate:")
        if "as_run" in p6_replicate:
            print(f"    - as_run: {p6_replicate['as_run']['n_pairs']} pairs")
        if "infra_excluded" in p6_replicate:
            print(f"    - infra_excluded: {p6_replicate['infra_excluded']['n_pairs']} pairs ({p6_replicate['infra_excluded']['infra_dead_count']} infra_dead dropped)")
    print(f"  Project Spend: ${spend_usd:.4f} USD")
    print("=" * 65)
    print(f"Results written to {results_file}")

    return results_data


def print_dry_run() -> None:
    """Print step 2 dry run command and token cost estimate."""
    p12_runner_cmd = (
        ".venv/bin/python projects/p12_attribution/run.py --dry-run --rung R4 --arms A "
        "--scenarios 150 --project p10_cascade --output-dir projects/p10_cascade"
    )
    # Estimate at P12-measured R4 tokens: 55002 in / 2891 out per run
    in_tok = 55002
    out_tok = 2891
    n_scenarios = 140
    in_cost = n_scenarios * in_tok * 0.60 / 1e6
    out_cost = n_scenarios * out_tok * 2.40 / 1e6
    total_cost = in_cost + out_cost

    print("\n" + "=" * 65)
    print("P10 Calibrated Cascade: Step 2 Dry-Run Cost Estimate")
    print("=" * 65)
    print("Step 2 P12-Runner Command:")
    print(f"  {p12_runner_cmd}")
    print("\n140-Scenario Estimate at P12-Measured R4 Tokens:")
    print(f"  Tokens per run:  {in_tok:,} in / {out_tok:,} out")
    print(f"  Total tokens:    {n_scenarios * in_tok:,} in / {n_scenarios * out_tok:,} out")
    print(f"  Pricing:         $0.60 / 1M in, $2.40 / 1M out")
    print(f"  Input cost:      ${in_cost:.4f} USD")
    print(f"  Output cost:     ${out_cost:.4f} USD")
    print(f"  Total est cost:  ${total_cost:.4f} USD  (within $8.00 p10 budget cap)")
    print("=" * 65)


def main() -> None:
    parser = argparse.ArgumentParser(description="P10 Calibrated Cascade Simulation")
    parser.add_argument("--simulate", action="store_true", default=True, help="Run simulation on sweep files")
    parser.add_argument(
        "--r2-file",
        type=str,
        default="projects/p12_attribution/sweep_output_R2_A.json",
        help="Path to R2 Arm A sweep output JSON",
    )
    parser.add_argument(
        "--r4-file",
        type=str,
        default="projects/p12_attribution/sweep_output_R4_A.json",
        help="Path to R4 Arm A sweep output JSON",
    )
    parser.add_argument(
        "--p6-db",
        type=str,
        default="projects/p06_passk/trace.db",
        help="Path to P6 trace.db for secondary replicate",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="projects/p10_cascade",
        help="Output directory for results.json and artifacts",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print step 2 P12 runner command and 140-scenario cost estimate without simulation",
    )

    args = parser.parse_args()

    if args.dry_run:
        print_dry_run()
        return

    simulate_cascade(
        r2_file=Path(args.r2_file),
        r4_file=Path(args.r4_file),
        p6_db=Path(args.p6_db),
        output_dir=Path(args.output_dir),
    )


if __name__ == "__main__":
    main()
