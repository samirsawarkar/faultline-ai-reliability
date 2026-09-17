"""Subprocess worker for Arm A evaluation using isolated .venv-inspect."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

import inspect_ai
from inspect_evals_mcptox import mcptox as mcptox_task


def main() -> None:
    parser = argparse.ArgumentParser(description="Arm A worker for MCPTox evaluation")
    parser.add_argument("--model", required=True, help="Model string (e.g. z-ai/glm-5.3-flash)")
    parser.add_argument("--judge", required=True, help="Judge model string")
    parser.add_argument("--sample-ids-file", required=True, help="Path to file containing sample IDs (JSON or newline-separated)")
    parser.add_argument("--log-dir", required=True, help="Directory to save eval logs")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")

    args = parser.parse_args()

    with open(args.sample_ids_file, "r", encoding="utf-8") as f:
        content = f.read().strip()
        try:
            sample_ids = json.loads(content)
        except Exception:
            sample_ids = [line.strip() for line in content.splitlines() if line.strip()]

    log_dir = Path(args.log_dir)
    log_dir.mkdir(parents=True, exist_ok=True)

    logs = inspect_ai.eval(
        tasks=mcptox_task,
        model=f"openai/{args.model}",
        task_args={"judge_model": f"openai/{args.judge}", "shuffle": True, "seed": args.seed},
        sample_id=sample_ids,
        log_dir=str(log_dir),
        temperature=0,
        max_connections=4,
    )

    if not logs:
        sys.stderr.write(f"Arm A eval produced no log files in {log_dir}\n")
        sys.exit(1)

    print(logs[0].location)


if __name__ == "__main__":
    main()
