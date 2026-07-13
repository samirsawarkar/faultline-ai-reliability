"""The single agent: a deterministic reason -> tool -> observe loop.

Why deterministic (no LLM) — this is the crux of Day 2 and defended in
DECISIONS.md (D-011): FAULTLINE measures what an *injected fault* does to an
agent. If the baseline agent had its own nondeterminism (sampling, timing,
coordination), a behavior change could never be cleanly attributed to the fault.
So the specimen is a fully-owned, deterministic policy. Every branch below is a
pure function of (env, task).

Termination is guaranteed structurally, not hoped for:
  * The loop is `while steps < step_cap` — there is no `while True` anywhere.
  * Each iteration performs exactly one tool call and increments `steps`.
  * Therefore the loop runs at most `step_cap` times and always returns an
    AgentOutcome — SOLVED if it finished inside budget, INCOMPLETE if it did not.
An agent that "can hang" is the Day-2 fail condition; this structure removes the
possibility.
"""
from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

from pydantic import ValidationError

from .contracts import (
    AgentOutcome,
    AgentStep,
    ArchiveSumTask,
    CalcCall,
    LookupCall,
    OutcomeStatus,
    SearchCall,
)
from .tools import ToolBox

DEFAULT_STEP_CAP = 12

# Pull the integer out of an archival-reference token, e.g. "Rune-4016" -> 4016.
_ARCHIVE_RE = re.compile(r"archival reference of (?P<ent>.+?) is [A-Za-z]+-(?P<num>\d+)\.")


class _EntityState:
    __slots__ = ("name", "searched", "doc_id", "number")

    def __init__(self, name: str) -> None:
        self.name = name
        self.searched = False
        self.doc_id: Optional[str] = None
        self.number: Optional[int] = None


class Agent:
    def __init__(self, env: Dict[str, Any], step_cap: int = DEFAULT_STEP_CAP) -> None:
        if step_cap <= 0:
            raise ValueError("step_cap must be positive")
        self._env = env
        self.step_cap = step_cap
        self._box = ToolBox(env)

    def run(self, task_input: Any) -> AgentOutcome:
        """Solve a task, ALWAYS returning a validated AgentOutcome."""
        # --- 1. Validate the task. A bad task is a structured INVALID outcome,
        #        never an exception that escapes to the caller. ---
        try:
            task = ArchiveSumTask.model_validate(task_input)
        except ValidationError as e:
            task_id = _best_effort_task_id(task_input)
            return AgentOutcome(
                task_id=task_id,
                status=OutcomeStatus.INVALID,
                steps_used=0,
                step_cap=self.step_cap,
                reason=f"task failed validation: {e.error_count()} error(s)",
            )

        states = [_EntityState(name) for name in task.entities]
        trace: List[AgentStep] = []
        total: Optional[int] = None
        steps = 0

        # --- 2. The bounded loop. ---
        while steps < self.step_cap:
            plan = self._next_action(states, total)
            if plan is None:  # nothing left to do -> solved before the cap
                break
            thought, call = plan
            steps += 1
            result = self._box.dispatch(call)
            trace.append(
                AgentStep(index=steps, thought=thought, tool_call=call, observation=result)
            )
            total = self._observe(states, total, call, result)

        # --- 3. Terminate cleanly, always structured. ---
        solved = total is not None
        cited = sorted({s.doc_id for s in states if s.doc_id is not None})
        if solved:
            return AgentOutcome(
                task_id=task.task_id,
                status=OutcomeStatus.SOLVED,
                answer=str(total),
                cited_sources=cited,
                steps_used=steps,
                step_cap=self.step_cap,
                trace=trace,
            )
        return AgentOutcome(
            task_id=task.task_id,
            status=OutcomeStatus.INCOMPLETE,
            cited_sources=cited,
            steps_used=steps,
            step_cap=self.step_cap,
            reason="step cap reached before the task was solved",
            trace=trace,
        )

    # -- reason: decide the single next action, or None when finished -------
    def _next_action(self, states: List[_EntityState], total: Optional[int]):
        for st in states:
            if st.number is not None:
                continue
            if not st.searched:
                return (
                    f"locate the fact document for {st.name!r}",
                    SearchCall(query=st.name),
                )
            if st.doc_id is not None:
                return (
                    f"read the archival reference of {st.name!r} from {st.doc_id}",
                    LookupCall(doc_id=st.doc_id),
                )
            # searched but no candidate was found: unsolvable within this policy.
            return None
        if total is None:
            expr = "+".join(str(st.number) for st in states)
            return (f"sum the {len(states)} archival numbers", CalcCall(expression=expr))
        return None

    # -- observe: fold a tool result back into state ------------------------
    def _observe(self, states, total, call, result):
        if isinstance(call, SearchCall):
            st = _find(states, call.query, by="name")
            if st is not None:
                st.searched = True
                st.doc_id = result.candidates[0].doc_id if result.candidates else None
        elif isinstance(call, LookupCall):
            st = _find(states, call.doc_id, by="doc")
            if st is not None and result.ok and result.text:
                st.number = _extract_number(result.text, st.name)
        elif isinstance(call, CalcCall):
            if result.ok:
                total = result.value
        return total


def _find(states, key, by):
    for st in states:
        if by == "name" and st.name == key:
            return st
        if by == "doc" and st.doc_id == key:
            return st
    return None


def _extract_number(text: str, entity: str) -> Optional[int]:
    for m in _ARCHIVE_RE.finditer(text):
        if m.group("ent") == entity:
            return int(m.group("num"))
    return None


def _best_effort_task_id(task_input: Any) -> str:
    if isinstance(task_input, dict):
        tid = task_input.get("task_id")
        if isinstance(tid, str) and tid:
            return tid
    return "unknown-task"
