import re

with open("faultline_p2/agent/contracts.py", "r") as f:
    code = f.read()

# Propose minimum change to DOC_ID_PATTERN: allow link documents
code = code.replace('DOC_ID_PATTERN = r"^doc-\d{4}$"', 'DOC_ID_PATTERN = r"^(doc-\d{4}|link-[a-f0-9]{12})$"')

# Replace ArchiveSumTask with ScenarioTask
old_task = """class ArchiveSumTask(BaseModel):
    \"\"\"Sum the numeric part of each named entity's archival reference.

    Deliberately multi-hop: every entity costs one `search` + one `lookup`, and
    the finishing `calc` costs one more. Step demand = 2*len(entities) + 1, which
    is what lets us drive a task *over budget* on demand (see experiment_budget).
    \"\"\"
    model_config = _STRICT
    task_id: str = Field(min_length=1)
    kind: Literal["archive_sum"] = "archive_sum"
    entities: List[str] = Field(min_length=1, max_length=64)"""

new_task = """class ScenarioTask(BaseModel):
    model_config = _STRICT
    task_id: str = Field(min_length=1)
    prompt: str = Field(min_length=1)"""

code = code.replace(old_task, new_task)

with open("faultline_p2/agent/contracts.py", "w") as f:
    f.write(code)
