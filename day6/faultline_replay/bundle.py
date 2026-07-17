"""Replay bundle — the self-contained capture of one run.

A bundle holds EVERYTHING needed to replay a captured run, and nothing that
would make the committed artifact machine-specific:

  seeds/inputs   the pure inputs to the program
  recorded_calls every provider call's input-digest + recorded output (VCR-style)
  state          initial + final program state
  versions       logical component versions + a schema fingerprint (guards replay)
  trace          the Day-4 trace produced during capture (the golden observable)

Deliberately NOT in the bundle: wall-clock time, hostname, python/platform, or
any real-provider entropy. Those are captured separately (environment.json) and
documented in LIMITATIONS.md as the reproducibility boundary — putting them here
would both break byte-reproducibility and overstate what replay can promise.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any, Dict, List

BUNDLE_FORMAT = "1.0.0"
PROGRAM_VERSION = "1.0.0"
SIMULATOR_VERSION = "1.0.0"

_DAY4 = Path(__file__).resolve().parents[2] / "day4"

# The span fields we depend on; captured as a fingerprint so a Day-4 schema
# change is detected at replay time instead of silently corrupting a replay.
TRACE_SCHEMA_FIELDS = (
    "attributes", "end_seq", "error", "input_ref", "kind", "name",
    "output_ref", "parent_span_id", "span_id", "start_seq", "status", "trace_id",
)


def canonical_bytes(obj: Any) -> bytes:
    text = json.dumps(obj, sort_keys=True, ensure_ascii=True, indent=2,
                      separators=(",", ": "))
    return (text + "\n").encode("utf-8")


def digest(obj: Any) -> str:
    compact = json.dumps(obj, sort_keys=True, ensure_ascii=True,
                         separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(compact).hexdigest()


def versions_block() -> Dict[str, Any]:
    """Logical, deterministic versions. No python/platform here by design."""
    return {
        "bundle_format": BUNDLE_FORMAT,
        "program": PROGRAM_VERSION,
        "simulator": SIMULATOR_VERSION,
        "trace_schema_fingerprint": digest(list(TRACE_SCHEMA_FIELDS)),
    }


def build_bundle(*, provider: str, inputs: Dict[str, Any],
                 recorded_calls: List[Dict[str, Any]],
                 state: Dict[str, Any], trace: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "bundle_format": BUNDLE_FORMAT,
        "provider": provider,
        "versions": versions_block(),
        "inputs": inputs,
        "recorded_calls": recorded_calls,
        "state": state,
        "trace": trace,
    }


def bundle_digest(bundle: Dict[str, Any]) -> str:
    return digest(bundle)


def save(bundle: Dict[str, Any], path: str) -> None:
    Path(path).write_bytes(canonical_bytes(bundle))


def load(path: str) -> Dict[str, Any]:
    return json.loads(Path(path).read_text())


class VersionMismatch(RuntimeError):
    """Bundle was captured under component versions this code can't replay."""


def check_versions(bundle: Dict[str, Any]) -> None:
    """Guard: refuse to over-claim. If the bundle's logical versions or trace
    schema fingerprint don't match this code, replay fidelity is NOT guaranteed,
    so we stop rather than produce a misleading 'exact' replay."""
    cur = versions_block()
    got = bundle.get("versions", {})
    for key in ("bundle_format", "program", "simulator", "trace_schema_fingerprint"):
        if got.get(key) != cur.get(key):
            raise VersionMismatch(
                f"version drift on {key!r}: bundle={got.get(key)!r} current={cur.get(key)!r}"
            )


def runtime_environment() -> Dict[str, Any]:
    """The uncaptured runtime (informational, NEVER part of the golden bundle)."""
    import platform
    return {
        "python_version": platform.python_version(),
        "platform": platform.platform(),
        "implementation": platform.python_implementation(),
        "note": "recorded for the record; the deterministic simulator does not "
                "depend on these, but a real provider / floating-point path would",
    }
