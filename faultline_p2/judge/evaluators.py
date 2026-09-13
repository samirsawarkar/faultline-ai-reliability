"""Automated Failure Mode Evaluators (Code Assertions + LLM Judge)."""
from __future__ import annotations

import json
import os
import sqlite3
from typing import Any, Dict, List, Optional
from dotenv import load_dotenv

from faultline_p2.judge.contracts import JudgeVerdict


class EvaluatorRegistry:
    """Registry of all failure mode evaluators."""

    def __init__(self, judge_model_name: Optional[str] = None, real: bool = False):
        load_dotenv()
        self.model_name = judge_model_name or os.getenv("MODEL_R7", "z-ai/glm-5.3")
        self.real = real

    def evaluate_mode(
        self,
        mode: str,
        scenario_id: str,
        tier: str,
        trace_spans: List[sqlite3.Row],
        sweep_item: Dict[str, Any],
        corpus_scenario: Any,
    ) -> JudgeVerdict:
        """Evaluate a specific failure mode on a scenario trace."""
        # 1. Deterministic Code Assertions
        if mode == "INFRASTRUCTURE_RATE_LIMIT":
            return self._eval_rate_limit(scenario_id, trace_spans, sweep_item)
        elif mode == "INFRASTRUCTURE_SERVER_ERROR":
            return self._eval_server_error(scenario_id, trace_spans, sweep_item)
        elif mode == "MALFORMED_TOOL_CALL":
            return self._eval_malformed_tool(scenario_id, trace_spans, sweep_item)
        elif mode == "MULTI_HOP_TRAVERSAL_EXHAUSTION":
            return self._eval_traversal_exhaustion(scenario_id, tier, trace_spans, sweep_item)

        # 2. Semantic LLM Judges
        elif mode == "OVERCONSTRAINED_SEARCH_LOOP":
            return self._eval_overconstrained_search(scenario_id, trace_spans, sweep_item, corpus_scenario)
        elif mode == "RETRIEVAL_FAILURE_ABSTENTION":
            return self._eval_abstention(scenario_id, sweep_item, corpus_scenario)
        elif mode == "ANSWER_EXTRACTION_TRUNCATION":
            return self._eval_extraction_truncation(scenario_id, sweep_item, corpus_scenario)
        elif mode == "PREMATURE_STOP_WRONG_HOP":
            return self._eval_premature_wrong_hop(scenario_id, tier, trace_spans, sweep_item, corpus_scenario)
        elif mode == "MULTI_HOP_DIRECTION_ERROR":
            return self._eval_direction_error(scenario_id, tier, trace_spans, sweep_item, corpus_scenario)

        raise ValueError(f"Unknown evaluator mode: {mode}")

    def _extract_trace_queries(self, sweep_item: Dict[str, Any]) -> List[str]:
        out = sweep_item.get("output") or {}
        trace = (out.get("trace") or []) if isinstance(out, dict) else []
        queries: List[str] = []
        for step in trace:
            if not isinstance(step, dict):
                continue
            tc = step.get("tool_call")
            if isinstance(tc, dict):
                q = tc.get("query") or tc.get("entity") or tc.get("doc_id") or tc.get("field") or ""
                if q:
                    queries.append(str(q))
        return queries

    # --- Code Assertion Evaluators ---

    def _eval_rate_limit(self, sid: str, spans: List[sqlite3.Row], sweep_item: Dict[str, Any]) -> JudgeVerdict:
        detected = False
        reasoning = ""
        output = sweep_item.get("output") or {}
        status = (output.get("status") or "") if isinstance(output, dict) else ""
        reason = (output.get("reason") or "") if isinstance(output, dict) else ""

        if "RateLimitError" in reason or "429" in reason or (status == "model_failure" and "RateLimit" in reason):
            detected = True
            reasoning = "Upstream HTTP 429 rate limit error recorded in sweep output reason."
        elif any(s["termination_reason"] and "429" in str(s["termination_reason"]) for s in spans):
            detected = True
            reasoning = "HTTP 429 rate limit recorded in span termination reason."

        return JudgeVerdict(
            scenario_id=sid,
            mode="INFRASTRUCTURE_RATE_LIMIT",
            detected=detected,
            confidence=1.0,
            reasoning=reasoning,
            is_llm_judge=False,
        )

    def _eval_server_error(self, sid: str, spans: List[sqlite3.Row], sweep_item: Dict[str, Any]) -> JudgeVerdict:
        detected = False
        reasoning = ""
        output = sweep_item.get("output") or {}
        reason = (output.get("reason") or "") if isinstance(output, dict) else ""

        if "InternalServerError" in reason or "500" in reason:
            detected = True
            reasoning = "Upstream HTTP 500 internal server error recorded in sweep output reason."

        return JudgeVerdict(
            scenario_id=sid,
            mode="INFRASTRUCTURE_SERVER_ERROR",
            detected=detected,
            confidence=1.0,
            reasoning=reasoning,
            is_llm_judge=False,
        )

    def _eval_malformed_tool(self, sid: str, spans: List[sqlite3.Row], sweep_item: Dict[str, Any]) -> JudgeVerdict:
        detected = False
        reasoning = ""
        output = sweep_item.get("output") or {}
        status = (output.get("status") or "") if isinstance(output, dict) else ""
        reason = (output.get("reason") or "") if isinstance(output, dict) else ""

        if status == "malformed" or "Malformed model output" in reason:
            detected = True
            reasoning = "Model emitted unstructured text or malformed JSON tool call."
        elif any(s["termination_reason"] and "malformed" in str(s["termination_reason"]).lower() for s in spans):
            detected = True
            reasoning = "Malformed output recorded in span termination."

        return JudgeVerdict(
            scenario_id=sid,
            mode="MALFORMED_TOOL_CALL",
            detected=detected,
            confidence=1.0,
            reasoning=reasoning,
            is_llm_judge=False,
        )

    def _eval_traversal_exhaustion(self, sid: str, tier: str, spans: List[sqlite3.Row], sweep_item: Dict[str, Any]) -> JudgeVerdict:
        detected = False
        reasoning = ""
        output = sweep_item.get("output") or {}
        steps = len(spans)

        # Only on T3 5-hop where steps hit limit without rate limit or malformed failure
        if tier == "T3" and steps >= 12:
            status = (output.get("status") or "") if isinstance(output, dict) else ""
            if status != "malformed" and "RateLimit" not in str(output):
                # Check if search was progressive across hops
                unique_queries = set(self._extract_trace_queries(sweep_item))
                if len(unique_queries) >= 4:
                    detected = True
                    reasoning = f"Step cap 12 reached on 5-hop scenario T3 with {len(unique_queries)} distinct queries."

        return JudgeVerdict(
            scenario_id=sid,
            mode="MULTI_HOP_TRAVERSAL_EXHAUSTION",
            detected=detected,
            confidence=1.0,
            reasoning=reasoning,
            is_llm_judge=False,
        )

    # --- LLM Judge Evaluators ---

    def _call_llm_judge(self, rubric: str, trace_context: str):
        """Invoke LLM judge via LiteLLM with strict temperature=0.0."""
        if not self.real:
            # Offline mock judge based on prompt rubric rules
            return self._offline_judge_heuristic(rubric, trace_context)

        import litellm
        api_base = os.getenv("AICREDITS_BASE_URL")
        api_key = os.getenv("AICREDITS_API_KEY")

        messages = [
            {"role": "system", "content": rubric},
            {"role": "user", "content": trace_context},
        ]

        extra_kwargs: Dict[str, Any] = {}
        if api_base:
            extra_kwargs["api_base"] = api_base
            extra_kwargs["custom_llm_provider"] = "openai"
        if api_key:
            extra_kwargs["api_key"] = api_key

        try:
            resp = litellm.completion(
                model=self.model_name,
                messages=messages,
                temperature=0.0,
                max_tokens=512,
                **extra_kwargs,
            )
            raw_text = resp.choices[0].message.content or ""
            usage = resp.usage
            tokens = {"prompt": usage.prompt_tokens or 0, "completion": usage.completion_tokens or 0}

            # Parse JSON
            parsed = self._extract_json(raw_text)
            detected = bool(parsed.get("detected", False))
            confidence = float(parsed.get("confidence", 0.9))
            reasoning = str(parsed.get("reasoning", raw_text[:120]))
            return detected, confidence, reasoning, tokens
        except Exception as e:
            return False, 0.0, f"Judge LLM call failed: {str(e)}", {"prompt": 0, "completion": 0}

    def _extract_json(self, text: str) -> Dict[str, Any]:
        text = text.strip()
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].split("```")[0].strip()
        try:
            return json.loads(text)
        except Exception:
            # Try regex search for boolean
            detected = "true" in text.lower() and '"detected": true' in text.lower()
            return {"detected": detected, "confidence": 0.8, "reasoning": text[:100]}

    def _offline_judge_heuristic(self, rubric: str, trace_context: str):
        """Deterministic offline heuristic fallback for testing without API spend."""
        t_lower = trace_context.lower()
        if "overconstrained_search_loop" in rubric.lower() or "overconstrained search" in rubric.lower():
            detected = ("step cap" in t_lower or "steps used: 12" in t_lower) and "malformed" not in t_lower and "ratelimit" not in t_lower
            return detected, 0.95, "Deterministic heuristic: overconstrained query loop detected", {"prompt": 100, "completion": 20}
        elif "abstention" in rubric.lower():
            detected = "couldn’t verify" in t_lower or "could not verify" in t_lower or "no matching document" in t_lower
            return detected, 0.95, "Deterministic heuristic: explicit refusal abstention detected", {"prompt": 100, "completion": 20}
        elif "truncation" in rubric.lower():
            detected = "quill systems is headquartered" in t_lower or "onyx" in t_lower
            return detected, 0.95, "Deterministic heuristic: token truncation detected", {"prompt": 100, "completion": 20}
        elif "premature" in rubric.lower():
            detected = "lumen-4035" in t_lower or ("intermediate" in t_lower and "step 2" in t_lower)
            return detected, 0.90, "Deterministic heuristic: premature stopping detected", {"prompt": 100, "completion": 20}
        elif "direction" in rubric.lower():
            detected = "wisp-4021" in t_lower or "reverse" in t_lower or "backward" in t_lower
            return detected, 0.90, "Deterministic heuristic: direction error detected", {"prompt": 100, "completion": 20}

        return False, 0.5, "Offline heuristic: no pattern matched", {"prompt": 50, "completion": 10}

    def _eval_overconstrained_search(self, sid: str, spans: List[sqlite3.Row], sweep_item: Dict[str, Any], sc: Any) -> JudgeVerdict:
        rubric = (
            "You are an expert AI reliability judge evaluating agent retrieval logs. "
            "Determine whether the agent experienced an OVERCONSTRAINED_SEARCH_LOOP.\n"
            "Rule: Return detected=true IF the agent issued overly constrained, multi-word queries that returned 0 candidates, "
            "looping through reformulations until step cap exhaustion (12 steps).\n"
            "Respond ONLY with valid JSON: {\"detected\": bool, \"confidence\": float, \"reasoning\": str}"
        )
        out = sweep_item.get("output") or {}
        reason = (out.get("reason") or "") if isinstance(out, dict) else ""
        context = f"Scenario: {sid}\nPrompt: {sc.prompt if sc else ''}\nSteps Used: {len(spans)}\n"
        context += f"Termination Reason: {reason}\n"
        queries = self._extract_trace_queries(sweep_item)
        context += f"Search Queries: {queries}\n"

        detected, conf, reason_str, tokens = self._call_llm_judge(rubric, context)
        return JudgeVerdict(
            scenario_id=sid,
            mode="OVERCONSTRAINED_SEARCH_LOOP",
            detected=detected,
            confidence=conf,
            reasoning=reason_str,
            is_llm_judge=True,
            tokens_used=tokens,
        )

    def _eval_abstention(self, sid: str, sweep_item: Dict[str, Any], sc: Any) -> JudgeVerdict:
        rubric = (
            "You are an expert AI reliability judge evaluating agent answers. "
            "Determine whether the agent output represents a RETRIEVAL_FAILURE_ABSTENTION.\n"
            "Rule: Return detected=true IF the agent explicitly stated that it could not find the information, "
            "refusing/abstaining from guessing rather than providing a fabricated answer.\n"
            "Respond ONLY with valid JSON: {\"detected\": bool, \"confidence\": float, \"reasoning\": str}"
        )
        out = sweep_item.get("output") or {}
        ans = (out.get("answer") or "") if isinstance(out, dict) else ""
        context = f"Scenario: {sid}\nPrompt: {sc.prompt if sc else ''}\nAgent Output Answer: {ans}\n"

        detected, conf, reason, tokens = self._call_llm_judge(rubric, context)
        return JudgeVerdict(
            scenario_id=sid,
            mode="RETRIEVAL_FAILURE_ABSTENTION",
            detected=detected,
            confidence=conf,
            reasoning=reason,
            is_llm_judge=True,
            tokens_used=tokens,
        )

    def _eval_extraction_truncation(self, sid: str, sweep_item: Dict[str, Any], sc: Any) -> JudgeVerdict:
        rubric = (
            "You are an expert AI reliability judge. Determine whether the agent made an ANSWER_EXTRACTION_TRUNCATION error.\n"
            "Rule: Return detected=true IF the agent found and cited the correct document, but truncated the final token (e.g. emitted 'Onyx' instead of 'Onyx-4413').\n"
            "Respond ONLY with valid JSON: {\"detected\": bool, \"confidence\": float, \"reasoning\": str}"
        )
        out = sweep_item.get("output") or {}
        ans = (out.get("answer") or "") if isinstance(out, dict) else ""
        exp = sc.final_answer if sc else ""
        cited = (out.get("cited_sources") or []) if isinstance(out, dict) else []
        req = sc.required_source if sc else ""
        context = f"Scenario: {sid}\nExpected: {exp}\nAgent Answer: {ans}\nCited Sources: {cited}\nRequired Source: {req}\n"

        detected, conf, reason, tokens = self._call_llm_judge(rubric, context)
        return JudgeVerdict(
            scenario_id=sid,
            mode="ANSWER_EXTRACTION_TRUNCATION",
            detected=detected,
            confidence=conf,
            reasoning=reason,
            is_llm_judge=True,
            tokens_used=tokens,
        )

    def _eval_premature_wrong_hop(self, sid: str, tier: str, spans: List[sqlite3.Row], sweep_item: Dict[str, Any], sc: Any) -> JudgeVerdict:
        rubric = (
            "You are an expert AI reliability judge. Determine whether the agent suffered a PREMATURE_STOP_WRONG_HOP.\n"
            "Rule: Return detected=true IF on a multi-hop task (T2/T3), the agent stopped after only 1-3 steps and output an intermediate entity rather than traversing to the final hop.\n"
            "Respond ONLY with valid JSON: {\"detected\": bool, \"confidence\": float, \"reasoning\": str}"
        )
        out = sweep_item.get("output") or {}
        ans = (out.get("answer") or "") if isinstance(out, dict) else ""
        context = f"Scenario: {sid} [{tier}]\nSteps: {len(spans)}\nAgent Answer: {ans}\nExpected Answer: {sc.final_answer if sc else ''}\n"

        detected, conf, reason, tokens = self._call_llm_judge(rubric, context)
        return JudgeVerdict(
            scenario_id=sid,
            mode="PREMATURE_STOP_WRONG_HOP",
            detected=detected,
            confidence=conf,
            reasoning=reason,
            is_llm_judge=True,
            tokens_used=tokens,
        )

    def _eval_direction_error(self, sid: str, tier: str, spans: List[sqlite3.Row], sweep_item: Dict[str, Any], sc: Any) -> JudgeVerdict:
        rubric = (
            "You are an expert AI reliability judge. Determine whether the agent made a MULTI_HOP_DIRECTION_ERROR.\n"
            "Rule: Return detected=true IF the agent searched in the reverse dependency direction across multi-hop entity links.\n"
            "Respond ONLY with valid JSON: {\"detected\": bool, \"confidence\": float, \"reasoning\": str}"
        )
        queries = self._extract_trace_queries(sweep_item)
        context = f"Scenario: {sid} [{tier}]\nPrompt: {sc.prompt if sc else ''}\nSearch Queries: {queries}\n"

        detected, conf, reason, tokens = self._call_llm_judge(rubric, context)
        return JudgeVerdict(
            scenario_id=sid,
            mode="MULTI_HOP_DIRECTION_ERROR",
            detected=detected,
            confidence=conf,
            reasoning=reason,
            is_llm_judge=True,
            tokens_used=tokens,
        )
