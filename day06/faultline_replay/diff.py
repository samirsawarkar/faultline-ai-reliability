"""Structured diff between two JSON-like values (traces, states, bundles)."""
from __future__ import annotations

from typing import Any, Dict, List

_MISSING = object()


def diff(a: Any, b: Any, path: str = "") -> List[Dict[str, Any]]:
    """Return a list of {path, a, b} where a and b differ. Empty => identical."""
    out: List[Dict[str, Any]] = []
    if isinstance(a, dict) and isinstance(b, dict):
        for key in sorted(set(a) | set(b)):
            out += diff(a.get(key, _MISSING), b.get(key, _MISSING), f"{path}.{key}")
    elif isinstance(a, list) and isinstance(b, list):
        if len(a) != len(b):
            out.append({"path": f"{path}[len]", "a": len(a), "b": len(b)})
        for i in range(min(len(a), len(b))):
            out += diff(a[i], b[i], f"{path}[{i}]")
    else:
        if a is _MISSING:
            out.append({"path": path, "a": None, "b": _short(b), "note": "only in b"})
        elif b is _MISSING:
            out.append({"path": path, "a": _short(a), "b": None, "note": "only in a"})
        elif a != b:
            out.append({"path": path, "a": _short(a), "b": _short(b)})
    return out


def _short(v: Any) -> Any:
    s = v if isinstance(v, (int, float, bool)) or v is None else str(v)
    if isinstance(s, str) and len(s) > 80:
        return s[:80] + "..."
    return s


def diff_summary(a: Any, b: Any) -> Dict[str, Any]:
    d = diff(a, b)
    return {"equal": not d, "diff_count": len(d), "diffs": d}
