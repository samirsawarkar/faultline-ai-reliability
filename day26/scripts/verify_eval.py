"""Re-run the frozen Day-13 test evaluation and compare exact results."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
for rel in ("day13", "day08", "day09", "day10", "day11"):
    path = str(ROOT / rel)
    if path not in sys.path:
        sys.path.insert(0, path)

from faultline_eval import build_dataset, evaluate, validate_result  # noqa: E402


def main() -> None:
    expected_path = ROOT / "day13/evidence/eval_result.json"
    expected = json.loads(expected_path.read_text(encoding="utf-8"))
    dataset = build_dataset()
    result = evaluate(dataset, "test")
    actual = result.to_dict()
    checks = {
        "dataset_version_matches": dataset.version == expected["dataset_version"],
        "result_id_matches": actual["result_id"] == expected["result_id"],
        "full_result_matches": actual == {
            key: value
            for key, value in expected.items()
            if key != "freshness_against_own_dataset"
        },
        "fresh": validate_result(result, dataset) == "fresh",
    }
    report = {
        "command": "python day26/scripts/verify_eval.py",
        "source_artifact": "day13/evidence/eval_result.json",
        "dataset_version": dataset.version,
        "result_id": actual["result_id"],
        "split": actual["split"],
        "sample_count": actual["sample_count"],
        "overall_f1": actual["overall"]["f1"],
        "checks": checks,
        "passed": all(checks.values()),
    }
    output = ROOT / "day26/evidence/eval_verification.json"
    output.parent.mkdir(exist_ok=True)
    output.write_text(
        json.dumps(report, sort_keys=True, ensure_ascii=True, indent=2) + "\n",
        encoding="utf-8",
    )
    if not report["passed"]:
        raise SystemExit("frozen evaluation does not reproduce")
    print(
        f"eval green: result_id={report['result_id']}; "
        f"F1={report['overall_f1']}"
    )


if __name__ == "__main__":
    main()
