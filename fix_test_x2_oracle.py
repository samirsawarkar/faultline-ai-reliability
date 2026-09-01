with open("tests/phase2/test_x2_solver.py", "r") as f:
    code = f.read()

if "oracle_check" not in code:
    code = code.replace("from faultline_p2.agent.contracts import ScenarioTask, OutcomeStatus",
    "from faultline_p2.agent.contracts import ScenarioTask, OutcomeStatus\nfrom faultline_p2.oracle._day01_oracle import oracle_check")
    
    code = code.replace("assert outcome.answer == sc.final_answer",
    "verdict = oracle_check({'id': sc.scenario_id, 'answer': sc.final_answer, 'required_source': sc.required_source}, {'answer': outcome.answer, 'cited_sources': outcome.cited_sources})\n        assert verdict['passed'], f'Oracle failed for {sc.scenario_id}: {verdict}'")
    code = code.replace("assert sc.required_source in outcome.cited_sources", "")

    with open("tests/phase2/test_x2_solver.py", "w") as f:
        f.write(code)
