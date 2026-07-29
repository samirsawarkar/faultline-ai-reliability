"""Load and parse the documented cold-start protocol."""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any, Dict, Optional

ROOT = Path(__file__).resolve().parents[2]
DAY = ROOT / "day27"
START = "<!-- COLD-START:BEGIN -->"
END = "<!-- COLD-START:END -->"


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_protocol() -> Dict[str, Any]:
    return load_json(DAY / "protocol.json")


def extract_cold_block(document: Optional[Path] = None) -> str:
    path = document or ROOT / "REPRODUCE.md"
    text = path.read_text(encoding="utf-8")
    if text.count(START) != 1 or text.count(END) != 1:
        raise ValueError("REPRODUCE.md must contain exactly one cold-start block")
    marked = text.split(START, 1)[1].split(END, 1)[0]
    matches = re.findall(r"```sh\n(.*?)```", marked, flags=re.DOTALL)
    if len(matches) != 1:
        raise ValueError("cold-start markers must wrap exactly one sh block")
    block = matches[0].strip()
    if not block:
        raise ValueError("cold-start block is empty")
    return block


def extract_expected_output(document: Optional[Path] = None) -> str:
    path = document or ROOT / "REPRODUCE.md"
    text = path.read_text(encoding="utf-8")
    if "## Required terminal result" not in text:
        raise ValueError("required terminal result section is missing")
    section = text.split("## Required terminal result", 1)[1].split(
        "\n## ", 1
    )[0]
    matches = re.findall(r"```text\n(.*?)```", section, flags=re.DOTALL)
    if len(matches) != 1:
        raise ValueError("required result must contain exactly one text block")
    return matches[0].strip()


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()
