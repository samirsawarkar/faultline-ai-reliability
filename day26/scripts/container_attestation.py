"""Print stable evidence produced inside the clean container image."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _load(name):
    return json.loads(
        (ROOT / "day26/evidence" / name).read_text(encoding="utf-8")
    )


def main() -> None:
    tests = _load("test_report.json")
    evaluation = _load("eval_verification.json")
    experiments = _load("fast_experiment_report.json")
    readme = _load("readme_traceability.json")
    attestation = {
        "test_count": tests["passed"],
        "tests_green": tests["passed_all"],
        "eval_result_id": evaluation["result_id"],
        "eval_green": evaluation["passed"],
        "fast_experiments_green": experiments["passed"],
        "readme_traceability_green": readme["passed"],
    }
    attestation["passed"] = all(
        (
            attestation["tests_green"],
            attestation["eval_green"],
            attestation["fast_experiments_green"],
            attestation["readme_traceability_green"],
        )
    )
    print(json.dumps(attestation, sort_keys=True, separators=(",", ":")))


if __name__ == "__main__":
    main()
