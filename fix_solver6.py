import re

with open("faultline_p2/agent/model.py", "r") as f:
    code = f.read()

start_idx = code.find('if self.behavior == "solver":')
end_idx = code.find('if self.behavior == "hard_failure":')

new_logic = """if self.behavior == "solver":
            if len(messages) == 2:
                prompt = messages[1]["content"]
                m1 = re.search(r"What is the .*? of (.*?)\?", prompt)
                m2 = re.search(r"In which district is (.*?) headquartered\?", prompt)
                m3 = re.search(r"Which firm is the external auditor of (.*?)\?", prompt)
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
                        # Even search: looking for link
                        for cand in candidates:
                            snippet = cand.get("snippet", "")
                            m_affil = re.search(r"is officially affiliated with (.*?)\.", snippet)
                            if m_affil:
                                return ModelResponse(tool_call={"tool": "search", "query": m_affil.group(1)})
                    else:
                        # Odd search: looking for fact
                        step_idx = current_searches // 2
                        if step_idx < len(steps):
                            step_text = steps[step_idx]
                            attr = None
                            if "internal codename" in step_text: attr = "internal codename"
                            elif "flagship product" in step_text: attr = "flagship product"
                            elif "external auditor" in step_text or "Which firm is the external auditor" in step_text: attr = "external auditor"
                            elif "archival reference" in step_text: attr = "archival reference"
                            elif "In which district" in step_text or "headquarters district" in step_text: attr = "headquarters district"
                            
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

        """

code = code[:start_idx] + new_logic + code[end_idx:]

with open("faultline_p2/agent/model.py", "w") as f:
    f.write(code)
