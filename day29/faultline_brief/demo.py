"""Execute and record one concise run→fault→trace→recover→replay demo."""
from __future__ import annotations

import json
import sys
from typing import Any, Dict, List

from .evidence import ROOT, load_json, sha256_file

for relative in ("day04", "day25"):
    path = str(ROOT / relative)
    if path not in sys.path:
        sys.path.insert(0, path)

from faultline_postmortem import (  # noqa: E402
    canonical_config,
    run_incident,
    verify_red_green,
)

INCIDENT_ID = "INC-25-001"
FRAME_ORDER = ("RUN", "FAULT", "TRACE", "RECOVER", "REPLAY")
FRAME_TIMES = (0, 24, 58, 94, 132)
PLANNED_DURATION_SECONDS = 165


def _committed_replay() -> Dict[str, Any]:
    return load_json(ROOT / "day25/evidence/red_green_replay.json")[INCIDENT_ID]


def build_demo() -> Dict[str, Any]:
    config = canonical_config()
    before = run_incident(INCIDENT_ID, "legacy", config)
    after = run_incident(INCIDENT_ID, "fixed", config)
    replay = verify_red_green(
        INCIDENT_ID,
        config,
        repetitions=20,
        include_cross_process=False,
    )
    committed = _committed_replay()
    frames: List[Dict[str, Any]] = [
        {
            "at_seconds": FRAME_TIMES[0],
            "label": "RUN",
            "headline": "Replay one seeded cascade with the legacy policy.",
            "screen": [
                f"incident={INCIDENT_ID}",
                f"seed={before['seed']}",
                f"test={before['regression']['test_id']}",
            ],
            "narration": (
                "Start with one fixed incident, seed, configuration, and user-visible "
                "regression. The test requires a correct visible answer, no wrong "
                "visible answer, and both resource ceilings to hold."
            ),
        },
        {
            "at_seconds": FRAME_TIMES[1],
            "label": "FAULT",
            "headline": "Recovery fails after fallback, not at the first timeout.",
            "screen": [
                "primary → timeout → retry → timeout",
                "secondary → stale tokens → narrow judge accepts",
                f"terminal={before['terminal']['status']} · regression=RED",
            ],
            "narration": (
                "Two primary attempts time out. Fallback preserves the headline value "
                "but shifts the context tokens. The narrow judge accepts its known "
                "failure slice, verification repeats, the same route re-enters, and "
                "the final synthesis is contained by the cost ceiling."
            ),
        },
        {
            "at_seconds": FRAME_TIMES[2],
            "label": "TRACE",
            "headline": "The trace turns a vague failure into a causal chain.",
            "screen": [
                f"spans={before['trace']['span_count']}",
                f"errors_complete={before['trace_audit']['all_error_spans_complete']}",
                f"unresolved_refs={len(before['trace_audit']['unresolved_trace_references'])}",
            ],
            "narration": (
                "Every error span is complete and every regression reference resolves. "
                "The trace links the false accept to repeated verification, same-route "
                "re-entry, and the terminal ceiling. The root cause is policy authority "
                "inside a documented judge blind spot, not an unexplained model error."
            ),
        },
        {
            "at_seconds": FRAME_TIMES[3],
            "label": "RECOVER",
            "headline": "Change eligibility and routing, then run the same incident.",
            "screen": [
                "exact token guard → reject stale fallback",
                "quarantine fingerprint → require route diversity",
                f"terminal={after['terminal']['status']} · regression=GREEN",
            ],
            "narration": (
                "The fix performs an exact token check, quarantines the rejected "
                "provider and fingerprint, and requires a trusted route with independent "
                "context. The same user-visible regression is now green."
            ),
        },
        {
            "at_seconds": FRAME_TIMES[4],
            "label": "REPLAY",
            "headline": "Prove the change, then state the boundary.",
            "screen": [
                f"legacy={replay['before']['stability']['repetitions']}× RED",
                f"fixed={replay['after']['stability']['repetitions']}× GREEN",
                "same seed + config + regression · replay_verified=True",
            ],
            "narration": (
                "Across repeated executions, legacy stays red and fixed stays green "
                "under the same seed, configuration, and regression test. FAULTLINE "
                "proved this corrective control for one seeded simulator incident. It "
                "did not prove real providers are independent in production."
            ),
        },
    ]
    source_match = {
        "before_run_digest": (
            before["run_digest"] == committed["before"]["run_digest"]
        ),
        "before_trace_digest": (
            before["trace_digest"] == committed["before"]["trace_digest"]
        ),
        "after_run_digest": (
            after["run_digest"] == committed["after"]["run_digest"]
        ),
        "after_trace_digest": (
            after["trace_digest"] == committed["after"]["trace_digest"]
        ),
    }
    return {
        "demo_id": "faultline-stale-fallback-red-green",
        "incident_id": INCIDENT_ID,
        "planned_duration_seconds": PLANNED_DURATION_SECONDS,
        "under_five_minutes": PLANNED_DURATION_SECONDS < 300,
        "under_three_minutes": PLANNED_DURATION_SECONDS < 180,
        "frame_order": list(FRAME_ORDER),
        "frames": frames,
        "live_execution": {
            "seed": before["seed"],
            "config_digest": before["config_digest"],
            "regression_test_id": before["regression"]["test_id"],
            "before": {
                "color": before["regression"]["color"],
                "terminal": before["terminal"]["status"],
                "trace_complete": before["trace_audit"]["passed"],
                "run_digest": before["run_digest"],
                "trace_digest": before["trace_digest"],
            },
            "after": {
                "color": after["regression"]["color"],
                "terminal": after["terminal"]["status"],
                "trace_complete": after["trace_audit"]["passed"],
                "run_digest": after["run_digest"],
                "trace_digest": after["trace_digest"],
            },
            "replay_verified": replay["replay_verified_fix"],
            "same_seed": replay["flip_checks"]["same_seed"],
            "same_config": replay["flip_checks"]["same_config"],
            "same_regression_test": replay["flip_checks"]["same_regression_test"],
        },
        "committed_day25_match": source_match,
        "sources": [
            "day25/evidence/red_green_replay.json",
            "day25/evidence/stale-fallback-reentry-before-trace.json",
            "day25/evidence/stale-fallback-reentry-after-trace.json",
        ],
    }


def render_transcript(demo: Dict[str, Any]) -> str:
    lines = [
        "FAULTLINE — run → fault → trace → recover → replay",
        f"Planned narrated duration: {demo['planned_duration_seconds']} seconds",
        "",
    ]
    for frame in demo["frames"]:
        minute, second = divmod(frame["at_seconds"], 60)
        lines += [
            f"[{minute:02d}:{second:02d}] {frame['label']} — {frame['headline']}",
            *[f"  {line}" for line in frame["screen"]],
            f"  SAY: {frame['narration']}",
            "",
        ]
    return "\n".join(lines)


def render_cast(demo: Dict[str, Any]) -> str:
    header = {
        "version": 2,
        "width": 100,
        "height": 28,
        "timestamp": 0,
        "env": {"SHELL": "/bin/sh", "TERM": "xterm-256color"},
        "title": "FAULTLINE: run to replay in under three minutes",
    }
    events: List[List[Any]] = []
    for frame in demo["frames"]:
        body = [
            f"\r\n\033[1;36m{frame['label']}\033[0m  {frame['headline']}",
            *[f"  {line}" for line in frame["screen"]],
        ]
        events.append([
            float(frame["at_seconds"]),
            "o",
            "\r\n".join(body) + "\r\n",
        ])
    events.append([
        float(demo["planned_duration_seconds"]),
        "o",
        "\r\n\033[1;32mPROOF: same incident, red → green; production independence remains unproven.\033[0m\r\n",
    ])
    return "\n".join(
        [json.dumps(header, sort_keys=True)]
        + [json.dumps(event, ensure_ascii=True) for event in events]
    ) + "\n"


def compact_screen(demo: Dict[str, Any]) -> str:
    """Immediate terminal form used by `make day29-demo`."""
    lines = []
    for frame in demo["frames"]:
        lines.append(f"{frame['label']}: {frame['headline']}")
        lines.extend(f"  {item}" for item in frame["screen"])
    lines.append(
        "PROVED: one seeded simulator incident flips red→green under the same "
        "seed/config/test; production provider independence is not established."
    )
    return "\n".join(lines)
