"""Assemble Day-26 reproduction evidence and Checkpoint 26."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

from .audit import (
    ROOT,
    audit_ci_contract,
    audit_container_contract,
    audit_pins,
    audit_readme_claims,
)
from .utils import load_json


def _load_evidence(name: str) -> Dict[str, Any]:
    path = ROOT / "day26/evidence" / name
    if not path.is_file():
        return {"passed": False, "missing": path.relative_to(ROOT).as_posix()}
    return load_json(path)


def build_report(require_container: bool = True) -> Dict[str, Any]:
    pins = audit_pins()
    readme = audit_readme_claims()
    container_contract = audit_container_contract()
    ci = audit_ci_contract()
    tests = _load_evidence("test_report.json")
    fast_tests = _load_evidence("fast_test_report.json")
    evaluation = _load_evidence("eval_verification.json")
    experiments = _load_evidence("fast_experiment_report.json")
    container_run = _load_evidence("container_verification.json")
    checks = {
        "results_first_readme_traceable": readme["passed"],
        "dependencies_versions_and_seeds_pinned": pins["passed"],
        "dockerfile_contract_valid": container_contract["passed"],
        "make_full_tests_green": tests.get("passed_all", False),
        "make_fast_tests_green": fast_tests.get("passed_all", False),
        "frozen_eval_green": evaluation.get("passed", False),
        "fast_experiment_subset_green": experiments.get("passed", False),
        "research_ci_contract_green": ci["passed"],
        "clean_container_reproduction_green": (
            container_run.get("passed", False) if require_container else True
        ),
    }
    checkpoint = {
        "checkpoint": 26,
        "mission": (
            "Make evidence self-explanatory, one-command runnable and continuously checked."
        ),
        "release_candidate": pins["pins"]["release_candidate"],
        "checks": checks,
        "fail_condition_triggered": not all(checks.values()),
        "passed": all(checks.values()),
    }
    return {
        "pins_audit": pins,
        "readme_traceability": readme,
        "container_contract": container_contract,
        "ci_contract": ci,
        "test_report": tests,
        "fast_test_report": fast_tests,
        "eval_verification": evaluation,
        "fast_experiment_report": experiments,
        "container_verification": container_run,
        "checkpoint_26": checkpoint,
    }


def render_checkpoint(report: Dict[str, Any]) -> str:
    checkpoint = report["checkpoint_26"]
    lines: List[str] = [
        "# CHECKPOINT 26 — one-command, continuously checked evidence",
        "",
        f"Release candidate: `{checkpoint['release_candidate']}`.",
        "",
        "| gate | passed |",
        "|---|---|",
    ]
    for name, passed in checkpoint["checks"].items():
        lines.append(f"| {name} | {passed} |")
    lines.extend([
        "",
        f"Fail condition triggered: **{checkpoint['fail_condition_triggered']}**.",
        f"Checkpoint passed: **{checkpoint['passed']}**.",
        "",
    ])
    return "\n".join(lines)
