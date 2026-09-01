import re

with open("faultline_p2/agent/tools.py", "r") as f:
    code = f.read()

old_search = """        for d in self._docs:
            title_n = _norm(d["title"])
            text_n = _norm(d["text"])"""

new_search = """        for d in self._docs:
            title_n = _norm(d["title"].replace(d["id"], ""))
            text_n = _norm(d["text"].replace(d["id"], ""))"""

code = code.replace(old_search, new_search)

with open("faultline_p2/agent/tools.py", "w") as f:
    f.write(code)
