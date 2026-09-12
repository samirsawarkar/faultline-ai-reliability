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

DOC_ID_PATTERN = r"^(doc-\d{4}|link-[a-f0-9]{12})$"
_STRICT = ConfigDict(extra="forbid")

class ToolName(str, Enum):
    SEARCH = "search"
    LOOKUP = "lookup"
    CALC = "calc"

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
    expression: str = Field(min_length=1, max_length=500)

ToolCall = Annotated[
    Union[SearchCall, LookupCall, CalcCall],
    Field(discriminator="tool"),
]
TOOL_CALL_ADAPTER: TypeAdapter = TypeAdapter(ToolCall)

class Candidate(BaseModel):
    model_config = _STRICT
    doc_id: str = Field(pattern=DOC_ID_PATTERN)
    title: str
    score: float = Field(ge=0.0)
    snippet: str = Field(max_length=500) # Added snippet

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

class ScenarioTask(BaseModel):
    model_config = _STRICT
    task_id: str = Field(min_length=1)
    prompt: str = Field(min_length=1)
    tier: str = ""

class AgentStep(BaseModel):
    model_config = _STRICT
    index: int = Field(ge=1)
    thought: str
    tool_call: Optional[ToolCall] = None
    observation: Optional[ToolResult] = None
    action_type: str # "tool" or "answer"

class OutcomeStatus(str, Enum):
    ANSWERED = "answered" # Renamed from SOLVED as per X5
    INCOMPLETE = "incomplete"
    INVALID = "invalid"
    STEP_CAP = "step_cap"
    TOOL_ERROR = "tool_error"
    MALFORMED = "malformed"
    MODEL_FAILURE = "model_failure"

class AgentOutcome(BaseModel):
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
        if self.status is OutcomeStatus.ANSWERED and self.answer is None:
            raise ValueError("an ANSWERED outcome must carry an answer")
        if self.status is not OutcomeStatus.ANSWERED and self.answer is not None:
            raise ValueError("a non-ANSWERED outcome must not carry an answer")
        if len(self.trace) != self.steps_used:
            raise ValueError("trace length must equal steps_used")
        return self
