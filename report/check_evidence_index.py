#!/usr/bin/env python3
"""Check that all rows in the Evidence Index resolve to real files, pointers, and commands."""
import json
import os
import re
import sys


def resolve_pointer(data, pointer):
    """Resolve an RFC 6901 JSON pointer inside parsed JSON data."""
    parts = [p.replace("~1", "/").replace("~0", "~") for p in pointer.strip("/").split("/")]
    curr = data
    for p in parts:
        if isinstance(curr, list):
            curr = curr[int(p)]
        elif isinstance(curr, dict):
            curr = curr[p]
        else:
            raise KeyError(f"Cannot traverse key '{p}' on non-container: {type(curr)}")
    return curr


def clean_cell(cell):
    """Strip LaTeX markup like \\code{...}, \\textbf{...}, \\_, etc."""
    s = cell.strip()
    s = s.replace(r"\_", "_")
    while True:
        m = re.search(r"\\[a-zA-Z]+\{([^{}]*)\}", s)
        if not m:
            break
        s = s[:m.start()] + m.group(1) + s[m.end():]
    s = s.replace("{", "").replace("}", "").strip()
    return s


def load_makefile_targets(repo_root):
    """Extract valid targets from Makefile."""
    makefile_path = os.path.join(repo_root, "Makefile")
    targets = set()
    if not os.path.exists(makefile_path):
        return targets
    with open(makefile_path, "r", encoding="utf-8") as f:
        for line in f:
            m = re.match(r"^([a-zA-Z0-9_-]+)\s*:", line)
            if m:
                targets.add(m.group(1))
    return targets


def main():
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    tex_path = os.path.join(repo_root, "report", "sec29_repo_reproduce_index.tex")

    if not os.path.exists(tex_path):
        print(f"Error: {tex_path} does not exist", file=sys.stderr)
        sys.exit(1)

    with open(tex_path, "r", encoding="utf-8") as f:
        content = f.read()

    m = re.search(r"\\section\*?\{(?:\d+\s*---\s*)?Evidence Index\}(.*?)\\begin\{longtable\}(.*?)\\end\{longtable\}", content, re.DOTALL)
    if not m:
        print("Error: Could not locate Evidence Index longtable", file=sys.stderr)
        sys.exit(1)

    table_body = m.group(2)
    makefile_targets = load_makefile_targets(repo_root)

    rows = []
    raw_rows = table_body.split(r"\\")
    for r in raw_rows:
        line = r.strip()
        if not line or line.startswith("%"):
            continue
        # Filter out rules and table headers
        cleaned_lines = []
        for l in line.split("\n"):
            ls = l.strip()
            if ls and not any(ls.startswith(c) for c in [r"\toprule", r"\midrule", r"\bottomrule", r"\endhead", r"\endfirsthead", r"\endfoot", r"\endlastfoot", r"\multicolumn"]):
                cleaned_lines.append(ls)
        if not cleaned_lines:
            continue
        line = " ".join(cleaned_lines)

        cells = line.split("&")
        if len(cells) >= 5:
            cleaned = [clean_cell(c) for c in cells]
            # Must start with a known Claim ID like C01, P00, etc.
            if re.match(r"^[CP]\d{2}", cleaned[0]):
                rows.append(cleaned)

    if len(rows) == 0:
        print("Error: No evidence rows found in Section 31 table!", file=sys.stderr)
        sys.exit(1)

    print(f"Checking {len(rows)} evidence index rows...")
    failures = 0

    for cells in rows:
        claim_id = cells[0]
        json_file = cells[2]
        pointer = cells[3]
        script_or_make = cells[4]

        # 1. Assert source JSON file exists
        full_json_path = os.path.join(repo_root, json_file)
        if not os.path.exists(full_json_path):
            print(f"[FAIL] {claim_id}: JSON file missing: {json_file}")
            failures += 1
            continue

        # 2. Assert JSON pointer resolves inside it
        try:
            with open(full_json_path, "r", encoding="utf-8") as f:
                json_data = json.load(f)
            val = resolve_pointer(json_data, pointer)
            val_str = str(val).replace("\n", " ")
            if len(val_str) > 40:
                val_str = val_str[:37] + "..."
        except Exception as e:
            print(f"[FAIL] {claim_id}: Pointer '{pointer}' failed in {json_file}: {e}")
            failures += 1
            continue

        # 3. Assert generating script or make target exists
        if script_or_make.startswith("make "):
            target = script_or_make.split(" ", 1)[1].strip()
            if target not in makefile_targets:
                print(f"[FAIL] {claim_id}: Makefile target '{target}' not found in Makefile")
                failures += 1
                continue
            script_disp = f"make {target}"
        else:
            full_script_path = os.path.join(repo_root, script_or_make)
            if not os.path.exists(full_script_path):
                print(f"[FAIL] {claim_id}: Script '{script_or_make}' not found")
                failures += 1
                continue
            script_disp = script_or_make

        print(f"[PASS] {claim_id:4s} | {json_file} -> {pointer} = {val_str} ({script_disp})")

    if failures > 0:
        print(f"\nCompleted with {failures} FAILURES.")
        sys.exit(1)
    else:
        print(f"\nAll {len(rows)} evidence rows VERIFIED successfully.")
        sys.exit(0)


if __name__ == "__main__":
    main()
