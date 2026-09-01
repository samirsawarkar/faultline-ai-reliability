import re

with open("faultline_p2/agent/agent.py", "r") as f:
    code = f.read()

# Rename SOLVED to ANSWERED
code = code.replace("OutcomeStatus.SOLVED", "OutcomeStatus.ANSWERED")

# Record the answer step
old_answer_block = """        if response.answer is not None:
            # Answer produced
            return AgentOutcome(
                task_id=task.task_id,
                status=OutcomeStatus.ANSWERED,
                answer=response.answer,
                cited_sources=response.cited_sources,
                steps_used=step_idx - 1,
                step_cap=step_cap,
                trace=trace
            )"""

new_answer_block = """        if response.answer is not None:
            # Answer produced
            trace.append(AgentStep(
                index=step_idx,
                thought=response.thought,
                action_type="answer"
            ))
            return AgentOutcome(
                task_id=task.task_id,
                status=OutcomeStatus.ANSWERED,
                answer=response.answer,
                cited_sources=response.cited_sources,
                steps_used=step_idx,
                step_cap=step_cap,
                trace=trace
            )"""

code = code.replace(old_answer_block, new_answer_block)

with open("faultline_p2/agent/agent.py", "w") as f:
    f.write(code)
