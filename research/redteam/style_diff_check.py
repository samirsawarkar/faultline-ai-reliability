#!/usr/bin/env python3
"""Style diff check comparing draft.md against pre-slop baseline.

Verifies that numbers, [@bib]/[C###] tags, table lines, and math lines
form identical multisets between the two files.
"""

import argparse
import collections
import re
import sys
from pathlib import Path


def check_multisets(baseline_path: Path, draft_path: Path) -> bool:
    if not baseline_path.exists():
        print(f"Error: Baseline file not found: {baseline_path}", file=sys.stderr)
        return False
    if not draft_path.exists():
        print(f"Error: Draft file not found: {draft_path}", file=sys.stderr)
        return False

    text_base = baseline_path.read_text(encoding="utf-8")
    text_draft = draft_path.read_text(encoding="utf-8")

    all_ok = True

    # 1. Numbers
    nums_base = collections.Counter(re.findall(r"\d+(?:\.\d+)?", text_base))
    nums_draft = collections.Counter(re.findall(r"\d+(?:\.\d+)?", text_draft))
    if nums_base != nums_draft:
        all_ok = False
        print("[FAIL] Numbers multiset mismatch:")
        print("  Missing in draft:", dict(nums_base - nums_draft))
        print("  Extra in draft:", dict(nums_draft - nums_base))
    else:
        print(f"[PASS] Numbers: {sum(nums_base.values())} numbers match perfectly.")

    # 2. [@bib]/[C###] tags
    tag_pattern = r"\[@[^\]]+\]|\[C\d+\]|@[a-zA-Z0-9_-]+"
    tags_base = collections.Counter(re.findall(tag_pattern, text_base))
    tags_draft = collections.Counter(re.findall(tag_pattern, text_draft))
    if tags_base != tags_draft:
        all_ok = False
        print("[FAIL] Tags multiset mismatch:")
        print("  Missing in draft:", dict(tags_base - tags_draft))
        print("  Extra in draft:", dict(tags_draft - tags_base))
    else:
        print(f"[PASS] Tags: {sum(tags_base.values())} tags match perfectly.")

    # 3. Table lines
    tbl_base = collections.Counter([l.strip() for l in text_base.splitlines() if l.strip().startswith("|")])
    tbl_draft = collections.Counter([l.strip() for l in text_draft.splitlines() if l.strip().startswith("|")])
    if tbl_base != tbl_draft:
        all_ok = False
        print("[FAIL] Table lines mismatch:")
        print("  Missing in draft:", dict(tbl_base - tbl_draft))
        print("  Extra in draft:", dict(tbl_draft - tbl_base))
    else:
        print(f"[PASS] Table lines: {sum(tbl_base.values())} table lines match perfectly.")

    # 4. Math lines
    math_base = collections.Counter([l.strip() for l in text_base.splitlines() if "$$" in l or l.strip().startswith("$")])
    math_draft = collections.Counter([l.strip() for l in text_draft.splitlines() if "$$" in l or l.strip().startswith("$")])
    if math_base != math_draft:
        all_ok = False
        print("[FAIL] Math lines mismatch:")
        print("  Missing in draft:", dict(math_base - math_draft))
        print("  Extra in draft:", dict(math_draft - math_base))
    else:
        print(f"[PASS] Math lines: {sum(math_base.values())} math lines match perfectly.")

    return all_ok


def main() -> None:
    parser = argparse.ArgumentParser(description="Style diff check")
    parser.add_argument(
        "baseline",
        help="Path to baseline draft_before_slop.md",
    )
    parser.add_argument(
        "--draft",
        default="research/paper/draft.md",
        help="Path to current draft.md",
    )
    args = parser.parse_args()

    success = check_multisets(Path(args.baseline), Path(args.draft))
    if success:
        print("\nSUCCESS: All multiset equality checks passed (exit 0).")
        sys.exit(0)
    else:
        print("\nFAILURE: Multiset checks failed (exit 1).", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
