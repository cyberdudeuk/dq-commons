# Build journal

## 2026-10-14 — v0.1.0 first release

**What was built**
- **`dqkit`:**
  - The GOV.UK issues framework, implemented exactly.
  - 15 check types, including 2 inclusion checks.
  - A metadata assessment with 20 checks against published requirements.
  - DQV JSON-LD, DQAP CSV, Great Expectations and R validate outputs.
  - A command line.
- **Vocabulary:** 8 dimensions and 43 issue types, in CSV, SKOS Turtle and JSON-LD.
- **Metadata model extension (proposal):** LinkML, JSON Schema, SHACL and an example.
- **NDL assessment:**
  - 84 curated pages harvested from data.gov.uk and assessed.
  - 8 chart data files checked with 49 rules.
  - Report and dashboard data.
- **Documentation:** PRD, theory of change, architecture, FTIR spec, user research bundle, screening, decisions and outreach drafts.
- **CI:** a GitHub Actions workflow.

**Checked**
- 21 unit tests pass, including the issues framework's worked example and its Table 4 bands.
- The JSON Schema is valid, and the example validates against it.
- The CLI commands run end to end.

**Not done / limits**
- SHACL is not machine-validated, because no RDF tooling was available in the build environment.
- LinkML generators were not run, so the JSON Schema and SHACL are hand-written.
- GitHub push is pending: this session has no repository attached for write access.
- Not tested with users.

## 2026-10-14 (later) — artefacts published and portal updated
- Published the NDL Collections Assurance artifact. Added a status table to the DQ Tooling Atlas, and a "with dqkit" option to the CDA effort model.
- Portal v2.1.0: `scripts/portal_add_pages.py` adds two pages and updates the menu on all 20 pages.
- Copied the research note into `docs/DQ_TOOLING_RESEARCH.md`.

## 2026-10-14 (evening) — v0.2.0 existing guidance built in
**Trigger:** 7 documents shared by the project lead:
- Issues Framework v1.0
- DQAP Implementation Guide v2.0
- Defra "Start here"
- IOPC trust scales
- the 2023 decision tree
- NHS England's Quality Framework for Data Science
- the DQ community note

**Built**
- **`docs/GUIDANCE-CROSSWALK.md` and a crosswalk page** with a live issues-framework calculator. It found 9 contradictions and errors, including an arithmetic slip in v1.0 Tables 7 and 8 (96.75% where the stated rule gives 96.25%).
- **`framework.py`:**
  - target policies low, mid and high, with low as the default (D-021)
  - error rates in words ("1 in 40 records")
  - tests reproducing the v1.0 tables
- **`trust.py`:** IOPC-style trust level (D-022). **`pathway.py`:** decision-tree route (D-023).
- **`workbook.py`:** a filled-in 10-tab DQAP workbook, plus run history (D-024). The Causes tab has an addressability column, from Defra.
- **Vocabulary:** 3 ESS "plus" dimensions (relevance, coherence and comparability, accessibility and clarity). **Model:** `trust_level`.
- **NDL rule files:** marked as external data with no influence. Assessment re-run; DQAP workbooks written for all 8 charts.
- **Portal v2.2.0:** new "DQ guidance crosswalk" page; NDL assurance page shows trust levels.

**Checked:** 30 tests pass. The model schema and example are valid. New pages have no errors and no sideways scroll at 1280 px or 400 px.

**Privacy:** the source documents name individuals. No names are copied into any output (D-013).
