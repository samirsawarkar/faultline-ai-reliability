import urllib.request
import re
import json
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
        # X3: Implement the seam properly but never invoke it.
        # We raise BEFORE dispatching, but we can return the kwargs if we are in a test mode,
        # or we just raise the kwargs as an exception to assert them in test.
        kwargs = {
            "model": self.model_name,
            "messages": messages,
            "temperature": 0.0,
            "max_tokens": 2048,
        }
        raise RuntimeError("LiteLLM Seam Not Invoked", kwargs)

class StubModel(ModelInterface):
    def __init__(self, behavior: str = "correct", scenarios: Optional[List[Any]] = None, explicit_responses: Optional[List[ModelResponse]] = None):
        self.behavior = behavior
        self.scenarios = scenarios or []
        self.explicit_responses = explicit_responses
        self.idx = 0
        
    def generate(self, messages: List[Dict[str, Any]]) -> ModelResponse:
        def urlopen_stub(*args, **kwargs):
            raise RuntimeError("Outbound network blocked")
        urllib.request.urlopen = urlopen_stub
        
        if self.explicit_responses is not None:
            if self.idx >= len(self.explicit_responses):
                raise RuntimeError("StubModel exhausted")
            resp = self.explicit_responses[self.idx]
            self.idx += 1
            return resp

        if self.behavior == "solver":
            # X2 Solver Stub
            # Y2: No tie-breaker. The solver never touches traversal_sources, required_source, or final_answer.
            if len(messages) == 2:
                prompt = messages[1]["content"]
                step1 = re.split(r'Step \d+: ', prompt)
                step1 = step1[1] if len(step1) > 1 else prompt
                m1 = re.search(r"What is the .*? of (.*?)\?", step1)
                m2 = re.search(r"In which district is (.*?) headquartered\?", step1)
                m3 = re.search(r"Which firm is the external auditor of (.*?)\?", step1)
                ent = None
                if m1: ent = m1.group(1)
                elif m2: ent = m2.group(1)
                elif m3: ent = m3.group(1)
                if ent:
                    return ModelResponse(tool_call={"tool": "search", "query": ent})
            else:
                last_tool_msg = messages[-1]["content"]
                result = json.loads(last_tool_msg)
                if result.get("tool") == "search" and result.get("candidates"):
                    candidates = result["candidates"]
                    
                    prompt = messages[1]["content"]
                    steps = re.split(r'Step \d+: ', prompt)
                    steps = steps[1:] if len(steps) > 1 else [prompt]
                    
                    current_searches = len([m for m in messages if m["role"] == "assistant" and m.get("tool_calls")])
                    
                    if current_searches % 2 == 0:
                        for cand in candidates:
                            snippet = cand.get("snippet", "")
                            m_affil = re.search(r"is officially affiliated with (.*?)\.", snippet)
                            if m_affil:
                                return ModelResponse(tool_call={"tool": "search", "query": m_affil.group(1)})
                    else:
                        step_idx = current_searches // 2
                        if step_idx < len(steps):
                            step_text = steps[step_idx]
                            
                            attr = None
                            m = re.search(r"What is the (.*?) of", step_text)
                            if m: attr = m.group(1)
                            else:
                                if "In which district" in step_text: attr = "headquarters district"
                                elif "Which firm is the external auditor" in step_text: attr = "external auditor"
                            
                            for cand in candidates:
                                snippet = cand.get("snippet", "")
                                if attr:
                                    m_fact = re.search(r"The " + re.escape(attr) + r" of .*? is (.*?)\.", snippet)
                                    if m_fact:
                                        ans = m_fact.group(1)
                                        expected_searches = 1 if len(steps) == 1 else len(steps) * 2 - 1
                                        if current_searches >= expected_searches:
                                            return ModelResponse(answer=ans, cited_sources=[cand["doc_id"]])
                                        else:
                                            return ModelResponse(tool_call={"tool": "search", "query": ans})
                                            
            return ModelResponse(answer="Solver failed to parse", cited_sources=[])

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
