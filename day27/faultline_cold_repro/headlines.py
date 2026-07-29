"""Regenerate and render the registered README headline results."""
from __future__ import annotations

import json
import os
import shlex
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "day26"))

from faultline_repro import audit_readme_claims  # noqa: E402

from .protocol import load_json, load_protocol, sha256_text  # noqa: E402


def _run_generator(command: str) -> Dict[str, Any]:
    env = os.environ.copy()
    env["PYTHONHASHSEED"] = "0"
    invocation = shlex.split(command)
    if invocation[0] == "make":
        invocation.insert(1, f"PY={sys.executable}")
    completed = subprocess.run(
        invocation,
        cwd=str(ROOT),
        env=env,
        capture_output=True,
        text=True,
    )
    output = completed.stdout + completed.stderr
    return {
        "command": command,
        "invocation": invocation,
        "exit_code": completed.returncode,
        "output_sha256": sha256_text(output),
        "failure_output": output[-4000:] if completed.returncode else None,
        "passed": completed.returncode == 0,
    }


def build_headline_result(run_generators: bool = True) -> Dict[str, Any]:
    manifest = load_json(ROOT / "day26/readme_claims.json")
    generators: List[Dict[str, Any]] = []
    if run_generators:
        for claim in manifest["claims"]:
            if claim["id"] == "tests":
                continue
            generators.append(_run_generator(claim["command"]))
            if not generators[-1]["passed"]:
                raise RuntimeError(
                    f"headline generator failed: {claim['command']}\n"
                    f"{generators[-1]['failure_output']}"
                )

    audit = audit_readme_claims()
    test_report = load_json(ROOT / "day26/evidence/test_report.json")
    records = [
        {
            "id": claim["id"],
            "result": claim["readme_result"],
            "values_match": all(
                value["matches"] and value["rendered_in_result"]
                for value in claim["values"]
            ),
        }
        for claim in audit["claims"]
    ]
    passed = (
        audit["passed"]
        and test_report["passed_all"]
        and test_report["collected"] == test_report["passed"]
        and all(record["values_match"] for record in records)
        and all(item["passed"] for item in generators)
    )
    return {
        "schema_version": "1.0.0",
        "release_revision": load_protocol()["release_revision"],
        "headlines": records,
        "test_gate": {
            "collected": test_report["collected"],
            "passed": test_report["passed"],
            "passed_all": test_report["passed_all"],
        },
        "generators": generators,
        "reader_questions": 0,
        "operator_improvisations": 0,
        "passed": passed,
    }


def render_headline_result(report: Dict[str, Any]) -> str:
    lines = [
        f"headline {item['id']}: {item['result']}"
        for item in report["headlines"]
    ]
    lines.extend(
        [
            f"reader questions: {report['reader_questions']}",
            f"operator improvisations: {report['operator_improvisations']}",
            f"cold reproduction: {'PASS' if report['passed'] else 'FAIL'}",
        ]
    )
    return "\n".join(lines)
