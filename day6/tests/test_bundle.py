"""Bundle integrity: version guard and replay divergence detection."""
from __future__ import annotations

import copy

import pytest

from faultline_replay import (
    VersionMismatch,
    capture_run,
    check_versions,
    replay_bundle,
)
from faultline_replay.providers import ReplayChannel, ReplayDivergence


def test_version_mismatch_refuses_replay():
    bundle = capture_run("simulator", 6, "sum the archive")
    tampered = copy.deepcopy(bundle)
    tampered["versions"]["simulator"] = "9.9.9"
    with pytest.raises(VersionMismatch):
        replay_bundle(tampered)


def test_schema_fingerprint_guards_replay():
    bundle = capture_run("simulator", 6, "sum the archive")
    bundle["versions"]["trace_schema_fingerprint"] = "deadbeef"
    with pytest.raises(VersionMismatch):
        check_versions(bundle)


def test_replay_diverges_on_off_path_call():
    bundle = capture_run("simulator", 6, "sum the archive")
    ch = ReplayChannel(bundle["recorded_calls"])
    # first recorded call is tool.retrieve; ask for something else
    with pytest.raises(ReplayDivergence):
        ch.call("tool.retrieve", {"step": "retrieve", "index": 99})


def test_replay_diverges_when_recording_exhausted():
    bundle = capture_run("simulator", 6, "sum the archive")
    ch = ReplayChannel(bundle["recorded_calls"])
    for step in ("retrieve", "sum", "verify"):
        ch.call(f"tool.{step}", {"step": step, "index": ("retrieve", "sum", "verify").index(step)})
    with pytest.raises(ReplayDivergence):
        ch.call("tool.extra", {"step": "extra", "index": 3})
