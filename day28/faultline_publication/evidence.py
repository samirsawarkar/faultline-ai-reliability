"""Small, dependency-free helpers for resolving committed evidence."""
from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any, Dict, Iterable

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


def committed_blob(artifact: str) -> str | None:
    completed = subprocess.run(
        ["git", "rev-parse", f"HEAD:{artifact}"],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip() if completed.returncode == 0 else None


def source_inventory(paths: Iterable[str]) -> Dict[str, Dict[str, str | None]]:
    return {
        path: {
            "sha256": sha256_file(ROOT / path),
            "git_blob_at_head": committed_blob(path),
        }
        for path in sorted(set(paths))
    }
