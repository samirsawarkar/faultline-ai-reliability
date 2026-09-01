import re
snippet = "The headquarters district of Dovetail Foundry is Talc-4643."
attr = "headquarters district"
m_fact = re.search(r"The " + re.escape(attr) + r" of .*? is (.*?)\.", snippet)
print(m_fact.groups())
