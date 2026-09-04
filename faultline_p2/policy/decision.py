"""Typed policy enforcement decisions."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict


@dataclass(frozen=True)
class PolicyDecision:
    """Typed decision returned by the runtime policy engine."""
    allowed: bool
    rule: str
    reason: str
    tool: str
    arguments: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "allowed": self.allowed,
            "rule": self.rule,
            "reason": self.reason,
            "tool": self.tool,
            "arguments": self.arguments,
        }
