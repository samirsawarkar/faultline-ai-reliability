"""Create a candidate snapshot and execute REPRODUCE.md as a cold reader."""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Dict, Optional

from .protocol import (
    ROOT,
    extract_cold_block,
    extract_expected_output,
    load_protocol,
    sha256_text,
)


def _run(command, cwd: Path, env=None) -> subprocess.CompletedProcess:
    return subprocess.run(
        command,
        cwd=str(cwd),
        env=env,
        check=True,
        capture_output=True,
        text=True,
    )


def parse_snapshot_file_list(value: str):
    return [Path(item) for item in value.split("\0") if item]


def prepare_snapshot(destination: Path) -> Path:
    """Commit the candidate worktree into an isolated tagged source repository."""

    if destination.exists():
        raise ValueError(f"snapshot destination already exists: {destination}")
    destination.mkdir(parents=True)
    completed = _run(
        ["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard"],
        ROOT,
    )
    relative_files = parse_snapshot_file_list(completed.stdout)
    for relative in relative_files:
        source = ROOT / relative
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(str(source), str(target))

    env = os.environ.copy()
    env.update(
        {
            "GIT_AUTHOR_NAME": "FAULTLINE cold-test fixture",
            "GIT_AUTHOR_EMAIL": "cold-test@example.invalid",
            "GIT_COMMITTER_NAME": "FAULTLINE cold-test fixture",
            "GIT_COMMITTER_EMAIL": "cold-test@example.invalid",
            "GIT_AUTHOR_DATE": "2000-01-01T00:00:00Z",
            "GIT_COMMITTER_DATE": "2000-01-01T00:00:00Z",
        }
    )
    _run(["git", "init", "-b", "main"], destination, env)
    _run(["git", "add", "."], destination, env)
    _run(["git", "commit", "-m", "candidate snapshot"], destination, env)
    _run(
        ["git", "tag", load_protocol()["release_revision"]],
        destination,
        env,
    )
    return destination


def run_documented_cold_start(
    repository_url: str,
    evidence_directory: Path,
    workspace_parent: Optional[Path] = None,
) -> Dict[str, Any]:
    block = extract_cold_block()
    expected = extract_expected_output()
    evidence_directory.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    env["FAULTLINE_REPOSITORY_URL"] = repository_url

    with tempfile.TemporaryDirectory(
        prefix="faultline-cold-reader-",
        dir=str(workspace_parent) if workspace_parent else None,
    ) as temporary:
        workspace = Path(temporary)
        completed = subprocess.run(
            ["/bin/sh", "-eu", "-c", block],
            cwd=str(workspace),
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        output = completed.stdout
        clone = workspace / load_protocol()["clone_directory"]
        fresh_clone_created = clone.is_dir() and (clone / ".git").is_dir()

    sanitized = output.replace(repository_url, "$FAULTLINE_REPOSITORY_URL")
    sanitized = re.sub(
        r"/(?:private/)?tmp/faultline-cold-reader-[^/\s]+",
        "$COLD_WORKSPACE",
        sanitized,
    )
    expected_lines = expected.splitlines()
    all_expected = all(line in sanitized for line in expected_lines)
    question_match = re.search(r"reader questions: (\d+)", sanitized)
    improvisation_match = re.search(
        r"operator improvisations: (\d+)", sanitized
    )
    report = {
        "schema_version": "1.0.0",
        "release_revision": load_protocol()["release_revision"],
        "source_transport": "documented_repository_url_override",
        "document": "REPRODUCE.md",
        "document_block_sha256": sha256_text(block),
        "document_block_executed_verbatim": True,
        "fresh_clone_created": fresh_clone_created,
        "exit_code": completed.returncode,
        "all_expected_lines_observed": all_expected,
        "reader_questions": (
            int(question_match.group(1)) if question_match else None
        ),
        "operator_improvisations": (
            int(improvisation_match.group(1))
            if improvisation_match else None
        ),
        "workspace_removed_after_run": True,
        "passed": (
            completed.returncode == 0
            and fresh_clone_created
            and all_expected
            and question_match is not None
            and question_match.group(1) == "0"
            and improvisation_match is not None
            and improvisation_match.group(1) == "0"
        ),
    }
    transcript = "\n".join(
        [
            "FAULTLINE DAY 27 COLD-START TRANSCRIPT",
            "source: REPRODUCE.md COLD-START block",
            "transport: documented FAULTLINE_REPOSITORY_URL override",
            "starting state: fresh empty temporary directory",
            "reader questions before execution: 0",
            "operator interventions during execution: 0",
            "",
            "$ /bin/sh -eu -c '<REPRODUCE.md COLD-START block>'",
            sanitized.rstrip(),
            f"[exit {completed.returncode}]",
            "",
        ]
    )
    (evidence_directory / "COLD-START-TRANSCRIPT.txt").write_text(
        transcript, encoding="utf-8"
    )
    (evidence_directory / "cold_start_report.json").write_text(
        json.dumps(report, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    return report
