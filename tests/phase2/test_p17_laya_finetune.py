"""Unit tests and data leakage guards for Project P17: Laya Fine-Tuning."""
from __future__ import annotations

import json
from pathlib import Path
import pytest

from projects.p17_laya_finetune.export_data import export_finetune_data


def test_export_data_strictly_excludes_test_ids(tmp_path):
    """Verify export_data.py strictly excludes all test split scenarios (leakage guard)."""
    manifest_path = Path("projects/p05_judge/manifest.json")
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    test_ids = set(manifest["test_ids"])
    train_manifest_ids = set(manifest["train_ids"])
    dev_manifest_ids = set(manifest["dev_ids"])

    assert len(test_ids) == 60
    assert len(train_manifest_ids) == 101
    assert len(dev_manifest_ids) == 39

    # Run data export to temp directory
    summary = export_finetune_data(output_dir=tmp_path)

    train_file = Path(summary["train_file"])
    dev_file = Path(summary["dev_file"])

    assert train_file.is_file()
    assert dev_file.is_file()

    with open(train_file, "r", encoding="utf-8") as f:
        train_rows = [json.loads(line) for line in f if line.strip()]

    with open(dev_file, "r", encoding="utf-8") as f:
        dev_rows = [json.loads(line) for line in f if line.strip()]

    assert len(train_rows) == 101
    assert len(dev_rows) == 39

    exported_train_ids = {r["scenario_id"] for r in train_rows}
    exported_dev_ids = {r["scenario_id"] for r in dev_rows}

    # CRITICAL LEAKAGE ASSERTIONS
    assert len(exported_train_ids.intersection(test_ids)) == 0, "DATA LEAKAGE: test IDs found in train.jsonl!"
    assert len(exported_dev_ids.intersection(test_ids)) == 0, "DATA LEAKAGE: test IDs found in dev.jsonl!"
    assert len(exported_train_ids.intersection(exported_dev_ids)) == 0, "Train and Dev splits overlap!"

    assert exported_train_ids == train_manifest_ids
    assert exported_dev_ids == dev_manifest_ids

    # Format check for Laya fine-tuning notebook compatibility
    for row in train_rows + dev_rows:
        assert "state" in row
        assert "question" in row
        assert "label" in row
        assert row["label"] in (0, 1)
        assert row["question"]["type"] == "noul"
        assert "instructions" in row["question"]
        assert "gold" in row
        assert "questions" in row
