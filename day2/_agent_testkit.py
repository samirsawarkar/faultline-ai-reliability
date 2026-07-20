"""Shared test helpers for the Day-2 suite.

Kept in a uniquely-named module (not `conftest`) so it can be imported by name
from the test files without colliding with other days' `conftest.py` when the
whole repo is collected in a single `pytest` run. Day 2's conftest puts this
directory on `sys.path`, so `from _agent_testkit import entities` resolves both
for a per-day run and for a root run.
"""
from __future__ import annotations


def entities(env, k=None):
    """Entity display names in deterministic corpus order (fact docs only)."""
    suffixes = ("Labs", "Works", "Foundry", "Collective", "Systems", "Union")
    names = [d["title"] for d in env["documents"] if d["title"].endswith(suffixes)]
    return names if k is None else names[:k]
