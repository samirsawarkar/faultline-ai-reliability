"""Golden scenario set selection for release gate."""
from __future__ import annotations

import hashlib
import json
from typing import Any, List, Optional, Sequence, Tuple


def select(
    scenarios: Sequence[Any],
    n: int = 30,
    pool: Optional[str] = "reserved",
) -> Tuple[List[str], str]:
    """Select a stable golden scenario set by hashing scenario IDs.

    Filters scenarios by pool (if provided and applicable), sorts IDs by
    sha256(scenario_id), takes the first n, and returns the selected IDs
    along with the manifest sha256 of the sorted ID list.
    """
    candidate_ids: List[str] = []
    for s in scenarios:
        if isinstance(s, str):
            candidate_ids.append(s)
            continue

        s_pool = getattr(s, "pool", None)
        if s_pool is None and isinstance(s, dict):
            s_pool = s.get("pool")

        if pool is not None and s_pool is not None and s_pool != pool:
            continue

        sid = getattr(s, "scenario_id", None) or getattr(s, "id", None)
        if sid is None and isinstance(s, dict):
            sid = s.get("scenario_id") or s.get("id")
        if sid is None:
            sid = str(s)
        candidate_ids.append(sid)

    unique_ids = sorted(list(set(candidate_ids)))
    sorted_by_hash = sorted(
        unique_ids,
        key=lambda sid: hashlib.sha256(sid.encode("utf-8")).hexdigest(),
    )
    golden_ids = sorted_by_hash[:n]
    manifest_sha256 = hashlib.sha256(json.dumps(golden_ids).encode("utf-8")).hexdigest()
    return golden_ids, manifest_sha256
