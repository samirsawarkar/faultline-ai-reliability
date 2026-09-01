from typing import Optional, Dict, Any, List, Protocol
from pydantic import BaseModel, Field

class ModelResponse(BaseModel):
    thought: str = ""
    tool_call: Optional[Dict[str, Any]] = None
    answer: Optional[str] = None
    cited_sources: List[str] = Field(default_factory=list)

class ModelInterface(Protocol):
    def generate(self, messages: List[Dict[str, Any]]) -> ModelResponse:
        ...

class LiteLLMModel(ModelInterface):
    def __init__(self, model_name: str, provider: str, version: str):
        self.model_name = model_name
        self.provider = provider
        self.version = version

    def generate(self, messages: List[Dict[str, Any]]) -> ModelResponse:
        import litellm
        raise RuntimeError("Network call attempted during zero-dollar phase!")

class StubModel(ModelInterface):
    def __init__(self, behavior: str = "correct", scenarios: Optional[List[Any]] = None, explicit_responses: Optional[List[ModelResponse]] = None):
        self.behavior = behavior
        self.scenarios = scenarios or []
        self.explicit_responses = explicit_responses
        self.idx = 0
        
    def generate(self, messages: List[Dict[str, Any]]) -> ModelResponse:
        import urllib.request
        def urlopen_stub(*args, **kwargs):
            raise RuntimeError("Outbound network blocked")
        urllib.request.urlopen = urlopen_stub
        
        if self.explicit_responses is not None:
            if self.idx >= len(self.explicit_responses):
                raise RuntimeError("StubModel exhausted")
            resp = self.explicit_responses[self.idx]
            self.idx += 1
            return resp

        if self.behavior == "hard_failure":
            raise RuntimeError("Simulated hard failure")
            
        if self.behavior == "malformed":
            return ModelResponse(thought="This is malformed, no tool, no answer")
            
        if self.behavior == "step_cap":
            return ModelResponse(tool_call={"tool": "search", "query": "looping"})
            
        user_msg = next((m["content"] for m in messages if m["role"] == "user"), "")
        scenario = next((s for s in self.scenarios if s.prompt == user_msg), None)
        
        if not scenario:
            return ModelResponse(answer="Unknown scenario", cited_sources=[])

        if self.behavior == "correct":
            return ModelResponse(answer=scenario.final_answer, cited_sources=[scenario.required_source])
            
        if self.behavior == "correct_wrong_citation":
            link_doc = next((d for d in scenario.traversal_sources if d.startswith("link-")), "doc-9999")
            return ModelResponse(answer=scenario.final_answer, cited_sources=[link_doc])
            
        if self.behavior == "wrong_answer":
            return ModelResponse(answer="Wrong Answer", cited_sources=[scenario.required_source])

        return ModelResponse(answer="Unhandled behavior", cited_sources=[])
