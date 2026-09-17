#!/usr/bin/env python3
"""
Build paper.pdf from paper.tex using xelatex.
Compiles twice for cross-references, outlines, and bookmarks.
"""
import subprocess
import sys
from pathlib import Path

pub_dir = Path(__file__).resolve().parent
tex_file = pub_dir / "paper.tex"
pdf_file = pub_dir / "paper.pdf"

if not tex_file.exists():
    print(f"Error: {tex_file} not found.", file=sys.stderr)
    sys.exit(1)

xelatex_bin = "/Users/samir/Library/TinyTeX/bin/universal-darwin/xelatex"
if not Path(xelatex_bin).exists():
    # Fallback to PATH
    xelatex_bin = "xelatex"

cmd = [xelatex_bin, "-interaction=nonstopmode", "paper.tex"]

print("=== Pass 1: xelatex ===")
res1 = subprocess.run(cmd, cwd=pub_dir, capture_output=True, text=True)
if res1.returncode != 0:
    print("Pass 1 failed. Error log:")
    print(res1.stdout[-1000:] if res1.stdout else "")
    sys.exit(res1.returncode)

print("=== Pass 2: xelatex ===")
res2 = subprocess.run(cmd, cwd=pub_dir, capture_output=True, text=True)
if res2.returncode != 0:
    print("Pass 2 failed. Error log:")
    print(res2.stdout[-1000:] if res2.stdout else "")
    sys.exit(res2.returncode)

print(f"Build complete: {pdf_file}")
