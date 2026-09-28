"""Single-Pass Test Split Evaluator for P17 Laya Fine-Tuning.

Evaluates either:
  1. Base Laya with pre-tuned threshold (--threshold X)
  2. Fine-tuned Laya checkpoint (--checkpoint PATH)

Computes confusion matrix, TPR/TNR with Wilson 95% CIs, Cohen's kappa,
Rogan-Gladen prevalence, and judges PASS/FAIL against PREREG criteria.
STRICT PROTOCOL: Requires --confirm to prevent accidental test set reads.
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
from faultline_p2.judge.metrics import calculate_evaluator_metrics
from projects.p17_laya_finetune.data_loader import load_dataset_records


def evaluate_test_candidate(
    threshold: float | None = None,
    checkpoint: str | None = None,
    candidate_name: str | None = None,
    output_path: Path | None = None,
    confirm: bool = False,
) -> Dict[str, Any]:
    if not confirm:
        print("=" * 65)
        print("PRE-FLIGHT GUARD: Single-pass test evaluation requires --confirm.")
        print("Per PREREG.md, the test split (n=60) may only be evaluated once per candidate.")
        print("Re-run with --confirm when ready.")
        print("=" * 65)
        return {}

    if threshold is None and checkpoint is None:
        raise ValueError("Must specify either --threshold (for base model) or --checkpoint (for fine-tuned model).")

    if candidate_name is None:
        candidate_name = "finetuned" if checkpoint else f"tuned_tau_{threshold:.4f}".replace(".", "_")

    if output_path is None:
        output_path = Path(f"projects/p17_laya_finetune/results_{candidate_name}.json")

    manifest, labels, contexts, splits = load_dataset_records()
    test_ids = splits["test"]
    assert len(test_ids) == 60, f"Expected 60 test scenarios, found {len(test_ids)}"

    # Load agent
    decision_threshold = 0.50 if threshold is None else threshold
    if checkpoint:
        print(f"Loading fine-tuned checkpoint from: {checkpoint}")
        import laya
        agent = laya.load(checkpoint)
        model_desc = f"fine-tuned ({checkpoint})"
    else:
        print(f"Loading base Laya model with tuned threshold tau = {decision_threshold:.4f}...")
        from faultline_p2.judge.laya_judge import get_laya_agent
        agent = get_laya_agent()
        model_desc = f"convaiinnovations/laya (base, tau={decision_threshold:.4f})"

    questions = {
        "detected": {
            "type": "noul",
            "instructions": OVERCONSTRAINED_SEARCH_RUBRIC,
        }
    }

    records: List[Dict[str, Any]] = []
    print(f"Executing single-pass evaluation on {len(test_ids)} test scenarios...")
    for idx, sid in enumerate(test_ids, 1):
        context = contexts[sid]
        gt = (labels[sid] == "OVERCONSTRAINED_SEARCH_LOOP")

        res = agent.predict(context, questions)
        ans = res["answers"]["detected"]
        p = float(ans["noul"])
        conf = float(ans.get("confidence", max(p, 1.0 - p)))
        pred = (p >= decision_threshold)

        records.append({
            "scenario_id": sid,
            "probability": p,
            "confidence": conf,
            "prediction": pred,
            "ground_truth": gt,
        })
        if idx % 15 == 0 or idx == len(test_ids):
            print(f"  Evaluated {idx}/{len(test_ids)} test instances...")

    preds = [r["prediction"] for r in records]
    gts = [r["ground_truth"] for r in records]

    metrics = calculate_evaluator_metrics(
        mode="OVERCONSTRAINED_SEARCH_LOOP",
        evaluator_type="laya_test_candidate",
        predictions=preds,
        ground_truth=gts,
    )

    n_pos = sum(gts)
    n_neg = len(gts) - n_pos
    assert n_pos == 14, f"Expected 14 test positives, found {n_pos}"
    assert n_neg == 46, f"Expected 46 test negatives, found {n_neg}"

    # Pre-registered success criteria: TPR >= 13/14 AND TNR >= 0.80
    tpr_target = 13.0 / 14.0
    tnr_target = 0.80
    tpr_pass = metrics.tpr >= tpr_target
    tnr_pass = metrics.tnr >= tnr_target
    prereg_pass = tpr_pass and tnr_pass

    results_data = {
        "metadata": {
            "candidate": candidate_name,
            "model_description": model_desc,
            "decision_threshold": decision_threshold,
            "test_sample_size": len(test_ids),
            "manifest_sha256": manifest["manifest_sha256"],
            "target_tpr": tpr_target,
            "target_tnr": tnr_target,
            "prereg_verdict": "PASS" if prereg_pass else "FAIL",
        },
        "metrics": {
            "confusion": {
                "tp": metrics.confusion.tp,
                "fp": metrics.confusion.fp,
                "tn": metrics.confusion.tn,
                "fn": metrics.confusion.fn,
                "total": metrics.confusion.total,
            },
            "sensitivity_tpr": metrics.tpr,
            "tpr_wilson_ci": metrics.tpr_wilson_ci,
            "tpr_meets_target": tpr_pass,
            "specificity_tnr": metrics.tnr,
            "tnr_wilson_ci": metrics.tnr_wilson_ci,
            "tnr_meets_target": tnr_pass,
            "accuracy": metrics.accuracy,
            "precision": metrics.precision,
            "cohen_kappa": metrics.cohen_kappa,
            "kappa_label": metrics.kappa_label,
            "raw_prevalence": metrics.raw_prevalence,
            "rogan_gladen_prevalence": metrics.rogan_gladen_prevalence,
        },
        "scenarios": records,
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results_data, f, indent=2)

    print("\n" + "=" * 65)
    print(f"P17 TEST SPLIT EVALUATION: {candidate_name.upper()}")
    print("=" * 65)
    print(f"Model                  : {model_desc}")
    print(f"Threshold              : {decision_threshold:.4f}")
    print(f"Sample Size            : {len(test_ids)} (14 Positives, 46 Negatives)")
    print("-" * 65)
    print(f"Confusion Matrix       : TP={metrics.confusion.tp}, FP={metrics.confusion.fp}, TN={metrics.confusion.tn}, FN={metrics.confusion.fn}")
    print(f"Sensitivity (TPR)      : {metrics.tpr:.4f} [Wilson CI: {metrics.tpr_wilson_ci}] {'[PASS]' if tpr_pass else '[FAIL]'}")
    print(f"Specificity (TNR)      : {metrics.tnr:.4f} [Wilson CI: {metrics.tnr_wilson_ci}] {'[PASS]' if tnr_pass else '[FAIL]'}")
    print(f"Cohen's Kappa          : {metrics.cohen_kappa:.4f} ({metrics.kappa_label})")
    print(f"Rogan-Gladen Prev      : {metrics.rogan_gladen_prevalence:.4f} (observed: {metrics.raw_prevalence:.4f})")
    print("-" * 65)
    print(f"PREREG CRITERIA STATUS : {'>>> PASS <<<' if prereg_pass else '>>> FAIL <<<'}")
    print(f"  Target: TPR >= 13/14 (0.9286), TNR >= 0.8000")
    print(f"  Actual: TPR = {metrics.tpr:.4f}, TNR = {metrics.tnr:.4f}")
    print("=" * 65)
    print(f"Results saved to: {output_path}")

    return results_data


def main():
    parser = argparse.ArgumentParser(description="P17 Laya Single-Pass Test Evaluator")
    parser.add_argument("--threshold", type=float, default=None, help="Probability threshold for base Laya model")
    parser.add_argument("--checkpoint", type=str, default=None, help="Path to fine-tuned Laya checkpoint directory")
    parser.add_argument("--candidate", type=str, default=None, help="Candidate name for results file")
    parser.add_argument("--output", type=str, default=None, help="Custom results destination path")
    parser.add_argument("--confirm", action="store_true", help="Confirm execution of single-pass test evaluation")
    args = parser.parse_args()

    out_path = Path(args.output) if args.output else None
    evaluate_test_candidate(
        threshold=args.threshold,
        checkpoint=args.checkpoint,
        candidate_name=args.candidate,
        output_path=out_path,
        confirm=args.confirm,
    )


if __name__ == "__main__":
    main()
