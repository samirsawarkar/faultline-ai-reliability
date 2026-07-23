"""FAULTLINE Day 1 package: deterministic environment + honest oracle.

Public surface:
    build_env(seed)        -> dict   (deterministic corpus + questions)
    canonical_bytes(obj)   -> bytes  (byte-stable serialization)
    env_digest(seed)       -> str    (sha256 of the canonical env bytes)
    oracle_check(q, resp)  -> dict   (correctness + required-source verdict)
"""
from .env import build_env, canonical_bytes, env_digest, SPEC_VERSION
from .oracle import oracle_check, normalize

__all__ = [
    "build_env",
    "canonical_bytes",
    "env_digest",
    "oracle_check",
    "normalize",
    "SPEC_VERSION",
]
