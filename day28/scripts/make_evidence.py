"""Regenerate all Day 28 publication evidence and fail on unsupported prose."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "day28"))

from faultline_publication import (  # noqa: E402
    audit_publication,
    build_checkpoint,
    build_figures,
    render_checkpoint,
)
from faultline_publication.evidence import DAY, EVIDENCE, dump_json  # noqa: E402


def main() -> None:
    figures = build_figures()
    audit = audit_publication()
    checkpoint = build_checkpoint(audit, figures)
    dump_json(EVIDENCE / "figure_manifest.json", figures)
    dump_json(EVIDENCE / "claim_audit.json", audit)
    dump_json(EVIDENCE / "checkpoint_28.json", checkpoint)
    rendered = render_checkpoint(checkpoint)
    (EVIDENCE / "CHECKPOINT-28.md").write_text(rendered, encoding="utf-8")
    (DAY / "CHECKPOINT-28.md").write_text(rendered, encoding="utf-8")
    print(
        f"Day 28: {audit['claim_count']} claims, {audit['figure_count']} figures, "
        f"{audit['limitation_count']} limitations"
    )
    print(f"claim audit: {'green' if audit['passed'] else 'red'}")
    print(f"Checkpoint 28: {'PASS' if checkpoint['passed'] else 'FAIL'}")
    if not checkpoint["passed"]:
        for error in audit["errors"]:
            print(f"  - {error}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
