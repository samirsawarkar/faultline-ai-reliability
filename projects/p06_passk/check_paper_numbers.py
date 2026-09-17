#!/usr/bin/env python3
"""
Verify that every decimal number in publications/publication_01_passk_reliability/paper.md
appears in research/experiments/raw/*.json (rounded to 2..5 decimal places).
"""
import glob
import json
import re
import sys
from pathlib import Path

def main() -> int:
    repo_root = Path(__file__).resolve().parent.parent.parent
    raw_dir = repo_root / "research" / "experiments" / "raw"
    paper_path = repo_root / "publications" / "publication_01_passk_reliability" / "paper.md"

    if not paper_path.exists():
        print(f"Error: {paper_path} not found.", file=sys.stderr)
        return 1

    # 1. Collect all numeric values from raw JSON files
    raw_numbers = set()

    def collect(obj):
        if isinstance(obj, (int, float)):
            raw_numbers.add(float(obj))
        elif isinstance(obj, dict):
            for k, v in obj.items():
                try:
                    raw_numbers.add(float(k))
                except ValueError:
                    pass
                collect(v)
        elif isinstance(obj, list):
            for item in obj:
                collect(item)

    json_files = list(raw_dir.glob("*.json"))
    if not json_files:
        print(f"Error: No JSON files found in {raw_dir}", file=sys.stderr)
        return 1

    for jf in json_files:
        try:
            with open(jf, "r", encoding="utf-8") as f:
                collect(json.load(f))
        except Exception as e:
            print(f"Warning: Failed to load {jf}: {e}", file=sys.stderr)

    print(f"Collected {len(raw_numbers)} distinct numbers from {len(json_files)} raw JSON files.")

    # 2. Read paper.md and strip bibliographic references
    paper_text = paper_path.read_text(encoding="utf-8")
    ref_idx = paper_text.find("## References")
    if ref_idx != -1:
        body_text = paper_text[:ref_idx]
    else:
        body_text = paper_text

    # Strip section numbers (e.g. ## 2.1 or ### A.1)
    body_text = re.sub(r"#+\s+[A-Z0-9\.]+", "", body_text)

    # 3. Extract scientific notation expressions (e.g. 5.92 \times 10^{-14})
    sci_numbers = []
    def replace_sci(m: re.Match) -> str:
        base = m.group(1)
        exp = m.group(2)
        sci_numbers.append(float(f"{base}e{exp}"))
        return " "

    body_no_sci = re.sub(r"(\d+\.\d+)\s*\\times\s*10\^\{(-?\d+)\}", replace_sci, body_text)

    # 4. Extract decimal numbers
    decimals = [float(d) for d in re.findall(r"(?<![a-zA-Z0-9_\-\.])[-+]?\d+\.\d+(?![a-zA-Z0-9_\-\.])", body_no_sci)]
    all_numbers = decimals + sci_numbers

    # Benign metadata/constants whitelist (temperature, significance levels, versions, licenses)
    whitelist = {0.0, 1.0, 0.05, 0.01, 3.11, 4.0}

    def match_value(v: float) -> bool:
        if v in whitelist:
            return True
        for r in raw_numbers:
            # Check direct match at 2..5 decimal places
            for places in [2, 3, 4, 5]:
                if round(v, places) == round(r, places):
                    return True
            # Check percentage match (e.g. 34.83% -> 0.3483)
            for places in [2, 3, 4, 5]:
                if round(v / 100.0, places) == round(r, places):
                    return True
        return False

    unmatched = [v for v in all_numbers if not match_value(v)]

    print(f"Total decimal/scientific numbers checked: {len(all_numbers)}")
    if unmatched:
        print(f"ERROR: {len(unmatched)} numbers in paper.md did not match any value in raw JSONs:", file=sys.stderr)
        for u in sorted(set(unmatched)):
            print(f"  Unmatched: {u}", file=sys.stderr)
        return 1

    print("SUCCESS: All paper.md decimal numbers verified against raw JSON artifacts.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
