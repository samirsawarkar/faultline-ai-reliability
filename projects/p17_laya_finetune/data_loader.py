"""Shared data loading utilities for P17 Laya Fine-Tuning."""
from __future__ import annotations

import csv
import json
from pathlib import Path
import sqlite3
import sys
from collections import defaultdict
from typing import Any, Dict, List, Tuple

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from faultline_p2.env.corpus import build_corpus
from faultline_p2.judge.evaluators import (
    OVERCONSTRAINED_SEARCH_RUBRIC,
    build_overconstrained_context,
)


def load_dataset_records(
    csv_path: Path = Path("projects/p04_taxonomy/coding_sheet.csv"),
    manifest_path: Path = Path("projects/p05_judge/manifest.json"),
    db_path: Path = Path("projects/p03_grounding/trace.db"),
    sweep_path: Path = Path("projects/p03_grounding/sweep_output.json"),
) -> Tuple[Dict[str, Any], Dict[str, str], Dict[str, str], Dict[str, List[str]]]:
    """Load scenarios, ground truth, manifest splits, and generated contexts.

    Returns:
        (manifest, labels_map, contexts_map, splits_map)
    """
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    with open(csv_path, "r", encoding="utf-8") as f:
        labels = {r["scenario_id"]: r["axial_failure_mode"] for r in csv.DictReader(f)}

    corpus = build_corpus()
    scenario_map = {s.scenario_id: s for s in corpus.scenarios}

    sweep_data: Dict[str, Any] = {}
    if sweep_path.exists():
        with open(sweep_path, "r", encoding="utf-8") as f:
            for item in json.load(f).get("results", []):
                sweep_data[item["task_id"]] = item

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    spans_by_sc: Dict[str, List[sqlite3.Row]] = defaultdict(list)
    for s in conn.execute("SELECT * FROM spans ORDER BY scenario_id, step_index ASC").fetchall():
        spans_by_sc[s["scenario_id"]].append(s)
    conn.close()

    contexts: Dict[str, str] = {}
    all_ids = manifest["train_ids"] + manifest["dev_ids"] + manifest["test_ids"]
    for sid in all_ids:
        sc = scenario_map.get(sid)
        spans = spans_by_sc.get(sid, [])
        sw = sweep_data.get(sid, {})
        contexts[sid] = build_overconstrained_context(sid, spans, sw, sc)

    splits = {
        "train": manifest["train_ids"],
        "dev": manifest["dev_ids"],
        "test": manifest["test_ids"],
    }

    return manifest, labels, contexts, splits
