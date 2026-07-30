"""Regenerate the Day 29 recording, audits, and checkpoint."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "day29"))

from faultline_brief import (  # noqa: E402
    audit_day29,
    build_checkpoint,
    build_demo,
    render_cast,
    render_checkpoint,
    render_transcript,
)
from faultline_brief.evidence import DAY, EVIDENCE, dump_json  # noqa: E402


def main() -> None:
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    demo = build_demo()
    (EVIDENCE / "faultline-demo.cast").write_text(
        render_cast(demo), encoding="utf-8"
    )
    (EVIDENCE / "DEMO-TRANSCRIPT.txt").write_text(
        render_transcript(demo), encoding="utf-8"
    )
    dump_json(EVIDENCE / "demo_run.json", demo)
    audit = audit_day29(demo)
    checkpoint = build_checkpoint(audit)
    dump_json(EVIDENCE / "day29_audit.json", audit)
    dump_json(EVIDENCE / "comprehension_report.json", audit["comprehension"])
    dump_json(EVIDENCE / "publication_bundle.json", audit["publication_bundle"])
    dump_json(EVIDENCE / "checkpoint_29.json", checkpoint)
    rendered = render_checkpoint(checkpoint)
    (EVIDENCE / "CHECKPOINT-29.md").write_text(rendered, encoding="utf-8")
    (DAY / "CHECKPOINT-29.md").write_text(rendered, encoding="utf-8")
    print(
        f"demo={checkpoint['demo_duration_seconds']}s; "
        f"case={checkpoint['case_study_words']} words; "
        f"numbers={checkpoint['verified_number_count']}"
    )
    print(
        "cold viewer: "
        + ("can state the proof" if not checkpoint["fail_condition_triggered"] else "FAILED")
    )
    print(f"Checkpoint 29: {'PASS' if checkpoint['passed'] else 'FAIL'}")
    if not checkpoint["passed"]:
        for key, passed in audit["checks"].items():
            if not passed:
                print(f"  - {key}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
