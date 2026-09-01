import re

prompt = "Step 1: What is the archival reference of Umbra Systems? Step 2: The organization holding archival reference from Step 1 is affiliated with a partner organization. What is the external auditor of that partner organization? Step 3: The organization holding external auditor from Step 2 is affiliated with a partner organization. What is the external auditor of that partner organization? Provide the final answer for Step 3."

steps = re.split(r'Step \d+: ', prompt)[1:]
if not steps:
    # T1 prompt
    steps = [prompt]
else:
    steps[-1] = steps[-1].split(" Provide the final answer")[0]

print(steps)

step1_match = re.search(r"What is the (.*) of (.*?)\?", steps[0])
print(step1_match.groups())

text = "The archival reference of Umbra Systems is Rune-4016."
ans_match = re.search(r"The .* of .* is (.*?)\.", text)
print(ans_match.group(1))

link_text = "Affiliation record: The organization holding archival reference Rune-4016 is officially affiliated with Nexa Corp."
link_match = re.search(r"is officially affiliated with (.*?)\.", link_text)
print(link_match.group(1))
