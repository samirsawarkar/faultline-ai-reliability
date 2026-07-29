"""Module entry point used by humans and the cross-process replay proof."""
from __future__ import annotations

import argparse
import json

from .cascade import run_cascade
from .config import CascadeConfig


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--config-json", required=True)
    args = parser.parse_args()
    config = CascadeConfig(**json.loads(args.config_json)).validate()
    print(run_cascade(args.seed, config)["incident_digest"])


if __name__ == "__main__":
    main()
