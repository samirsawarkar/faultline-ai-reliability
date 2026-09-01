from faultline_p2.env.corpus import build_corpus
from faultline_p2.agent.model import StubModel
from faultline_p2.agent.agent import run_agent
from faultline_p2.agent.contracts import ScenarioTask

corpus = build_corpus()
sc = corpus.scenarios[0]
print(sc.prompt)
print("Expected:", sc.final_answer)

env = {"documents": corpus.documents}
model = StubModel(behavior="solver")
task = ScenarioTask(task_id=sc.scenario_id, prompt=sc.prompt, tier=sc.tier)
outcome = run_agent(task, env, model, step_cap=12)
for t in outcome.trace:
    print(t.model_dump())
