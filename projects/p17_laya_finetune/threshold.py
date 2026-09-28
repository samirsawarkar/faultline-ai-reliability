"""Threshold Search on Train+Dev for Laya OVERCONSTRAINED_SEARCH_LOOP Pre-Filter.

Evaluates base Laya on train and dev splits (n=140: 101 train, 39 dev),
records calibrated probabilities, selects the highest decision threshold
that preserves TPR=1.0 (all 22 positives caught), and reports TNR.
DOES NOT READ OR TOUCH THE TEST SPLIT.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any, Dict, List

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from faultline_p2.judge.evaluators import OVERCONSTRAINED_SEARCH_RUBRIC
from faultline_p2.judge.laya_judge import get_laya_agent
from faultline_p2.judge.metrics import calculate_evaluator_metrics
from projects.p17_laya_finetune.data_loader import load_dataset_records


def run_threshold_search(
    output_path: Path = Path("projects/p17_laya_finetune/threshold_results.json"),
) -> Dict[str, Any]:
    manifest, labels, contexts, splits = load_dataset_records()

    train_ids = splits["train"]
    dev_ids = splits["dev"]
    test_ids = splits["test"]
    train_dev_ids = train_ids + dev_ids

    # Strict leakage assertion
    overlap = set(train_dev_ids).intersection(set(test_ids))
    assert len(overlap) == 0, f"LEAKAGE DETECTED: {overlap} found in test split!"
    assert len(train_dev_ids) == 140, f"Expected 140 train+dev scenarios, got {len(train_dev_ids)}"

    print(f"Loading Laya decision model for evaluation on train+dev ({len(train_dev_ids)} scenarios)...")
    agent = get_laya_agent()

    questions = {
        "detected": {
            "type": "noul",
            "instructions": OVERCONSTRAINED_SEARCH_RUBRIC,
        }
    }

    records: List[Dict[str, Any]] = []
    print("Evaluating scenarios on train and dev splits...")
    for idx, sid in enumerate(train_dev_ids, 1):
        context = contexts[sid]
        gt = (labels[sid] == "OVERCONSTRAINED_SEARCH_LOOP")
        split_name = "train" if sid in train_ids else "dev"

        res = agent.predict(context, questions)
        ans = res["answers"]["detected"]
        p = float(ans["noul"])
        conf = float(ans.get("confidence", max(p, 1.0 - p)))

        records.append({
            "scenario_id": sid,
            "split": split_name,
            "probability": p,
            "confidence": conf,
            "ground_truth": gt,
        })
        if idx % 20 == 0 or idx == len(train_dev_ids):
            print(f"  Processed {idx}/{len(train_dev_ids)} scenarios...")

    pos_records = [r for r in records if r["ground_truth"]]
    neg_records = [r for r in records if not r["ground_truth"]]

    assert len(pos_records) == 22, f"Expected 22 positives across train+dev, found {len(pos_records)}"
    assert len(neg_records) == 118, f"Expected 118 negatives across train+dev, found {len(neg_records)}"

    pos_probs = [r["probability"] for r in pos_records]
    neg_probs = [r["probability"] for r in neg_records]

    min_pos_p = min(pos_probs)
    max_pos_p = max(pos_probs)

    def evaluate_at_threshold(tau: float) -> Dict[str, Any]:
        preds = [r["probability"] >= tau for r in records]
        gts = [r["ground_truth"] for r in records]
        metrics = calculate_evaluator_metrics(
            mode="OVERCONSTRAINED_SEARCH_LOOP",
            evaluator_type="laya_prefilter",
            predictions=preds,
            ground_truth=gts,
        )
        return {
            "threshold": tau,
            "tp": metrics.confusion.tp,
            "fp": metrics.confusion.fp,
            "tn": metrics.confusion.tn,
            "fn": metrics.confusion.fn,
            "tpr": metrics.tpr,
            "tnr": metrics.tnr,
            "tpr_wilson_ci": metrics.tpr_wilson_ci,
            "tnr_wilson_ci": metrics.tnr_wilson_ci,
            "cohen_kappa": metrics.cohen_kappa,
            "accuracy": metrics.accuracy,
            "precision": metrics.precision,
        }

    # Generate candidate thresholds from probabilities and grid
    candidate_taus = sorted(list(set(
        [round(i * 0.005, 4) for i in range(201)]
        + [round(p, 6) for p in pos_probs + neg_probs]
    )))

    # Find optimal threshold subject to recall >= 0.95
    best_tau_95 = None
    best_eval_95 = None
    best_tnr_95 = -1.0

    # Also track optimal threshold for strict TPR = 1.0 (all 22 positives caught)
    best_tau_100 = min_pos_p
    eval_100 = evaluate_at_threshold(best_tau_100)

    for tau in candidate_taus:
        ev = evaluate_at_threshold(tau)
        if ev["tpr"] >= 0.95:
            # Maximizing TNR, breaking ties with higher TPR then higher tau
            if (ev["tnr"] > best_tnr_95 or
                (ev["tnr"] == best_tnr_95 and best_eval_95 is not None and ev["tpr"] > best_eval_95["tpr"]) or
                (ev["tnr"] == best_tnr_95 and best_eval_95 is not None and ev["tpr"] == best_eval_95["tpr"] and tau > best_tau_95)):
                best_tnr_95 = ev["tnr"]
                best_tau_95 = tau
                best_eval_95 = ev

    assert best_eval_95 is not None, "No threshold satisfied recall >= 95%"

    eval_default = evaluate_at_threshold(0.50)

    # Threshold curve sweep for plotting/reporting
    sweep_taus = sorted(list(set([0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, best_tau_95, best_tau_100] + pos_probs)))
    curve = [evaluate_at_threshold(t) for t in sweep_taus]

    report = {
        "metadata": {
            "model": "convaiinnovations/laya",
            "evaluator_mode": "OVERCONSTRAINED_SEARCH_LOOP",
            "split_evaluated": "train+dev",
            "total_scenarios": len(train_dev_ids),
            "train_count": len(train_ids),
            "dev_count": len(dev_ids),
            "positives": len(pos_records),
            "negatives": len(neg_records),
        },
        "probability_distribution": {
            "positives": {
                "min": min_pos_p,
                "max": max_pos_p,
                "values": sorted(pos_probs),
            },
            "negatives": {
                "min": min(neg_probs),
                "max": max(neg_probs),
            },
        },
        "optimal_threshold_recall_95": {
            "threshold": best_tau_95,
            "evaluation": best_eval_95,
        },
        "optimal_threshold_tpr_1_0": {
            "threshold": best_tau_100,
            "evaluation": eval_100,
        },
        "default_threshold_0_5": {
            "threshold": 0.50,
            "evaluation": eval_default,
        },
        "threshold_curve": curve,
        "records": records,
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print("\n" + "=" * 65)
    print("P17 LAYA THRESHOLD TUNING REPORT (TRAIN + DEV ONLY, n=140)")
    print("=" * 65)
    print(f"Total Scenarios Evaluated: {len(train_dev_ids)} (Train: {len(train_ids)}, Dev: {len(dev_ids)})")
    print(f"Ground Truth Positives   : {len(pos_records)} / 140 ({len(pos_records)/140:.1%})")
    print(f"Positive p range         : [{min_pos_p:.4f}, {max_pos_p:.4f}]")
    print("-" * 65)
    print(f"DEFAULT THRESHOLD (tau = 0.50):")
    print(f"  TP: {eval_default['tp']}, FP: {eval_default['fp']}, TN: {eval_default['tn']}, FN: {eval_default['fn']}")
    print(f"  TPR: {eval_default['tpr']:.4f}, TNR: {eval_default['tnr']:.4f}, Kappa: {eval_default['cohen_kappa']:.4f}")
    print("-" * 65)
    print(f"OPTIMAL THRESHOLD FOR RECALL >= 95% (tau = {best_tau_95:.4f}):")
    print(f"  TP: {best_eval_95['tp']}, FP: {best_eval_95['fp']}, TN: {best_eval_95['tn']}, FN: {best_eval_95['fn']}")
    print(f"  TPR: {best_eval_95['tpr']:.4f} [Wilson CI: {best_eval_95['tpr_wilson_ci']}]")
    print(f"  TNR: {best_eval_95['tnr']:.4f} [Wilson CI: {best_eval_95['tnr_wilson_ci']}]")
    print(f"  Cohen's Kappa: {best_eval_95['cohen_kappa']:.4f}")
    print("-" * 65)
    print(f"STRICT TPR=1.0 THRESHOLD (tau = {best_tau_100:.4f}):")
    print(f"  TP: {eval_100['tp']}, FP: {eval_100['fp']}, TN: {eval_100['tn']}, FN: {eval_100['fn']}")
    print(f"  TPR: {eval_100['tpr']:.4f} [Wilson CI: {eval_100['tpr_wilson_ci']}]")
    print(f"  TNR: {eval_100['tnr']:.4f} [Wilson CI: {eval_100['tnr_wilson_ci']}]")
    print(f"  Cohen's Kappa: {eval_100['cohen_kappa']:.4f}")
    print("=" * 65)
    print(f"Saved threshold analysis to: {output_path}")

    return report


def main():
    parser = argparse.ArgumentParser(description="P17 Laya Threshold Search on Train+Dev")
    parser.add_argument(
        "--output",
        default="projects/p17_laya_finetune/threshold_results.json",
        help="Destination JSON path for threshold results",
    )
    args = parser.parse_args()
    run_threshold_search(Path(args.output))


if __name__ == "__main__":
    main()
