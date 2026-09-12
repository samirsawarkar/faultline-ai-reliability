# FAULTLINE Technical Case Study PDF Generator

This directory contains the complete LaTeX source documents, converted vector figures, and build automation used to generate the definitive technical portfolio case study:

```text
FAULTLINE_AI_Reliability_Engineering_Case_Study.pdf
```

## 1. Document Specifications
- **Title:** FAULTLINE: Engineering Reliability Under Controlled Failure
- **Subtitle:** A Reproducible Reliability Workbench for Document-Grounded AI Systems
- **Author:** Samir Sawarkar
- **Document Version:** 1.0.0 (Definitive Technical Portfolio Edition)
- **Target Page Count:** 48 pages (strictly bounded under 50 pages)
- **Design System:** Professional staff-engineering whitepaper format; Helvetica/Inconsolata typography; custom TikZ architecture diagrams and control flows; vector PDF figures; tabularx/booktabs data tables; status indicators and claim tags.

---

## 2. Directory Layout
```text
report/
  ├── figures/                     # Vector PDF figures converted from SVGs
  │   ├── fig1_depth.pdf           # Q1 Tool depth compounding
  │   ├── fig2_detector.pdf        # Q2 Detector recall & miss audit
  │   ├── fig3_retry.pdf           # Q3 Retry crossover under correlation
  │   ├── fig4_fallback.pdf        # Q4 Fallback quality vs availability
  │   ├── fig5_policy.pdf          # Q5 Policy Pareto frontier & stress attacks
  │   ├── p01_baseline.pdf         # P01 baseline dress rehearsal
  │   ├── p02_otel.pdf             # P02 OpenTelemetry GenAI traces
  │   ├── p13_slo.pdf              # P13 SRE multi-burn-rate evaluation
  │   ├── p15_resilience.pdf       # P15 Agent resilience & load shedding
  │   └── p16_policy.pdf           # P16 Zero-detector runtime policy
  ├── main.tex                     # Master LaTeX document (preamble, styling, TOC)
  ├── sec01_executive_summary.tex  # 01 Executive Summary, Thesis, Three Enemies
  ├── sec02_reliability_problem.tex# 02 Reliability Problem & 03 Architecture Diagram
  ├── sec04_principles_boundary.tex# 04 Design Principles & 05 System Boundary
  ├── sec06_core_architecture.tex  # 06 Deterministic World, 07 Oracle, 08 Agent
  ├── sec09_faults_observability.tex# 09 Taxonomy, 10 Injection, 11 Tracing, 12 Detection
  ├── sec13_recovery_engineering.tex# 13 Recovery Mechanisms, Matrix, P15, P16
  ├── sec14_methodology_statistics.tex# 14 Methodology, 15 Statistics, 16 Judge, 17 Repro
  ├── sec18_experiment_results.tex # 18 Standardized Q1-Q5 Results & Figures
  ├── sec19_30day_built.tex        # 19 30-Day Progression Table & 20 Component Inventory
  ├── sec21_phase2_decisions.tex   # 21 Phase 2 State/Hypotheses & 22 ADR Table
  ├── sec23_failures_limitations.tex# 23 What Failed, 24 Limitations, 25 Threat Model
  ├── sec26_framework_lessons.tex  # 26 Decision Framework & 27 Engineering Lessons
  ├── sec28_interview_version.tex  # 28 Interview Walkthroughs & 15 Deep Q&As
  ├── sec29_repo_reproduce_index.tex# 29 Repo Map, 30 Repro, 31 Index, 32 Roadmap, 33 Assessment
  └── README.md                    # This file
```

---

## 3. How the PDF is Generated

### Step 1: Figure Conversion (SVG $\to$ Vector PDF)
All original SVG figures from `day28/evidence/figures/` and `projects/*/figure.svg` are converted to vector PDF using `pymupdf` to preserve 100% vector fidelity:
```bash
/opt/homebrew/bin/python3 -c "
import os, pymupdf
os.makedirs('report/figures', exist_ok=True)
svg_files = [
    ('day28/evidence/figures/figure-1-depth-reliability.svg', 'report/figures/fig1_depth.pdf'),
    ('day28/evidence/figures/figure-2-detector-recall.svg', 'report/figures/fig2_detector.pdf'),
    ('day28/evidence/figures/figure-3-retry-crossover.svg', 'report/figures/fig3_retry.pdf'),
    ('day28/evidence/figures/figure-4-fallback-quality.svg', 'report/figures/fig4_fallback.pdf'),
    ('day28/evidence/figures/figure-5-policy-frontier.svg', 'report/figures/fig5_policy.pdf'),
    ('projects/p01_baseline/figure.svg', 'report/figures/p01_baseline.pdf'),
    ('projects/p02_otel_exporter/figure.svg', 'report/figures/p02_otel.pdf'),
    ('projects/p13_slo_incident/figure.svg', 'report/figures/p13_slo.pdf'),
    ('projects/p15_resilience/figure.svg', 'report/figures/p15_resilience.pdf'),
    ('projects/p16_runtime_policy/figure.svg', 'report/figures/p16_policy.pdf'),
]
for src, dst in svg_files:
    if os.path.exists(src):
        doc = pymupdf.open(src)
        pdfbytes = doc.convert_to_pdf()
        out = pymupdf.open('pdf', pdfbytes)
        out.save(dst)
"
```

### Step 2: LaTeX Compilation
Compile the master document using `pdflatex` (two passes to resolve the table of contents, cross-references, and figure numbers):
```bash
cd report
/Users/samir/Library/TinyTeX/bin/universal-darwin/pdflatex -interaction=nonstopmode main.tex
/Users/samir/Library/TinyTeX/bin/universal-darwin/pdflatex -interaction=nonstopmode main.tex
```

### Step 3: Copy to Root Portfolio Artifact
```bash
cp report/main.pdf ../FAULTLINE_AI_Reliability_Engineering_Case_Study.pdf
```

---

## 4. Verification and Quality Audit Checklist
- [x] **Page Budget:** Exactly 48 pages (strictly under 50 pages).
- [x] **Zero Errors:** Clean compilation with exit code 0.
- [x] **Honesty & Integrity:** All Phase 1 results bound to committed JSON pointers; Phase 2 clearly labeled as completed foundation with unrun paid model sweeps ($0 spent).
- [x] **Complete Scope:** Covers all 33 required engineering sections without truncation.
- [x] **Vector Quality:** All 10 figures embedded as native vector PDFs.
- [x] **Defense Alignment:** Verbatim answers matching the recorded oral defense guide in `day30/evidence/mock-defense-transcript.md`.
