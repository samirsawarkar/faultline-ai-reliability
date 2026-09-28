"""Stratified sampling and task-grouped train/dev/test split for P18 trace triage.

Produces projects/p18_trace_triage/manifest.json containing 400 runs across
6 benchmarks x 2 success states (12 strata), split 50/20/30 by task group
to guarantee zero task leakage between splits.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Tuple
import random


def build_or_load_index(
    scratch_dir: Path | None = None,
    hf_cache: Path | None = None,
) -> List[Dict[str, Any]]:
    """Load or generate the metadata index for Exgentic traces."""
    if scratch_dir is None:
        scratch_dir = Path(os.environ.get("SCRATCH_DIR", "/Volumes/SamirDrive/scratch/faultline"))
    if hf_cache is None:
        hf_cache = Path(os.environ.get("HF_HOME", "/Volumes/SamirDrive/cache/huggingface"))

    index_path = scratch_dir / "p18_trace_index.json"
    if index_path.exists():
        with open(index_path, "r", encoding="utf-8") as f:
            return json.load(f)

    # If index does not exist, build it from parquet files
    import glob
    import pyarrow.parquet as pq
    import pyarrow.compute as pc

    pattern = str(hf_cache / "hub/datasets--Exgentic--agent-llm-traces-v2/snapshots/*/data/train/*.parquet")
    files = sorted(glob.glob(pattern))
    if not files:
        raise FileNotFoundError(f"No parquet shards found at {pattern}")

    scratch_dir.mkdir(parents=True, exist_ok=True)
    records = []

    for f in files:
        t = pq.read_table(f, columns=["run_id", "session_id", "benchmark", "success", "steps", "spans"])
        num_rows = len(t)
        span0 = pc.list_element(t["spans"], 0)
        attrs0 = pc.struct_field(span0, "attributes")
        inp_msgs = pc.struct_field(attrs0, "gen_ai.input.messages")

        run_ids = t["run_id"].to_pylist()
        session_ids = t["session_id"].to_pylist()
        benchmarks = t["benchmark"].to_pylist()
        successes = t["success"].to_pylist()
        steps_list = t["steps"].to_pylist()

        for i in range(num_rows):
            b = benchmarks[i]
            raw_inp = inp_msgs[i].as_py()
            prompt = ""
            if raw_inp:
                try:
                    msgs = json.loads(raw_inp)
                    for m in msgs:
                        if m.get("role") == "user":
                            for p in m.get("parts", []):
                                if p.get("type") == "text":
                                    prompt = p.get("content", "")
                                    break
                            if prompt:
                                break
                except Exception:
                    pass
            tg = f"{b}:{hashlib.sha256(prompt.encode('utf-8')).hexdigest()[:16]}"
            records.append({
                "shard_path": f,
                "row_idx": i,
                "run_id": run_ids[i],
                "session_id": session_ids[i],
                "benchmark": b,
                "success": bool(successes[i]),
                "steps": steps_list[i],
                "task_group": tg,
            })

    with open(index_path, "w", encoding="utf-8") as out:
        json.dump(records, out)

    return records


def sample_manifest(
    seed: int = 42,
    target_total: int = 400,
    output_path: Path = Path("projects/p18_trace_triage/manifest.json"),
    scratch_dir: Path | None = None,
    hf_cache: Path | None = None,
) -> Dict[str, Any]:
    """Generate deterministic stratified sample and task-grouped train/dev/test split."""
    records = build_or_load_index(scratch_dir=scratch_dir, hf_cache=hf_cache)

    # 1. Group records into benchmark x success strata
    strata: Dict[Tuple[str, bool], List[Dict[str, Any]]] = defaultdict(list)
    for r in records:
        strata[(r["benchmark"], r["success"])].append(r)

    sorted_strata_keys = sorted(strata.keys())
    num_strata = len(sorted_strata_keys)
    base_per_stratum = target_total // num_strata
    remainder = target_total % num_strata

    # 2. Stratified sampling with fixed seed
    rng_sample = random.Random(seed)
    sampled_runs: List[Dict[str, Any]] = []
    stratum_counts: Dict[str, int] = {}

    for idx, key in enumerate(sorted_strata_keys):
        count = base_per_stratum + (1 if idx < remainder else 0)
        pool = sorted(strata[key], key=lambda x: (x["session_id"], x["run_id"]))
        chosen = rng_sample.sample(pool, count)
        sampled_runs.extend(chosen)
        stratum_counts[f"{key[0]}:{key[1]}"] = len(chosen)

    # Sort sampled runs deterministically by session_id
    sampled_runs.sort(key=lambda x: x["session_id"])

    # 3. Unique task groups in the sample
    task_groups = sorted(list(set(r["task_group"] for r in sampled_runs)))
    num_tasks = len(task_groups)

    # 4. Task-grouped split: 50% train / 20% dev / 30% test
    rng_split = random.Random(seed)
    shuffled_tasks = list(task_groups)
    rng_split.shuffle(shuffled_tasks)

    n_train_tasks = round(0.50 * num_tasks)
    n_dev_tasks = round(0.20 * num_tasks)
    n_test_tasks = num_tasks - n_train_tasks - n_dev_tasks

    train_task_set = set(shuffled_tasks[:n_train_tasks])
    dev_task_set = set(shuffled_tasks[n_train_tasks : n_train_tasks + n_dev_tasks])
    test_task_set = set(shuffled_tasks[n_train_tasks + n_dev_tasks :])

    # Ensure zero task leakage
    assert len(train_task_set.intersection(dev_task_set)) == 0, "Leakage: train and dev overlap!"
    assert len(train_task_set.intersection(test_task_set)) == 0, "Leakage: train and test overlap!"
    assert len(dev_task_set.intersection(test_task_set)) == 0, "Leakage: dev and test overlap!"

    task_to_split = {}
    for tg in train_task_set:
        task_to_split[tg] = "train"
    for tg in dev_task_set:
        task_to_split[tg] = "dev"
    for tg in test_task_set:
        task_to_split[tg] = "test"

    # Assign split to each run
    for r in sampled_runs:
        r["split"] = task_to_split[r["task_group"]]

    split_runs = defaultdict(list)
    for r in sampled_runs:
        split_runs[r["split"]].append(r["session_id"])

    manifest_data = {
        "spec_version": "1.0.0",
        "seed": seed,
        "total_runs": len(sampled_runs),
        "total_tasks": num_tasks,
        "stratum_counts": stratum_counts,
        "splits": {
            "train": {
                "task_count": len(train_task_set),
                "run_count": len(split_runs["train"]),
                "task_groups": sorted(list(train_task_set)),
                "session_ids": sorted(split_runs["train"]),
            },
            "dev": {
                "task_count": len(dev_task_set),
                "run_count": len(split_runs["dev"]),
                "task_groups": sorted(list(dev_task_set)),
                "session_ids": sorted(split_runs["dev"]),
            },
            "test": {
                "task_count": len(test_task_set),
                "run_count": len(split_runs["test"]),
                "task_groups": sorted(list(test_task_set)),
                "session_ids": sorted(split_runs["test"]),
            },
        },
        "runs": sampled_runs,
    }

    # Write manifest deterministically
    output_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_bytes = json.dumps(manifest_data, indent=2, sort_keys=True).encode("utf-8")
    with open(output_path, "wb") as f:
        f.write(manifest_bytes)

    manifest_hash = hashlib.sha256(manifest_bytes).hexdigest()
    manifest_data["manifest_sha256"] = manifest_hash

    return manifest_data


def compute_manifest_sha256(path: Path) -> str:
    """Return SHA-256 of the given manifest file."""
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description="P18 Trace Triage Sample Generator")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--target-total", type=int, default=400)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("projects/p18_trace_triage/manifest.json"),
    )
    args = parser.parse_args()

    manifest = sample_manifest(
        seed=args.seed,
        target_total=args.target_total,
        output_path=args.output,
    )

    sha = compute_manifest_sha256(args.output)
    print(f"Generated manifest: {args.output}")
    print(f"Total runs: {manifest['total_runs']} ({manifest['total_tasks']} tasks)")
    print(f"Splits: train={manifest['splits']['train']['run_count']} runs ({manifest['splits']['train']['task_count']} tasks), "
          f"dev={manifest['splits']['dev']['run_count']} runs ({manifest['splits']['dev']['task_count']} tasks), "
          f"test={manifest['splits']['test']['run_count']} runs ({manifest['splits']['test']['task_count']} tasks)")
    print(f"Manifest SHA-256: {sha}")


if __name__ == "__main__":
    main()
