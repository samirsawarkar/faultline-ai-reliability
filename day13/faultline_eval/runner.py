"""The evaluation runner — immutable results bound to the exact data + code.

`evaluate(dataset, split)` runs each sample in the chosen split through
`run_and_predict` (which owns the reuse of Days 9-11), scores the prediction
against the sample's oracle-grounded `expected_faulty`, and returns a FROZEN
`EvalResult`. The result carries the `dataset_version` and `code_version` it was
computed against and a `result_id` derived from them — so a result can always be
checked for freshness and never silently reused against different data.
"""
from __future__ import annotations

import hashlib
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT / "day09") not in sys.path:
    sys.path.insert(0, str(_ROOT / "day09"))

from faultline_detect.score import Confusion  # noqa: E402 (reuse Day 9)

from .dataset import Dataset, Sample
from .predict import run_and_predict

CODE_VERSION = "eval-1.0.0"


def _confusion(rows: List[Sample], preds: Dict[str, bool]) -> Confusion:
    tp = fp = fn = tn = 0
    for s in rows:
        pred = preds[s.sample_id]
        if s.expected_faulty and pred:
            tp += 1
        elif not s.expected_faulty and pred:
            fp += 1
        elif s.expected_faulty and not pred:
            fn += 1
        else:
            tn += 1
    return Confusion(tp=tp, fp=fp, fn=fn, tn=tn)


@dataclass(frozen=True)
class EvalResult:
    dataset_version: str
    code_version: str
    split: str
    sample_count: int
    overall: Dict[str, Any]
    per_modality: Dict[str, Any]
    result_id: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "result_id": self.result_id,
            "dataset_version": self.dataset_version,
            "code_version": self.code_version,
            "split": self.split,
            "sample_count": self.sample_count,
            "overall": self.overall,
            "per_modality": self.per_modality,
        }


def evaluate(dataset: Dataset, split: str = "test") -> EvalResult:
    rows = dataset.split(split)
    preds = {s.sample_id: run_and_predict(s.modality, s.is_fault, s.kind,
                                          s.severity, s.seed) for s in rows}

    per_modality: Dict[str, Any] = {}
    for mod in sorted({s.modality for s in rows}):
        per_modality[mod] = _confusion([s for s in rows if s.modality == mod], preds).to_dict()

    overall = _confusion(rows, preds).to_dict()
    result_id = hashlib.sha256(
        json.dumps([dataset.version, CODE_VERSION, split], sort_keys=True).encode()
    ).hexdigest()[:16]

    return EvalResult(
        dataset_version=dataset.version, code_version=CODE_VERSION, split=split,
        sample_count=len(rows), overall=overall, per_modality=per_modality,
        result_id=result_id)
