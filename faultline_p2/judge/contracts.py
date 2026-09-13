"""Pydantic Contracts for Judge Validation and Evaluation."""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple
from pydantic import BaseModel, Field


class JudgeVerdict(BaseModel):
    """Binary verdict for a specific failure mode evaluation."""
    scenario_id: str
    mode: str
    detected: bool
    confidence: float = Field(ge=0.0, le=1.0, default=1.0)
    reasoning: str = ""
    is_llm_judge: bool = False
    tokens_used: Dict[str, int] = Field(default_factory=lambda: {"prompt": 0, "completion": 0})


class ConfusionMatrix(BaseModel):
    """Confusion counts against human ground truth."""
    tp: int = 0
    fp: int = 0
    tn: int = 0
    fn: int = 0
    total: int = 0


class EvaluatorMetrics(BaseModel):
    """Full performance metrics for an automated evaluator."""
    mode: str
    evaluator_type: str  # 'code_assertion' or 'llm_judge'
    confusion: ConfusionMatrix
    tpr: float  # Sensitivity / Recall
    tpr_wilson_ci: Tuple[float, float]
    tnr: float  # Specificity
    tnr_wilson_ci: Tuple[float, float]
    precision: float
    accuracy: float
    cohen_kappa: float
    kappa_label: str
    raw_prevalence: float
    rogan_gladen_prevalence: float


class SplitManifest(BaseModel):
    """Content-addressed train/dev/test split manifest."""
    spec_version: str = "1.0.0"
    total_scenarios: int
    train_count: int
    dev_count: int
    test_count: int
    train_ids: List[str]
    dev_ids: List[str]
    test_ids: List[str]
    manifest_sha256: str = ""
