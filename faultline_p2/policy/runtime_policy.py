"""Runtime policy engine enforcing tool authorization and argument constraints."""
from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Set
from .decision import PolicyDecision

DOC_ID_REGEX = re.compile(r"^(doc-\d{4}|link-[a-f0-9]{12})$")


class RuntimePolicy:
    """Authorization layer sitting between agent controller and execution tools."""

    def __init__(
        self,
        allowlist: Optional[Set[str]] = None,
        doc_id_pattern: Optional[re.Pattern] = None,
        max_query_length: int = 200,
        max_calls_per_run: int = 10,
    ) -> None:
        self.allowlist: Set[str] = allowlist if allowlist is not None else {"search", "lookup", "calc"}
        self.doc_id_pattern = doc_id_pattern or DOC_ID_REGEX
        self.max_query_length = max_query_length
        self.max_calls_per_run = max_calls_per_run

        # Per-run call budget tracking
        self.run_call_counts: Dict[str, int] = {}

        # Telemetry
        self.total_evaluations: int = 0
        self.allowed_count: int = 0
        self.denied_count: int = 0
        self.denials_by_rule: Dict[str, int] = {
            "allowlist": 0,
            "doc_id_pattern": 0,
            "query_length": 0,
            "call_budget": 0,
            "deny_by_default": 0,
        }

    def reset_run(self, run_id: str) -> None:
        """Reset budget tracking for a specific run."""
        self.run_call_counts[run_id] = 0

    def evaluate(
        self,
        raw_call: Any,
        run_id: Optional[str] = None,
        trace_store: Optional[Any] = None,
    ) -> PolicyDecision:
        """Evaluate an attempted tool call against policy rules."""
        self.total_evaluations += 1
        rid = run_id or "default"

        # 1. Envelope & Deny-by-default Check
        if not isinstance(raw_call, dict) or "tool" not in raw_call:
            return self._record_decision(
                allowed=False,
                rule="deny_by_default",
                reason="Malformed tool envelope: missing 'tool' key or not a dictionary",
                tool="unknown",
                arguments=raw_call if isinstance(raw_call, dict) else {},
                run_id=run_id,
                trace_store=trace_store,
            )

        tool_name = str(raw_call.get("tool", "")).strip()

        # 2. Tool Allowlist Check
        if tool_name not in self.allowlist:
            return self._record_decision(
                allowed=False,
                rule="allowlist",
                reason=f"Tool '{tool_name}' is forbidden; not present in allowlist {sorted(list(self.allowlist))}",
                tool=tool_name,
                arguments=raw_call,
                run_id=run_id,
                trace_store=trace_store,
            )

        # 3. Per-Run Call Budget Check
        current_calls = self.run_call_counts.get(rid, 0)
        if current_calls >= self.max_calls_per_run:
            return self._record_decision(
                allowed=False,
                rule="call_budget",
                reason=f"Per-run tool budget exhausted ({current_calls}/{self.max_calls_per_run} calls used)",
                tool=tool_name,
                arguments=raw_call,
                run_id=run_id,
                trace_store=trace_store,
            )

        # 4. Argument-Level Constraints
        if tool_name == "lookup":
            doc_id = raw_call.get("doc_id")
            if not isinstance(doc_id, str):
                return self._record_decision(
                    allowed=False,
                    rule="doc_id_pattern",
                    reason="Argument 'doc_id' must be a non-empty string",
                    tool=tool_name,
                    arguments=raw_call,
                    run_id=run_id,
                    trace_store=trace_store,
                )
            # Path traversal / malicious pattern check
            if not self.doc_id_pattern.match(doc_id):
                return self._record_decision(
                    allowed=False,
                    rule="doc_id_pattern",
                    reason=f"Doc ID '{doc_id}' fails pattern constraint r'{self.doc_id_pattern.pattern}'",
                    tool=tool_name,
                    arguments=raw_call,
                    run_id=run_id,
                    trace_store=trace_store,
                )

        elif tool_name == "search":
            query = raw_call.get("query")
            if not isinstance(query, str) or len(query) == 0:
                return self._record_decision(
                    allowed=False,
                    rule="query_length",
                    reason="Search query must be a non-empty string",
                    tool=tool_name,
                    arguments=raw_call,
                    run_id=run_id,
                    trace_store=trace_store,
                )
            if len(query) > self.max_query_length:
                return self._record_decision(
                    allowed=False,
                    rule="query_length",
                    reason=f"Search query length ({len(query)}) exceeds maximum bound ({self.max_query_length})",
                    tool=tool_name,
                    arguments=raw_call,
                    run_id=run_id,
                    trace_store=trace_store,
                )

        elif tool_name == "calc":
            expr = raw_call.get("expression")
            if not isinstance(expr, str) or len(expr) == 0 or len(expr) > 500:
                return self._record_decision(
                    allowed=False,
                    rule="deny_by_default",
                    reason="Calc expression must be a non-empty string <= 500 characters",
                    tool=tool_name,
                    arguments=raw_call,
                    run_id=run_id,
                    trace_store=trace_store,
                )

        # All checks passed: record increment and allow
        self.run_call_counts[rid] = current_calls + 1
        return self._record_decision(
            allowed=True,
            rule="allowed",
            reason="All policy constraints verified and call permitted",
            tool=tool_name,
            arguments=raw_call,
            run_id=run_id,
            trace_store=trace_store,
        )

    def _record_decision(
        self,
        allowed: bool,
        rule: str,
        reason: str,
        tool: str,
        arguments: Dict[str, Any],
        run_id: Optional[str],
        trace_store: Optional[Any],
    ) -> PolicyDecision:
        decision = PolicyDecision(
            allowed=allowed,
            rule=rule,
            reason=reason,
            tool=tool,
            arguments=arguments,
        )

        if allowed:
            self.allowed_count += 1
        else:
            self.denied_count += 1
            self.denials_by_rule[rule] = self.denials_by_rule.get(rule, 0) + 1

        if trace_store and hasattr(trace_store, "log_policy_decision"):
            try:
                trace_store.log_policy_decision(
                    run_id=run_id,
                    tool_name=tool,
                    allowed=allowed,
                    rule=rule,
                    reason=reason,
                )
            except Exception:
                pass

        return decision
