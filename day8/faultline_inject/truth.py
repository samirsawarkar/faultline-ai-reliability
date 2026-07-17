"""The ground-truth log — labels written at injection time, kept out of band.

This is the load-bearing idea of Day 8's honesty. When the injector decides a
call's fate, it writes the truth *here*, from the decision itself — not by
inspecting the output it later produces. The system under test (and any detector
built on it) sees only the boundary's output and its trace span; it never sees a
`GroundTruthLog` entry. So the label is an INDEPENDENT record of what really
happened, and "did the detector find the fault?" is a fair question rather than a
lookup.

Every call gets exactly one entry — faulted or clean — so the log is a complete,
seq-indexed labelling of the whole run (a dataset), not just a list of faults.
Entries are keyed to the trace by `span_id`, which is how a labelled trace is
reconstructed without ever putting the label inside the span.
"""
from __future__ import annotations

import dataclasses
import json
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

CLEAN_LABEL = "clean"


@dataclass(frozen=True)
class TruthEntry:
    seq: int                       # 0-based call ordinal within the run
    span_id: Optional[str]         # link to the trace span (None if untraced)
    component: str
    input_digest: str
    fired: bool                    # was a fault injected on this call
    label: str                     # ground-truth class ("clean" or spec.label)
    fault_id: Optional[str] = None
    mode: Optional[str] = None
    severity: Optional[int] = None
    trigger: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return dataclasses.asdict(self)


@dataclass
class GroundTruthLog:
    run_seed: int
    entries: List[TruthEntry] = field(default_factory=list)

    def record(self, entry: TruthEntry) -> None:
        # Entries arrive in call order; the seq must be contiguous and gap-free,
        # so the log is provably a complete labelling and not a lossy sample.
        expected = len(self.entries)
        if entry.seq != expected:
            raise ValueError(
                f"ground-truth seq gap: got {entry.seq}, expected {expected}")
        self.entries.append(entry)

    def fired_seqs(self) -> List[int]:
        return [e.seq for e in self.entries if e.fired]

    def labels_by_seq(self) -> Dict[int, str]:
        return {e.seq: e.label for e in self.entries}

    def label_strings(self) -> List[str]:
        """The ground-truth annotation namespace a leakage check must find absent
        from any observable surface: the labels and the fault ids that tie a call
        back to its truth. Deliberately NOT the mode words ("error", "drop", …):
        a mode names a fault *kind* whose effect is often legitimately observable
        (a raised error, an empty result), and it collides with generic words like
        a span's status "error". Leakage means the *answer key* — the label — is
        readable from the sample, not that the fault had a visible effect. Labels
        use a reserved "fault:" prefix precisely so this check is exact."""
        out = set()
        for e in self.entries:
            out.add(e.label)
            if e.fault_id:
                out.add(e.fault_id)
        out.discard(CLEAN_LABEL)  # "clean" is the absence of a fault, not a tell
        return sorted(out)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "run_seed": self.run_seed,
            "count": len(self.entries),
            "fired": len(self.fired_seqs()),
            "entries": [e.to_dict() for e in self.entries],
        }

    def to_json(self) -> bytes:
        text = json.dumps(self.to_dict(), sort_keys=True, ensure_ascii=True, indent=2)
        return (text + "\n").encode("utf-8")
