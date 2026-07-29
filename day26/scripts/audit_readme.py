"""Verify every results-table number against its generator and JSON result."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "day26"))

from faultline_repro import audit_readme_claims  # noqa: E402


def main() -> None:
    report = audit_readme_claims()
    output = ROOT / "day26/evidence/readme_traceability.json"
    output.parent.mkdir(exist_ok=True)
    output.write_text(
        json.dumps(report, sort_keys=True, ensure_ascii=True, indent=2) + "\n",
        encoding="utf-8",
    )
    if not report["passed"]:
        raise SystemExit("README result traceability failed")
    print(f"README traceability green: {len(report['claims'])} result rows")


if __name__ == "__main__":
    main()
