import re

with open("faultline_p2/agent/model.py", "r") as f:
    code = f.read()

code = code.replace("""                prompt = messages[1]["content"]
                m1 = re.search(r"What is the .*? of (.*?)\\?", prompt)
                m2 = re.search(r"In which district is (.*?) headquartered\\?", prompt)
                m3 = re.search(r"Which firm is the external auditor of (.*?)\\?", prompt)""",
"""                prompt = messages[1]["content"]
                step1 = re.split(r'Step \d+: ', prompt)
                step1 = step1[1] if len(step1) > 1 else prompt
                m1 = re.search(r"What is the .*? of (.*?)\\?", step1)
                m2 = re.search(r"In which district is (.*?) headquartered\\?", step1)
                m3 = re.search(r"Which firm is the external auditor of (.*?)\\?", step1)""")

with open("faultline_p2/agent/model.py", "w") as f:
    f.write(code)
