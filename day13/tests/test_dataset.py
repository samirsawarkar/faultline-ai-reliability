"""Versioned dataset: content-addressed version, deterministic disjoint splits,
oracle-grounded labels — nothing ambiguous."""
from __future__ import annotations

import copy
import dataclasses

from faultline_eval import DEFAULT_CONFIG, build_dataset


def test_version_is_content_addressed_and_deterministic():
    a = build_dataset()
    b = build_dataset()
    assert a.version == b.version and len(a.version) == 16


def test_changing_the_config_changes_the_version():
    cfg = copy.deepcopy(DEFAULT_CONFIG)
    cfg["F1"]["seeds"] = cfg["F1"]["seeds"] + [7]
    assert build_dataset(cfg).version != build_dataset().version


def test_splits_are_disjoint_and_cover_all_samples():
    ds = build_dataset()
    train = {s.sample_id for s in ds.split("train")}
    test = {s.sample_id for s in ds.split("test")}
    assert train.isdisjoint(test)
    assert len(train) + len(test) == len(ds.samples)
    assert train and test


def test_every_fault_kind_is_represented_in_both_splits():
    ds = build_dataset()
    fault_kinds = {(s.modality, s.kind) for s in ds.samples if s.is_fault}
    train_kinds = {(s.modality, s.kind) for s in ds.split("train") if s.is_fault}
    test_kinds = {(s.modality, s.kind) for s in ds.split("test") if s.is_fault}
    assert fault_kinds == train_kinds == test_kinds     # stratified by kind


def test_sample_ids_are_unique_content_hashes():
    ds = build_dataset()
    ids = [s.sample_id for s in ds.samples]
    assert len(ids) == len(set(ids))


def test_labels_are_oracle_grounded_not_detector_derived():
    ds = build_dataset()
    for s in ds.samples:
        assert s.expected_faulty == s.is_fault
        assert s.expected_label == (s.modality if s.is_fault else "clean")


def test_samples_are_immutable():
    ds = build_dataset()
    with __import__("pytest").raises(dataclasses.FrozenInstanceError):
        ds.samples[0].split = "train"  # type: ignore[misc]
