"""Dependency-free evidence helpers for the Day 29 briefing."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Dict

ROOT = Path(__file__).resolve().parents[2]
DAY = ROOT / "day29"
EVIDENCE = DAY / "evidence"


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def dump_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, sort_keys=True, ensure_ascii=True, indent=2) + "\n",
        encoding="utf-8",
    )


def resolve_pointer(document: Any, pointer: str) -> Any:
    if pointer == "":
        return document
    if not pointer.startswith("/"):
        raise ValueError(f"invalid JSON pointer: {pointer}")
    value = document
    for raw in pointer[1:].split("/"):
        key = raw.replace("~1", "/").replace("~0", "~")
        value = value[int(key)] if isinstance(value, list) else value[key]
    return value


def source_value(artifact: str, pointer: str) -> Any:
    return resolve_pointer(load_json(ROOT / artifact), pointer)


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def word_count(text: str) -> int:
    return len(text.split())


def estimated_read_seconds(text: str, words_per_minute: int = 180) -> int:
    words = word_count(text)
    return (words * 60 + words_per_minute - 1) // words_per_minute
