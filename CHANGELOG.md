# Changelog

Releases and version numbers come from `knowledge/releases.yaml`, which also feeds the portal's What's new drawer. Semantic versioning: major for breaking changes to files, identifiers or links; minor for new features and pages; patch for fixes and content.

## 1.6.0 — 2026-10-30
### Added
- `roles.html` (For your role) from `knowledge/stakeholders.yaml`: 13 roles with needs, decisions, what to watch, measures and routes; key dates (confirmed or to confirm); a CDO Council brief built from live effort scenarios and the portfolio's Q-FAIR picture, downloadable as Markdown; a gap register of 20 gaps (9 addressed, 7 partly, 4 open) with filters.
- `dqkit/qfair.py`: Good / Improving / Attention required for Quality, Findable, Accessible, Interoperable and Reusable, with reasons, from measured results and the asset record only.
- CDA return columns: `gds_accessroute`, `gds_conformsto`, `gds_licence`, `gds_provenance`, `gds_qfair_*` (5 areas and overall), `gds_baselineconfidence`. `dqkit check` prints the Q-FAIR line; MCP `check_data` returns it.
- `knowledge/effort.yaml` and `dqkit/effort.py`; `dqkit effort`; MCP tool `estimate_effort` (14 tools).
- Baseline page: Q-FAIR fields in the minimum entry set and a self-rating; a Q-FAIR effort row.
- `tests/test_roles_qfair_effort.py` (8 tests), including Python and portal agreement on the effort model.
### Changed
- The baseline page reads its activities from `knowledge/effort.yaml`.
- Glossary and thesaurus: Q-FAIR, data quality baseline (graph: 470 concepts).

## 1.5.0 — 2026-10-30
### Added
- `dqkit/playbook.py` and `dqkit playbook init | status | guide`: a workspace per critical data asset (6 CSV templates, a checklist README, a status file) and an evidence-based status that reads the register, rules, `dqkit check` results, DQV, history and review files.
- MCP tool `playbook` (13 tools); workspace paths are kept inside the server's folder.
- Playbook page: progress report download (Markdown) and the toolkit commands.
- `.github/workflows/pages.yml` publishes the portal and bundle to GitHub Pages; `.github/workflows/release.yml` and `scripts/release_notes.py` turn version tags into GitHub releases.
- `tests/test_playbook.py`.
### Fixed
- Three playbook steps containing "word: text" were parsed as mappings and showed as "[object Object]"; quoted, and the playbook test now checks every step, checklist item and output is text.
- Version drift: `pyproject.toml` (was 1.1.0), `dqkit.__version__` (was 0.1.0) and the MCP server (was 1.2.0) now match the release record, enforced by a test.

## 1.4.0 — 2026-10-30
### Added
- Data quality management playbook for critical data assets (`playbook.html`, `knowledge/playbook.yaml`, `docs/DQ-MANAGEMENT-PLAYBOOK.md`): 7 principles, 8 stages (identify, define, baseline, prioritise, fix at source, report, sustain, annual review), each with steps, outputs, a checklist you can tick, RACI, UK DAM policy and DQAP clauses, comparable frameworks elsewhere, an inclusion check and a toolkit route. Rhythm, escalation, measures, 6 downloadable CSV templates, 7 inclusion checks and a finder for 11 jurisdictions. Generic: a terms table maps it to any mandate.
- `scripts/build_playbook_doc.py` (with `--check` in CI) keeps the document and the page in step.
- Horizon scan (October 2026), 10 new library items and 2 home page slides, each read at source: GDS guidance on AI-ready datasets, National Data Library growth, OSR 2025/26 forward look, NHS Scotland data quality strategy, ODCS v3.1.0, ODPS v1.0.0, CEN/CLC/TS 18331:2026, prEN 18352 (draft), EMA data quality framework and US H.R. 9341.
- Playbook cycle as a lineage flow in the knowledge graph (468 concepts, 1,092 relationships).
### Changed
- All 86 previously unverified sources checked; framework cards show the date checked; two frameworks with no public document are labelled "Not publicly available" and can be filtered.
- Notes added: Open Standards Board recommendations (RFC 4180 and OpenAPI 3, not CSVW); ICO accuracy guidance under review after the Data (Use and Access) Act 2025; 2020 news item marked historical.
### Fixed
- Links and dimension mappings corrected during verification; duplicate library title; empty-link warnings in content health.

## 1.3.0 — 2026-10-15
### Added
- Knowledge map page: glossary (39 terms), ISO 25964-style thesaurus, data dictionary with an entity relationship diagram, taxonomies, ontology (23 classes, 27 relationship types) and an interactive knowledge graph of 460 concepts and over 1,000 relationships, with a trail, path finder, lineage diagrams and framework-to-evidence traceability.
- `dqkit/graph.py`, `dqkit graph` (export, find, trace), MCP tool `explore_knowledge`; `vocab/knowledge-graph.ttl` and `.jsonld` (SKOS and OWL, linked to the published quality vocabulary).
- Events page: verified events and recurring events, list and month views, filters, accessibility notes, .ics downloads, moderated submissions.
- Skills and training page: 10 skills aligned with DDaT, a skills check against each role's target level, a downloadable development plan and a catalogue of 13 courses, pathways, qualifications and guidance (free first).
- Commons logo and favicon; "What is a Commons?" panel on the home page.
- What's new drawer with collapsible releases and New, Changed and Fixed flags; New and Updated flags in menus; releases on Help us build this.
- Solution build and development bundle (`scripts/build_bundle.py`, `docs/bundle/index.html`), also published as a standalone page.
### Changed
- The version number now comes from `knowledge/releases.yaml`.

## 1.2.1 — 2026-10-15
### Added
- Framework packs for the UN National Quality Assurance Framework (`un-nqaf`) and the IMF Data Quality Assessment Framework (`imf-dqaf`), linked from UK and the world and the international scenarios (BL-16, XDMH-230).
- Content provenance on every page: when its content was last reviewed and by which role (BL-21).
- Weekly content health run keeps one GitHub issue open for owning roles while there are findings (BL-19).
- Accessibility workflow with axe-core on every page, desktop light and phone dark (`scripts/a11y_check.mjs`, BL-18). First run will be on GitHub.
- Architecture: v1.2 solution, high-level (diagram) and low-level design.
### Changed
- Retired the March 2026 legacy IT news slide (over 6 months old, flagged by the content health check); added a slide for the new packs.

## 1.2.0 — 2026-10-15
### Added
- Metadata Weaver (`dqkit weave`, `dqkit/weaver.py`, browser port, portal page, MCP tool `weave_metadata`): reads DCAT, schema.org, CKAN or ODCS; writes all four; reports gaps, fields a standard can't carry, and the 13 CDA metadata properties.
- Contract change control: `validate_odcs`, `diff_odcs` (breaking changes and semantic version), `dqkit contract-check`, MCP tool `check_contract`; ODCS export carries SLA and support channels.
- UK and the world page and `knowledge/global.yaml`: Crown Dependencies, 14 Overseas Territories, the Commonwealth, and 18 international and supranational frameworks, bodies and networks. Surveys, scenarios, search and contribution forms include them.
- Help us build this page and `knowledge/build.yaml`: roadmap, 24-item MoSCoW backlog, wishlist and votes (moved from Community), co-design methods, charter, house rules, guidelines, safeguards, contributors, GitHub resources, self-checking routines and a contact form with in-app replies and no published email.
- `CHARTER.md`, `CODE_OF_CONDUCT.md`, `CONTRIBUTORS.md` and `.all-contributorsrc`, generated or kept in step with the portal.
- `scripts/backlog_to_issues.py` and the Backlog to issues workflow: one GitHub issue per backlog item, idempotent.
- `scripts/self_check.py` and the Content health workflow; a trust panel on Help us build this.
- GOV.UK blog features in the media centre and on the home page; three new carousel slides.
- An icon set (`portal/src/icons.svg`) used in menus, page headings, tiles, carousel, spotlight, cards and the footer.
- Footer: licences, notices (not official, not legal advice, AI-assisted, no tracking), get involved, and a colophon without personal details.
### Changed
- Roadmap moved from About, and wishlist from Community, to Help us build this.
- Atlassian site address in `integrations/config.yaml` is now a placeholder.
- Git history authored with a GitHub no-reply address instead of a personal email.

## 1.1.0 — 2026-10-15
### Added
- Data contracts: ODCS v3, Frictionless Table Schema and W3C CSVW, export and import (`dqkit contract`, checker); Great Expectations and R validate exports in the browser; data profile; Excel, ODS, JSON and JSON Lines in the browser.
- Reconciliation of two dataset versions (`dqkit reconcile`, Legacy page).
- Govern pages: Buying and suppliers (clause builder, tender scoring), Legacy and modernisation, Interoperability and standards (with the metadata Rosetta).
- Front page carousel and spotlight; Library and knowledge base; Media centre; Accessibility and privacy page.
- Opt-in maturity benchmarking; review dates on knowledge files; monthly link checker; xAPI learning record; DDaT role mapping; MCP domain manifest.
### Fixed
- Theme colours of context banners, heading levels, carousel pause, target sizes, survey save overwriting other answers.

## 1.0.0 — 2026-10-15
### Changed
- **Renamed: Public Sector Data Quality Commons.** A general data quality hub and toolkit for the whole public sector; the NDL and DAM policy are now scenarios.
### Added
- Portal pages: About (mission, objectives, roadmap), User guide, Maturity self-assessment, AI assistant, Frameworks and standards (registry, crosswalk, benchmarking, packs, clause by clause), Learn (pathways, modules, tutorials, glossary), AI for data quality, Scenarios, Community (library, wishlist, networks, moderation), Surveys and commissions, Operating model.
- Grouped navigation, site search on the home page, and guided tours.
- Toolkit: identifier checks (NHS number, NI number, postcode, LEI, UPRN, GSS code, company, charity, school URN, ODS code); value sets; data sources (TSV, Excel, ODS, JSON, JSONL, Parquet, SQLite, SQL, CKAN); 12 framework packs; `dqkit pack` and `dqkit crosswalk`; MCP server; rule library.
- Knowledge base (`knowledge/`), AI rule-drafting evaluation set.
- GitHub issue forms, backlog sync to Jira, docs publishing to Confluence, operating model and user guide.
### Fixed
- Invalid YAML in issue forms; values lost to unquoted commas; hidden panels shown; crosswalk overflow on phones.

## 0.4.0 — 2026-10-15
### Added
- **NDL Data Quality Portal.** One separate portal for all the data quality work. `scripts/build_dq_portal.py` builds it from the latest results. New pages: home (roles, deadline, status), pipeline status, check your data (in-browser checker with a rule builder), and share and learn. Merged in: NDL assurance, January baseline, guidance and tooling.
- **Pipeline.**
  - `dqkit run PORTFOLIO` measures every asset that is due, keeps history, and writes `portfolio.json`, `escalations.json`, one DQV catalogue, a run summary and `cda-return.csv`.
  - `dqkit suggest DATA` drafts a starter rules file.
  - The weekly GitHub Actions workflow tests, measures, commits, raises escalation issues and publishes to Pages.
- **Browser engine.** A JavaScript port of the kit, with a 30-case parity check against Python.
- **CDA return export** in the proposed Dataverse columns.
- **Packaging.** `pyproject.toml` (`pip install -e .` gives a `dqkit` command).
- **Tests.** 60 in total: pipeline, portal build and parity.
### Fixed
- An empty or all-text column could make a check crash under pandas 3. The parity check found it.
- An unknown target policy now gives a plain error in both engines.
- The January baseline page now counts working days from today, not from a fixed date.

## 0.3.0 — 2026-10-14
### Added
- `control_point` on every rule (source, pipeline or reporting), from the controls model in the brief research note.
- Issue operations (`dqkit/operations.py`): defect volume, control failure rate, cycles open, overdue issues with escalation, and recurrence. A new Operations tab in the workbook.
- Workbook Issues log: control point, cycles open, escalation, recurring, source system and immediate risk. Actions tab: action type (containment, corrective, preventive) and how success will be checked.
- `--case-study`: drafts the GDS case study template (.md and .docx) from results. The NDL charts each get one.
- `dqkit survey`: reshapes and summarises the Cross-Government DQ Solutions Survey export, with personal data removed.
- `docs/SURVEY-REVIEW.md` (12 fixes before launch). Crosswalk extended to 15 sources and 18 findings.
- Illustrative escalation example (`examples/illustrative-escalation/`).

## 0.2.0 — 2026-10-14
### Added
- Filled-in DQAP Excel workbook (`--workbook`) and run history (`--history`).
- IOPC-style trust level and decision-tree DQAP route in every check summary.
- ESS "plus" dimensions, and `trust_level` in the metadata model.
- Guidance crosswalk of 9 sources, with 9 findings.
### Changed
- Default targets now use the low end of each framework range (D-021). The previous defaults are available as `target_policy: mid`.
- The Issues log now shows plain-English error rates.

## 0.1.0 — 2026-10-14
### Added
- `dqkit` rules engine, the GOV.UK issues framework, a metadata assessment, and DQV, DQAP, GX and R validate outputs.
- A cross-government issue vocabulary (43 types) and an inclusion dimension.
- A proposed DQV quality extension for the cross-government metadata exchange model.
- The NDL collections assessment (84 pages, 8 chart files) and its report.
- Documentation set and CI.


