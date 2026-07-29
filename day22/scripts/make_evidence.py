"""Regenerate the deterministic Day-22 matrix, attacks, and findings."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for rel in ("", "../day14", "../day18", "../day20"):
    sys.path.insert(0, str((ROOT / rel).resolve()))

from faultline_recovery_matrix import build_report, render_matrix  # noqa: E402

EVIDENCE = ROOT / "evidence"


def _dump(path: Path, obj) -> None:
    path.write_text(
        json.dumps(obj, sort_keys=True, ensure_ascii=True, indent=2) + "\n",
        encoding="utf-8",
    )


def main() -> None:
    EVIDENCE.mkdir(exist_ok=True)
    report = build_report()
    _dump(EVIDENCE / "six_mechanism_matrix.json", report["matrix"])
    _dump(EVIDENCE / "recovery_attacks.json", report["attacks"])
    _dump(
        EVIDENCE / "checkpoint_22.json",
        {
            "checkpoint_22": report["checkpoint_22"],
            "best_by_fault": report["best_by_fault"],
            "composition_policy": report["composition_policy"],
            "fail_condition_guard": report["matrix"]["fail_condition_guard"],
        },
    )
    (EVIDENCE / "SIX_MECHANISM_MATRIX.md").write_text(
        render_matrix(report), encoding="utf-8"
    )

    print("Day 22 evidence written:")
    print(
        f"  matrix: {report['matrix']['design']['cells']} paired cells; "
        f"{report['matrix']['design']['paired_seeds_per_cell']} seeds/cell"
    )
    print(
        "  recovery-induced harms measured: "
        f"{report['matrix']['recovery_induced_harm_audit']['total']}"
    )
    print(f"  Checkpoint 22 passed: {report['checkpoint_22']['passed']}")


if __name__ == "__main__":
    main()
