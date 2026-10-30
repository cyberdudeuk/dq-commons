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
| F-10 | Filled-in DQAP workbook matching the published templates | Done | `workbook.py`; test `test_workbook_tabs` |
| F-11 | Trust level that says how data may be used (IOPC) | Done | `trust.py`; 3 tests |
| F-12 | Route for internal or external data (decision tree) | Done | `pathway.py`; test |
| F-13 | Trend over repeated measurements (DQAP step 9; Defra Annex 3) | Done | `--history` |
| F-14 | Where each control belongs: source, pipeline or reporting | Done | `control_point`; test |
| F-15 | Issue ageing, overdue escalation and recurrence (GDS DQ Week metrics) | Done | `operations.py`; test |
| F-16 | Draft case study in the GDS template, with no personal data | Done | `casestudy.py`; test |
| F-17 | Survey analysis with personal data removed | Done | `survey.py`; test on made-up data |
| F-18 | Measure a portfolio of assets on a schedule, with history and escalation | Done | `dqkit run`; `tests/test_pipeline.py` |
| F-19 | Draft a starter rules file from a data file | Done | `dqkit suggest`; test on all 8 charts |
| F-20 | CDA return rows from measured results | Done | `cdareturn.py`; test |
| F-21 | One portal for all data quality work, built from the latest results | Done | `build_dq_portal.py`; `tests/test_portal.py` |
| F-22 | Check data in the browser without uploading it, with the same answers as Python | Done | `engine.js`; 30-case parity check |
| F-23 | Weekly automated run with GitHub issues for escalations | Built, untested on GitHub | `dq-pipeline.yml`; structure tested |

## Technical

| ID | Requirement | Status |
|---|---|---|
| T-01 | Python 3.10+; pandas, PyYAML, jsonschema only | Done |
| T-02 | No network access at run time | Done |
| T-03 | Deterministic: an `--as-of` date fixes all time-based checks | Done |
| T-04 | Unit tests run in CI | Done (`.github/workflows/ci.yml`; 60 tests) |
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

## v1.0.0 additions
- **F-30** Grouped navigation and guided tour on every page with a tour; Escape closes; focus returns to the opener.
- **F-31** Home search across pages, frameworks and scenarios.
- **F-32** Maturity self-assessment: 8 themes x 5 levels, results with radar chart and table alternative, next steps; stored only in the browser.
- **F-33** Frameworks: filterable registry, crosswalk matrix, benchmarking, packs, clause table with gap filter.
- **F-34** AI assistant: tools validate_rules, run_rules, list_checks, describe_data, find_frameworks, crosswalk, score_issue; validation loop up to 2 retries; deterministic suggester when AI is unavailable.
- **F-35** Community: contributions to a moderated queue; personal data patterns blocked before saving; wishlist with up to 5 votes per member; moderation panel for editors.
- **F-36** Surveys: privacy notice first; one response per member, editable; totals with suppression under 5; commission requests.
- **T-10** Every page passes: no script errors, no sideways scroll at 390 px, labelled controls, no heading skips, contrast 4.5:1 (3:1 large), no hidden panel visible.
- **I-10** Backlog sync and Confluence publish run as dry runs without secrets and exit 0.

## v1.1.0 additions
- **F-40** Contract export and import round-trips every rule (same ids and checks) and gives identical results on real data.
- **F-41** Reconciliation reports counts, missing, new, duplicate keys, totals and changed values; CLI exits 1 on differences.
- **F-42** Clause builder: choose by theme and MoSCoW, buyer name substituted, copy and download; disclaimer always included.
- **F-43** Front page carousel: pause, previous, next, dots; holds on hover and focus; static with reduced motion; hidden slides not tabbable.
- **F-44** Library: curated items, knowledge base reader by URL fragment, members' items, moderated publishing. Media: blog reader, vlog and podcast lists, submissions require captions or transcript for video and audio.
- **F-45** Benchmark: opt-in, groups under 5 hidden, editors publish.
- **T-11** Every knowledge file has a review within 12 months; every internal link in the knowledge base resolves to a page.

## v1.2 requirements

- **F-40** Weave a record from DCAT, schema.org, CKAN or ODCS into all four, with gaps and CDA coverage, in Python and the browser with identical results.
- **F-41** Validate an ODCS contract and classify changes between versions as breaking or not; suggest the semantic version.
- **F-42** Create one GitHub issue per backlog item, idempotently.
- **F-43** Contact the team without any email address being published or required.
- **T-20** Content health report fails on personal or sensitive data, mismatched claims and overdue reviews.
- **R-10** No personal details in the colophon, commits or contact routes.
- **I-20** MCP tools `weave_metadata` and `check_contract` are read-only.

## v1.3 requirements

- **F-50** Explore any concept and its relationships; trace the shortest path between two concepts.
- **F-51** Glossary, thesaurus, data dictionary, taxonomies, ontology and lineage views from one source.
- **F-52** Events in list and month views, with .ics downloads and moderated submissions.
- **F-53** Skills check against a role's target level, with a downloadable development plan.
- **F-54** What's new drawer and menu flags from one release record.
- **T-30** Every graph relationship type is declared in the ontology; no dangling links; one connected graph.
- **T-31** The committed build bundle matches the documents.
- **I-30** MCP tool `explore_knowledge` is read-only.

## v1.4 requirements
| ID | Requirement | Type | Met by |
|---|---|---|---|
| F-140 | Show 8 playbook stages with steps, outputs, checklist, RACI, clauses, inclusion check and toolkit link | Functional | `playbook.html` |
| F-141 | Remember checklist ticks per browser only; clear on request | Functional | localStorage `dqc.playbook` |
| F-142 | Download blank CSV templates (6) through the artifact downloads capability or a browser download | Functional | `playbook.html#templates` |
| T-140 | Playbook document generated from YAML; CI fails if stale | Technical | `scripts/build_playbook_doc.py --check` |
| T-141 | Verification states yes, partly, unpublished; health counter accepts any YAML quoting | Technical | `scripts/self_check.py`, `tests/test_packs.py` |
| I-140 | Playbook stages linked into the knowledge graph as a lineage flow | Integration | `knowledge/ontology.yaml` |
