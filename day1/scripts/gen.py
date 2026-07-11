#!/usr/bin/env python3
"""CLI: emit the canonical environment for a seed (or a digest manifest).

Usage:
    python scripts/gen.py --seed 7                 # print env JSON to stdout
    python scripts/gen.py --seed 7 --out env.json  # write env JSON to a file
    python scripts/gen.py --digests 0 19           # sha256 per seed in [0,19]

stdout is exactly canonical_bytes(env): safe to diff, hash, or commit.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from faultline import build_env, canonical_bytes, env_digest  # noqa: E402


def main() -> int:
    p = argparse.ArgumentParser(description="Deterministic FAULTLINE env generator")
    p.add_argument("--seed", type=int, help="seed to generate")
    p.add_argument("--out", type=Path, help="write env JSON here instead of stdout")
    p.add_argument("--digests", nargs=2, type=int, metavar=("LO", "HI"),
                   help="print 'seed sha256' for each seed in [LO, HI]")
    args = p.parse_args()

    if args.digests is not None:
        lo, hi = args.digests
        for seed in range(lo, hi + 1):
            print(f"{seed}\t{env_digest(seed)}")
        return 0

    if args.seed is None:
        p.error("provide --seed or --digests")

    data = canonical_bytes(build_env(args.seed))
    if args.out:
        args.out.write_bytes(data)
        print(f"wrote {len(data)} bytes -> {args.out}", file=sys.stderr)
    else:
        sys.stdout.buffer.write(data)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
