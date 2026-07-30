# FAULTLINE developer entry points. `make test` is the one-command gate.
#
# Day 1 is stdlib-only; Day 2+ needs pydantic. `make venv` builds a local
# .venv from the pinned requirements so a fresh clone runs in two commands:
#   make venv && make test
#
# All targets run from the repo root with a relative interpreter path, so the
# repo works even when checked out under a directory whose name contains spaces.
PY ?= ./.venv/bin/python

.PHONY: help venv test test-day01 test-day02 test-day03 test-day04 test-day05 test-day06 test-day07 test-day08 test-day09 test-day10 test-day11 test-day12 test-day13 test-day14 test-day15 test-day16 test-day17 test-day18 test-day19 test-day20 test-day21 test-day22 test-day23 test-day24 test-day25 test-day26 test-day27 test-day28 determinism attack \
        day03-baseline day03-attack day04-traces day05-evidence day06-replay day07-q1 day08-inject day09-detect day10-contracts day11-spectrum day12-catalog day13-eval day13-evidence day14-stats day15-q2 day16-judge day17-subgroups day18-recovery day19-retry day20-breaker day21-q4 day22-matrix day23-cascade day24-q5 day25-postmortems \
        test-report test-fast-report eval-verify experiment-fast readme-audit day26-evidence cold-reproduce day27-audit day27-evidence day28-publication reproduce reproduce-fast container-reproduce release-check evidence clean

help:
	@echo "make venv          create .venv and install pinned deps"
	@echo "make test          run the full gate (day01 … day28)"
	@echo "make reproduce     full tests + eval + fast experiments + README audit"
	@echo "make reproduce-fast CI-sized tests + eval + deterministic experiments"
	@echo "make container-reproduce build and attest the pinned clean image"
	@echo "make cold-reproduce execute the documented clone-to-number inner gate"
	@echo "make release-check clean container plus final Checkpoint 26"
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
	@echo "make day15-q2      regenerate Day 15 Q2 per-class confusion + failures"
	@echo "make day16-judge   regenerate Day 16 judge validation + agreement/bias report"
	@echo "make day17-subgroups regenerate Day 17 subgroup report + evaluation audit"
	@echo "make day18-recovery regenerate Day 18 recovery report + traces"
	@echo "make day19-retry  regenerate Day 19 retry sweep + crossover curve"
	@echo "make day20-breaker regenerate Day 20 breaker report + state diagram + traces"
	@echo "make day21-q4      regenerate Day 21 availability/quality + detector evidence"
	@echo "make day22-matrix  regenerate Day 22 six-mechanism recovery matrix + attacks"
	@echo "make day23-cascade regenerate Day 23 seeded incident + trace + causal graph"
	@echo "make day24-q5      regenerate Day 24 policy comparison + paired Q5 evidence"
	@echo "make day25-postmortems regenerate Day 25 incidents + red-to-green replay"
	@echo "make day26-evidence assemble traceability + reproduction checkpoint"
	@echo "make day27-evidence assemble cold-reader Checkpoint 27"
	@echo "make day28-publication regenerate article figures + claim audit"
	@echo "make evidence      regenerate all committed evidence artifacts"
	@echo "make clean         remove caches"

venv:
	python3 -m venv .venv
	$(PY) -m pip install pip==26.0.1
	$(PY) -m pip install -r requirements.txt

test: test-day01 test-day02 test-day03 test-day04 test-day05 test-day06 test-day07 test-day08 test-day09 test-day10 test-day11 test-day12 test-day13 test-day14 test-day15 test-day16 test-day17 test-day18 test-day19 test-day20 test-day21 test-day22 test-day23 test-day24 test-day25 test-day26 test-day27 test-day28

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

test-day15:
	$(PY) -m pytest day15/tests/ -q

test-day16:
	$(PY) -m pytest day16/tests/ -q

test-day17:
	$(PY) -m pytest day17/tests/ -q

test-day18:
	$(PY) -m pytest day18/tests/ -q

test-day19:
	$(PY) -m pytest day19/tests/ -q

test-day20:
	$(PY) -m pytest day20/tests/ -q

test-day21:
	$(PY) -m pytest day21/tests/ -q

test-day22:
	$(PY) -m pytest day22/tests/ -q

test-day23:
	$(PY) -m pytest day23/tests/ -q

test-day24:
	$(PY) -m pytest day24/tests/ -q

test-day25:
	$(PY) -m pytest day25/tests/ -q

test-day26:
	$(PY) -m pytest day26/tests/ -q

test-day27:
	$(PY) -m pytest day27/tests/ -q

test-day28:
	$(PY) -m pytest day28/tests/ -q

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

day13-evidence:
	$(PY) day13/scripts/make_evidence.py

day14-stats:
	$(PY) day14/scripts/make_evidence.py

day15-q2:
	$(PY) day15/scripts/make_evidence.py

day16-judge:
	$(PY) day16/scripts/make_evidence.py

day17-subgroups:
	$(PY) day17/scripts/make_evidence.py

day18-recovery:
	$(PY) day18/scripts/make_evidence.py

day19-retry:
	$(PY) day19/scripts/make_evidence.py

day20-breaker:
	$(PY) day20/scripts/make_evidence.py

day21-q4:
	$(PY) day21/scripts/make_evidence.py

day22-matrix:
	$(PY) day22/scripts/make_evidence.py

day23-cascade:
	$(PY) day23/scripts/make_evidence.py

day24-q5:
	$(PY) day24/scripts/make_evidence.py

day25-postmortems:
	$(PY) day25/scripts/make_evidence.py

test-report:
	$(PY) day26/scripts/run_test_gate.py --profile full --output day26/evidence/test_report.json

test-fast-report:
	$(PY) day26/scripts/run_test_gate.py --profile fast --output day26/evidence/fast_test_report.json

eval-verify:
	$(PY) day26/scripts/verify_eval.py

experiment-fast:
	$(PY) day26/scripts/run_fast_experiments.py

readme-audit:
	$(PY) day26/scripts/audit_readme.py

day26-evidence:
	$(PY) day26/scripts/make_evidence.py

day27-audit:
	$(PY) day27/scripts/audit_reproduction.py

day27-evidence:
	$(PY) day27/scripts/make_evidence.py

day28-publication:
	$(PY) day28/scripts/make_evidence.py

cold-reproduce:
	sh day27/scripts/cold_reproduce.sh

reproduce: test-day28 day28-publication test-report eval-verify experiment-fast readme-audit day27-audit
	$(PY) day26/scripts/make_evidence.py --allow-missing-container

reproduce-fast: test-day28 day28-publication test-fast-report eval-verify experiment-fast readme-audit day27-audit
	$(PY) day26/scripts/make_evidence.py --allow-missing-container

container-reproduce:
	$(PY) day26/scripts/container_reproduce.py

release-check: container-reproduce day26-evidence

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
	$(PY) day15/scripts/make_evidence.py
	$(PY) day16/scripts/make_evidence.py
	$(PY) day17/scripts/make_evidence.py
	$(PY) day18/scripts/make_evidence.py
	$(PY) day19/scripts/make_evidence.py
	$(PY) day20/scripts/make_evidence.py
	$(PY) day21/scripts/make_evidence.py
	$(PY) day22/scripts/make_evidence.py
	$(PY) day23/scripts/make_evidence.py
	$(PY) day24/scripts/make_evidence.py
	$(PY) day25/scripts/make_evidence.py
	$(PY) day26/scripts/make_evidence.py
	$(PY) day27/scripts/make_evidence.py
	$(PY) day28/scripts/make_evidence.py

clean:
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
	find . -type d -name .pytest_cache -prune -exec rm -rf {} +
