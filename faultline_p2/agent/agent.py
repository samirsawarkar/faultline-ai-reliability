from typing import Dict, Any, List
from .contracts import (
    ScenarioTask, AgentOutcome, OutcomeStatus, AgentStep, 
    TOOL_CALL_ADAPTER, ToolCall, ToolResult
)
from .tools import ToolBox
from .model import ModelInterface, ModelResponse

def run_agent(
    task: ScenarioTask, 
    env: Dict[str, Any], 
    model: ModelInterface, 
    step_cap: int = 8
) -> AgentOutcome:
    toolbox = ToolBox(env)
    
    # We maintain messages to send to the model
    # System prompt will be added here
    messages = [
        {"role": "system", "content": "SYSTEM PROMPT"},
        {"role": "user", "content": task.prompt}
    ]
    
    trace: List[AgentStep] = []
    
    for step_idx in range(1, step_cap + 1):
        try:
            response = model.generate(messages)
        except Exception as e:
            return AgentOutcome(
                task_id=task.task_id,
                status=OutcomeStatus.MODEL_FAILURE,
                steps_used=step_idx - 1,
                step_cap=step_cap,
                reason=f"Model failure: {str(e)}",
                trace=trace
            )
            
        if response.answer is not None:
            # Answer produced
            return AgentOutcome(
                task_id=task.task_id,
                status=OutcomeStatus.SOLVED,
                answer=response.answer,
                cited_sources=response.cited_sources,
                steps_used=step_idx - 1,
                step_cap=step_cap,
                trace=trace
            )
            
        if response.tool_call is None:
            # Malformed output (no answer and no tool call)
            return AgentOutcome(
                task_id=task.task_id,
                status=OutcomeStatus.MALFORMED,
                steps_used=step_idx - 1,
                step_cap=step_cap,
                reason="Malformed model output: missing answer and tool call",
                trace=trace
            )
            
        # Parse and execute tool call
        try:
            call_obj = TOOL_CALL_ADAPTER.validate_python(response.tool_call)
        except Exception as e:
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
            # Tool error
            return AgentOutcome(
                task_id=task.task_id,
                status=OutcomeStatus.TOOL_ERROR,
                steps_used=step_idx - 1,
                step_cap=step_cap,
                reason=f"Tool error: {str(e)}",
                trace=trace
            )
            
        # Add to trace
        trace.append(AgentStep(
            index=step_idx,
            thought=response.thought,
            tool_call=call_obj,
            observation=result,
            action_type="tool"
        ))
        
        # Append to messages for next turn
        messages.append({
            "role": "assistant",
            "content": response.thought,
            "tool_calls": [response.tool_call]
        })
        messages.append({
            "role": "tool",
            "content": result.model_dump_json()
        })
        
    return AgentOutcome(
        task_id=task.task_id,
        status=OutcomeStatus.STEP_CAP,
        steps_used=step_cap,
        step_cap=step_cap,
        reason="Step cap reached",
        trace=trace
    )
