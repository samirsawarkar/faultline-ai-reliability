with open("faultline_p2/agent/tools.py", "r") as f:
    code = f.read()
code = code.replace("300", "500")
code = code.replace("150", "250")
with open("faultline_p2/agent/tools.py", "w") as f:
    f.write(code)

with open("DECISIONS.md", "r") as f:
    dec = f.read()
dec = dec.replace("300 characters", "500 characters").replace("300-char", "500-char").replace("300 chars", "500 chars")
with open("DECISIONS.md", "w") as f:
    f.write(dec)
