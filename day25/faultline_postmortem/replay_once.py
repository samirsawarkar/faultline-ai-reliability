"""Small CLI used by the cross-process/hash-seed replay proof."""
from __future__ import annotations

import argparse
import json

from .config import PostmortemConfig
from .runner import run_incident


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--incident", required=True)
    parser.add_argument("--version", choices=("legacy", "fixed"), required=True)
    parser.add_argument("--config-json", required=True)
    args = parser.parse_args()
    config = PostmortemConfig(**json.loads(args.config_json)).validate()
    result = run_incident(args.incident, args.version, config)
    print(
        json.dumps(
            {
                "run_digest": result["run_digest"],
                "trace_digest": result["trace_digest"],
                "regression_color": result["regression"]["color"],
            },
            sort_keys=True,
            separators=(",", ":"),
        )
    )


if __name__ == "__main__":
    main()
