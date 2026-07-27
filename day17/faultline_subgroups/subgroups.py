"""Slice a results table into subgroups by one or more dimensions.

A `row` is a dict with dimension keys (e.g. fault, severity) and a binary
`correct` field. `slice_by` groups rows by the chosen dimension tuple and returns a
gated rate per subgroup (Wilson CI + min-sample verdict), sorted deterministically.
"""
from __future__ import annotations

from typing import Any, Dict, List, Sequence

from .gate import subgroup_rate


def _key(row: Dict[str, Any], dims: Sequence[str]):
    return tuple(row[d] for d in dims)


def slice_by(rows: List[Dict[str, Any]], dims: Sequence[str],
             outcome: str = "correct") -> List[Dict[str, Any]]:
    """One gated subgroup per distinct combination of `dims` values."""
    groups: Dict[tuple, List[Dict[str, Any]]] = {}
    for r in rows:
        groups.setdefault(_key(r, dims), []).append(r)

    out: List[Dict[str, Any]] = []
    for key in sorted(groups, key=lambda k: tuple(str(x) for x in k)):
        members = groups[key]
        n = len(members)
        correct = sum(1 for m in members if m[outcome])
        row = {"dims": dict(zip(dims, key)), **subgroup_rate(correct, n)}
        out.append(row)
    return out


def overall_rate(rows: List[Dict[str, Any]], outcome: str = "correct") -> float:
    if not rows:
        return 0.0
    return round(sum(1 for r in rows if r[outcome]) / len(rows), 6)
