"""Exact replay of captured simulator runs (the core deliverable)."""
from __future__ import annotations

from faultline_replay import (
    canonical_bytes,
    capture_run,
    diff_summary,
    replay_bundle,
)


def test_simulator_replay_is_byte_identical():
    bundle = capture_run("simulator", 6, "sum the archive")
    replayed = replay_bundle(bundle)
    d = diff_summary(bundle["trace"], replayed["trace"])
    assert d["equal"], d["diffs"]
    assert replayed["calls_consumed"] == 3


def test_simulator_reexecution_is_byte_identical():
    """The simulator is a pure function of captured state: re-running live from
    the same inputs reproduces the exact trace (true reproducibility, not just
    playback)."""
    a = capture_run("simulator", 6, "sum the archive")
    b = capture_run("simulator", 6, "sum the archive")
    assert canonical_bytes(a["trace"]) == canonical_bytes(b["trace"])
    assert canonical_bytes(a["recorded_calls"]) == canonical_bytes(b["recorded_calls"])


def test_capture_records_seeds_inputs_calls_state_versions():
    bundle = capture_run("simulator", 6, "sum the archive")
    assert bundle["inputs"]["seed"] == 6
    assert bundle["inputs"]["task"] == "sum the archive"
    assert len(bundle["recorded_calls"]) == 3
    assert all("input_digest" in c and "output" in c for c in bundle["recorded_calls"])
    assert bundle["state"]["final"]["results"]
    assert set(bundle["versions"]) >= {"bundle_format", "program", "simulator",
                                       "trace_schema_fingerprint"}


def test_failed_run_replays_exactly():
    bundle = capture_run("simulator", 6, "sum the archive", fail_at="sum")
    assert bundle["state"]["failed"] is True
    replayed = replay_bundle(bundle)
    d = diff_summary(bundle["trace"], replayed["trace"])
    assert d["equal"], d["diffs"]
    # the failure is reproduced, not re-invented
    assert any(s["status"] == "error" for s in replayed["trace"]["spans"])
