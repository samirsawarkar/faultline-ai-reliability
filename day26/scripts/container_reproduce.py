"""Build the pinned image, read its attestation, and record a stable proof."""
from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PINS = json.loads((ROOT / "day26/pins.json").read_text(encoding="utf-8"))
IMAGE = "faultline:0.26.0-rc1"


def main() -> None:
    if shutil.which("docker") is None:
        raise SystemExit("docker executable not found")
    subprocess.run(
        ["docker", "build", "--pull", "--tag", IMAGE, "."],
        cwd=str(ROOT),
        check=True,
    )
    completed = subprocess.run(
        [
            "docker",
            "run",
            "--rm",
            "--entrypoint",
            "python",
            IMAGE,
            "day26/scripts/container_attestation.py",
        ],
        cwd=str(ROOT),
        check=True,
        capture_output=True,
        text=True,
    )
    attestation = json.loads(completed.stdout.strip())
    report = {
        "command": "make container-reproduce",
        "image": IMAGE,
        "base": (
            PINS["container"]["base_tag"]
            + "@"
            + PINS["container"]["base_digest"]
        ),
        "attestation": attestation,
        "passed": attestation["passed"],
    }
    output = ROOT / "day26/evidence/container_verification.json"
    output.parent.mkdir(exist_ok=True)
    output.write_text(
        json.dumps(report, sort_keys=True, ensure_ascii=True, indent=2) + "\n",
        encoding="utf-8",
    )
    if not report["passed"]:
        raise SystemExit("clean-container reproduction failed")
    print(
        f"container green: {attestation['test_count']} tests; "
        f"eval={attestation['eval_result_id']}"
    )


if __name__ == "__main__":
    main()
