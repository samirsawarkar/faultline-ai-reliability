"""Deterministic pure-function rule detectors for P18 failure types.

Implements CEO-approved definitions for:
- T1 UNRECOVERED_TOOL_ERROR
- T2 REPEATED_CALL_NO_PROGRESS
Operating as pure functions directly over span lists.
"""
from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Optional, Tuple

from projects.p18_trace_triage.adapter import extract_trace_events


def normalize_tool_arguments(args: Any) -> str:
    """Normalize tool arguments into a deterministic canonical string."""
    if args is None:
        return "{}"
    if isinstance(args, str):
        s = args.strip()
        if (s.startswith("{") and s.endswith("}")) or (s.startswith("[") and s.endswith("]")):
            try:
                parsed = json.loads(s)
                return json.dumps(parsed, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
            except Exception:
                pass
        return re.sub(r"\s+", " ", s)
    if isinstance(args, dict):
        return json.dumps(args, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return str(args)


def eval_unrecovered_tool_error(
    spans: List[Dict[str, Any]],
) -> Tuple[bool, Optional[int], str]:
    """T1 UNRECOVERED_TOOL_ERROR.

    Code rule: A tool/API call errors (error.type, error text in tool result)
    and the run never succeeds at that step/operation afterwards.

    Returns:
        (detected, evidence_step, reasoning)
    """
    if not spans:
        return False, None, "Empty spans"

    events = extract_trace_events(spans)
    steps = events["steps"]

    # Record errors by tool name and step
    tool_errors: List[Dict[str, Any]] = []
    span_errors: List[Dict[str, Any]] = []

    for st in steps:
        step_idx = st["step_index"]
        if st["has_error"] and st["error_desc"].startswith("Span error:"):
            span_errors.append({"step": step_idx, "desc": st["error_desc"]})

        for tc in st["tool_calls"]:
            if tc["is_error"]:
                tool_errors.append({
                    "step": step_idx,
                    "name": tc["name"],
                    "arguments": tc["arguments"],
                    "response": tc["response"],
                })

    # Check tool errors: was there a subsequent successful call to the same tool?
    for err in tool_errors:
        err_step = err["step"]
        tool_name = err["name"]
        recovered = False

        for future_st in steps:
            if future_st["step_index"] <= err_step:
                continue
            for tc in future_st["tool_calls"]:
                if tc["name"] == tool_name and not tc["is_error"]:
                    recovered = True
                    break
            if recovered:
                break

        if not recovered:
            snippet = err["response"][:80].replace("\n", " ") if err["response"] else "error"
            reason = (
                f"Tool '{tool_name}' failed at step {err_step} ({snippet}) "
                f"and no subsequent call to '{tool_name}' succeeded."
            )
            return True, err_step, reason

    # Check unrecovered span-level API errors
    for s_err in span_errors:
        s_step = s_err["step"]
        # Check if subsequent steps had any successful tool calls or assistant output
        has_future_success = any(
            len(future_st["tool_calls"]) > 0 and not future_st["has_error"]
            for future_st in steps
            if future_st["step_index"] > s_step
        )
        if not has_future_success:
            return True, s_step, f"Unrecovered span error at step {s_step}: {s_err['desc']}"

    return False, None, "No unrecovered tool errors detected."


def eval_repeated_call_no_progress(
    spans: List[Dict[str, Any]],
) -> Tuple[bool, Optional[int], str]:
    """T2 REPEATED_CALL_NO_PROGRESS.

    Code rule: The same tool call (same name + same normalized arguments)
    issued >= 3 times with no new information in between.

    Returns:
        (detected, evidence_step, reasoning)
    """
    if not spans:
        return False, None, "Empty spans"

    events = extract_trace_events(spans)
    steps = events["steps"]

    # Collect chronological sequence of all tool calls
    all_calls: List[Dict[str, Any]] = []
    for st in steps:
        step_idx = st["step_index"]
        for tc in st["tool_calls"]:
            norm_args = normalize_tool_arguments(tc["arguments"])
            all_calls.append({
                "step": step_idx,
                "name": tc["name"],
                "norm_args": norm_args,
                "key": (tc["name"], norm_args),
                "response": tc["response"].strip() if tc["response"] else "",
            })

    # Find tool calls issued >= 3 times
    calls_by_key: Dict[Tuple[str, str], List[int]] = {}
    for idx, c in enumerate(all_calls):
        calls_by_key.setdefault(c["key"], []).append(idx)

    for (tool_name, norm_args), indices in calls_by_key.items():
        if len(indices) < 3:
            continue

        # Check consecutive occurrences where all 3 responses are identical after whitespace normalization
        for i in range(len(indices) - 2):
            idx1, idx2, idx3 = indices[i], indices[i + 1], indices[i + 2]
            resp1 = re.sub(r"\s+", " ", all_calls[idx1]["response"]).strip()
            resp2 = re.sub(r"\s+", " ", all_calls[idx2]["response"]).strip()
            resp3 = re.sub(r"\s+", " ", all_calls[idx3]["response"]).strip()

            if resp1 == resp2 == resp3:
                evidence_step = all_calls[idx3]["step"]
                reason = (
                    f"Tool '{tool_name}' with arguments {norm_args[:60]} issued "
                    f">= 3 times (steps {all_calls[idx1]['step']}, {all_calls[idx2]['step']}, {evidence_step}) "
                    f"where all 3 responses are identical after whitespace normalization."
                )
                return True, evidence_step, reason

    return False, None, "No repeated calls without progress detected."
