"""Typed contracts for the FAULTLINE single agent.

Everything the agent touches at a boundary — tool calls, tool results, the task
it is given, and the outcome it returns — is a Pydantic model. This is the wall
that makes two of Day 2's failure conditions unreachable:

  * "bypass validation"  -> impossible: a ToolCall / Task / AgentOutcome cannot
    exist without passing model validation, and `extra="forbid"` rejects any
    stray field instead of silently ignoring it.
  * "return an unstructured outcome" -> impossible: `Agent.run` is typed to
    return `AgentOutcome`, whose own `model_validator` enforces cross-field
    invariants (a SOLVED outcome MUST carry an answer; steps_used <= step_cap).

Schema validity (this file) is NOT semantic correctness (see verdict.py and
LEARN.md). A model can validate and still be wrong. Both layers are required.
"""
from enum import Enum
from typing import List, Optional, Union

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    TypeAdapter,
    model_validator,
)
from typing_extensions import Annotated, Literal

# --- ID / value shapes reused below -----------------------------------------
DOC_ID_PATTERN = r"^doc-\d{4}$"
_STRICT = ConfigDict(extra="forbid")


class ToolName(str, Enum):
    """The three tools this agent is allowed to invoke — nothing else."""
    SEARCH = "search"
    LOOKUP = "lookup"
    CALC = "calc"


# ===========================================================================
# Tool calls  (input to the toolbox) — a discriminated union on `tool`
# ===========================================================================
class SearchCall(BaseModel):
    model_config = _STRICT
    tool: Literal["search"] = "search"
    query: str = Field(min_length=1, max_length=200)


class LookupCall(BaseModel):
    model_config = _STRICT
    tool: Literal["lookup"] = "lookup"
    doc_id: str = Field(pattern=DOC_ID_PATTERN)


class CalcCall(BaseModel):
    model_config = _STRICT
    tool: Literal["calc"] = "calc"
    # Arbitrary text is accepted here on purpose; the SAFE arithmetic evaluator
    # in tools.py is what rejects anything that is not pure integer arithmetic.
    expression: str = Field(min_length=1, max_length=500)


ToolCall = Annotated[
    Union[SearchCall, LookupCall, CalcCall],
    Field(discriminator="tool"),
]
# Adapter used to validate *untyped* input (e.g. a dict from an external caller).
# This is the object tests use to prove validation cannot be bypassed.
TOOL_CALL_ADAPTER: TypeAdapter = TypeAdapter(ToolCall)


# ===========================================================================
# Tool results (output of the toolbox) — a discriminated union on `tool`
# ===========================================================================
class Candidate(BaseModel):
    model_config = _STRICT
    doc_id: str = Field(pattern=DOC_ID_PATTERN)
    title: str
    score: float = Field(ge=0.0)


class SearchResult(BaseModel):
    model_config = _STRICT
    tool: Literal["search"] = "search"
    ok: bool = True
    error: Optional[str] = None
    candidates: List[Candidate] = Field(default_factory=list)


class LookupResult(BaseModel):
    model_config = _STRICT
    tool: Literal["lookup"] = "lookup"
    ok: bool
    error: Optional[str] = None
    doc_id: Optional[str] = None
    title: Optional[str] = None
    text: Optional[str] = None


class CalcResult(BaseModel):
    model_config = _STRICT
    tool: Literal["calc"] = "calc"
    ok: bool
    error: Optional[str] = None
    expression: str
    value: Optional[int] = None


ToolResult = Annotated[
    Union[SearchResult, LookupResult, CalcResult],
    Field(discriminator="tool"),
]


# ===========================================================================
# The task the agent is asked to solve
# ===========================================================================
class ArchiveSumTask(BaseModel):
    """Sum the numeric part of each named entity's archival reference.

    Deliberately multi-hop: every entity costs one `search` + one `lookup`, and
    the finishing `calc` costs one more. Step demand = 2*len(entities) + 1, which
    is what lets us drive a task *over budget* on demand (see experiment_budget).
    """
    model_config = _STRICT
    task_id: str = Field(min_length=1)
    kind: Literal["archive_sum"] = "archive_sum"
    entities: List[str] = Field(min_length=1, max_length=64)


# ===========================================================================
# Reasoning trace + terminal outcome
# ===========================================================================
class AgentStep(BaseModel):
    model_config = _STRICT
    index: int = Field(ge=1)
    thought: str
    tool_call: ToolCall
    observation: ToolResult


class OutcomeStatus(str, Enum):
    SOLVED = "solved"        # task completed and answer produced
    INCOMPLETE = "incomplete"  # ran out of step budget — clean, honest stop
    INVALID = "invalid"      # the task itself failed validation


class AgentOutcome(BaseModel):
    """The ONLY thing `Agent.run` may return. Structured by construction."""
    model_config = _STRICT
    task_id: str
    status: OutcomeStatus
    answer: Optional[str] = None
    cited_sources: List[str] = Field(default_factory=list)
    steps_used: int = Field(ge=0)
    step_cap: int = Field(gt=0)
    reason: Optional[str] = None
    trace: List[AgentStep] = Field(default_factory=list)

    @model_validator(mode="after")
    def _invariants(self) -> "AgentOutcome":
        if self.steps_used > self.step_cap:
            raise ValueError("steps_used cannot exceed step_cap")
        if self.status is OutcomeStatus.SOLVED and self.answer is None:
            raise ValueError("a SOLVED outcome must carry an answer")
        if self.status is not OutcomeStatus.SOLVED and self.answer is not None:
            raise ValueError("a non-SOLVED outcome must not carry an answer")
        if len(self.trace) != self.steps_used:
            raise ValueError("trace length must equal steps_used")
        return self
