"""Small, dependency-free helpers for resolving committed evidence."""
from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any, Dict, Iterable, Optional

ROOT = Path(__file__).resolve().parents[2]
DAY = ROOT / "day28"
EVIDENCE = DAY / "evidence"
FIGURES = EVIDENCE / "figures"


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def dump_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, sort_keys=True, ensure_ascii=True, indent=2) + "\n",
        encoding="utf-8",
    )


def resolve_pointer(document: Any, pointer: str) -> Any:
    """Resolve an RFC-6901 JSON pointer."""
    if pointer == "":
        return document
    if not pointer.startswith("/"):
        raise ValueError(f"JSON pointer must start with '/': {pointer}")
    value = document
    for raw in pointer[1:].split("/"):
        key = raw.replace("~1", "/").replace("~0", "~")
        value = value[int(key)] if isinstance(value, list) else value[key]
    return value


def source_value(artifact: str, pointer: str) -> Any:
    return resolve_pointer(load_json(ROOT / artifact), pointer)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return digest.hexdigest()


def _git_source_identity(artifact: str) -> Optional[Dict[str, Any]]:
    """Prove that the working byte stream is exactly the blob stored at HEAD."""
    try:
        head = subprocess.run(
            ["git", "rev-parse", f"HEAD:{artifact}"],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
        )
        working = subprocess.run(
            ["git", "hash-object", artifact],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
        )
    except FileNotFoundError:
        return None
    if head.returncode != 0 or working.returncode != 0:
        return None
    head_blob = head.stdout.strip()
    working_blob = working.stdout.strip()
    return {
        "git_blob_at_head": head_blob,
        "provenance_method": "git_head",
        "verified": head_blob == working_blob,
    }


def _manifest_source_identity(artifact: str) -> Optional[Dict[str, Any]]:
    """Verify source bytes against the Git-backed audit shipped in an image.

    Docker intentionally excludes `.git`. The committed publication audit is
    therefore the portable provenance witness inside the clean image. Host CI
    creates that witness only after `_git_source_identity` proves exact HEAD
    identity.
    """
    manifest_path = EVIDENCE / "claim_audit.json"
    if not manifest_path.is_file():
        return None
    try:
        record = load_json(manifest_path)["sources"][artifact]
        blob = record["git_blob_at_head"]
        expected_sha256 = record["sha256"]
    except (KeyError, TypeError, json.JSONDecodeError):
        return None
    blob_valid = (
        isinstance(blob, str)
        and len(blob) == 40
        and all(character in "0123456789abcdef" for character in blob)
    )
    return {
        "git_blob_at_head": blob if blob_valid else None,
        "provenance_method": "committed_manifest",
        "verified": (
            blob_valid
            and expected_sha256 == sha256_file(ROOT / artifact)
        ),
    }


def source_identity(artifact: str) -> Dict[str, Any]:
    identity = _git_source_identity(artifact)
    if identity is not None:
        return identity
    identity = _manifest_source_identity(artifact)
    if identity is not None:
        return identity
    return {
        "git_blob_at_head": None,
        "provenance_method": "unverified",
        "verified": False,
    }


def committed_blob(artifact: str) -> str | None:
    identity = source_identity(artifact)
    return identity["git_blob_at_head"] if identity["verified"] else None


def source_inventory(paths: Iterable[str]) -> Dict[str, Dict[str, str | None]]:
    return {
        path: {
            "sha256": sha256_file(ROOT / path),
            "git_blob_at_head": committed_blob(path),
        }
        for path in sorted(set(paths))
    }
