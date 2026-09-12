"""Test sha256 equality of frozen day01 files against faultline_p2 copies."""
import hashlib
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent

PAIRS = [
    (
        REPO_ROOT / "day01" / "faultline" / "oracle.py",
        REPO_ROOT / "faultline_p2" / "oracle" / "_day01_oracle.py",
    ),
    (
        REPO_ROOT / "day01" / "faultline" / "env.py",
        REPO_ROOT / "faultline_p2" / "env" / "_day01_env.py",
    ),
]


def test_frozen_copies_sha256_equality():
    for original, copy in PAIRS:
        assert original.is_file(), f"Original file not found: {original}"
        assert copy.is_file(), f"Copy file not found: {copy}"

        orig_bytes = original.read_bytes()
        copy_bytes = copy.read_bytes()

        orig_hash = hashlib.sha256(orig_bytes).hexdigest()
        copy_hash = hashlib.sha256(copy_bytes).hexdigest()

        assert orig_hash == copy_hash, (
            f"Hash mismatch for frozen file copy!\n"
            f"Original: {original.resolve()} (sha256: {orig_hash})\n"
            f"Copy:     {copy.resolve()} (sha256: {copy_hash})"
        )
