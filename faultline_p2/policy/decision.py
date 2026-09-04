"""Typed policy enforcement decisions."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Protocol, runtime_checkable


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


@runtime_checkable
class PolicyProtocol(Protocol):
    """Protocol for runtime authorization policy engines."""

    def evaluate(
        self,
        raw_call: Any,
        run_id: Optional[str] = None,
        trace_store: Optional[Any] = None,
    ) -> PolicyDecision:
        """Evaluate a tool call against policy rules."""
        ...
