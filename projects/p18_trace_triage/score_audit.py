"""Scoring for P18 CEO Audit against LLM judge and code rules.

Reads:
- audit_labels.json (CEO ratings: yes / no / unsure)
- audit_manifest.json (100 runs with strata definitions)
- labels.jsonl (Judge evaluations)
- rules.py (Code rules for T1 and T2)

Per failure type (T1..T4), computes:
- Judge vs CEO
- Rule vs CEO (for T1 and T2)
Reporting:
- TP, FP, TN, FN, count of 'unsure' (excluded from diagnostic rates)
- Sensitivity / TPR with Wilson 95% CI
- Specificity / TNR with Wilson 95% CI
- Cohen's kappa
Evaluated across:
1. Stratum A alone (unbiased random sample, n=50)
2. All 100 runs (enriched sample)
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from faultline_p2.judge.metrics import (
    compute_cohen_kappa,
    compute_confusion_matrix,
)
from faultline_p2.stats.intervals import wilson_interval


def load_audit_labels(path: Path) -> Dict[str, Dict[str, Any]]:
    """Load CEO audit labels from audit_labels.json."""
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data


def compute_binary_metrics(
    predictions: List[bool],
    ground_truth: List[bool],
    unsure_count: int = 0,
) -> Dict[str, Any]:
    """Calculate diagnostic performance and agreement metrics for binary rater against ground truth."""
    if not predictions or len(predictions) != len(ground_truth):
        return {
            "total_evaluated": 0,
            "unsure_count": unsure_count,
            "tp": 0,
            "fp": 0,
            "tn": 0,
            "fn": 0,
            "tpr": None,
            "tpr_ci": (None, None),
            "tnr": None,
            "tnr_ci": (None, None),
            "cohen_kappa": None,
        }

    conf = compute_confusion_matrix(predictions, ground_truth)
    positives = conf.tp + conf.fn
    negatives = conf.tn + conf.fp

    tpr = (conf.tp / positives) if positives > 0 else None
    tpr_ci = wilson_interval(conf.tp, positives) if positives > 0 else (None, None)

    tnr = (conf.tn / negatives) if negatives > 0 else None
    tnr_ci = wilson_interval(conf.tn, negatives) if negatives > 0 else (None, None)

    kappa = compute_cohen_kappa(predictions, ground_truth)

    return {
        "total_evaluated": len(predictions),
        "unsure_count": unsure_count,
        "tp": conf.tp,
        "fp": conf.fp,
        "tn": conf.tn,
        "fn": conf.fn,
        "tpr": round(tpr, 4) if tpr is not None else None,
        "tpr_ci": (round(tpr_ci[0], 4), round(tpr_ci[1], 4)) if tpr_ci[0] is not None else (None, None),
        "tnr": round(tnr, 4) if tnr is not None else None,
        "tnr_ci": (round(tnr_ci[0], 4), round(tnr_ci[1], 4)) if tnr_ci[0] is not None else (None, None),
        "cohen_kappa": round(kappa, 4) if kappa is not None else None,
    }


def score_audit(
    audit_labels: Dict[str, Any],
    audit_manifest: Dict[str, Any],
    judge_labels: Dict[str, Any],
    rule_evals: Optional[Dict[str, Dict[str, bool]]] = None,
    exclude_ids: Optional[Sequence[str]] = None,
    rater: str = "CEO",
) -> Dict[str, Any]:
    """Score audit labels against judge labels and code rules.

    Evaluates Stratum A alone (unbiased) and All 100 runs (enriched).
    Supports excluding session IDs (e.g. non-blind trial runs) via exclude_ids.
    """
    excluded_set = set(exclude_ids or [])
    all_runs = audit_manifest.get("runs", [])

    # Identify excluded runs appearing in the audit manifest
    excluded_in_audit = [r["session_id"] for r in all_runs if r["session_id"] in excluded_set]

    # Filter runs
    filtered_runs = [r for r in all_runs if r["session_id"] not in excluded_set]
    stratum_a_runs = [r for r in filtered_runs if r.get("stratum") in ("A_random", "random")]

    subsets = {
        "stratum_a_unbiased": stratum_a_runs,
        "all_100_enriched": filtered_runs,
    }

    results: Dict[str, Any] = {
        "rater": rater,
        "total_audit_manifest_runs": len(all_runs),
        "excluded_count": len(excluded_in_audit),
        "excluded_ids": sorted(excluded_in_audit),
        "stratum_a_count": len(stratum_a_runs),
        "all_count": len(filtered_runs),
    }

    for subset_name, subset_runs in subsets.items():
        subset_res: Dict[str, Any] = {}

        for failure_type in ["T1", "T2", "T3", "T4"]:
            type_res: Dict[str, Any] = {}

            # Collect pairs for Judge vs CEO/Rater
            judge_preds: List[bool] = []
            judge_gts: List[bool] = []
            judge_unsure = 0

            for r in subset_runs:
                sid = r["session_id"]
                ceo_rec = audit_labels.get(sid, {})
                ceo_val = ceo_rec.get(failure_type)

                if ceo_val == "unsure" or ceo_val is None:
                    judge_unsure += 1
                    continue
                elif ceo_val in ("yes", True):
                    gt = True
                elif ceo_val in ("no", False):
                    gt = False
                else:
                    judge_unsure += 1
                    continue

                j_rec = judge_labels.get(sid, {})
                if "evaluation" in j_rec:
                    j_val = j_rec["evaluation"].get(failure_type, {}).get("label")
                elif failure_type in j_rec:
                    j_val = j_rec[failure_type].get("label") if isinstance(j_rec[failure_type], dict) else j_rec[failure_type]
                else:
                    j_val = None

                if j_val is not None:
                    judge_preds.append(bool(j_val))
                    judge_gts.append(gt)

            type_res["judge_vs_ceo"] = compute_binary_metrics(
                predictions=judge_preds,
                ground_truth=judge_gts,
                unsure_count=judge_unsure,
            )

            # For T1 and T2: evaluate Rule vs CEO/Rater
            if failure_type in ("T1", "T2") and rule_evals is not None:
                rule_preds: List[bool] = []
                rule_gts: List[bool] = []
                rule_unsure = 0

                for r in subset_runs:
                    sid = r["session_id"]
                    ceo_rec = audit_labels.get(sid, {})
                    ceo_val = ceo_rec.get(failure_type)

                    if ceo_val == "unsure" or ceo_val is None:
                        rule_unsure += 1
                        continue
                    elif ceo_val in ("yes", True):
                        gt = True
                    elif ceo_val in ("no", False):
                        gt = False
                    else:
                        rule_unsure += 1
                        continue

                    r_dict = rule_evals.get(sid, {})
                    if failure_type in r_dict:
                        rule_preds.append(bool(r_dict[failure_type]))
                        rule_gts.append(gt)

                type_res["rule_vs_ceo"] = compute_binary_metrics(
                    predictions=rule_preds,
                    ground_truth=rule_gts,
                    unsure_count=rule_unsure,
                )

            subset_res[failure_type] = type_res

        results[subset_name] = subset_res

    return results


def format_score_table(results: Dict[str, Any], rater: Optional[str] = None) -> str:
    """Format audit scoring results as a human-readable text report."""
    rater_name = rater or results.get("rater", "CEO")
    excluded_count = results.get("excluded_count", 0)
    excluded_ids = results.get("excluded_ids", [])
    n_a = results.get("stratum_a_count", 50)
    n_all = results.get("all_count", 100)

    lines: List[str] = []
    lines.append("=" * 88)
    lines.append(f"P18 AUDIT EVALUATION REPORT: {rater_name.upper()} GROUND TRUTH VS JUDGE & CODE RULES")
    lines.append("=" * 88)
    lines.append(f"Rater: {rater_name}")
    if excluded_count > 0:
        lines.append(f"Excluded runs ({excluded_count}): {', '.join(excluded_ids)}")

    subsets = [
        ("stratum_a_unbiased", f"STRATUM A: UNBIASED RANDOM SAMPLE (n={n_a})"),
        ("all_100_enriched", f"ALL {n_all} RUNS: ENRICHED SAMPLE (CAUTION: OVER-REPRESENTS POSITIVES)"),
    ]

    for subset_key, title in subsets:
        lines.append(f"\n--- {title} ---")
        header = f"{'Type':<6} | {'Evaluator':<12} | {'TP':>3} {'FP':>3} {'TN':>3} {'FN':>3} {'Unsure':>6} | {'TPR (95% CI)':<22} | {'TNR (95% CI)':<22} | {'Kappa':>6}"
        lines.append(header)
        lines.append("-" * len(header))

        sub_data = results.get(subset_key, {})
        for ftype in ["T1", "T2", "T3", "T4"]:
            tdata = sub_data.get(ftype, {})
            # Judge
            j_m = tdata.get("judge_vs_ceo", {})
            tpr_str = f"{j_m.get('tpr', 0.0):.2f} [{j_m.get('tpr_ci', (0,0))[0] or 0.0:.2f}, {j_m.get('tpr_ci', (0,0))[1] or 0.0:.2f}]" if j_m.get("tpr") is not None else "N/A"
            tnr_str = f"{j_m.get('tnr', 0.0):.2f} [{j_m.get('tnr_ci', (0,0))[0] or 0.0:.2f}, {j_m.get('tnr_ci', (0,0))[1] or 0.0:.2f}]" if j_m.get("tnr") is not None else "N/A"
            kappa_str = f"{j_m.get('cohen_kappa', 0.0):.2f}" if j_m.get("cohen_kappa") is not None else "N/A"

            lines.append(
                f"{ftype:<6} | {'Judge (LLM)':<12} | {j_m.get('tp',0):>3} {j_m.get('fp',0):>3} {j_m.get('tn',0):>3} {j_m.get('fn',0):>3} {j_m.get('unsure_count',0):>6} | {tpr_str:<22} | {tnr_str:<22} | {kappa_str:>6}"
            )

            # Rule
            if "rule_vs_ceo" in tdata:
                r_m = tdata["rule_vs_ceo"]
                r_tpr_str = f"{r_m.get('tpr', 0.0):.2f} [{r_m.get('tpr_ci', (0,0))[0] or 0.0:.2f}, {r_m.get('tpr_ci', (0,0))[1] or 0.0:.2f}]" if r_m.get("tpr") is not None else "N/A"
                r_tnr_str = f"{r_m.get('tnr', 0.0):.2f} [{r_m.get('tnr_ci', (0,0))[0] or 0.0:.2f}, {r_m.get('tnr_ci', (0,0))[1] or 0.0:.2f}]" if r_m.get("tnr") is not None else "N/A"
                r_kappa_str = f"{r_m.get('cohen_kappa', 0.0):.2f}" if r_m.get("cohen_kappa") is not None else "N/A"
                lines.append(
                    f"{'':<6} | {'Code Rule':<12} | {r_m.get('tp',0):>3} {r_m.get('fp',0):>3} {r_m.get('tn',0):>3} {r_m.get('fn',0):>3} {r_m.get('unsure_count',0):>6} | {r_tpr_str:<22} | {r_tnr_str:<22} | {r_kappa_str:>6}"
                )

    lines.append("=" * 88)
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Score P18 CEO Audit Labels")
    parser.add_argument("audit_labels", type=Path, help="Path to audit_labels.json")
    parser.add_argument(
        "--audit-manifest",
        type=Path,
        default=Path("projects/p18_trace_triage/audit_manifest.json"),
    )
    parser.add_argument(
        "--labels",
        type=Path,
        default=Path("projects/p18_trace_triage/labels.jsonl"),
    )
    parser.add_argument(
        "--output-json",
        type=Path,
        default=None,
        help="Optional path to output results as JSON",
    )
    parser.add_argument(
        "--exclude",
        type=str,
        default=None,
        help="Comma-separated list of session IDs to exclude from all rates",
    )
    parser.add_argument(
        "--rater",
        type=str,
        default="CEO",
        help="Name of audit rater (printed in report header)",
    )
    args = parser.parse_args()

    if not args.audit_labels.exists():
        print(f"Error: Audit labels file not found at {args.audit_labels}")
        sys.exit(1)

    audit_labels = load_audit_labels(args.audit_labels)
    with open(args.audit_manifest, "r", encoding="utf-8") as f:
        audit_manifest = json.load(f)

    # Load judge labels
    judge_labels: Dict[str, Any] = {}
    with open(args.labels, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                rec = json.loads(line)
                sid = rec.get("session_id") or rec.get("run_id")
                if sid:
                    judge_labels[sid] = rec

    # Load and compute rules for audit runs
    from projects.p18_trace_triage.select_audit import evaluate_rules_for_manifest
    rule_evals = evaluate_rules_for_manifest(audit_manifest)

    exclude_list = (
        [s.strip() for s in args.exclude.split(",") if s.strip()]
        if args.exclude
        else None
    )

    results = score_audit(
        audit_labels=audit_labels,
        audit_manifest=audit_manifest,
        judge_labels=judge_labels,
        rule_evals=rule_evals,
        exclude_ids=exclude_list,
        rater=args.rater,
    )

    report_text = format_score_table(results, rater=args.rater)
    print(report_text)

    if args.output_json:
        args.output_json.parent.mkdir(parents=True, exist_ok=True)
        with open(args.output_json, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2)
        print(f"Metrics saved to {args.output_json}")


if __name__ == "__main__":
    main()
