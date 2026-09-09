import time
import json
import tiktoken
from typing import Dict, Any, List, Optional
from .contracts import (
    ScenarioTask, AgentOutcome, OutcomeStatus, AgentStep, 
    TOOL_CALL_ADAPTER, ToolCall, ToolResult
)
from .tools import ToolBox
from .model import ModelInterface, ModelResponse
from faultline_p2.trace.store import TraceStore
from faultline_p2.policy import PolicyProtocol

def count_tokens(messages: List[Dict[str, Any]]) -> int:
    enc = tiktoken.get_encoding("cl100k_base")
    return len(enc.encode(json.dumps(messages)))

def run_agent(
    task: ScenarioTask, 
    env: Dict[str, Any], 
    model: ModelInterface, 
    step_cap: int = 12,
    trace_store: Optional[TraceStore] = None,
    run_id: Optional[str] = None,
    policy: Optional[PolicyProtocol] = None,
) -> AgentOutcome:
    if policy is None and isinstance(env, dict):
        policy = env.get("policy")
    toolbox = ToolBox(env)
    
    messages = [
        {"role": "system", "content": "You are a fact-finding agent..."},
        {"role": "user", "content": task.prompt}
    ]
    
    trace: List[AgentStep] = []
    
    model_name = getattr(model, "model_name", "stub")
    provider = getattr(model, "provider", "local")
    version = getattr(model, "version", "1.0")
    
    for step_idx in range(1, step_cap + 1):
        prompt_tokens = count_tokens(messages)
        start_time = time.time()
        
        try:
            response = model.generate(messages)
        except Exception as e:
            latency = (time.time() - start_time) * 1000
            if trace_store and run_id:
                trace_store.log_span(
                    run_id=run_id, scenario_id=task.task_id, tier=task.tier, step_index=step_idx,
                    model_name=model_name, provider=provider, model_version=version,
                    prompt_tokens=prompt_tokens, completion_tokens=0, latency_ms=latency,
                    termination_reason=OutcomeStatus.MODEL_FAILURE.value
                )
            return AgentOutcome(
                task_id=task.task_id,
                status=OutcomeStatus.MODEL_FAILURE,
                steps_used=step_idx - 1,
                step_cap=step_cap,
                reason=f"Model failure: {str(e)}",
                trace=trace
            )
            
        latency = (time.time() - start_time) * 1000
        completion_tokens = count_tokens([response.model_dump(exclude_none=True)])
        
        if response.answer is not None:
            trace.append(AgentStep(index=step_idx, thought=response.thought, action_type="answer"))
            if trace_store and run_id:
                trace_store.log_span(
                    run_id=run_id, scenario_id=task.task_id, tier=task.tier, step_index=step_idx,
                    model_name=model_name, provider=provider, model_version=version,
                    tool_name="answer", prompt_tokens=prompt_tokens, completion_tokens=completion_tokens,
                    latency_ms=latency, termination_reason=OutcomeStatus.ANSWERED.value
                )
            return AgentOutcome(
                task_id=task.task_id,
                status=OutcomeStatus.ANSWERED,
                answer=response.answer,
                cited_sources=response.cited_sources,
                steps_used=step_idx,
                step_cap=step_cap,
                trace=trace
            )
            
        if response.tool_call is None:
            if trace_store and run_id:
                trace_store.log_span(
                    run_id=run_id, scenario_id=task.task_id, tier=task.tier, step_index=step_idx,
                    model_name=model_name, provider=provider, model_version=version,
                    prompt_tokens=prompt_tokens, completion_tokens=completion_tokens, latency_ms=latency,
                    termination_reason=OutcomeStatus.MALFORMED.value
                )
            return AgentOutcome(
                task_id=task.task_id,
                status=OutcomeStatus.MALFORMED,
                steps_used=step_idx - 1,
                step_cap=step_cap,
                reason="Malformed model output: missing answer and tool call",
                trace=trace
            )
            
        if policy is not None:
            decision = policy.evaluate(response.tool_call, run_id=run_id, trace_store=trace_store)
            if not decision.allowed:
                trace.append(AgentStep(
                    index=step_idx,
                    thought=response.thought,
                    action_type="policy_denial"
                ))
                if trace_store and run_id:
                    tool_name = response.tool_call.get("tool", "unknown") if isinstance(response.tool_call, dict) else "unknown"
                    trace_store.log_span(
                        run_id=run_id, scenario_id=task.task_id, tier=task.tier, step_index=step_idx,
                        model_name=model_name, provider=provider, model_version=version,
                        tool_name=tool_name, prompt_tokens=prompt_tokens, completion_tokens=completion_tokens,
                        latency_ms=latency, termination_reason="policy_denial"
                    )
                messages.append({
                    "role": "assistant",
                    "content": response.thought,
                    "tool_calls": [response.tool_call]
                })
                messages.append({
                    "role": "tool",
                    "content": json.dumps({"error": f"POLICY_DENIED: [{decision.rule}] {decision.reason}"})
                })
                continue

        try:
            call_obj = TOOL_CALL_ADAPTER.validate_python(response.tool_call)
        except Exception as e:
            if trace_store and run_id:
                trace_store.log_span(
                    run_id=run_id, scenario_id=task.task_id, tier=task.tier, step_index=step_idx,
                    model_name=model_name, provider=provider, model_version=version,
                    prompt_tokens=prompt_tokens, completion_tokens=completion_tokens, latency_ms=latency,
                    termination_reason=OutcomeStatus.MALFORMED.value
                )
            return AgentOutcome(
                task_id=task.task_id,
                status=OutcomeStatus.MALFORMED,
                steps_used=step_idx - 1,
                step_cap=step_cap,
                reason=f"Malformed tool call: {str(e)}",
                trace=trace
            )
            
        try:
            result = toolbox.dispatch(call_obj)
        except Exception as e:
            if trace_store and run_id:
                trace_store.log_span(
                    run_id=run_id, scenario_id=task.task_id, tier=task.tier, step_index=step_idx,
                    model_name=model_name, provider=provider, model_version=version,
                    tool_name=call_obj.tool, prompt_tokens=prompt_tokens, completion_tokens=completion_tokens,
                    latency_ms=latency, termination_reason=OutcomeStatus.TOOL_ERROR.value
                )
            return AgentOutcome(
                task_id=task.task_id,
                status=OutcomeStatus.TOOL_ERROR,
                steps_used=step_idx - 1,
                step_cap=step_cap,
                reason=f"Tool error: {str(e)}",
                trace=trace
            )
            
        trace.append(AgentStep(
            index=step_idx, thought=response.thought, tool_call=call_obj, observation=result, action_type="tool"
        ))
        
        if trace_store and run_id:
            trace_store.log_span(
                run_id=run_id, scenario_id=task.task_id, tier=task.tier, step_index=step_idx,
                model_name=model_name, provider=provider, model_version=version,
                tool_name=call_obj.tool, prompt_tokens=prompt_tokens, completion_tokens=completion_tokens,
                latency_ms=latency, termination_reason=None
            )
        
        if response.raw_tool_call:
            raw_tc = response.raw_tool_call
            messages.append({
                "role": "assistant",
                "content": response.thought if response.thought else None,
                "tool_calls": [raw_tc],
            })
            messages.append({
                "role": "tool",
                "tool_call_id": raw_tc.get("id", f"call_{step_idx}"),
                "content": result.model_dump_json(),
            })
        else:
            messages.append({
                "role": "assistant",
                "content": response.thought,
                "tool_calls": [response.tool_call],
            })
            messages.append({
                "role": "tool",
                "tool_call_id": f"call_{step_idx}",
                "content": result.model_dump_json(),
            })
        
    # step cap
    if trace_store and run_id:
        trace_store.log_span(
            run_id=run_id, scenario_id=task.task_id, tier=task.tier, step_index=step_cap,
            model_name=model_name, provider=provider, model_version=version,
            prompt_tokens=prompt_tokens, completion_tokens=completion_tokens, latency_ms=latency,
            termination_reason=OutcomeStatus.STEP_CAP.value
        )
    return AgentOutcome(
        task_id=task.task_id,
        status=OutcomeStatus.STEP_CAP,
        steps_used=step_cap,
        step_cap=step_cap,
        reason="Step cap reached",
        trace=trace
    )
