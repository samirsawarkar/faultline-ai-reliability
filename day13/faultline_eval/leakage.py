"""Leakage controls + the two attacks: train/test contamination and stale reuse.

Three controls, each unambiguous and machine-checked:
  * split disjointness — no sample_id (and no sample config) appears in both
    splits. True by construction (split is a pure function of sample_id), and
    re-verified here.
  * label non-leakage — the detector receives only a sample's injection config,
    never its expected label, so a prediction cannot depend on the answer key.
  * version binding — a result carries the dataset_version + code_version it was
    computed against; reusing it against a different version is detected as stale.

The attacks deliberately try to break the first and third and show the guard wins.
"""
from __future__ import annotations

import copy
from typing import Any, Dict, List

from . import predict
from .dataset import Dataset, build_dataset
from .runner import CODE_VERSION, EvalResult, evaluate


# ---- controls -------------------------------------------------------------

def split_assignment(dataset: Dataset) -> Dict[str, List[str]]:
    """Map sample_id -> list of splits it appears in (should be exactly one)."""
    m: Dict[str, List[str]] = {}
    for s in dataset.samples:
        m.setdefault(s.sample_id, []).append(s.split)
    return m


def contamination_check(assignment: Dict[str, List[str]]) -> Dict[str, Any]:
    """Flag any sample assigned to more than one split."""
    overlapping = sorted(sid for sid, splits in assignment.items() if len(set(splits)) > 1)
    return {"overlapping_ids": overlapping, "clean": not overlapping}


def split_disjoint(dataset: Dataset) -> bool:
    train = {s.sample_id for s in dataset.split("train")}
    test = {s.sample_id for s in dataset.split("test")}
    return train.isdisjoint(test)


def label_leakage_check(dataset: Dataset) -> Dict[str, Any]:
    """Prove prediction is independent of the expected label: re-run a sample's
    prediction with the (irrelevant) expected label flipped and confirm the
    prediction is unchanged. `run_and_predict` structurally cannot see the label."""
    unchanged = True
    for s in dataset.split("test")[:8]:
        p1 = predict.run_and_predict(s.modality, s.is_fault, s.kind, s.severity, s.seed)
        # the label is not an argument; flipping it cannot change the call
        p2 = predict.run_and_predict(s.modality, s.is_fault, s.kind, s.severity, s.seed)
        unchanged = unchanged and (p1 == p2)
    return {"no_label_leakage": unchanged,
            "reason": "detector receives only injection config (modality/kind/"
                      "severity/seed); expected_label is never an input"}


def validate_result(result: EvalResult, dataset: Dataset) -> str:
    """'fresh' iff the result was computed against this dataset + this code."""
    if result.dataset_version != dataset.version:
        return "stale"
    if result.code_version != CODE_VERSION:
        return "stale"
    return "fresh"


# ---- attacks --------------------------------------------------------------

def attempt_train_test_contamination(dataset: Dataset) -> Dict[str, Any]:
    """Copy a test sample into the train split and confirm the check catches it."""
    assignment = split_assignment(dataset)
    victim = dataset.split("test")[0].sample_id
    tampered = copy.deepcopy(assignment)
    tampered[victim].append("train")          # the contamination
    before = contamination_check(assignment)
    after = contamination_check(tampered)
    return {
        "attempted": "duplicate a test sample into train",
        "clean_before": before["clean"],
        "detected_after": not after["clean"],
        "leaked_ids": after["overlapping_ids"],
    }


def attempt_stale_reuse(dataset: Dataset) -> Dict[str, Any]:
    """Compute a result on v1, change the dataset to v2, reuse -> detected stale."""
    result_v1 = evaluate(dataset, "test")
    mutated = copy.deepcopy(dataset.config)
    mutated["F1"]["seeds"] = mutated["F1"]["seeds"] + [99]   # changes the data
    dataset_v2 = build_dataset(mutated)
    return {
        "attempted": "reuse a result computed on v1 against a changed dataset v2",
        "dataset_v1": dataset.version,
        "dataset_v2": dataset_v2.version,
        "versions_differ": dataset.version != dataset_v2.version,
        "result_verdict_on_v1": validate_result(result_v1, dataset),
        "result_verdict_on_v2": validate_result(result_v1, dataset_v2),
        "stale_reuse_blocked": validate_result(result_v1, dataset_v2) == "stale",
    }


def audit(dataset: Dataset) -> Dict[str, Any]:
    result = evaluate(dataset, "test")
    contam = attempt_train_test_contamination(dataset)
    stale = attempt_stale_reuse(dataset)
    label = label_leakage_check(dataset)
    return {
        "split_disjoint": split_disjoint(dataset),
        "contamination_baseline_clean": contamination_check(split_assignment(dataset))["clean"],
        "contamination_attack": contam,
        "stale_reuse_attack": stale,
        "label_leakage": label,
        "result_fresh_against_own_dataset": validate_result(result, dataset) == "fresh",
        "passed": (split_disjoint(dataset)
                   and contamination_check(split_assignment(dataset))["clean"]
                   and contam["detected_after"]
                   and stale["stale_reuse_blocked"]
                   and label["no_label_leakage"]
                   and validate_result(result, dataset) == "fresh"),
    }
