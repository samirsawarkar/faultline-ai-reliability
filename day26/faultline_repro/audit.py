"""Audit result traceability, exact pins, Docker, Make, and research CI."""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, List

from .utils import json_pointer, load_json

ROOT = Path(__file__).resolve().parents[2]


def _requirements() -> Dict[str, str]:
    pins = {}
    for raw in (ROOT / "requirements.txt").read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if "==" not in line or any(op in line for op in (">=", "<=", "~=", "!=")):
            raise ValueError(f"dependency is not exactly pinned: {line}")
        name, version = line.split("==", 1)
        pins[name] = version
    return pins


def audit_pins() -> Dict[str, Any]:
    pins = load_json(ROOT / "day26/pins.json")
    requirements = _requirements()
    checks = {
        "schema_version_pinned": pins["schema_version"] == "1.0.0",
        "container_python_pinned": bool(
            re.fullmatch(r"\d+\.\d+\.\d+", pins["python"]["container"])
        ),
        "ci_python_patch_versions_pinned": all(
            re.fullmatch(r"\d+\.\d+\.\d+", version)
            for version in pins["python"]["ci"]
        ),
        "dependencies_match_lock": requirements == pins["dependencies"],
        "base_image_digest_pinned": bool(
            re.fullmatch(r"sha256:[0-9a-f]{64}", pins["container"]["base_digest"])
        ),
        "actions_pinned_to_full_sha": all(
            re.fullmatch(r"[0-9a-f]{40}", action["sha"])
            for action in pins["actions"].values()
        ),
        "seeds_explicit": all(
            value is not None for value in pins["seeds"].values()
        ),
        "release_candidate_named": bool(
            re.fullmatch(r"v\d+\.\d+\.\d+-rc\d+", pins["release_candidate"])
        ),
    }
    return {
        "pins": pins,
        "requirements": requirements,
        "checks": checks,
        "passed": all(checks.values()),
    }


def audit_readme_claims(readme_path: Path = None) -> Dict[str, Any]:
    readme_path = readme_path or ROOT / "README.md"
    readme = readme_path.read_text(encoding="utf-8")
    manifest = load_json(ROOT / "day26/readme_claims.json")
    start = manifest["results_block_start"]
    end = manifest["results_block_end"]
    if start not in readme or end not in readme:
        raise ValueError("README results block markers are missing")
    block = readme.split(start, 1)[1].split(end, 1)[0]
    makefile = (ROOT / "Makefile").read_text(encoding="utf-8")
    records: List[Dict[str, Any]] = []
    for claim in manifest["claims"]:
        value_checks = []
        for value in claim["values"]:
            artifact = ROOT / value["artifact"]
            actual = (
                json_pointer(load_json(artifact), value["json_pointer"])
                if artifact.is_file()
                else None
            )
            value_checks.append(
                {
                    **value,
                    "artifact_exists": artifact.is_file(),
                    "actual": actual,
                    "matches": actual == value["value"],
                    "rendered_in_result": value["rendered"]
                    in claim["readme_result"],
                }
            )
        target = claim["command"].split()[-1]
        record = {
            "id": claim["id"],
            "readme_result": claim["readme_result"],
            "result_present": claim["readme_result"] in block,
            "generator": claim["generator"],
            "generator_exists": (ROOT / claim["generator"]).is_file(),
            "command": claim["command"],
            "command_target_present": (
                f"{target}:" in makefile
                if claim["command"].startswith("make ")
                else True
            ),
            "values": value_checks,
        }
        record["passed"] = (
            record["result_present"]
            and record["generator_exists"]
            and record["command_target_present"]
            and all(
                item["artifact_exists"]
                and item["matches"]
                and item["rendered_in_result"]
                for item in value_checks
            )
        )
        records.append(record)
    result_cells = []
    for line in block.splitlines():
        if line.startswith("|") and not line.startswith("|---"):
            columns = [column.strip() for column in line.strip("|").split("|")]
            if len(columns) >= 2 and columns[0] != "Question":
                result_cells.append(columns[1].replace("**", "").strip())
    expected_cells = [claim["readme_result"] for claim in manifest["claims"]]
    checks = {
        "results_first": (
            readme.index(start) < readme.index("## Method")
            if "## Method" in readme else False
        ),
        "every_manifest_claim_passes": all(
            record["passed"] for record in records
        ),
        "no_unregistered_result_rows": sorted(result_cells)
        == sorted(expected_cells),
    }
    try:
        readme_label = readme_path.relative_to(ROOT).as_posix()
    except ValueError:
        readme_label = str(readme_path)
    return {
        "readme": readme_label,
        "claims": records,
        "result_rows": result_cells,
        "checks": checks,
        "passed": all(checks.values()),
    }


def audit_container_contract() -> Dict[str, Any]:
    pins = load_json(ROOT / "day26/pins.json")
    dockerfile = (ROOT / "Dockerfile").read_text(encoding="utf-8")
    dockerignore = (ROOT / ".dockerignore").read_text(encoding="utf-8")
    expected_from = (
        f"FROM {pins['container']['base_tag']}@"
        f"{pins['container']['base_digest']}"
    )
    checks = {
        "base_tag_and_digest_match_pins": expected_from in dockerfile,
        "pip_version_matches_pins": (
            f"ARG PIP_VERSION={pins['container']['pip']}" in dockerfile
        ),
        "make_version_matches_pins": (
            f"make={pins['os_dependencies']['make']}" in dockerfile
        ),
        "full_reproduction_runs_at_build": "RUN make PY=python reproduce" in dockerfile,
        "non_root_runtime": "USER faultline" in dockerfile,
        "hash_seed_fixed": "PYTHONHASHSEED=0" in dockerfile,
        "git_excluded_from_context": ".git" in dockerignore.splitlines(),
        "venv_excluded_from_context": ".venv" in dockerignore.splitlines(),
    }
    return {"checks": checks, "passed": all(checks.values())}


def audit_ci_contract() -> Dict[str, Any]:
    pins = load_json(ROOT / "day26/pins.json")
    workflow = (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")
    checks = {
        "checkout_sha_pinned": (
            f"actions/checkout@{pins['actions']['checkout']['sha']}" in workflow
        ),
        "setup_python_sha_pinned": (
            f"actions/setup-python@{pins['actions']['setup_python']['sha']}"
            in workflow
        ),
        "python_patch_matrix_pinned": all(
            f'"{version}"' in workflow for version in pins["python"]["ci"]
        ),
        "full_tests_run": "make PY=python test" in workflow,
        "eval_and_fast_experiments_run": (
            "make PY=python reproduce-fast" in workflow
        ),
        "clean_container_build_runs": "docker build" in workflow,
        "evidence_diff_checked": "git diff --exit-code" in workflow,
    }
    return {"checks": checks, "passed": all(checks.values())}
