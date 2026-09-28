"""Export train and dev splits for Laya fine-tuning on OVERCONSTRAINED_SEARCH_LOOP.

Exports train.jsonl (101 cases) and dev.jsonl (39 cases) in the format expected
by Laya's official fine-tuning notebook (laya_finetune_typed_decisions_2xT4_kaggle.ipynb).
STRICT LEAKAGE GUARD: Does NOT include or export any test scenarios.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any, Dict

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from faultline_p2.judge.evaluators import OVERCONSTRAINED_SEARCH_RUBRIC
from projects.p17_laya_finetune.data_loader import load_dataset_records


def export_finetune_data(
    output_dir: Path = Path("projects/p17_laya_finetune"),
) -> Dict[str, Any]:
    manifest, labels, contexts, splits = load_dataset_records()

    train_ids = splits["train"]
    dev_ids = splits["dev"]
    test_ids = splits["test"]

    # Strict leakage validation
    assert len(set(train_ids).intersection(set(test_ids))) == 0, "LEAKAGE: train overlaps test!"
    assert len(set(dev_ids).intersection(set(test_ids))) == 0, "LEAKAGE: dev overlaps test!"
    assert len(train_ids) == 101, f"Expected 101 train IDs, got {len(train_ids)}"
    assert len(dev_ids) == 39, f"Expected 39 dev IDs, got {len(dev_ids)}"

    output_dir.mkdir(parents=True, exist_ok=True)
    train_file = output_dir / "train.jsonl"
    dev_file = output_dir / "dev.jsonl"

    def make_record(sid: str) -> Dict[str, Any]:
        context = contexts[sid]
        gt = (labels[sid] == "OVERCONSTRAINED_SEARCH_LOOP")
        label_int = 1 if gt else 0
        choice_str = "true" if gt else "false"
        probs = {"false": 0.0 if gt else 1.0, "true": 1.0 if gt else 0.0}

        q_dict = {
            "type": "noul",
            "instructions": OVERCONSTRAINED_SEARCH_RUBRIC,
        }
        gold_q = {
            "type": "noul",
            "choice": choice_str,
            "probabilities": probs,
        }

        return {
            "scenario_id": sid,
            "state": context,
            "question": q_dict,
            "label": label_int,
            # Full structure matching typed-decisions dataset in Laya fine-tuning notebook:
            "questions": {
                "detected": q_dict,
            },
            "gold": {
                "detected": gold_q,
            },
        }

    train_records = [make_record(sid) for sid in train_ids]
    dev_records = [make_record(sid) for sid in dev_ids]

    train_pos = sum(1 for r in train_records if r["label"] == 1)
    dev_pos = sum(1 for r in dev_records if r["label"] == 1)

    assert train_pos == 17, f"Expected 17 train positives, got {train_pos}"
    assert dev_pos == 5, f"Expected 5 dev positives, got {dev_pos}"

    with open(train_file, "w", encoding="utf-8") as f:
        for r in train_records:
            f.write(json.dumps(r) + "\n")

    with open(dev_file, "w", encoding="utf-8") as f:
        for r in dev_records:
            f.write(json.dumps(r) + "\n")

    print(f"Exported train set: {train_file} ({len(train_records)} rows, {train_pos} positives, {len(train_records)-train_pos} negatives)")
    print(f"Exported dev set  : {dev_file} ({len(dev_records)} rows, {dev_pos} positives, {len(dev_records)-dev_pos} negatives)")
    print(f"Test split held out untouched: {len(test_ids)} scenarios.")

    return {
        "train_file": str(train_file),
        "train_count": len(train_records),
        "train_positives": train_pos,
        "dev_file": str(dev_file),
        "dev_count": len(dev_records),
        "dev_positives": dev_pos,
        "test_held_out": len(test_ids),
    }


def main():
    parser = argparse.ArgumentParser(description="Export Laya Fine-Tuning Data")
    parser.add_argument(
        "--output-dir",
        default="projects/p17_laya_finetune",
        help="Directory to save train.jsonl and dev.jsonl",
    )
    args = parser.parse_args()
    export_finetune_data(Path(args.output_dir))


if __name__ == "__main__":
    main()
