with open("tests/phase2/test_w1_2_loop.py", "r") as f:
    code = f.read()

code = code.replace("OutcomeStatus.SOLVED", "OutcomeStatus.ANSWERED")

with open("tests/phase2/test_w1_2_loop.py", "w") as f:
    f.write(code)
