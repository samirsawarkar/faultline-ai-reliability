"""Regenerate the Day-25 postmortems, traces, replay proof, and checkpoint."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for rel in ("", "../day04"):
    path = str((ROOT / rel).resolve())
    if path not in sys.path:
        sys.path.insert(0, path)

from faultline_postmortem import (  # noqa: E402
    build_report,
    render_case_study,
    render_checkpoint,
    render_incident,
)

EVIDENCE = ROOT / "evidence"


def _dump(path: Path, value) -> None:
    path.write_text(
        json.dumps(value, sort_keys=True, ensure_ascii=True, indent=2) + "\n",
        encoding="utf-8",
    )


def main() -> None:
    EVIDENCE.mkdir(exist_ok=True)
    report = build_report(repetitions=20, include_cross_process=True)
    public = {
        key: value for key, value in report.items() if key != "_runs"
    }
    _dump(EVIDENCE / "incident_reports.json", public["incident_reports"])
    _dump(EVIDENCE / "red_green_replay.json", public["red_green_replay"])
    _dump(EVIDENCE / "checkpoint_25.json", public["checkpoint_25"])

    for incident_id, incident in public["incident_reports"].items():
        slug = incident["slug"]
        runs = report["_runs"][incident_id]
        _dump(EVIDENCE / f"{slug}-before-trace.json", runs["before"]["trace"])
        _dump(EVIDENCE / f"{slug}-after-trace.json", runs["after"]["trace"])
        (EVIDENCE / f"{incident_id}.md").write_text(
            render_incident(incident), encoding="utf-8"
        )

    (EVIDENCE / "CASE_STUDY.md").write_text(
        render_case_study(public), encoding="utf-8"
    )
    (EVIDENCE / "CHECKPOINT-25.md").write_text(
        render_checkpoint(public), encoding="utf-8"
    )

    print("Day 25 evidence written:")
    for incident_id, replay in public["red_green_replay"].items():
        print(
            f"  {incident_id}: "
            f"{replay['before']['regression']['color']}->"
            f"{replay['after']['regression']['color']}; "
            f"verified={replay['replay_verified_fix']}"
        )
    print(f"  gate={public['checkpoint_25']['gate']['passed']}")


if __name__ == "__main__":
    main()
