"""Provenance policy engine enforcing tool allowlists, argument schema, and input grounding."""
from __future__ import annotations

import ast
import json
import re
from typing import Any, Dict, List, Optional

from faultline_p2.policy.decision import PolicyDecision

EOS_TOKENS = [
    "<end_of_turn>",
    "</s>",
    "<|eot_id|>",
    "<|im_end|>",
    "<|endoftext|>",
    "<｜end of sentence｜>",
    "<｜endofsentence｜>",
    "<|end_of_sentence|>",
]


def parse_tool_block(system_prompt: str) -> Dict[str, List[str]]:
    """Parse MCPTox system prompt tool definitions into mapping of tool name to argument names."""
    tools: Dict[str, List[str]] = {}
    current_tool: Optional[str] = None
    in_args = False

    for line in system_prompt.split("\n"):
        line_s = line.strip()
        if line_s.startswith("Tool:"):
            current_tool = line_s.split("Tool:", 1)[1].strip()
            tools[current_tool] = []
            in_args = False
        elif line_s.startswith("Arguments:"):
            in_args = True
        elif in_args and line_s.startswith("- "):
            arg_part = line_s[2:].strip()
            if arg_part.lower() == "no arguments":
                continue
            if ":" in arg_part:
                candidate = arg_part.split(":", 1)[0].strip()
                if re.match(r"^[a-zA-Z0-9_-]+$", candidate):
                    if current_tool and candidate not in tools[current_tool]:
                        tools[current_tool].append(candidate)
        elif line_s.startswith("Description:"):
            in_args = False

    return tools


def _extract_balanced_braces(text: str) -> List[str]:
    """Extract all top-level balanced {...} string blocks respecting quotes."""
    results: List[str] = []
    i = 0
    n = len(text)
    while i < n:
        if text[i] == "{":
            start = i
            depth = 1
            in_str: Optional[str] = None
            escape = False
            i += 1
            while i < n and depth > 0:
                ch = text[i]
                if escape:
                    escape = False
                elif ch == "\\":
                    escape = True
                elif in_str:
                    if ch == in_str:
                        in_str = None
                else:
                    if ch == '"' or ch == "'":
                        in_str = ch
                    elif ch == "{":
                        depth += 1
                    elif ch == "}":
                        depth -= 1
                i += 1
            if depth == 0:
                results.append(text[start:i])
        else:
            i += 1
    return results


def _parse_single_object(s: str) -> Optional[Dict[str, Any]]:
    """Try parsing a single JSON/Python dict string."""
    try:
        res = json.loads(s)
        if isinstance(res, dict):
            return res
    except Exception:
        pass

    # Substitute bare true/false/null as whole words before literal_eval
    sub_s = re.sub(r"\btrue\b", "True", s)
    sub_s = re.sub(r"\bfalse\b", "False", sub_s)
    sub_s = re.sub(r"\bnull\b", "None", sub_s)

    try:
        res = ast.literal_eval(sub_s)
        if isinstance(res, dict):
            return res
    except Exception:
        pass

    return None


def parse_response(text: Any) -> List[Dict[str, Any]]:
    """Parse model response text into a list of tool call dictionaries."""
    if not isinstance(text, str):
        return []

    s = text
    # Strip EOS tokens anywhere in text
    for eos in EOS_TOKENS:
        s = s.replace(eos, " ")

    # Strip code fences, including fences glued to opening braces (```json{ -> {)
    s = re.sub(r"```(?:json)?", " ", s)
    s = s.replace("```", " ")

    candidates = _extract_balanced_braces(s)
    parsed: List[Dict[str, Any]] = []
    for c in candidates:
        obj = _parse_single_object(c)
        if obj is not None:
            parsed.append(obj)

    return parsed


class ProvenancePolicy:
    """Evaluates agent tool calls against MCP tool definitions and user query grounding."""

    def __init__(self) -> None:
        self.total_evaluations: int = 0
        self.allowed_count: int = 0
        self.denied_count: int = 0
        self.denials_by_rule: Dict[str, int] = {
            "envelope": 0,
            "multi_call": 0,
            "unknown_tool": 0,
            "extra_argument": 0,
            "provenance": 0,
        }

    def evaluate(
        self,
        raw_call: Any,
        query: str,
        listed_tools: Dict[str, List[str]],
    ) -> PolicyDecision:
        """Evaluate a tool call against the 5-stage provenance policy."""
        self.total_evaluations += 1

        # 1. 'envelope' container check
        if isinstance(raw_call, list):
            if len(raw_call) == 0:
                self.denied_count += 1
                self.denials_by_rule["envelope"] += 1
                return PolicyDecision(
                    allowed=False,
                    rule="envelope",
                    reason="raw_call must not be an empty list",
                    tool="unknown",
                    arguments={},
                )
            if len(raw_call) > 1:
                # 2. 'multi_call' rule: rejected if 2+ objects provided
                self.denied_count += 1
                self.denials_by_rule["multi_call"] += 1
                return PolicyDecision(
                    allowed=False,
                    rule="multi_call",
                    reason=f"Protocol requires exactly one call; received {len(raw_call)} calls",
                    tool="multiple",
                    arguments={},
                )
            call = raw_call[0]
        elif isinstance(raw_call, dict):
            call = raw_call
        else:
            self.denied_count += 1
            self.denials_by_rule["envelope"] += 1
            return PolicyDecision(
                allowed=False,
                rule="envelope",
                reason="raw_call must be a dict or list of dicts",
                tool="unknown",
                arguments={},
            )

        # 1b. 'envelope' dict structure check
        if (
            not isinstance(call, dict)
            or not isinstance(call.get("tool"), str)
            or not isinstance(call.get("arguments"), dict)
        ):
            self.denied_count += 1
            self.denials_by_rule["envelope"] += 1
            tool = call.get("tool") if isinstance(call, dict) and isinstance(call.get("tool"), str) else "unknown"
            args = call.get("arguments") if isinstance(call, dict) and isinstance(call.get("arguments"), dict) else {}
            return PolicyDecision(
                allowed=False,
                rule="envelope",
                reason="raw_call must be a dict with 'tool' str and 'arguments' dict",
                tool=tool,
                arguments=args,
            )

        tool = call["tool"]
        arguments = call["arguments"]

        # 3. 'unknown_tool' rule: tool must be in listed_tools
        if tool not in listed_tools:
            self.denied_count += 1
            self.denials_by_rule["unknown_tool"] += 1
            return PolicyDecision(
                allowed=False,
                rule="unknown_tool",
                reason=f"Tool '{tool}' not in listed tools",
                tool=tool,
                arguments=arguments,
            )

        # 4. 'extra_argument' rule: every argument key must be declared for the tool (extra=forbid)
        declared_args = set(listed_tools.get(tool, []))
        for k in arguments.keys():
            if k not in declared_args:
                self.denied_count += 1
                self.denials_by_rule["extra_argument"] += 1
                return PolicyDecision(
                    allowed=False,
                    rule="extra_argument",
                    reason=f"Argument '{k}' not declared for tool '{tool}'",
                    tool=tool,
                    arguments=arguments,
                )

        # 5. 'provenance' rule: every leaf string value must be grounded in query
        norm_query = self._normalize(query)
        leaves = self._extract_leaves(arguments)

        for leaf in leaves:
            if not isinstance(leaf, str):
                continue
            if len(leaf) <= 3:
                continue
            norm_leaf = self._normalize(leaf)
            if len(norm_leaf) <= 3:
                continue
            if norm_leaf in norm_query:
                continue
            tokens_gt_3 = [t for t in norm_leaf.split() if len(t) > 3]
            if all(t in norm_query for t in tokens_gt_3):
                continue

            self.denied_count += 1
            self.denials_by_rule["provenance"] += 1
            return PolicyDecision(
                allowed=False,
                rule="provenance",
                reason=f"Argument leaf value '{leaf}' is not grounded in user query",
                tool=tool,
                arguments=arguments,
            )

        self.allowed_count += 1
        return PolicyDecision(
            allowed=True,
            rule="allow",
            reason="Tool call permitted by provenance policy",
            tool=tool,
            arguments=arguments,
        )

    @staticmethod
    def _normalize(s: str) -> str:
        s = s.lower().strip()
        while len(s) >= 2 and ((s[0] == "'" and s[-1] == "'") or (s[0] == '"' and s[-1] == '"')):
            s = s[1:-1].strip()
        s = re.sub(r"\s+", " ", s).strip()
        return s

    @classmethod
    def _extract_leaves(cls, obj: Any) -> List[Any]:
        if isinstance(obj, dict):
            res = []
            for v in obj.values():
                res.extend(cls._extract_leaves(v))
            return res
        elif isinstance(obj, (list, tuple)):
            res = []
            for v in obj:
                res.extend(cls._extract_leaves(v))
            return res
        else:
            return [obj]
