from faultline_p2.env.corpus import build_corpus
from faultline_p2.agent.model import StubModel
from faultline_p2.agent.agent import run_agent
from faultline_p2.agent.contracts import ScenarioTask, OutcomeStatus

corpus = build_corpus()
env = {"documents": corpus.documents}
model = StubModel(behavior="solver", scenarios=corpus.scenarios)

for sc in corpus.scenarios:
    task = ScenarioTask(task_id=sc.scenario_id, prompt=sc.prompt, tier=sc.tier)
    outcome = run_agent(task, env, model, step_cap=12)
    if outcome.answer != sc.final_answer:
        print(f"FAILED on {sc.scenario_id} {sc.tier}")
        print("Prompt:", sc.prompt)
        print("Expected:", sc.final_answer)
        print("Got:", outcome.answer)
        for t in outcome.trace:
            print("Step", t.index)
            if t.tool_call:
                print("Tool call:", t.tool_call.model_dump())
            if t.observation:
                print("Obs snippet:", t.observation.model_dump().get("candidates", [{}])[0].get("snippet"))
        break
