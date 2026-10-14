# Functional, technical and integration requirements (FTIR)

## Functional

| ID | Requirement | Status | Evidence |
|---|---|---|---|
| F-01 | Score any rule result with the GOV.UK issues framework | Done | `tests/` FrameworkMatchesGovUk (8 tests) |
| F-02 | 15 check types covering the six DAMA UK dimensions | Done | `dqkit/rules.py` |
| F-03 | Inclusion checks: unknown or defaulted characteristics, quality gaps between groups | Done | `not_unknown`, `group_disparity` |
| F-04 | DQAP template rows (Rules section and Data Issues Log) | Done | `to_dqap_csv` |
| F-05 | W3C DQV JSON-LD output | Done | `dqv.py` |
| F-06 | Export to Great Expectations and R validate | Done (unsupported checks listed, not dropped) | `exporters.py` |
| F-07 | Assess catalogue records against DAM, CDA, NDL, DQAP, FAIR and inclusion criteria | Done | `metadata.py` (20 checks, 13 properties) |
| F-08 | Plain-English CLI summaries | Done | `cli.py` |
| F-09 | Web form for non-technical users | Not started | Backlog |

## Technical

| ID | Requirement | Status |
|---|---|---|
| T-01 | Python 3.10+; pandas, PyYAML, jsonschema only | Done |
| T-02 | No network access at run time | Done |
| T-03 | Deterministic: an `--as-of` date fixes all time-based checks | Done |
| T-04 | Unit tests run in CI | Done (`.github/workflows/ci.yml`; 21 tests) |
| T-05 | Generated vocabulary files stay in sync with the CSV source | Done (CI diff check) |
| T-06 | JSON Schema validates the example record | Done |
| T-07 | SHACL validated with pySHACL | Pending: RDF tooling was unavailable in the build environment |

## Integration

| ID | Requirement | Status |
|---|---|---|
| I-01 | DQV JSON-LD loadable by DCAT catalogues | Ready; not yet tested against a live catalogue |
| I-02 | Dataverse columns for the departmental return | Mapping designed (see ARCHITECTURE.md LLD) |
| I-03 | Purview: map rules to Purview data quality rules | Not started |
| I-04 | Proposal to the cross-government metadata exchange model | Drafted (docs/outreach/co-cddo-metadata-model-proposal.md); not submitted |
| I-05 | NDL page template fields | Recommended in assessments/ndl/REPORT.md |
