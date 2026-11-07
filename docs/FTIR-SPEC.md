# Functional, technical and integration requirements (FTIR)

## Functional

| ID | Requirement | Status | Evidence |
|---|---|---|---|
| F-01 | Score any rule result with the GOV.UK issues framework | Done | `tests/` FrameworkMatchesGovUk (8 tests) |
| F-02 | 17 check types covering the six DAMA UK dimensions, including identifiers and outliers | Done | `dqkit/rules.py` |
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
| I-04 | Proposal to the cross-government metadata exchange model | Drafted and held privately; not submitted |
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

## v1.5 requirements
| ID | Requirement | Type | Met by |
|---|---|---|---|
| F-150 | Create a playbook workspace without overwriting existing files | Functional | `dqkit playbook init` |
| F-151 | Report each stage as done, in progress or to do from evidence files and checklist ticks, and name the next step | Functional | `dqkit playbook status` |
| F-152 | Download a progress report from the playbook page | Functional | `playbook.html` |
| I-150 | MCP tool `playbook`; workspace paths confined to the server folder | Integration | `dqkit/mcp_server.py` |
| T-150 | Portal and bundle published to GitHub Pages on push to main | Technical | `pages.yml` |
| T-151 | Tags create releases only if listed in the release record; versions tested to agree | Technical | `release.yml`, `tests/test_playbook.py` |

## v1.6 requirements
| ID | Requirement | Type | Met by |
|---|---|---|---|
| F-160 | Show needs, decisions, risks, measures, routes and affecting gaps for 13 roles (23 from v2.9.0, see F-290); remember the chosen role | Functional | `roles.html` |
| F-161 | Build a CDO Council brief from current effort scenarios and portfolio results; download as Markdown | Functional | Withdrawn in 2.0.0 (held privately) |
| F-162 | Filter the gap register by status, severity and affected role | Functional | `roles.html#gaps` |
| F-163 | Rate Q-FAIR per asset with reasons; never infer missing fields | Functional | `dqkit/qfair.py` |
| I-160 | CDA return carries 11 new columns (Q-FAIR fields, ratings, confidence) | Integration | `dqkit/cdareturn.py` |
| I-161 | MCP tool `estimate_effort`; `check_data` returns Q-FAIR | Integration | `dqkit/mcp_server.py` |
| T-160 | Effort model has one source; Python and browser agree on a known case | Technical | `knowledge/effort.yaml`, tests |

## v2.8 and v2.9 requirements
| ID | Requirement | Type | Met by |
|---|---|---|---|
| F-280 | Site map, Ask the Commons, Use the Commons your way, Share on every page | Functional | `sitemap.html`, `ask.html`, `reuse.html`, shell |
| I-280 | Read-only open data API, releases feed and sitemap built with the portal | Integration | `api/`, `feed.xml`, `sitemap.xml` |
| F-290 | Show 23 roles (13 everyday, 10 change and delivery) grouped in the picker; F-160 updated | Functional | `roles.html`, `knowledge/stakeholders.yaml` |
| F-291 | Change lifecycle with gate questions, a RACI with one accountable role per activity, a service blueprint and journeys | Functional | `roles.html#change`, `knowledge/change-delivery.yaml` |
| F-292 | Data management wheel: 11 knowledge areas, audience views, maturity overlay, lifecycle, records frameworks, join-up plan download | Functional | `wheel.html`, `knowledge/dama-wheel.yaml` |
| F-293 | Feedback routes on every page, including a Microsoft Form when its link is configured; no names or emails | Functional | shell feedback strip, `build.html#feedback`, `knowledge/feedback.yaml` |
| I-290 | Microsoft Form question set as a Word document for Quick import | Integration | `downloads/dq-commons-feedback-form-questions.docx` |
| T-290 | Mappings, RACI, blueprint and feedback checked by tests | Technical | `tests/test_wheel_change_feedback.py` |

## v2.10 requirements
| ID | Requirement | Type | Met by |
|---|---|---|---|
| F-300 | Standards catalogue of open standards for data, digital, cyber and technology, with GOV.UK status, Rosetta concepts, Weaver support and links to sister portals; filterable | Functional | `interop.html#catalogue`, `knowledge/standards-catalogue.yaml` |
| F-301 | Metadata Weaver writes metadata quality as W3C DQV; identical in Python and JavaScript | Functional | `dqkit/weaver.py`, `engine.js`, `weaver.html`, `dqkit weave --to dqv` |
| F-302 | Comparison of the three portals, lineage map operable by keyboard, trace one thing, journeys and join-up plan | Functional | `ecosystem.html`, `knowledge/ecosystem.yaml` |
| I-300 | Cross-reference manifest with shared keys (DAMA areas, roles, standards, pages) for sister portals | Integration | `api/xref.json`; reads the playbooks' `data/xref.json` |
| I-301 | "Continue in a sister portal" links on pages where a journey moves on | Integration | `related_elsewhere()` in the build |
| T-300 | Catalogue fields, Rosetta completeness, DQV output and cross-portal ids checked by tests; no internal workbook names published | Technical | `tests/test_ecosystem_standards.py` |

## v2.11 requirements
| ID | Requirement | Type | Met by |
|---|---|---|---|
| F-310 | Introduce the Commons to prospective consumers and recruit a research panel without storing contact details in public | Functional | `research.html`, `knowledge/research.yaml` |
| F-311 | Research bundle for email: invitation, email file, consent, sign-up questions, session guides, zip | Functional | `downloads/research/`, `research_bundle()` |
| F-312 | Open roadmap: pipeline, objectives, Now/Next/Later with capacity, published scores, what-if weights, tracing, strategy anchors | Functional | `roadmap.html`, `knowledge/roadmap.yaml` |
| I-310 | Wishlist votes and backlog issues from GitHub shown beside the scores | Integration | `github_live()` |
| T-310 | Every open item scored; MoSCoW matches score band; sign-up privacy; bundle has no addresses | Technical | `tests/test_research_roadmap.py` |

## v2.13 requirements
| ID | Requirement | Type | Met by |
|---|---|---|---|
| F-330 | Turn one rules file into the native rules of the major platforms, offline, listing anything not exported | Functional | `connectors.html#weave`, `dqkit/weaves.py`, `DQ.weaves` |
| F-331 | Directory of the vendors in the Gartner Magic Quadrant and Forrester Wave for data quality, and related catalogues and platforms, with sourced facts | Functional | `connectors.html#directory`, `knowledge/vendors.yaml` |
| F-332 | Each vendor's AI agent and MCP offerings for cataloguing and metadata | Functional | `connectors.html#ai` |
| F-333 | Crosswalk of Commons checks against platform rule types | Functional | `connectors.html#crosswalk`, `weaves.crosswalk()` |
| I-330 | Weaves from the command line and the Commons MCP server | Integration | `dqkit export --to`, `weave_rules` |
| I-331 | Vendor GitHub repositories confirmed monthly | Integration | `scripts/check_vendor_repos.py`, link-check workflow |
| T-330 | Weaves, crosswalk, vendor data and parity tested | Technical | `tests/test_weaves.py`, `scripts/parity_check.py` |

## v2.12 requirements
| ID | Requirement | Type | Met by |
|---|---|---|---|
| F-320 | Routes to contribute, join working groups and champion the Commons; a communications kit; badges with code for GitHub, social media and email signatures | Functional | `getinvolved.html`, `knowledge/participation.yaml`, `badges/`, `downloads/getinvolved/` |
| F-321 | Governance bodies with purpose, aims, outcomes, rules of engagement and terms-of-reference status; question routes | Functional | `governance.html`, `knowledge/governance-bodies.yaml` |
| F-322 | Display options: text size, spacing, readable font, colours including high contrast, reduced movement | Functional | shell |
| F-323 | Every outside link labelled by kind of source | Functional | shell, `guide.html#sources` |
| F-324 | Journeys that continue across the three portals | Functional | `ecosystem.html#journeys`, shell |
| I-320 | Evidence from public code imported from the repos catalogue open edition | Integration | `scripts/import_code_evidence.py` |
| I-321 | DAM requirement ids per playbook stage, published in the manifest | Integration | `api/xref.json` |
| T-320 | Governance, participation, badges, code evidence, requirement links and shell features tested | Technical | `tests/test_participation_governance.py` |
