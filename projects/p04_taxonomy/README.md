# Project P4 — Failure Taxonomy (Human Open Coding)

> **Contract Note (`PHASE2-BUILD.md`):**
> P4 is an **owner-only** manual qualitative analysis project ($0 compute). The agent provides only trace-viewing tools and export helpers. Model-generated failure taxonomies are strictly forbidden.

---

## 1. Trace Viewer & Coding Tools

### Interactive Trace Inspection
```bash
# View traces filtered by status/tier
.venv/bin/python projects/p04_taxonomy/viewer.py --failed-only --tier T3

# View a specific scenario trace in detail
.venv/bin/python projects/p04_taxonomy/viewer.py --scenario s-0042
```

### Exporting Coding Sheet
```bash
.venv/bin/python projects/p04_taxonomy/export_sheet.py
```
This generates:
- `projects/p04_taxonomy/coding_sheet.csv`
- `projects/p04_taxonomy/coding_sheet.md`

---

## 2. Methodology & Workflow

1. **Open Coding**:
   - Inspect each failed trace end-to-end.
   - Record the first deviation / root failure in plain, unconstrained natural language.
2. **Axial Coding**:
   - Cluster open coding observations into 5–8 mutually exclusive, rigorous binary failure modes.
   - Author clear definitions, positive/negative examples, and boundary rules.
3. **Saturation Check**:
   - Verify that examining additional traces introduces no new failure modes.
4. **Hypothesis H2 Verification**:
   - Compare discovered empirical modes against the Phase 1 injected catalog (F1–F6) to determine whether $\ge 2$ modes are genuinely absent from the simulation catalog.

---

## 3. Deliverables

- `coding_sheet.csv` / `coding_sheet.md`: Annotated human coding notes across real traces.
- `DECISIONS.md`: Finalized axial mode definitions, boundary rules, saturation evidence, and H2 resolution.
- `results.json`: Summary statistics of mode prevalence across the evaluated trace set.
