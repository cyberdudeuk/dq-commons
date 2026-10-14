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
