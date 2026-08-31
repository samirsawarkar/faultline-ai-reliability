from __future__ import annotations

import argparse
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "day30"))

from faultline_launch.report import build_checkpoint  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--allow-pending",
        action="store_true",
        help="write and audit local evidence without requiring external receipts",
    )
    args = parser.parse_args()
    checkpoint = build_checkpoint()
    audit = checkpoint["audit"]
    print(
        f"defense={audit['defense']['questions']} questions; "
        f"messages={audit['outreach']['targets']}; "
        f"oss_opened={audit['oss']['opened_or_merged']}"
    )
    if checkpoint["passed"]:
        print("Checkpoint 30: PASS")
        return 0
    print(
        "Checkpoint 30: PENDING — "
        + ", ".join(audit["external_actions_pending"])
    )
    return 0 if args.allow_pending else 2


if __name__ == "__main__":
    raise SystemExit(main())
