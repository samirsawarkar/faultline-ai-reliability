import re

with open("faultline_p2/agent/model.py", "r") as f:
    code = f.read()

old_logic = """                    # Is it a fact snippet?
                    # "The X of Y is Z."
                    m_fact = re.search(r"The .*? of .*? is (.*?)\.", snippet)
                    if m_fact:
                        ans = m_fact.group(1)"""

new_logic = """                    # Is it a fact snippet?
                    # "The [attr] of [ent] is [val]."
                    # We need to find the specific attribute we are looking for.
                    # We know what we searched for (ent) or (attr from prompt).
                    # Actually, the last question asked "What is the [attr] of [ent]?"
                    # Let's extract the attr from the current step's prompt.
                    prompt = messages[1]["content"]
                    steps = re.split(r'Step \d+: ', prompt)
                    if len(steps) > 1:
                        steps = steps[1:]
                    else:
                        steps = [prompt]
                    
                    # current step index = how many searches so far / 2
                    current_searches = len([m for m in messages if m["role"] == "assistant" and m.get("tool_calls")])
                    step_idx = current_searches // 2
                    if step_idx < len(steps):
                        current_step_text = steps[step_idx]
                        m_attr = re.search(r"What is the (.*?) of", current_step_text)
                        if m_attr:
                            attr = m_attr.group(1)
                            # Now search for "The <attr> of ... is <val>."
                            m_fact = re.search(r"The " + re.escape(attr) + r" of .*? is (.*?)\.", snippet)
                            if m_fact:
                                ans = m_fact.group(1)
                                
                                expected_searches = 1 if len(steps) == 1 else len(steps) * 2 - 1
                                if current_searches >= expected_searches:
                                    return ModelResponse(answer=ans, cited_sources=[cand["doc_id"]])
                                else:
                                    return ModelResponse(tool_call={"tool": "search", "query": ans})"""

code = code.replace(old_logic, new_logic)

with open("faultline_p2/agent/model.py", "w") as f:
    f.write(code)
