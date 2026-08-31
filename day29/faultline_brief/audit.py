"""Audit the timed demo, four-layer case study, and comprehension evidence."""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List

from .comprehension import run_comprehension_attack
from .demo import FRAME_ORDER
from .evidence import (
    DAY,
    EVIDENCE,
    ROOT,
    estimated_read_seconds,
    load_json,
    resolve_pointer,
    sha256_file,
    word_count,
)


def _audit_five_numbers(case_text: str) -> Dict[str, Any]:
    spec = load_json(DAY / "case_study.json")
    records: List[Dict[str, Any]] = []
    errors: List[str] = []
    for item in spec["verified_numbers"]:
        artifact = ROOT / item["artifact"]
        value = resolve_pointer(load_json(artifact), item["pointer"])
        rendered = format(value, item["format"]) if item.get("format") else str(value)
        matched = rendered == item["token"] and item["token"] in case_text
        records.append({**item, "resolved": rendered, "matched": matched})
        if not matched:
            errors.append(
                f"{item['id']}: token={item['token']} resolved={rendered}"
            )
    return {
        "declared_count": len(spec["verified_numbers"]),
        "exactly_five": len(spec["verified_numbers"]) == 5,
        "records": records,
        "errors": errors,
        "passed": len(spec["verified_numbers"]) == 5
        and all(record["matched"] for record in records),
    }


def _audit_publication_bundle() -> Dict[str, Any]:
    bundle = load_json(DAY / "publication_bundle.json")
    records = []
    for item in bundle["artifacts"]:
        path = ROOT / item["path"]
        records.append({
            **item,
            "exists": path.is_file(),
            "sha256": sha256_file(path) if path.is_file() else None,
        })
    root_readme = (ROOT / "README.md").read_text(encoding="utf-8")
    checks = {
        "repo_article_demo_case_study_present": all(
            item["exists"] for item in records
        ),
        "one_coordinated_bundle": len(records) == 4,
        "root_readme_has_three_minute_path": (
            "Three-minute staff-engineer path" in root_readme
        ),
    }
    return {
        "artifacts": records,
        "checks": checks,
        "passed": all(checks.values()),
    }


def audit_day29(demo: Dict[str, Any]) -> Dict[str, Any]:
    demo_text = (DAY / "DEMO.md").read_text(encoding="utf-8")
    case_text = (DAY / "CASE-STUDY.md").read_text(encoding="utf-8")
    cast_path = EVIDENCE / "faultline-demo.cast"
    cast_lines = cast_path.read_text(encoding="utf-8").splitlines()
    cast_events = [json.loads(line) for line in cast_lines[1:]]
    layer_headings = re.findall(r"^## Layer \d · .+$", case_text, re.MULTILINE)
    numbers = _audit_five_numbers(case_text)
    comprehension = run_comprehension_attack()
    bundle = _audit_publication_bundle()
    case_words = word_count(case_text)
    case_read_seconds = estimated_read_seconds(case_text)
    checks = {
        "demo_sequence_complete": demo["frame_order"] == list(FRAME_ORDER),
        "demo_under_five_minutes": demo["under_five_minutes"],
        "demo_under_three_minutes": demo["under_three_minutes"],
        "recording_duration_matches": (
            int(cast_events[-1][0]) == demo["planned_duration_seconds"]
        ),
        "live_before_red": (
            demo["live_execution"]["before"]["color"] == "red"
        ),
        "live_after_green": (
            demo["live_execution"]["after"]["color"] == "green"
        ),
        "live_traces_complete": (
            demo["live_execution"]["before"]["trace_complete"]
            and demo["live_execution"]["after"]["trace_complete"]
        ),
        "same_seed_config_test": all(
            demo["live_execution"][key]
            for key in ("same_seed", "same_config", "same_regression_test")
        ),
        "replay_verified": demo["live_execution"]["replay_verified"],
        "live_run_matches_committed_day25": all(
            demo["committed_day25_match"].values()
        ),
        "case_study_exactly_four_layers": len(layer_headings) == 4,
        "case_study_one_page_word_budget": case_words <= 500,
        "case_study_under_three_minute_read": case_read_seconds <= 180,
        "case_study_exactly_five_verified_numbers": numbers["passed"],
        "cold_viewer_can_state_proof": comprehension[
            "cold_viewer_can_state_what_faultline_proved"
        ],
        "dead_weight_attack_red_to_green": comprehension["passed"],
        "human_test_caveat_explicit": (
            comprehension["human_participant"] is False
            and "not an empirical human" in comprehension["method_caveat"]
        ),
        "publication_bundle_complete": bundle["passed"],
    }
    errors = numbers["errors"]
    return {
        "checks": checks,
        "demo": {
            "planned_duration_seconds": demo["planned_duration_seconds"],
            "frame_order": demo["frame_order"],
            "cast_sha256": sha256_file(cast_path),
            "transcript_sha256": sha256_file(
                EVIDENCE / "DEMO-TRANSCRIPT.txt"
            ),
        },
        "case_study": {
            "word_count": case_words,
            "estimated_read_seconds": case_read_seconds,
            "layer_headings": layer_headings,
            "five_numbers": numbers,
            "sha256": sha256_file(DAY / "CASE-STUDY.md"),
        },
        "comprehension": comprehension,
        "publication_bundle": bundle,
        "errors": errors,
        "passed": all(checks.values()) and not errors,
    }
