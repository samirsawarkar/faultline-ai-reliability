"""Scoring — detector signals graded against INJECTION TRUTH, and nothing else.

This module is where the mission's fail condition is met head-on: "Detector
scores are not computed against injection truth." Every score here is a confusion
matrix built by joining, per call `seq`, a detector's predicted-positive set to
the Day-8 `GroundTruthLog` — the record written at injection time. There is no
other source of labels, and `score` will refuse to run if the detector's seqs
don't line up with a complete, contiguous truth log.

A "positive" is fault-family-specific:
  * F1 schema:   truth-positive = a call the injector marked as an F1 corruption;
                 detector-positive = the schema detector raised a repair signal.
  * F2 latency:  truth-positive = a call the injector marked as an F2 latency
                 fault; detector-positive = the duration detector raised a
                 timeout signal.
"""
from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable, List, Optional, Set

_DAY8 = Path(__file__).resolve().parents[2] / "day8"
if str(_DAY8) not in sys.path:
    sys.path.insert(0, str(_DAY8))

from faultline_inject import GroundTruthLog, TruthEntry  # noqa: E402

from .detectors import DurationSignal, SchemaSignal  # noqa: E402
from .injectors import is_f1, is_f2  # noqa: E402


def _round(x: Optional[float]) -> Optional[float]:
    return None if x is None else round(x, 6)


@dataclass(frozen=True)
class Confusion:
    tp: int
    fp: int
    fn: int
    tn: int

    @property
    def n(self) -> int:
        return self.tp + self.fp + self.fn + self.tn

    @property
    def precision(self) -> Optional[float]:
        denom = self.tp + self.fp
        return None if denom == 0 else self.tp / denom

    @property
    def recall(self) -> Optional[float]:
        denom = self.tp + self.fn
        return None if denom == 0 else self.tp / denom

    @property
    def f1(self) -> Optional[float]:
        p, r = self.precision, self.recall
        if not p or not r:      # None or 0 -> F1 undefined/zero
            return 0.0 if (p == 0 or r == 0) else None
        return 2 * p * r / (p + r)

    def to_dict(self) -> dict:
        return {"tp": self.tp, "fp": self.fp, "fn": self.fn, "tn": self.tn,
                "n": self.n, "precision": _round(self.precision),
                "recall": _round(self.recall), "f1": _round(self.f1)}


# --- turning detector signals into a predicted-positive seq set ---

def schema_positives(signals: Iterable[SchemaSignal]) -> Set[int]:
    return {s.seq for s in signals if s.repair_signal}


def duration_positives(signals: Iterable[DurationSignal]) -> Set[int]:
    return {s.seq for s in signals if s.timeout_signal}


# --- truth-positive predicates (read straight off the injection log) ---

def truth_is_f1(e: TruthEntry) -> bool:
    return e.fired and is_f1(e.label)


def truth_is_f2(e: TruthEntry) -> bool:
    return e.fired and is_f2(e.label)


def score(predicted_positive: Set[int], truth: GroundTruthLog,
          truth_positive: Callable[[TruthEntry], bool]) -> Confusion:
    """Confusion matrix of `predicted_positive` (detector) vs `truth_positive`
    applied to the injection log. Raises if the detector's seqs are not a subset
    of the truth log's contiguous 0..n-1 seqs (no scoring without alignment)."""
    seqs = [e.seq for e in truth.entries]
    if seqs != list(range(len(truth.entries))):
        raise ValueError("truth log is not a complete, contiguous labelling")
    valid_seqs = set(seqs)
    stray = predicted_positive - valid_seqs
    if stray:
        raise ValueError(f"detector flagged seqs absent from truth: {sorted(stray)}")

    tp = fp = fn = tn = 0
    for e in truth.entries:
        actual = truth_positive(e)
        predicted = e.seq in predicted_positive
        if actual and predicted:
            tp += 1
        elif not actual and predicted:
            fp += 1
        elif actual and not predicted:
            fn += 1
        else:
            tn += 1
    return Confusion(tp=tp, fp=fp, fn=fn, tn=tn)
