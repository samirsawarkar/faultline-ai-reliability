"""Tolerance band computation from baseline runs."""
from __future__ import annotations

from typing import Any, Dict, List, Sequence


def from_runs(
    runs_by_source: Dict[str, Dict[str, Dict[str, Any]]],
    golden_ids: Sequence[str],
) -> Dict[str, Any]:
    """Compute pass rate and malformed rate tolerance band across baseline sources.

    Tolerance rule:
    - PASS if candidate pass_rate >= (min_pass - 1/n_golden) AND malformed_rate <= (max_malformed + 1/n_golden)
    - FAIL if candidate pass_rate < (min_pass - 3/n_golden)
    - otherwise WARN
    """
    n_golden = len(golden_ids)
    if n_golden == 0:
        raise ValueError("golden_ids cannot be empty")
    if not runs_by_source:
        raise ValueError("runs_by_source cannot be empty")

    source_metrics: Dict[str, Dict[str, Any]] = {}
    pass_rates: List[float] = []
    malformed_rates: List[float] = []

    for source_name, runs in runs_by_source.items():
        pass_count = 0
        malformed_count = 0
        for sid in golden_ids:
            run_data = runs.get(sid, {})
            if run_data.get("grounded") is True:
                pass_count += 1
            if run_data.get("status") == "malformed":
                malformed_count += 1
        p_rate = pass_count / n_golden
        m_rate = malformed_count / n_golden
        pass_rates.append(p_rate)
        malformed_rates.append(m_rate)
        source_metrics[source_name] = {
            "pass_count": pass_count,
            "pass_rate": p_rate,
            "malformed_count": malformed_count,
            "malformed_rate": m_rate,
        }

    min_pass = min(pass_rates)
    max_pass = max(pass_rates)
    mean_pass = sum(pass_rates) / len(pass_rates)
    max_malformed = max(malformed_rates)

    agreement: Dict[str, int] = {}
    for sid in golden_ids:
        passed_sources = sum(
            1 for s in runs_by_source.values() if s.get(sid, {}).get("grounded") is True
        )
        agreement[sid] = passed_sources

    slack = 1.0 / n_golden
    fail_slack = 3.0 / n_golden

    return {
        "pass_rate": {
            "min": min_pass,
            "max": max_pass,
            "mean": mean_pass,
            "sources": len(runs_by_source),
        },
        "malformed_rate": {
            "max": max_malformed,
        },
        "per_scenario_agreement": agreement,
        "golden_ids": list(golden_ids),
        "tolerance_rule": {
            "n_golden": n_golden,
            "slack_pass": slack,
            "slack_fail": fail_slack,
            "slack_malformed": slack,
            "min_pass_threshold": min_pass - slack,
            "fail_pass_threshold": min_pass - fail_slack,
            "max_malformed_threshold": max_malformed + slack,
            "rule_description": (
                "PASS if candidate pass_rate >= (min_observed - 1/n_golden) "
                "AND malformed_rate <= (max_observed + 1/n_golden); "
                "FAIL if pass_rate < (min_observed - 3/n_golden); "
                "otherwise WARN."
            ),
        },
        "sources": source_metrics,
    }
