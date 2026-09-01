with open("tests/phase2/test_x2_solver.py", "r") as f:
    code = f.read()

code = code.replace('model = StubModel(behavior="solver")', 'model = StubModel(behavior="solver", scenarios=corpus.scenarios)')

with open("tests/phase2/test_x2_solver.py", "w") as f:
    f.write(code)
