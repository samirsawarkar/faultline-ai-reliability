# FAULTLINE developer entry points. `make test` is the one-command gate.
#
# Day 1 is stdlib-only; Day 2+ needs pydantic. `make venv` builds a local
# .venv from the pinned requirements so a fresh clone runs in two commands:
#   make venv && make test
#
# All targets run from the repo root with a relative interpreter path, so the
# repo works even when checked out under a directory whose name contains spaces.
PY := ./.venv/bin/python

.PHONY: help venv test test-day1 test-day2 test-day3 test-day4 determinism attack \
        day3-baseline day3-attack day4-traces evidence clean

help:
	@echo "make venv          create .venv and install pinned deps"
	@echo "make test          run the full gate (day1 + day2 + day3 + day4)"
	@echo "make determinism   re-prove Day 1 cross-process determinism"
	@echo "make attack        re-run the Day 2 over-budget termination attack"
	@echo "make day3-baseline rebuild the Day 3 baseline.json + figure"
	@echo "make day3-attack   re-run the Day 3 mislabeled-input attack"
	@echo "make day4-traces   regenerate Day 4 traces + 100-run failure report"
	@echo "make evidence      regenerate all committed evidence artifacts"
	@echo "make clean         remove caches"

venv:
	python3 -m venv .venv
	$(PY) -m pip install --upgrade pip
	$(PY) -m pip install -r requirements.txt

test: test-day1 test-day2 test-day3 test-day4

test-day1:
	$(PY) -m pytest day1/tests/ -q

test-day2:
	$(PY) -m pytest day2/tests/ -q

test-day3:
	$(PY) -m pytest day3/tests/ -q

test-day4:
	$(PY) -m pytest day4/tests/ -q

determinism:
	$(PY) day1/scripts/experiment_determinism.py

attack:
	$(PY) day2/scripts/experiment_budget.py

day3-baseline:
	$(PY) day3/scripts/build_baseline.py

day3-attack:
	$(PY) day3/scripts/attack_mislabeled.py

day4-traces:
	$(PY) day4/scripts/make_traces.py

evidence:
	$(PY) day1/scripts/experiment_determinism.py
	$(PY) day2/scripts/experiment_budget.py
	$(PY) day2/scripts/run_agent.py
	$(PY) day2/scripts/schema_vs_semantic.py
	$(PY) day3/scripts/build_baseline.py
	$(PY) day3/scripts/attack_mislabeled.py
	$(PY) day4/scripts/make_traces.py

clean:
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
	find . -type d -name .pytest_cache -prune -exec rm -rf {} +
