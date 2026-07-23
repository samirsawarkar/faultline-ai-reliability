# FAULTLINE developer entry points. `make test` is the one-command gate.
#
# Day 1 is stdlib-only; Day 2+ needs pydantic. `make venv` builds a local
# .venv from the pinned requirements so a fresh clone runs in two commands:
#   make venv && make test
#
# All targets run from the repo root with a relative interpreter path, so the
# repo works even when checked out under a directory whose name contains spaces.
PY := ./.venv/bin/python

.PHONY: help venv test test-day01 test-day02 test-day03 test-day04 test-day05 test-day06 test-day07 test-day08 test-day09 test-day10 test-day11 test-day12 test-day13 test-day14 determinism attack \
        day03-baseline day03-attack day04-traces day05-evidence day06-replay day07-q1 day08-inject day09-detect day10-contracts day11-spectrum day12-catalog day13-eval day14-stats evidence clean

help:
	@echo "make venv          create .venv and install pinned deps"
	@echo "make test          run the full gate (day01 … day14)"
	@echo "make determinism   re-prove Day 1 cross-process determinism"
	@echo "make attack        re-run the Day 2 over-budget termination attack"
	@echo "make day03-baseline rebuild the Day 3 baseline.json + figure"
	@echo "make day03-attack   re-run the Day 3 mislabeled-input attack"
	@echo "make day04-traces   regenerate Day 4 traces + 100-run failure report"
	@echo "make day05-evidence rebuild the Day 5 store, viewer, SVG + attack report"
	@echo "make day06-replay   regenerate Day 6 replay bundle + difference report"
	@echo "make day07-q1       regenerate Day 7 Q1 results + measured-vs-naive figure"
	@echo "make day08-inject   regenerate Day 8 fault-injection evidence"
	@echo "make day09-detect   regenerate Day 9 detector sweep + scored runs"
	@echo "make day10-contracts regenerate Day 10 contract report + false negatives"
	@echo "make day11-spectrum regenerate Day 11 spectrum map + Q2 hypothesis"
	@echo "make day12-catalog regenerate Day 12 fault catalog + gallery + audit"
	@echo "make day13-eval    run the Day 13 versioned eval on the test split"
	@echo "make day14-stats   regenerate Day 14 stats verification + paired comparison"
	@echo "make evidence      regenerate all committed evidence artifacts"
	@echo "make clean         remove caches"

venv:
	python3 -m venv .venv
	$(PY) -m pip install --upgrade pip
	$(PY) -m pip install -r requirements.txt

test: test-day01 test-day02 test-day03 test-day04 test-day05 test-day06 test-day07 test-day08 test-day09 test-day10 test-day11 test-day12 test-day13 test-day14

test-day01:
	$(PY) -m pytest day01/tests/ -q

test-day02:
	$(PY) -m pytest day02/tests/ -q

test-day03:
	$(PY) -m pytest day03/tests/ -q

test-day04:
	$(PY) -m pytest day04/tests/ -q

test-day05:
	$(PY) -m pytest day05/tests/ -q

test-day06:
	$(PY) -m pytest day06/tests/ -q

test-day07:
	$(PY) -m pytest day07/tests/ -q

test-day08:
	$(PY) -m pytest day08/tests/ -q

test-day09:
	$(PY) -m pytest day09/tests/ -q

test-day10:
	$(PY) -m pytest day10/tests/ -q

test-day11:
	$(PY) -m pytest day11/tests/ -q

test-day12:
	$(PY) -m pytest day12/tests/ -q

test-day13:
	$(PY) -m pytest day13/tests/ -q

test-day14:
	$(PY) -m pytest day14/tests/ -q

determinism:
	$(PY) day01/scripts/experiment_determinism.py

attack:
	$(PY) day02/scripts/experiment_budget.py

day03-baseline:
	$(PY) day03/scripts/build_baseline.py

day03-attack:
	$(PY) day03/scripts/attack_mislabeled.py

day04-traces:
	$(PY) day04/scripts/make_traces.py

day05-evidence:
	$(PY) day05/scripts/make_evidence.py

day06-replay:
	$(PY) day06/scripts/make_evidence.py

day07-q1:
	$(PY) day07/scripts/run_q1.py

day08-inject:
	$(PY) day08/scripts/make_evidence.py

day09-detect:
	$(PY) day09/scripts/make_evidence.py

day10-contracts:
	$(PY) day10/scripts/make_evidence.py

day11-spectrum:
	$(PY) day11/scripts/make_evidence.py

day12-catalog:
	$(PY) day12/scripts/make_evidence.py

day13-eval:
	$(PY) day13/scripts/eval.py --split test

day14-stats:
	$(PY) day14/scripts/make_evidence.py

evidence:
	$(PY) day01/scripts/experiment_determinism.py
	$(PY) day02/scripts/experiment_budget.py
	$(PY) day02/scripts/run_agent.py
	$(PY) day02/scripts/schema_vs_semantic.py
	$(PY) day03/scripts/build_baseline.py
	$(PY) day03/scripts/attack_mislabeled.py
	$(PY) day04/scripts/make_traces.py
	$(PY) day05/scripts/make_evidence.py
	$(PY) day06/scripts/make_evidence.py
	$(PY) day07/scripts/run_q1.py
	$(PY) day08/scripts/make_evidence.py
	$(PY) day09/scripts/make_evidence.py
	$(PY) day10/scripts/make_evidence.py
	$(PY) day11/scripts/make_evidence.py
	$(PY) day12/scripts/make_evidence.py
	$(PY) day13/scripts/make_evidence.py
	$(PY) day14/scripts/make_evidence.py

clean:
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
	find . -type d -name .pytest_cache -prune -exec rm -rf {} +
