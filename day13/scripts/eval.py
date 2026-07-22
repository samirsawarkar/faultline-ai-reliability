"""The reproducible eval command.

    python day13/scripts/eval.py [--split test|train]

Builds the versioned dataset, evaluates the chosen split against oracle-grounded
truth, and prints the immutable result. Deterministic: same command -> same
result_id and numbers, on any machine.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for rel in ("", "../day8", "../day9", "../day10", "../day11"):
    sys.path.insert(0, str((ROOT / rel).resolve()))

from faultline_eval import build_dataset, evaluate, validate_result  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", default="test", choices=["test", "train"])
    args = ap.parse_args()

    ds = build_dataset()
    result = evaluate(ds, args.split)
    print(json.dumps({
        "dataset_version": ds.version,
        "freshness": validate_result(result, ds),
        "result": result.to_dict(),
    }, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
