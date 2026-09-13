"""Metrics computation for judge validation: Cohen's kappa, TPR, TNR, Rogan-Gladen."""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence, Tuple
from faultline_p2.judge.contracts import ConfusionMatrix, EvaluatorMetrics
from faultline_p2.stats.intervals import wilson_interval


def compute_confusion_matrix(predictions: Sequence[bool], ground_truth: Sequence[bool]) -> ConfusionMatrix:
    """Compute TP, FP, TN, FN for binary classifications."""
    if len(predictions) != len(ground_truth):
        raise ValueError(f"Lengths must match: predictions={len(predictions)}, ground_truth={len(ground_truth)}")

    tp = fp = tn = fn = 0
    for p, g in zip(predictions, ground_truth):
        if p and g:
            tp += 1
        elif p and not g:
            fp += 1
        elif not p and g:
            fn += 1
        else:
            tn += 1

    return ConfusionMatrix(tp=tp, fp=fp, tn=tn, fn=fn, total=len(predictions))


def compute_cohen_kappa(predictions: Sequence[bool], ground_truth: Sequence[bool]) -> float:
    """Compute Cohen's kappa for two binary raters."""
    n = len(predictions)
    if n == 0 or len(ground_truth) != n:
        raise ValueError("Require equal, non-empty prediction and ground truth sequences")

    # Observed agreement
    po = sum(1 for p, g in zip(predictions, ground_truth) if p == g) / n

    # Expected chance agreement
    p_pred_true = sum(1 for p in predictions if p) / n
    p_pred_false = 1.0 - p_pred_true
    p_gt_true = sum(1 for g in ground_truth if g) / n
    p_gt_false = 1.0 - p_gt_true

    pe = (p_pred_true * p_gt_true) + (p_pred_false * p_gt_false)

    if pe == 1.0:
        return 1.0  # Perfect agreement on constant rater
    if pe == 0.0:
        return 0.0

    return (po - pe) / (1.0 - pe)


def kappa_label(kappa: float) -> str:
    """Landis & Koch standard bands for interpreting Cohen's kappa."""
    if kappa < 0.0:
        return "poor / worse than chance"
    if kappa < 0.20:
        return "slight"
    if kappa < 0.40:
        return "fair"
    if kappa < 0.60:
        return "moderate"
    if kappa < 0.80:
        return "substantial"
    return "almost perfect"


def compute_rogan_gladen_prevalence(observed_prevalence: float, tpr: float, tnr: float) -> float:
    """Apply Rogan-Gladen estimator to correct observed prevalence for imperfect diagnostic tests.

    P_adj = (P_obs + TNR - 1) / (TPR + TNR - 1)
    """
    denom = tpr + tnr - 1.0
    if abs(denom) < 1e-6:
        return observed_prevalence  # Uninformative test

    p_adj = (observed_prevalence + tnr - 1.0) / denom
    return max(0.0, min(1.0, p_adj))


def calculate_evaluator_metrics(
    mode: str,
    evaluator_type: str,
    predictions: Sequence[bool],
    ground_truth: Sequence[bool],
) -> EvaluatorMetrics:
    """Calculate full diagnostic and agreement metrics for an evaluator against human ground truth."""
    conf = compute_confusion_matrix(predictions, ground_truth)
    total = conf.total
    positives = conf.tp + conf.fn
    negatives = conf.tn + conf.fp

    # Sensitivity / TPR
    tpr = conf.tp / positives if positives > 0 else 1.0
    tpr_ci = wilson_interval(conf.tp, positives) if positives > 0 else (0.0, 1.0)

    # Specificity / TNR
    tnr = conf.tn / negatives if negatives > 0 else 1.0
    tnr_ci = wilson_interval(conf.tn, negatives) if negatives > 0 else (0.0, 1.0)

    # Precision
    predicted_pos = conf.tp + conf.fp
    precision = conf.tp / predicted_pos if predicted_pos > 0 else (1.0 if conf.tp == 0 and conf.fn == 0 else 0.0)

    # Accuracy
    accuracy = (conf.tp + conf.tn) / total if total > 0 else 0.0

    # Cohen's kappa
    kappa = compute_cohen_kappa(predictions, ground_truth)
    k_label = kappa_label(kappa)

    # Prevalence
    raw_prev = positives / total if total > 0 else 0.0
    obs_prev = predicted_pos / total if total > 0 else 0.0
    rogan_gladen_prev = compute_rogan_gladen_prevalence(obs_prev, tpr, tnr)

    return EvaluatorMetrics(
        mode=mode,
        evaluator_type=evaluator_type,
        confusion=conf,
        tpr=round(tpr, 4),
        tpr_wilson_ci=(round(tpr_ci[0], 4), round(tpr_ci[1], 4)),
        tnr=round(tnr, 4),
        tnr_wilson_ci=(round(tnr_ci[0], 4), round(tnr_ci[1], 4)),
        precision=round(precision, 4),
        accuracy=round(accuracy, 4),
        cohen_kappa=round(kappa, 4),
        kappa_label=k_label,
        raw_prevalence=round(raw_prev, 4),
        rogan_gladen_prevalence=round(rogan_gladen_prev, 4),
    )
