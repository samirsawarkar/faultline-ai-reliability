import re

with open("faultline_p2/agent/contracts.py", "r") as f:
    code = f.read()

# Add tier to ScenarioTask
if "tier: str" not in code:
    code = code.replace("prompt: str = Field(min_length=1)", "prompt: str = Field(min_length=1)\n    tier: str = \"\"")
    with open("faultline_p2/agent/contracts.py", "w") as f:
        f.write(code)

