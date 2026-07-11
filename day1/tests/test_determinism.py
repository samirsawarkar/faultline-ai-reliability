"""Determinism tests -- the mission's pass/fail gate.

FAIL condition for Day 1: the environment or oracle is not deterministic.
These tests are the machine proof that it is.

Run:  python -m pytest tests/ -v
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from faultline import build_env, canonical_bytes, env_digest, oracle_check  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
SEEDS = list(range(20))  # the required "20 seeds"


def test_same_seed_byte_identical_in_process():
    """Same seed, generated twice in one process -> identical bytes."""
    for seed in SEEDS:
        a = canonical_bytes(build_env(seed))
        b = canonical_bytes(build_env(seed))
        assert a == b, f"seed {seed} not stable within a process"


def test_different_seeds_differ():
    """Non-degenerate: distinct seeds must yield distinct environments."""
    digests = {seed: env_digest(seed) for seed in SEEDS}
    assert len(set(digests.values())) == len(SEEDS), "seed collision detected"


def test_byte_identical_across_fresh_processes_and_hashseeds():
    """The real attack: regenerate in fresh interpreters with DIFFERENT
    PYTHONHASHSEED values. Byte-identical output proves no dependence on
    hash randomization, dict ordering, or process state.

    This is the '20 seeds twice, byte-identical' evidence, hardened.
    """
    script = (
        "import sys; sys.path.insert(0, r'%s');"
        "from faultline import env_digest;"
        "print('\\n'.join(f'{s} {env_digest(s)}' for s in range(20)))"
    ) % str(ROOT)

    def run(hashseed: str) -> str:
        env = dict(os.environ, PYTHONHASHSEED=hashseed)
        out = subprocess.run(
            [sys.executable, "-c", script],
            capture_output=True, text=True, check=True, env=env,
        )
        return out.stdout

    run_a = run("0")
    run_b = run("1")
    run_c = run("random")
    assert run_a == run_b == run_c, "output depends on PYTHONHASHSEED"

    # And it matches the in-process digests -> one canonical truth.
    expected = "\n".join(f"{s} {env_digest(s)}" for s in SEEDS) + "\n"
    assert run_a == expected


def test_oracle_is_deterministic():
    """Oracle verdict is a pure function of (question, response)."""
    q = build_env(3)["questions"][0]
    resp = {"answer": q["answer"], "cited_sources": [q["required_source"]]}
    verdicts = [oracle_check(q, resp) for _ in range(50)]
    assert all(v == verdicts[0] for v in verdicts)
    assert verdicts[0]["passed"] is True


def test_oracle_rejects_uncited_but_correct():
    """The honesty rule: correct token without the required source fails."""
    q = build_env(3)["questions"][0]
    verdict = oracle_check(q, {"answer": q["answer"], "cited_sources": []})
    assert verdict["correct"] is True
    assert verdict["cited_required"] is False
    assert verdict["passed"] is False
