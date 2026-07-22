"""FAULTLINE Day 13: leakage-resistant, versioned, oracle-grounded evaluation.

Builds on Days 8-12. Public surface:
    dataset:  Sample, Dataset, DatasetConfig(DEFAULT_CONFIG), build_dataset,
              GENERATOR_VERSION
    predict:  run_and_predict
    runner:   evaluate, EvalResult, CODE_VERSION
    leakage:  split_disjoint, contamination_check, label_leakage_check,
              validate_result, attempt_train_test_contamination,
              attempt_stale_reuse, audit
    card:     dataset_card
"""
from . import card, dataset, leakage, predict, runner
from .card import dataset_card
from .dataset import DEFAULT_CONFIG, GENERATOR_VERSION, Dataset, Sample, build_dataset
from .leakage import (
    attempt_stale_reuse,
    attempt_train_test_contamination,
    audit,
    contamination_check,
    label_leakage_check,
    split_disjoint,
    validate_result,
)
from .predict import run_and_predict
from .runner import CODE_VERSION, EvalResult, evaluate

__all__ = [
    "Sample", "Dataset", "DEFAULT_CONFIG", "GENERATOR_VERSION", "build_dataset",
    "run_and_predict",
    "evaluate", "EvalResult", "CODE_VERSION",
    "split_disjoint", "contamination_check", "label_leakage_check",
    "validate_result", "attempt_train_test_contamination", "attempt_stale_reuse",
    "audit", "dataset_card",
    "card", "dataset", "leakage", "predict", "runner",
]
