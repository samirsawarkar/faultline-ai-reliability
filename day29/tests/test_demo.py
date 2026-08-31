"""The demo is a real, deterministic run→fault→trace→recover→replay."""
import json
import time

import pytest

from faultline_brief.demo import (
    FRAME_ORDER,
    build_demo,
    compact_screen,
    render_cast,
    render_transcript,
)


@pytest.fixture(scope="module")
def demo():
    return build_demo()


def test_demo_is_under_three_minutes(demo):
    assert demo["planned_duration_seconds"] == 165
    assert demo["under_three_minutes"] is True
    assert demo["under_five_minutes"] is True


def test_demo_has_required_sequence_once(demo):
    assert demo["frame_order"] == list(FRAME_ORDER)
    assert [frame["label"] for frame in demo["frames"]] == list(FRAME_ORDER)


def test_live_legacy_is_red_and_trace_complete(demo):
    before = demo["live_execution"]["before"]
    assert before["color"] == "red"
    assert before["terminal"] == "contained_cost_ceiling"
    assert before["trace_complete"] is True


def test_live_fixed_is_green_and_trace_complete(demo):
    after = demo["live_execution"]["after"]
    assert after["color"] == "green"
    assert after["terminal"] == "recovered_correct"
    assert after["trace_complete"] is True


def test_demo_controls_seed_config_and_regression(demo):
    assert demo["live_execution"]["same_seed"] is True
    assert demo["live_execution"]["same_config"] is True
    assert demo["live_execution"]["same_regression_test"] is True
    assert demo["live_execution"]["replay_verified"] is True


def test_live_run_matches_committed_day25_evidence(demo):
    assert all(demo["committed_day25_match"].values())


def test_each_frame_has_screen_and_narration(demo):
    for frame in demo["frames"]:
        assert frame["headline"]
        assert frame["screen"]
        assert frame["narration"]


def test_cast_is_valid_ordered_asciinema_v2(demo):
    lines = render_cast(demo).splitlines()
    header = json.loads(lines[0])
    events = [json.loads(line) for line in lines[1:]]
    assert header["version"] == 2
    assert [event[0] for event in events] == sorted(
        event[0] for event in events
    )
    assert int(events[-1][0]) == demo["planned_duration_seconds"]


def test_transcript_and_compact_output_expose_proof(demo):
    transcript = render_transcript(demo)
    compact = compact_screen(demo)
    for label in FRAME_ORDER:
        assert label in transcript
        assert label in compact
    assert "PROVED:" in compact
    assert "production provider independence is not established" in compact


def test_demo_build_is_deterministic(demo):
    assert build_demo() == demo


def test_live_demo_executes_far_below_five_minutes():
    started = time.monotonic()
    result = build_demo()
    elapsed = time.monotonic() - started
    assert result["live_execution"]["replay_verified"] is True
    assert elapsed < 300
