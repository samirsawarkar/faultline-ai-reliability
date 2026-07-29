"""Audits for assumption-free instructions and their cold-reader evidence."""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict

from .protocol import ROOT, extract_cold_block, load_json, load_protocol

EVIDENCE = ROOT / "day27/evidence"


def audit_document(document: Path = None) -> Dict[str, Any]:
    path = document or ROOT / "REPRODUCE.md"
    text = path.read_text(encoding="utf-8")
    protocol = load_protocol()
    try:
        block = extract_cold_block(path)
        parse_error = None
    except ValueError as exc:
        block = ""
        parse_error = str(exc)
    lines = [line for line in block.splitlines() if line.strip()]
    checks = {
        "single_machine_executable_block": parse_error is None,
        "public_repository_exact": protocol["repository_url"] in block,
        "documented_repository_override": (
            "FAULTLINE_REPOSITORY_URL" in block
            and "FAULTLINE_REPOSITORY_URL" in text.split(
                "<!-- COLD-START:BEGIN -->", 1
            )[0]
        ),
        "release_revision_exact": (
            f"--branch {protocol['release_revision']}" in block
        ),
        "clone_directory_exact": (
            block.count(protocol["clone_directory"]) >= 2
        ),
        "one_cold_command": lines[-1:] == ["make cold-reproduce"],
        "no_host_python_bootstrap": not any(
            token in block for token in ("pip install", "python -m venv", ".venv")
        ),
        "all_headline_values_explicit": all(
            claim["readme_result"] in text
            for claim in load_json(ROOT / "day26/readme_claims.json")["claims"]
        ),
        "host_requirements_explicit": all(
            token in text
            for token in (
                "Git `2.39`",
                "GNU Make `3.81`",
                "Docker Engine or Docker Desktop",
                "2 CPU cores",
                "4 GiB memory",
                "5 GiB free disk",
                "outbound HTTPS",
            )
        ),
        "daemon_preflight_explicit": "docker version" in text,
        "failure_actions_explicit": all(
            symptom in text
            for symptom in (
                "Remote branch",
                "Cannot connect to the Docker daemon",
                "no space left on device",
                "expected number differs",
                "clone destination already exists",
            )
        ),
        "no_placeholders_or_todos": not re.search(
            r"\b(?:TODO|TBD|CHANGEME|YOUR_[A-Z_]+)\b", text
        ),
        "claim_boundary_explicit": (
            "do not prove production" in text.lower()
        ),
    }
    try:
        document_label = path.relative_to(ROOT).as_posix()
    except ValueError:
        document_label = str(path)
    return {
        "document": document_label,
        "parse_error": parse_error,
        "cold_block": block,
        "checks": checks,
        "passed": all(checks.values()),
    }


def _missing(name: str) -> Dict[str, Any]:
    return {"artifact": name, "missing": True, "passed": False}


def audit_transcript() -> Dict[str, Any]:
    path = EVIDENCE / "cold_start_report.json"
    if not path.is_file():
        return _missing(path.name)
    report = load_json(path)
    checks = {
        "not_a_bootstrap_fixture": not report.get("bootstrap_only", False),
        "document_block_executed_verbatim": report.get(
            "document_block_executed_verbatim", False
        ),
        "fresh_clone_created": report.get("fresh_clone_created", False),
        "exit_zero": report.get("exit_code") == 0,
        "all_expected_lines_observed": report.get(
            "all_expected_lines_observed", False
        ),
        "reader_questions_zero": report.get("reader_questions") == 0,
        "operator_improvisations_zero": (
            report.get("operator_improvisations") == 0
        ),
        "transcript_written": (
            EVIDENCE / "COLD-START-TRANSCRIPT.txt"
        ).is_file(),
    }
    return {"report": report, "checks": checks, "passed": all(checks.values())}


def audit_friction() -> Dict[str, Any]:
    path = EVIDENCE / "friction_log.json"
    if not path.is_file():
        return _missing(path.name)
    report = load_json(path)
    entries = report.get("entries", [])
    checks = {
        "ambiguities_were_treated_as_defects": len(entries) >= 5,
        "every_friction_has_resolution": all(
            item.get("status") == "resolved"
            and item.get("resolution")
            and item.get("verification")
            for item in entries
        ),
        "final_reader_questions_zero": report.get(
            "final_reader_questions"
        ) == 0,
        "final_operator_improvisations_zero": report.get(
            "final_operator_improvisations"
        ) == 0,
        "rendered_log_written": (EVIDENCE / "FRICTION-LOG.md").is_file(),
    }
    return {"report": report, "checks": checks, "passed": all(checks.values())}


def audit_peer() -> Dict[str, Any]:
    path = EVIDENCE / "peer_attempt.json"
    if not path.is_file():
        return _missing(path.name)
    report = load_json(path)
    checks = {
        "not_a_bootstrap_fixture": not report.get("bootstrap_only", False),
        "attempt_requested": report.get("requested", False),
        "peer_had_no_prior_context": report.get("cold_context", False),
        "peer_used_only_reproduce_document": report.get(
            "used_only_reproduce_document", False
        ),
        "peer_questions_zero": report.get("reader_questions") == 0,
        "peer_improvisations_zero": report.get("operator_improvisations") == 0,
        "peer_workspace_unchanged": not report.get("workspace_modified", True),
        "peer_request_rendered": (EVIDENCE / "PEER-REQUEST.md").is_file(),
    }
    return {"report": report, "checks": checks, "passed": all(checks.values())}
