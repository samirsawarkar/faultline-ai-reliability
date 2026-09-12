import urllib.request
import re
import json
import time
from typing import Optional, Dict, Any, List, Protocol
from pydantic import BaseModel, Field

class ModelResponse(BaseModel):
    thought: str = ""
    tool_call: Optional[Dict[str, Any]] = None
    answer: Optional[str] = None
    cited_sources: List[str] = Field(default_factory=list)
    raw_tool_call: Optional[Dict[str, Any]] = None

class ModelInterface(Protocol):
    def generate(self, messages: List[Dict[str, Any]]) -> ModelResponse:
        ...

class LiteLLMModel(ModelInterface):
    def __init__(self, model_name: str, provider: str, version: str, dry_run: bool = True):
        self.model_name = model_name
        self.provider = provider
        self.version = version
        self.dry_run = dry_run

    def generate(self, messages: List[Dict[str, Any]]) -> ModelResponse:
        import litellm
        import os
        from dotenv import load_dotenv
        load_dotenv()

        kwargs = {
            "model": self.model_name,
            "messages": messages,
            "temperature": 0.0,
            "max_tokens": 2048,
        }
        if self.dry_run:
            raise RuntimeError("LiteLLM Seam Not Invoked", kwargs)

        extra_kwargs: Dict[str, Any] = {}
        api_base = os.getenv("AICREDITS_BASE_URL")
        api_key = os.getenv("AICREDITS_API_KEY")
        if api_base:
            extra_kwargs["api_base"] = api_base
            extra_kwargs["custom_llm_provider"] = "openai"
        if api_key:
            extra_kwargs["api_key"] = api_key

        tools = [
            {
                "type": "function",
                "function": {
                    "name": "search",
                    "description": "Search documents by a query string. Returns matching document IDs, titles, and snippets.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "Search query string"}
                        },
                        "required": ["query"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "lookup",
                    "description": "Look up full text of a document by doc_id.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "doc_id": {"type": "string", "description": "Document ID"}
                        },
                        "required": ["doc_id"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "calc",
                    "description": "Perform basic integer arithmetic expression (+ - *).",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "expression": {"type": "string", "description": "Arithmetic expression"}
                        },
                        "required": ["expression"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "answer",
                    "description": "Provide the final answer and cited document ID.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "answer": {"type": "string", "description": "Final answer"},
                            "cited_source": {"type": "string", "description": "Document ID containing the fact"}
                        },
                        "required": ["answer", "cited_source"],
                    },
                },
            },
        ]

        resp = None
        max_attempts = 5
        for attempt in range(max_attempts):
            try:
                resp = litellm.completion(
                    model=self.model_name,
                    messages=messages,
                    tools=tools,
                    temperature=0.0,
                    max_tokens=2048,
                    **extra_kwargs,
                )
                break
            except Exception as e:
                err_str = str(e).lower()
                is_rate_limit = "429" in err_str or "rate" in err_str or "limit" in err_str or "timeout" in err_str
                if attempt < max_attempts - 1 and is_rate_limit:
                    sleep_time = (0.5 * (2 ** attempt)) + (0.1 * attempt)
                    time.sleep(sleep_time)
                else:
                    raise e

        msg = resp.choices[0].message
        thought = msg.content or getattr(msg, "reasoning_content", "") or ""
        
        if getattr(msg, "tool_calls", None) and len(msg.tool_calls) > 0:
            tc = msg.tool_calls[0]
            fn_name = tc.function.name
            try:
                fn_args = json.loads(tc.function.arguments) if tc.function.arguments else {}
            except Exception:
                fn_args = {}
                
            raw_tc = tc.model_dump() if hasattr(tc, "model_dump") else (tc if isinstance(tc, dict) else {"id": getattr(tc, "id", "call_0"), "type": "function", "function": {"name": fn_name, "arguments": tc.function.arguments}})
            
            if fn_name == "answer":
                ans = fn_args.get("answer")
                src = fn_args.get("cited_source") or fn_args.get("doc_id") or ""
                return ModelResponse(
                    thought=thought,
                    answer=str(ans) if ans is not None else "",
                    cited_sources=[str(src)] if src else [],
                    raw_tool_call=raw_tc
                )
            elif fn_name in ["search", "lookup", "calc"]:
                return ModelResponse(
                    thought=thought,
                    tool_call={"tool": fn_name, **fn_args},
                    raw_tool_call=raw_tc
                )

        if msg.content:
            try:
                data = json.loads(msg.content.strip())
                if isinstance(data, dict):
                    if "answer" in data:
                        src = data.get("cited_source") or data.get("doc_id") or ""
                        return ModelResponse(thought=thought, answer=str(data["answer"]), cited_sources=[str(src)] if src else [])
                    elif "tool" in data:
                        return ModelResponse(thought=thought, tool_call=data)
            except Exception:
                pass
                
        return ModelResponse(thought=thought, answer=None, tool_call=None)

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
