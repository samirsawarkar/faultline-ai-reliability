import pytest
from faultline_p2.env.corpus import build_corpus
from faultline_p2.agent.model import StubModel
from faultline_p2.agent.agent import run_agent
from faultline_p2.agent.contracts import ScenarioTask, OutcomeStatus
from faultline_p2.oracle._day01_oracle import oracle_check

def test_solver_all_scenarios():
    corpus = build_corpus()
    env = {"documents": corpus.documents}
    model = StubModel(behavior="solver", scenarios=corpus.scenarios)
    
    tier_steps = {"T1": [], "T2": [], "T3": []}
    tier_tokens = {"T1": {"prompt": 0, "completion": 0}, "T2": {"prompt": 0, "completion": 0}, "T3": {"prompt": 0, "completion": 0}}
    total_tool_calls = 0
    
    for sc in corpus.scenarios:
        task = ScenarioTask(task_id=sc.scenario_id, prompt=sc.prompt, tier=sc.tier)
        outcome = run_agent(task, env, model, step_cap=12)
        assert outcome.status == OutcomeStatus.ANSWERED, f"Scenario {sc.scenario_id} failed: {outcome.reason}"
        verdict = oracle_check({'id': sc.scenario_id, 'answer': sc.final_answer, 'required_source': sc.required_source}, {'answer': outcome.answer, 'cited_sources': outcome.cited_sources})
        assert verdict['passed'], f'Oracle failed for {sc.scenario_id}: {verdict}'
        
        
        tier_steps[sc.tier].append(outcome.steps_used)
        total_tool_calls += (outcome.steps_used - 1)  # the last step is 'answer'
        
    print(f"\nSteps Used Distribution (average):")
    for t in ["T1", "T2", "T3"]:
        avg = sum(tier_steps[t]) / len(tier_steps[t]) if tier_steps[t] else 0
        print(f"{t}: ~{avg:.1f} steps")
    print(f"Total Tool Calls: {total_tool_calls}")

