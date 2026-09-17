"""Analysis layer for Project P8 (MCPTox Tool Poisoning and Provenance Contract).

Inputs:
  - projects/p08_mcptox/results.json
  - projects/p08_mcptox/manifest.json
  - projects/p08_mcptox/trace.db
  - projects/p08_mcptox/logs/arm_b/<rung>/responses.jsonl
  - projects/p08_mcptox/logs/arm_a/<rung>/*.eval
  - projects/p08_mcptox/replay_results.json
  - projects/p08_mcptox/ledger.jsonl

Outputs:
  - projects/p08_mcptox/analysis.json
"""
from __future__ import annotations

import json
from pathlib import Path
import sqlite3
from typing import Any, Dict, List, Optional, Tuple
from collections import Counter, defaultdict
import numpy as np

from inspect_ai.log import read_eval_log
from faultline_p2.stats.intervals import wilson_interval
from faultline_p2.stats.paired import mcnemar_from_pairs


def get_arm_a_eval_log(arm_a_dir: Path) -> Any:
    """Find and return the successful 300-sample eval log in arm_a dir."""
    eval_files = sorted(list(arm_a_dir.glob("*.eval")))
    if not eval_files:
        raise FileNotFoundError(f"No .eval files found in {arm_a_dir}")
    
    # Select eval file with status success and 300 samples
    for ef in eval_files:
        log = read_eval_log(str(ef))
        if getattr(log, "status", None) == "success" and len(getattr(log, "samples", [])) == 300:
            return log
            
    # Fallback to file with most samples
    best_log = None
    max_samples = -1
    for ef in eval_files:
        log = read_eval_log(str(ef))
        n_samples = len(getattr(log, "samples", []))
        if n_samples > max_samples:
            max_samples = n_samples
            best_log = log
    return best_log


def compute_rates(success_count: int, valid_count: int, total_count: int) -> Dict[str, Any]:
    """Compute ASR over valid and over all with Wilson 95% CIs."""
    asr_valid = float(success_count / valid_count) if valid_count > 0 else 0.0
    ci_valid = list(wilson_interval(success_count, valid_count)) if valid_count > 0 else [0.0, 0.0]
    
    asr_all = float(success_count / total_count) if total_count > 0 else 0.0
    ci_all = list(wilson_interval(success_count, total_count)) if total_count > 0 else [0.0, 0.0]
    
    return {
        "n": total_count,
        "n_valid": valid_count,
        "success": success_count,
        "asr_over_valid": asr_valid,
        "wilson_ci_over_valid": ci_valid,
        "asr_over_all": asr_all,
        "wilson_ci_over_all": ci_all,
    }


def run_analysis(base_dir: Optional[Path] = None) -> Dict[str, Any]:
    if base_dir is None:
        base_dir = Path("projects/p08_mcptox")
        
    results_path = base_dir / "results.json"
    manifest_path = base_dir / "manifest.json"
    trace_db_path = base_dir / "trace.db"
    replay_path = base_dir / "replay_results.json"
    ledger_path = base_dir / "ledger.jsonl"
    logs_dir = base_dir / "logs"
    output_path = base_dir / "analysis.json"

    with open(results_path, "r", encoding="utf-8") as f:
        results_data = json.load(f)
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest_data = json.load(f)
    with open(replay_path, "r", encoding="utf-8") as f:
        replay_data = json.load(f)

    # Cost from ledger.jsonl
    ledger_costs: Dict[str, float] = defaultdict(float)
    if ledger_path.exists():
        with open(ledger_path, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                entry = json.loads(line)
                rid = entry.get("run_id")
                if rid:
                    ledger_costs[rid] += float(entry.get("usd", 0.0))

    # Spans from trace.db
    spans_conn = sqlite3.connect(str(trace_db_path))
    spans_cur = spans_conn.cursor()

    rungs = ["R1", "R2", "R3", "R4", "R5", "R6"]
    paradigms = ["Template-1", "Template-2", "Template-3"]
    security_risks = sorted(list(manifest_data.get("counts", {}).get("subsample", {}).get("security_risk", {}).keys()))

    analysis_data: Dict[str, Any] = {
        "spec_version": "v1.3",
        "experiment": "p08_mcptox",
        "rungs": {},
        "pooled": {},
    }

    # Tracking for pooled calculations
    pooled_paradigm_counts: Dict[str, Dict[str, Dict[str, int]]] = {
        p: {"arm_a": defaultdict(int), "arm_b": defaultdict(int)} for p in paradigms
    }
    pooled_risk_counts: Dict[str, Dict[str, Dict[str, int]]] = {
        r: {"arm_a": defaultdict(int), "arm_b": defaultdict(int)} for r in security_risks
    }

    all_pairs_a_success: List[bool] = []
    all_pairs_b_success: List[bool] = []

    pooled_retry_mechanics = {
        "step1_allow": 0,
        "step1_blocked": 0,
        "step1_no_call": 0,
        "retried_step1_blocked": 0,
        "retried_allowed": 0,
        "retried_blocked_again": 0,
        "step2_rejected_call": 0,
        "step2_no_call": 0,
        "residual_leak_success": 0,
        "retried_allowed_categories": defaultdict(int),
    }

    for rung in rungs:
        rung_model = results_data["rungs"][rung]["model"]
        
        # 1. Arm A
        arm_a_log = get_arm_a_eval_log(logs_dir / "arm_a" / rung)
        arm_a_samples: Dict[str, Dict[str, Any]] = {}
        sample_meta: Dict[str, Dict[str, Any]] = {}

        for sample in arm_a_log.samples:
            sid = sample.id
            sample_meta[sid] = sample.metadata
            score = sample.scores.get("mcptox_scorer") if sample.scores else None
            cat = score.metadata.get("outcome", "Invalid") if (score and score.metadata) else "Invalid"
            arm_a_samples[sid] = {
                "category": cat,
                "success": (cat == "Success"),
                "valid": (cat != "Invalid"),
                "paradigm": sample.metadata.get("paradigm"),
                "security_risk": sample.metadata.get("security_risk"),
                "server_name": sample.metadata.get("server_name"),
            }

        # 2. Arm B
        arm_b_file = logs_dir / "arm_b" / rung / "responses.jsonl"
        arm_b_entries: List[Dict[str, Any]] = []
        with open(arm_b_file, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    arm_b_entries.append(json.loads(line))

        arm_b_by_sample: Dict[str, Dict[int, Dict[str, Any]]] = defaultdict(dict)
        for entry in arm_b_entries:
            arm_b_by_sample[entry["sample_id"]][entry["step"]] = entry

        arm_b_samples: Dict[str, Dict[str, Any]] = {}
        
        # Retry mechanics
        step1_outcomes = Counter()
        step1_blocked_by_rule = Counter()
        retried_blocked_total = 0
        retried_allowed_total = 0
        retried_blocked_again_total = 0
        step2_rejected_call_total = 0
        step2_no_call_total = 0
        retried_allowed_cats = Counter()

        for sid, steps in arm_b_by_sample.items():
            meta = sample_meta[sid]
            p = meta.get("paradigm")
            sr = meta.get("security_risk")
            
            if 2 in steps:
                # Step 1 was blocked, so sample was retried
                s1 = steps[1]
                s2 = steps[2]
                rule = s1["decision"]["rule"]
                step1_outcomes["blocked"] += 1
                step1_blocked_by_rule[rule] += 1
                retried_blocked_total += 1

                final_cat = s2["category"]
                if s2["decision"]["rule"] == "allow":
                    retried_allowed_total += 1
                    retried_allowed_cats[final_cat] += 1
                    pooled_retry_mechanics["retried_allowed_categories"][final_cat] += 1
                else:
                    retried_blocked_again_total += 1
                    if s2.get("parsed_calls"):
                        step2_rejected_call_total += 1
                    else:
                        step2_no_call_total += 1

                arm_b_samples[sid] = {
                    "category": final_cat,
                    "success": (final_cat == "Success"),
                    "valid": (final_cat != "Invalid"),
                    "retried": True,
                    "step1_rule": rule,
                    "final_rule": s2["decision"]["rule"],
                    "paradigm": p,
                    "security_risk": sr,
                }
            else:
                # Only step 1
                s1 = steps[1]
                final_cat = s1["category"]
                if not s1.get("parsed_calls"):
                    step1_outcomes["no_call"] += 1
                elif s1["decision"]["rule"] == "allow":
                    step1_outcomes["allow"] += 1
                else:
                    step1_outcomes["blocked"] += 1
                    step1_blocked_by_rule[s1["decision"]["rule"]] += 1

                arm_b_samples[sid] = {
                    "category": final_cat,
                    "success": (final_cat == "Success"),
                    "valid": (final_cat != "Invalid"),
                    "retried": False,
                    "step1_rule": s1["decision"]["rule"],
                    "final_rule": s1["decision"]["rule"],
                    "paradigm": p,
                    "security_risk": sr,
                }

        residual_leak = retried_allowed_cats.get("Success", 0)
        pooled_retry_mechanics["step1_allow"] += step1_outcomes["allow"]
        pooled_retry_mechanics["step1_blocked"] += retried_blocked_total
        pooled_retry_mechanics["step1_no_call"] += step1_outcomes["no_call"]
        pooled_retry_mechanics["retried_step1_blocked"] += retried_blocked_total
        pooled_retry_mechanics["retried_allowed"] += retried_allowed_total
        pooled_retry_mechanics["retried_blocked_again"] += retried_blocked_again_total
        pooled_retry_mechanics["step2_rejected_call"] += step2_rejected_call_total
        pooled_retry_mechanics["step2_no_call"] += step2_no_call_total
        pooled_retry_mechanics["residual_leak_success"] += residual_leak

        # Breakdown by Paradigm & Security Risk for this rung
        rung_paradigm_data = {"arm_a": {}, "arm_b": {}}
        for p in paradigms:
            # Arm A
            a_tot = sum(1 for s in arm_a_samples.values() if s["paradigm"] == p)
            a_val = sum(1 for s in arm_a_samples.values() if s["paradigm"] == p and s["valid"])
            a_suc = sum(1 for s in arm_a_samples.values() if s["paradigm"] == p and s["success"])
            rung_paradigm_data["arm_a"][p] = compute_rates(a_suc, a_val, a_tot)
            pooled_paradigm_counts[p]["arm_a"]["total"] += a_tot
            pooled_paradigm_counts[p]["arm_a"]["valid"] += a_val
            pooled_paradigm_counts[p]["arm_a"]["success"] += a_suc

            # Arm B
            b_tot = sum(1 for s in arm_b_samples.values() if s["paradigm"] == p)
            b_val = sum(1 for s in arm_b_samples.values() if s["paradigm"] == p and s["valid"])
            b_suc = sum(1 for s in arm_b_samples.values() if s["paradigm"] == p and s["success"])
            rung_paradigm_data["arm_b"][p] = compute_rates(b_suc, b_val, b_tot)
            pooled_paradigm_counts[p]["arm_b"]["total"] += b_tot
            pooled_paradigm_counts[p]["arm_b"]["valid"] += b_val
            pooled_paradigm_counts[p]["arm_b"]["success"] += b_suc

        rung_risk_data = {"arm_a": {}, "arm_b": {}}
        for r in security_risks:
            a_tot = sum(1 for s in arm_a_samples.values() if s["security_risk"] == r)
            a_val = sum(1 for s in arm_a_samples.values() if s["security_risk"] == r and s["valid"])
            a_suc = sum(1 for s in arm_a_samples.values() if s["security_risk"] == r and s["success"])
            rung_risk_data["arm_a"][r] = compute_rates(a_suc, a_val, a_tot)
            pooled_risk_counts[r]["arm_a"]["total"] += a_tot
            pooled_risk_counts[r]["arm_a"]["valid"] += a_val
            pooled_risk_counts[r]["arm_a"]["success"] += a_suc

            b_tot = sum(1 for s in arm_b_samples.values() if s["security_risk"] == r)
            b_val = sum(1 for s in arm_b_samples.values() if s["security_risk"] == r and s["valid"])
            b_suc = sum(1 for s in arm_b_samples.values() if s["security_risk"] == r and s["success"])
            rung_risk_data["arm_b"][r] = compute_rates(b_suc, b_val, b_tot)
            pooled_risk_counts[r]["arm_b"]["total"] += b_tot
            pooled_risk_counts[r]["arm_b"]["valid"] += b_val
            pooled_risk_counts[r]["arm_b"]["success"] += b_suc

        # Pairwise comparison on this rung
        attacks_removed = 0
        attacks_induced = 0
        both_success = 0
        both_fail = 0

        for sid in arm_a_samples:
            a_s = arm_a_samples[sid]["success"]
            b_s = arm_b_samples[sid]["success"]
            all_pairs_a_success.append(a_s)
            all_pairs_b_success.append(b_s)
            if a_s and not b_s:
                attacks_removed += 1
            elif b_s and not a_s:
                attacks_induced += 1
            elif a_s and b_s:
                both_success += 1
            else:
                both_fail += 1

        # Spans tokens and latency
        # Arm A spans
        spans_cur.execute(
            "SELECT scenario_id, sum(prompt_tokens), sum(completion_tokens) FROM spans WHERE run_id = ? GROUP BY scenario_id",
            (f"p08_armA_{rung}",),
        )
        arm_a_span_rows = spans_cur.fetchall()
        a_prompts = [r[1] for r in arm_a_span_rows]
        a_comps = [r[2] for r in arm_a_span_rows]
        a_totals = [r[1] + r[2] for r in arm_a_span_rows]

        # Arm B spans
        spans_cur.execute(
            "SELECT scenario_id, sum(prompt_tokens), sum(completion_tokens), sum(latency_ms) FROM spans WHERE run_id = ? GROUP BY scenario_id",
            (f"p08_armB_{rung}",),
        )
        arm_b_span_rows = spans_cur.fetchall()
        b_prompts = [r[1] for r in arm_b_span_rows]
        b_comps = [r[2] for r in arm_b_span_rows]
        b_totals = [r[1] + r[2] for r in arm_b_span_rows]
        b_latencies = [r[3] for r in arm_b_span_rows]

        arm_a_success_count = sum(1 for s in arm_a_samples.values() if s["success"])
        arm_a_valid_count = sum(1 for s in arm_a_samples.values() if s["valid"])
        arm_b_success_count = sum(1 for s in arm_b_samples.values() if s["success"])
        arm_b_valid_count = sum(1 for s in arm_b_samples.values() if s["valid"])

        analysis_data["rungs"][rung] = {
            "model": rung_model,
            "arm_a": {
                **compute_rates(arm_a_success_count, arm_a_valid_count, len(arm_a_samples)),
                "by_paradigm": rung_paradigm_data["arm_a"],
                "by_security_risk": rung_risk_data["arm_a"],
                "tokens": {
                    "mean_prompt": float(np.mean(a_prompts)) if a_prompts else 0.0,
                    "mean_completion": float(np.mean(a_comps)) if a_comps else 0.0,
                    "mean_total": float(np.mean(a_totals)) if a_totals else 0.0,
                },
                "latency_ms": None,
                "latency_note": "Arm A per-call gateway latency is not recorded in spans",
                "spend_usd": float(round(ledger_costs[f"p08_armA_{rung}"], 6)),
            },
            "arm_b": {
                **compute_rates(arm_b_success_count, arm_b_valid_count, len(arm_b_samples)),
                "by_paradigm": rung_paradigm_data["arm_b"],
                "by_security_risk": rung_risk_data["arm_b"],
                "tokens": {
                    "mean_prompt": float(np.mean(b_prompts)) if b_prompts else 0.0,
                    "mean_completion": float(np.mean(b_comps)) if b_comps else 0.0,
                    "mean_total": float(np.mean(b_totals)) if b_totals else 0.0,
                },
                "latency_ms": {
                    "p50": float(round(np.percentile(b_latencies, 50), 2)) if b_latencies else 0.0,
                    "p95": float(round(np.percentile(b_latencies, 95), 2)) if b_latencies else 0.0,
                },
                "spend_usd": float(round(ledger_costs[f"p08_armB_{rung}"], 6)),
                "false_block_proxy": int(results_data["rungs"][rung]["arm_b"].get("false_block_proxy", 0)),
            },
            "retry_mechanics": {
                "step1_outcomes": {
                    "allow": int(step1_outcomes["allow"]),
                    "blocked_total": int(retried_blocked_total),
                    "blocked_by_rule": dict(step1_blocked_by_rule),
                    "no_call": int(step1_outcomes["no_call"]),
                },
                "retried_step1_blocked": int(retried_blocked_total),
                "retried_allowed": int(retried_allowed_total),
                "retried_blocked_again": int(retried_blocked_again_total),
                "step2_rejected_call": int(step2_rejected_call_total),
                "step2_no_call": int(step2_no_call_total),
                "retried_allowed_categories": dict(retried_allowed_cats),
                "residual_leak_success": int(residual_leak),
            },
            "comparison": {
                "attacks_removed": int(attacks_removed),
                "attacks_induced": int(attacks_induced),
                "both_success": int(both_success),
                "both_fail": int(both_fail),
                "false_block_proxy": int(results_data["rungs"][rung]["arm_b"].get("false_block_proxy", 0)),
            },
        }

    # Pooled summaries
    pooled_by_paradigm = {}
    for p in paradigms:
        ca = pooled_paradigm_counts[p]["arm_a"]
        cb = pooled_paradigm_counts[p]["arm_b"]
        pooled_by_paradigm[p] = {
            "arm_a": compute_rates(ca["success"], ca["valid"], ca["total"]),
            "arm_b": compute_rates(cb["success"], cb["valid"], cb["total"]),
        }

    pooled_by_risk = {}
    for r in security_risks:
        ca = pooled_risk_counts[r]["arm_a"]
        cb = pooled_risk_counts[r]["arm_b"]
        pooled_by_risk[r] = {
            "arm_a": compute_rates(ca["success"], ca["valid"], ca["total"]),
            "arm_b": compute_rates(cb["success"], cb["valid"], cb["total"]),
        }

    # Pooled McNemar test across all 1800 pairs
    pooled_mcnemar = mcnemar_from_pairs(all_pairs_a_success, all_pairs_b_success)
    
    # Replay passthrough
    replay_pooled = replay_data.get("pooled", {})
    replay_summary = {
        "pooled": {
            "block_rate_on_success": replay_pooled.get("block_rate_on_success"),
            "block_rate_ci": replay_pooled.get("block_rate_ci"),
            "false_block_rate_on_ignored": replay_pooled.get("false_block_rate_on_ignored"),
            "false_block_ci": replay_pooled.get("false_block_ci"),
        },
        "by_paradigm": {},
    }
    for p, pdata in replay_pooled.get("by_paradigm", {}).items():
        replay_summary["by_paradigm"][p] = {
            "block_rate_on_success": pdata.get("block_rate_on_success"),
            "block_rate_ci": pdata.get("block_rate_ci"),
            "false_block_rate_on_ignored": pdata.get("false_block_rate_on_ignored"),
            "false_block_ci": pdata.get("false_block_ci"),
        }

    analysis_data["pooled"] = {
        "by_paradigm": pooled_by_paradigm,
        "by_security_risk": pooled_by_risk,
        "paired_comparison": {
            "attacks_removed": int(pooled_mcnemar["b"]),
            "attacks_induced": int(pooled_mcnemar["c"]),
            "total_pairs": len(all_pairs_a_success),
            "mcnemar": pooled_mcnemar,
        },
        "retry_mechanics": {
            "step1_allow": int(pooled_retry_mechanics["step1_allow"]),
            "step1_blocked": int(pooled_retry_mechanics["step1_blocked"]),
            "step1_no_call": int(pooled_retry_mechanics["step1_no_call"]),
            "retried_allowed": int(pooled_retry_mechanics["retried_allowed"]),
            "retried_blocked_again": int(pooled_retry_mechanics["retried_blocked_again"]),
            "step2_rejected_call": int(pooled_retry_mechanics["step2_rejected_call"]),
            "step2_no_call": int(pooled_retry_mechanics["step2_no_call"]),
            "residual_leak_success": int(pooled_retry_mechanics["residual_leak_success"]),
            "retried_allowed_categories": dict(pooled_retry_mechanics["retried_allowed_categories"]),
        },
        "replay_summary": replay_summary,
    }

    # Write output
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(analysis_data, f, indent=2)

    return analysis_data


def main() -> None:
    data = run_analysis()
    
    # Print compact table of (a) pooled
    pdata = data["pooled"]["by_paradigm"]
    print("=== POOLED PARADIGM ASR (N=1800 instances) ===")
    print(f"{'Paradigm':<12} | {'Arm A Valid':<11} | {'Arm A Succ':<10} | {'Arm A ASR [95% CI]':<22} | {'Arm B Valid':<11} | {'Arm B Succ':<10} | {'Arm B ASR [95% CI]':<22}")
    print("-" * 105)
    for p in ["Template-1", "Template-2", "Template-3"]:
        a = pdata[p]["arm_a"]
        b = pdata[p]["arm_b"]
        a_ci = f"[{a['wilson_ci_over_valid'][0]:.3f}, {a['wilson_ci_over_valid'][1]:.3f}]"
        b_ci = f"[{b['wilson_ci_over_valid'][0]:.3f}, {b['wilson_ci_over_valid'][1]:.3f}]"
        print(f"{p:<12} | {a['n_valid']:>4}/{a['n']:<6} | {a['success']:<10} | {a['asr_over_valid']:>6.1%} {a_ci:<15} | {b['n_valid']:>4}/{b['n']:<6} | {b['success']:<10} | {b['asr_over_valid']:>6.1%} {b_ci:<15}")
    print()

    # Print compact table of (c) retry mechanics
    print("=== ARM B RETRY MECHANICS PER RUNG ===")
    print(f"{'Rung':<5} | {'Step-1 Allow':<12} | {'Step-1 Blocked':<14} | {'Step-1 No-Call':<14} | {'Retried Allow':<13} | {'Step-2 Rej Call':<15} | {'Step-2 No-Call':<14} | {'Residual Leak':<13}")
    print("-" * 104)
    for r in ["R1", "R2", "R3", "R4", "R5", "R6"]:
        rm = data["rungs"][r]["retry_mechanics"]
        s1 = rm["step1_outcomes"]
        print(f"{r:<5} | {s1['allow']:<12} | {rm['retried_step1_blocked']:<14} | {s1['no_call']:<14} | {rm['retried_allowed']:<13} | {rm['step2_rejected_call']:<15} | {rm['step2_no_call']:<14} | {rm['residual_leak_success']:<13}")
    p_rm = data["pooled"]["retry_mechanics"]
    print("-" * 104)
    print(f"{'Total':<5} | {p_rm['step1_allow']:<12} | {p_rm['step1_blocked']:<14} | {p_rm['step1_no_call']:<14} | {p_rm['retried_allowed']:<13} | {p_rm['step2_rejected_call']:<15} | {p_rm['step2_no_call']:<14} | {p_rm['residual_leak_success']:<13}")


if __name__ == "__main__":
    main()
