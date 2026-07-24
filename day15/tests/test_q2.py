"""Q2: per-class confusion + intervals, and proof that no FP/FN is hidden.

Fail condition: false positives or false negatives are hidden by aggregate metrics.
These tests assert the opposite — every class is reported, and every FP/FN is
enumerated and traced.
"""
from __future__ import annotations

import faultline_q2 as q

ALL_FAULTS = {"F1", "F2", "F3", "F4", "F5", "F6"}


def test_report_is_deterministic():
    assert q.build_report(split="all") == q.build_report(split="all")


def test_every_fault_has_its_own_confusion_and_intervals():
    pc = q.build_report(split="all")["per_class_confusion"]
    assert set(pc) == ALL_FAULTS
    for m, c in pc.items():
        for key in ("tp", "fp", "fn", "tn", "recall_ci95", "precision_ci95"):
            assert key in c, f"{m} missing {key}"


def test_no_false_positives_are_hidden():
    # precision is 1.0 everywhere here; assert it by counting FPs per class, not by
    # trusting an aggregate.
    pc = q.build_report(split="all")["per_class_confusion"]
    assert sum(c["fp"] for c in pc.values()) == 0
    assert all(c["fp"] == 0 for c in pc.values())


def test_false_negatives_are_all_accounted_for():
    rep = q.build_report(split="all")
    nh = rep["no_hiding"]
    assert nh["reconciled"] is True
    assert nh["failures_listed"] == nh["total_false_positives"] + nh["total_false_negatives"]
    assert (nh["fn_taxonomy"]["irreducible_semantic_escape"]
            + nh["fn_taxonomy"]["threshold_reducible"]) == nh["total_false_negatives"]


def test_aggregate_would_hide_the_spread():
    aw = q.build_report(split="all")["aggregation_warning"]
    # micro and macro differ -> the classes are imbalanced in accuracy
    assert aw["micro_recall"] != aw["macro_recall"]
    recalls = list(aw["per_class_recall"].values())
    assert max(recalls) - min(recalls) > 0.3      # a real per-class spread


def test_every_failure_is_enumerated_with_a_complete_trace():
    outcomes = q.run_outcomes(split="all")
    failures = q.collect_failures(outcomes)
    expected_ids = {o["sample_id"] for o in outcomes if o["outcome"] in ("FP", "FN")}
    assert {f["sample_id"] for f in failures} == expected_ids     # nothing dropped
    for f in failures:
        spans = f["trace"]["spans"]
        assert spans and all(s["end_seq"] is not None for s in spans)   # complete
        assert f["why"]


def test_trace_matches_the_scored_prediction():
    outcomes = {o["sample_id"]: o for o in q.run_outcomes(split="all")}
    for f in q.collect_failures(list(outcomes.values())):
        assert f["predicted_faulty"] == outcomes[f["sample_id"]]["predicted_faulty"]


def test_semantic_escapes_are_the_irreducible_false_negatives():
    outcomes = q.run_outcomes(split="all")
    failures = q.collect_failures(outcomes)
    escapes = {f["kind"] for f in failures if "irreducible" in f["why"]}
    assert escapes <= {"drift_value", "offbase_tokens", "context_drift"}
    assert {"drift_value", "context_drift"} <= escapes      # both present as FNs
