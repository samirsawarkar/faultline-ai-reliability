"""Repeated and cross-process proof that one seed+configuration reproduces the chain."""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List

from .cascade import CANONICAL_SEED, EXPECTED_CHAIN, run_cascade
from .config import CascadeConfig, canonical_config


def canonical_digest(value: Any) -> str:
    payload = json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _cross_process_digests(
    seed: int,
    config: CascadeConfig,
    hashseeds: List[int],
) -> List[Dict[str, Any]]:
    root = Path(__file__).resolve().parents[2]
    pythonpath = os.pathsep.join(
        str(root / day)
        for day in ("day23", "day04", "day14", "day16", "day20", "day21")
    )
    code = (
        "import json,sys;"
        "from faultline_cascade import CascadeConfig,run_cascade;"
        "cfg=CascadeConfig(**json.loads(sys.argv[2]));"
        "print(run_cascade(int(sys.argv[1]),cfg)['incident_digest'])"
    )
    config_json = json.dumps(config.to_dict(), sort_keys=True, separators=(",", ":"))
    outputs = []
    for hashseed in hashseeds:
        env = os.environ.copy()
        env["PYTHONPATH"] = pythonpath
        env["PYTHONHASHSEED"] = str(hashseed)
        completed = subprocess.run(
            [sys.executable, "-c", code, str(seed), config_json],
            check=True,
            capture_output=True,
            text=True,
            env=env,
        )
        outputs.append(
            {"python_hash_seed": hashseed, "digest": completed.stdout.strip()}
        )
    return outputs


def replay_stability(
    seed: int = CANONICAL_SEED,
    config: CascadeConfig = None,
    repetitions: int = 20,
    include_cross_process: bool = True,
) -> Dict[str, Any]:
    config = (config or canonical_config()).validate()
    if repetitions < 2:
        raise ValueError("repetitions must be at least 2")
    runs = [run_cascade(seed, config) for _ in range(repetitions)]
    digests = [run["incident_digest"] for run in runs]
    trace_digests = [run["trace_digest"] for run in runs]
    chains = [[event["label"] for event in run["events"]] for run in runs]
    cross = (
        _cross_process_digests(seed, config, [0, 1, 7, 99])
        if include_cross_process
        else []
    )
    expected_digest = digests[0]
    cross_stable = (
        all(item["digest"] == expected_digest for item in cross)
        if include_cross_process
        else None
    )
    return {
        "seed": seed,
        "config": config.to_dict(),
        "config_digest": runs[0]["config_digest"],
        "repetitions": repetitions,
        "unique_incident_digests": sorted(set(digests)),
        "unique_trace_digests": sorted(set(trace_digests)),
        "unique_label_chains": sorted(
            {json.dumps(chain, separators=(",", ":")) for chain in chains}
        ),
        "expected_chain": list(EXPECTED_CHAIN),
        "in_process_stable": (
            len(set(digests)) == 1
            and len(set(trace_digests)) == 1
            and all(tuple(chain) == EXPECTED_CHAIN for chain in chains)
        ),
        "cross_process_runs": cross,
        "cross_process_stable": cross_stable,
        "all_runs_trace_complete_and_labelled": all(
            run["audit"]["passed"] for run in runs
        ),
        "reproducible_from_one_seed_and_config": (
            len(set(digests)) == 1
            and len(set(trace_digests)) == 1
            and all(tuple(chain) == EXPECTED_CHAIN for chain in chains)
            and (cross_stable if include_cross_process else True)
            and all(run["audit"]["passed"] for run in runs)
        ),
    }
