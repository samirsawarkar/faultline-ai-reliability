import sys
from pathlib import Path

# Make `faultline_agent` and `_agent_testkit` importable when pytest is run from
# anywhere. Shared helpers live in _agent_testkit (not here) so they can be
# imported by name without colliding with other days' conftest in a root run.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
