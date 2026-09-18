"""Evaluation of candidate runs against release gate tolerance band."""
from __future__ import annotations

from typing import Any, Dict, List, Sequence, Union


def evaluate(
    candidate_runs: Union[Dict[str, Dict[str, Any]], Sequence[Dict[str, Any]]],
    band: Dict[str, Any],
) -> Dict[str, Any]:
    """Evaluate candidate model runs against a pre-computed tolerance band.

    Returns:
    {
        "verdict": "PASS" | "WARN" | "FAIL",
        "metrics": {...},
        "band_used": band,
        "per_scenario_diff": regressions,
        "regressions": regressions,
    }
    """
    runs_map: Dict[str, Dict[str, Any]] = {}
    if isinstance(candidate_runs, dict):
        runs_map = candidate_runs
    else:
        for r in candidate_runs:
            sid = r.get("scenario_id") or r.get("task_id")
            if sid:
                runs_map[str(sid)] = r

    golden_ids: List[str] = band.get("golden_ids") or list(band.get("per_scenario_agreement", {}).keys())
    n_golden = len(golden_ids)
    if n_golden == 0:
        raise ValueError("band does not contain any golden scenarios")

    pass_count = sum(1 for sid in golden_ids if runs_map.get(sid, {}).get("grounded") is True)
    pass_rate = pass_count / n_golden

    malformed_count = sum(1 for sid in golden_ids if runs_map.get(sid, {}).get("status") == "malformed")
    malformed_rate = malformed_count / n_golden

    min_pass = band["pass_rate"]["min"]
    max_malformed = band["malformed_rate"]["max"]

    eps = 1e-9
    slack = 1.0 / n_golden
    fail_slack = 3.0 / n_golden

    pass_threshold = min_pass - slack
    fail_threshold = min_pass - fail_slack
    malformed_threshold = max_malformed + slack

    if pass_rate < fail_threshold - eps:
        verdict = "FAIL"
    elif pass_rate >= pass_threshold - eps and malformed_rate <= malformed_threshold + eps:
        verdict = "PASS"
    else:
        verdict = "WARN"

    total_sources = band["pass_rate"].get("sources", 1)
    agreement = band.get("per_scenario_agreement", {})
    regressions = [
        sid for sid in golden_ids
        if agreement.get(sid, 0) == total_sources and not runs_map.get(sid, {}).get("grounded", False)
    ]

    metrics = {
        "n_golden": n_golden,
        "pass_count": pass_count,
        "pass_rate": pass_rate,
        "malformed_count": malformed_count,
        "malformed_rate": malformed_rate,
        "pass_threshold": pass_threshold,
        "fail_threshold": fail_threshold,
        "malformed_threshold": malformed_threshold,
    }

    return {
        "verdict": verdict,
        "metrics": metrics,
        "band_used": band,
        "per_scenario_diff": regressions,
        "regressions": regressions,
    }
