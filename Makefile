# FAULTLINE developer entry points. `make test` is the one-command gate.
#
# Day 1 is stdlib-only; Day 2+ needs pydantic. `make venv` builds a local
# .venv from the pinned requirements so a fresh clone runs in two commands:
#   make venv && make test
#
# All targets run from the repo root with a relative interpreter path, so the
# repo works even when checked out under a directory whose name contains spaces.
PY := ./.venv/bin/python

.PHONY: help venv test test-day1 test-day2 test-day3 test-day4 test-day5 test-day6 test-day7 test-day8 determinism attack \
        day3-baseline day3-attack day4-traces day5-evidence day6-replay day7-q1 day8-inject evidence clean

help:
	@echo "make venv          create .venv and install pinned deps"
	@echo "make test          run the full gate (day1 … day7)"
	@echo "make determinism   re-prove Day 1 cross-process determinism"
	@echo "make attack        re-run the Day 2 over-budget termination attack"
	@echo "make day3-baseline rebuild the Day 3 baseline.json + figure"
	@echo "make day3-attack   re-run the Day 3 mislabeled-input attack"
	@echo "make day4-traces   regenerate Day 4 traces + 100-run failure report"
	@echo "make day5-evidence rebuild the Day 5 store, viewer, SVG + attack report"
	@echo "make day6-replay   regenerate Day 6 replay bundle + difference report"
	@echo "make day7-q1       regenerate Day 7 Q1 results + measured-vs-naive figure"
	@echo "make day8-inject   regenerate Day 8 fault-injection evidence"
	@echo "make evidence      regenerate all committed evidence artifacts"
	@echo "make clean         remove caches"

venv:
	python3 -m venv .venv
	$(PY) -m pip install --upgrade pip
	$(PY) -m pip install -r requirements.txt

test: test-day1 test-day2 test-day3 test-day4 test-day5 test-day6 test-day7 test-day8

test-day1:
	$(PY) -m pytest day1/tests/ -q

test-day2:
	$(PY) -m pytest day2/tests/ -q

test-day3:
	$(PY) -m pytest day3/tests/ -q

test-day4:
	$(PY) -m pytest day4/tests/ -q

test-day5:
	$(PY) -m pytest day5/tests/ -q

test-day6:
	$(PY) -m pytest day6/tests/ -q

test-day7:
	$(PY) -m pytest day7/tests/ -q

test-day8:
	$(PY) -m pytest day8/tests/ -q

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

day5-evidence:
	$(PY) day5/scripts/make_evidence.py

day6-replay:
	$(PY) day6/scripts/make_evidence.py

day7-q1:
	$(PY) day7/scripts/run_q1.py

day8-inject:
	$(PY) day8/scripts/make_evidence.py

evidence:
	$(PY) day1/scripts/experiment_determinism.py
	$(PY) day2/scripts/experiment_budget.py
	$(PY) day2/scripts/run_agent.py
	$(PY) day2/scripts/schema_vs_semantic.py
	$(PY) day3/scripts/build_baseline.py
	$(PY) day3/scripts/attack_mislabeled.py
	$(PY) day4/scripts/make_traces.py
	$(PY) day5/scripts/make_evidence.py
	$(PY) day6/scripts/make_evidence.py
	$(PY) day7/scripts/run_q1.py
	$(PY) day8/scripts/make_evidence.py

clean:
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
	find . -type d -name .pytest_cache -prune -exec rm -rf {} +
