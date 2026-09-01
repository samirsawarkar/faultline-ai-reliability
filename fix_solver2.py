import re

with open("faultline_p2/agent/model.py", "r") as f:
    code = f.read()

import re

# We will replace the solver logic
start_idx = code.find('if self.behavior == "solver":')
end_idx = code.find('if self.behavior == "hard_failure":')

new_logic = """if self.behavior == "solver":
            if len(messages) == 2:
                prompt = messages[1]["content"]
                m = re.search(r"What is the .*? of (.*?)\?", prompt)
                if m:
                    return ModelResponse(tool_call={"tool": "search", "query": m.group(1)})
            else:
                last_tool_msg = messages[-1]["content"]
                result = json.loads(last_tool_msg)
                if result.get("tool") == "search" and result.get("candidates"):
                    cand = result["candidates"][0]
                    snippet = cand.get("snippet", "")
                    
                    m_affil = re.search(r"is officially affiliated with (.*?)\.", snippet)
                    if m_affil:
                        return ModelResponse(tool_call={"tool": "search", "query": m_affil.group(1)})
                    
                    prompt = messages[1]["content"]
                    steps = re.split(r'Step \d+: ', prompt)
                    steps = steps[1:] if len(steps) > 1 else [prompt]
                    
                    current_searches = len([m for m in messages if m["role"] == "assistant" and m.get("tool_calls")])
                    step_idx = current_searches // 2
                    if step_idx < len(steps):
                        m_attr = re.search(r"What is the (.*?) of", steps[step_idx])
                        if m_attr:
                            attr = m_attr.group(1)
                            m_fact = re.search(r"The " + re.escape(attr) + r" of .*? is (.*?)\.", snippet)
                            if m_fact:
                                ans = m_fact.group(1)
                                expected_searches = 1 if len(steps) == 1 else len(steps) * 2 - 1
                                if current_searches >= expected_searches:
                                    return ModelResponse(answer=ans, cited_sources=[cand["doc_id"]])
                                else:
                                    return ModelResponse(tool_call={"tool": "search", "query": ans})
            return ModelResponse(answer="Solver failed to parse", cited_sources=[])

        """

code = code[:start_idx] + new_logic + code[end_idx:]

with open("faultline_p2/agent/model.py", "w") as f:
    f.write(code)
