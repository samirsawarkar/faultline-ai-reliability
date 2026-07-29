"""Repeated and cross-process proof of each incident's red→green fix."""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List

from .catalog import get_incident
from .config import PostmortemConfig, canonical_config
from .runner import run_incident


def _cross_process(
    incident_id: str,
    version: str,
    config: PostmortemConfig,
    hashseeds: List[int],
) -> List[Dict[str, Any]]:
    root = Path(__file__).resolve().parents[2]
    pythonpath = os.pathsep.join(str(root / day) for day in ("day25", "day04"))
    config_json = json.dumps(
        config.to_dict(), sort_keys=True, separators=(",", ":")
    )
    records = []
    for hashseed in hashseeds:
        env = os.environ.copy()
        env["PYTHONPATH"] = pythonpath
        env["PYTHONHASHSEED"] = str(hashseed)
        completed = subprocess.run(
            [
                sys.executable,
                "-m",
                "faultline_postmortem.replay_once",
                "--incident",
                incident_id,
                "--version",
                version,
                "--config-json",
                config_json,
            ],
            check=True,
            capture_output=True,
            text=True,
            env=env,
        )
        payload = json.loads(completed.stdout)
        records.append({"python_hash_seed": hashseed, **payload})
    return records


def _version_stability(runs: List[Dict[str, Any]]) -> Dict[str, Any]:
    run_digests = sorted({run["run_digest"] for run in runs})
    trace_digests = sorted({run["trace_digest"] for run in runs})
    colors = sorted({run["regression"]["color"] for run in runs})
    return {
        "repetitions": len(runs),
        "unique_run_digests": run_digests,
        "unique_trace_digests": trace_digests,
        "unique_regression_colors": colors,
        "all_traces_complete": all(
            run["trace_audit"]["passed"] for run in runs
        ),
        "stable": (
            len(run_digests) == 1
            and len(trace_digests) == 1
            and len(colors) == 1
            and all(run["trace_audit"]["passed"] for run in runs)
        ),
    }


def verify_red_green(
    incident_id: str,
    config: PostmortemConfig = None,
    repetitions: int = 20,
    include_cross_process: bool = True,
) -> Dict[str, Any]:
    if repetitions < 2:
        raise ValueError("repetitions must be at least 2")
    config = (config or canonical_config()).validate()
    spec = get_incident(incident_id)
    before_runs = [
        run_incident(incident_id, "legacy", config)
        for _ in range(repetitions)
    ]
    after_runs = [
        run_incident(incident_id, "fixed", config)
        for _ in range(repetitions)
    ]
    before = before_runs[0]
    after = after_runs[0]
    before_stability = _version_stability(before_runs)
    after_stability = _version_stability(after_runs)
    cross = {}
    if include_cross_process:
        for version, expected in (("legacy", before), ("fixed", after)):
            records = _cross_process(
                incident_id, version, config, [0, 1, 7, 99]
            )
            cross[version] = {
                "runs": records,
                "stable": all(
                    record["run_digest"] == expected["run_digest"]
                    and record["trace_digest"] == expected["trace_digest"]
                    and record["regression_color"]
                    == expected["regression"]["color"]
                    for record in records
                ),
            }
    flip = {
        "same_seed": before["seed"] == after["seed"] == spec.seed,
        "same_config": (
            before["config_digest"] == after["config_digest"]
        ),
        "same_regression_test": (
            before["regression"]["test_id"]
            == after["regression"]["test_id"]
            == spec.regression_test_id
        ),
        "before_is_red": (
            before["regression"]["color"] == "red"
            and not before["regression"]["passed"]
        ),
        "after_is_green": (
            after["regression"]["color"] == "green"
            and after["regression"]["passed"]
        ),
        "post_fix_stays_green": (
            after_stability["stable"]
            and after_stability["unique_regression_colors"] == ["green"]
        ),
    }
    result = {
        "incident_id": incident_id,
        "seed": spec.seed,
        "config_digest": before["config_digest"],
        "regression_test_id": spec.regression_test_id,
        "before": {
            "policy_version": before["policy_version"],
            "run_digest": before["run_digest"],
            "trace_digest": before["trace_digest"],
            "terminal": before["terminal"],
            "metrics": before["metrics"],
            "regression": before["regression"],
            "stability": before_stability,
        },
        "after": {
            "policy_version": after["policy_version"],
            "run_digest": after["run_digest"],
            "trace_digest": after["trace_digest"],
            "terminal": after["terminal"],
            "metrics": after["metrics"],
            "regression": after["regression"],
            "stability": after_stability,
        },
        "cross_process": cross,
        "flip_checks": flip,
    }
    cross_ok = (
        all(item["stable"] for item in cross.values())
        if include_cross_process
        else True
    )
    result["replay_verified_fix"] = (
        before_stability["stable"]
        and after_stability["stable"]
        and all(flip.values())
        and cross_ok
    )
    return result
