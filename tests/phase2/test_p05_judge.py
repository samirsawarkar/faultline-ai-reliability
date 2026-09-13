"""Unit tests for Project P5: Judge Validation."""
from __future__ import annotations

import csv
import json
from pathlib import Path
import pytest

from faultline_p2.judge.contracts import ConfusionMatrix, EvaluatorMetrics, JudgeVerdict, SplitManifest
from faultline_p2.judge.evaluators import EvaluatorRegistry
from faultline_p2.judge.metrics import (
    calculate_evaluator_metrics,
    compute_cohen_kappa,
    compute_confusion_matrix,
    compute_rogan_gladen_prevalence,
    kappa_label,
)
from projects.p05_judge.run import EVALUATOR_SPECS, ensure_split_manifest, generate_figure


def test_p05_split_manifest_determinism(tmp_path):
    csv_path = Path("projects/p04_taxonomy/coding_sheet.csv")
    manifest_path1 = tmp_path / "manifest1.json"
    manifest_path2 = tmp_path / "manifest2.json"

    m1 = ensure_split_manifest(csv_path, manifest_path1, seed=42)
    m2 = ensure_split_manifest(csv_path, manifest_path2, seed=42)

    assert m1.total_scenarios == 200
    assert m1.train_count == 101  # 50% rounded
    assert m1.dev_count == 39    # 20% rounded
    assert m1.test_count == 60   # 30% test
    assert m1.train_ids == m2.train_ids
    assert m1.dev_ids == m2.dev_ids
    assert m1.test_ids == m2.test_ids
    assert m1.manifest_sha256 == m2.manifest_sha256
    assert len(set(m1.train_ids).intersection(set(m1.test_ids))) == 0
    assert len(set(m1.dev_ids).intersection(set(m1.test_ids))) == 0


def test_p05_metrics_cohen_kappa():
    # Perfect agreement
    p = [True, True, False, False, True]
    g = [True, True, False, False, True]
    assert compute_cohen_kappa(p, g) == 1.0

    # Opposite agreement
    p = [True, True, True, True]
    g = [False, False, False, False]
    assert compute_cohen_kappa(p, g) <= 0.0

    # Intermediate known agreement
    p = [True, True, False, False, True, False, True, False]
    g = [True, False, False, False, True, True, True, False]
    k = compute_cohen_kappa(p, g)
    assert 0.0 < k < 1.0
    label = kappa_label(k)
    assert isinstance(label, str)


def test_p05_rogan_gladen_prevalence():
    # Perfect test: Rogan-Gladen equals observed
    assert compute_rogan_gladen_prevalence(0.30, 1.0, 1.0) == pytest.approx(0.30)

    # Imperfect test: TPR=0.80, TNR=0.90, P_obs=0.35
    # P_adj = (0.35 + 0.90 - 1.0) / (0.80 + 0.90 - 1.0) = 0.25 / 0.70 = 0.3571
    p_adj = compute_rogan_gladen_prevalence(0.35, 0.80, 0.90)
    assert 0.35 < p_adj < 0.36


def test_p05_calculate_evaluator_metrics():
    preds = [True, True, False, True, False, False, True, False]
    gts = [True, False, False, True, False, True, True, False]

    metrics = calculate_evaluator_metrics("TEST_MODE", "code_assertion", preds, gts)
    assert isinstance(metrics, EvaluatorMetrics)
    assert metrics.mode == "TEST_MODE"
    assert metrics.confusion.total == 8
    assert 0.0 <= metrics.tpr <= 1.0
    assert 0.0 <= metrics.tnr <= 1.0
    assert 0.0 <= metrics.accuracy <= 1.0
    assert metrics.tpr_wilson_ci[0] <= metrics.tpr_wilson_ci[1]


def test_p05_evaluators_offline_execution():
    registry = EvaluatorRegistry(judge_model_name="z-ai/glm-5.3", real=False)

    # Rate limit test
    sweep_item = {"output": {"status": "model_failure", "reason": "RateLimitError 429"}}
    v_rl = registry.evaluate_mode("INFRASTRUCTURE_RATE_LIMIT", "s-0001", "T1", [], sweep_item, None)
    assert v_rl.detected is True
    assert v_rl.mode == "INFRASTRUCTURE_RATE_LIMIT"

    # Malformed tool test
    sweep_item_mal = {"output": {"status": "malformed", "reason": "Malformed model output"}}
    v_mal = registry.evaluate_mode("MALFORMED_TOOL_CALL", "s-0002", "T1", [], sweep_item_mal, None)
    assert v_mal.detected is True

    # Offline LLM Judge heuristic for abstention
    sweep_item_abs = {"output": {"status": "answered", "answer": "I couldn’t verify the external auditor."}}
    v_abs = registry.evaluate_mode("RETRIEVAL_FAILURE_ABSTENTION", "s-0020", "T1", [], sweep_item_abs, None)
    assert v_abs.detected is True


def test_p05_figure_generation(tmp_path):
    results_mock = {
        "metadata": {"judge_model": "z-ai/glm-5.3"},
        "evaluators": {
            "INFRASTRUCTURE_RATE_LIMIT": {
                "evaluator_type": "code_assertion",
                "cohen_kappa": 0.95,
                "tpr": 1.0,
                "tnr": 0.98,
            },
            "OVERCONSTRAINED_SEARCH_LOOP": {
                "evaluator_type": "llm_judge",
                "cohen_kappa": 0.88,
                "tpr": 0.92,
                "tnr": 0.95,
            },
            "MALFORMED_TOOL_CALL": {
                "evaluator_type": "code_assertion",
                "cohen_kappa": 1.0,
                "tpr": 1.0,
                "tnr": 1.0,
            },
        },
    }
    fig_path = tmp_path / "figure.svg"
    generate_figure(results_mock, fig_path)
    assert fig_path.is_file()
    content = fig_path.read_text(encoding="utf-8")
    assert "<svg" in content
    assert "P5 Judge Validation" in content
    assert "H3 Target" in content
