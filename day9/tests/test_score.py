"""Scores are computed against INJECTION TRUTH — the mission's fail condition.

These tests prove the scorer reads the Day-8 ground-truth log: change the truth
and the score changes; feed a lazy/greedy detector and the confusion reflects it;
misalign the seqs and it refuses to score.
"""
from __future__ import annotations

import dataclasses
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1].parent / "day8"))
from faultline_inject import GroundTruthLog, TruthEntry

from faultline_detect import (
    f1_corruption_spec,
    run,
    schema_detect,
    schema_positives,
    score,
    truth_is_f1,
)


def _f1_run():
    spec = f1_corruption_spec("*", 5, mode="corrupt", trigger="every_n",
                              trigger_value="2", seed=1)
    obs, truth, _ = run([spec], 1)
    pos = schema_positives(schema_detect(o.seq, o.output) for o in obs)
    return pos, truth


def test_perfect_detector_scores_against_truth():
    pos, truth = _f1_run()
    c = score(pos, truth, truth_is_f1)
    assert (c.tp, c.fp, c.fn, c.tn) == (6, 0, 0, 6)   # 6 faulted, 6 clean
    assert c.precision == 1.0 and c.recall == 1.0


def test_scrambling_the_truth_changes_the_score():
    # Flip every `fired` flag: now no call is an F1 truth-positive, so the same
    # detector output becomes all false positives. If the scorer ignored truth,
    # the confusion would not move.
    pos, truth = _f1_run()
    flipped = GroundTruthLog(truth.run_seed)
    flipped.entries.extend(dataclasses.replace(e, fired=not e.fired) for e in truth.entries)
    c0 = score(pos, truth, truth_is_f1)
    c1 = score(pos, flipped, truth_is_f1)
    assert (c0.tp, c0.fp) == (6, 0)
    assert (c1.tp, c1.fp) == (0, 6)                    # score followed the truth


def test_greedy_detector_loses_precision_against_truth():
    _, truth = _f1_run()
    all_seqs = {e.seq for e in truth.entries}          # flags everything
    c = score(all_seqs, truth, truth_is_f1)
    assert c.fp == 6 and c.tp == 6                      # 6 clean calls now FPs
    assert c.precision == 0.5 and c.recall == 1.0


def test_lazy_detector_has_zero_recall():
    _, truth = _f1_run()
    c = score(set(), truth, truth_is_f1)               # flags nothing
    assert c.tp == 0 and c.recall == 0.0


def test_stray_predicted_seq_is_rejected():
    pos, truth = _f1_run()
    with pytest.raises(ValueError):
        score(pos | {999}, truth, truth_is_f1)


def test_non_contiguous_truth_is_rejected():
    truth = GroundTruthLog(1)
    truth.entries.append(TruthEntry(seq=0, span_id=None, component="c",
                                    input_digest="d", fired=False, label="clean"))
    truth.entries.append(TruthEntry(seq=2, span_id=None, component="c",
                                    input_digest="d", fired=False, label="clean"))
    with pytest.raises(ValueError):
        score(set(), truth, truth_is_f1)
