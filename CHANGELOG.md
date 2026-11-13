# Changelog

Releases and version numbers come from `knowledge/releases.yaml`, which also feeds the portal's What's new drawer. Semantic versioning: major for breaking changes to files, identifiers or links; minor for new features and pages; patch for fixes and content.

## 2.16.0 — 2026-11-13
### Added
- `knowledge/communities.yaml`: `questions`, four answered questions on reference and master data, shown on `community.html#questions`; the proposed reference and master data special interest group.
- `knowledge/vendors.yaml`: a `mdm` group (Master and reference data) with Semarchy; vendor cards show a `public_sector` line where one is recorded.
- `knowledge/standards-catalogue.yaml`: the Person data standard (alpha); 60 standards. `knowledge/build.yaml`: Zingg and dedupe.
- Tests: answered questions are complete, use https links and hold no email address (with negative tests); every vendor group has a heading on the connectors page (with a negative test).

## 2.15.1 — 2026-11-13
### Fixed
- `knowledge/ecosystem.yaml`: the catalogue's crosswalks view is `#interop` (was `#crosswalk`, which the catalogue doesn't have), in `catalogue_views` and the Weaver's lineage. The catalogue's standards claim corrected (16 graded per repository, 41 interoperability standards; was 24), and its comparison entries updated for its 7.17 to 7.19 releases (devolved nations, procurement in Scotland and Wales, datasets that name code).
- `wheel.html` and `roles.html` follow `hashchange`, so a link to another area or role updates an open page.
### Added
- `knowledge/standards-catalogue.yaml`: Croissant (MLCommons) and LinkML, both tracked by the repos asset catalogue; 59 standards.
- Tests: every catalogue link is a view in the catalogue's own `data/xref.json` (when the catalogue is checked out alongside, with `CATALOGUE_DIR`); every "N-standard catalogue" claim equals the catalogue's length; both pages listen for `hashchange`.

## 2.15.0 — 2026-11-07
### Added
- `roadmap.html#glance`: a constellation of open backlog items (x: feasibility plus effort, y: weighted need, inclusion and alignment), shapes by MoSCoW band, with a list view.
- `portal/src/js/journey-bar.js`, published as `js/journey-bar.js`: the cross-portal journey bar as one self-contained script that sets styles on its own elements, so it works under strict Content-Security-Policies. Adopted by the DAM capability playbooks (every page) and the GitHub repos catalogue (in its page parts and published page; C-DIST-01 to 03 pass).
### Changed
- `diagrams.js`: a spacing pass keeps constellation points and labels apart; optional short labels; clickable labels; lower quadrant captions at the foot of their quadrant.
- `map.html`: each step names its Morgan Map layer (decision, evidence, execution).

## 2.14.0 — 2026-11-07
### Added
- Page `map.html` (Start) and `portal/src/js/diagrams.js` (injected as `__DIAGRAMS__`): a dependency-free diagram kit with a constellation (two axes in the style of a Morgan Map), a swimlane flow (in the spirit of Mermaid) and grouped relationship columns. Each diagram has focusable named elements, shapes as well as colours, a details panel, a list view, theme colours and forced-colours support. The page maps each workflow step by who does it (person, decision, person with a Commons tool, toolkit) and how much it matters (required by the DAM policy, recommended by guidance, good practice), all derived from `models/dq-capability.yaml` by published rules; shows the same workflow as a flow; the 22 records and their `ref:` links; and the lineage of a rule through the Commons (D-DIAG-01).
- `knowledge/provenance.yaml` and `scripts/audit_provenance.py`: a register of content classes (sourced, derived, real example, template, estimate, assessment, illustrative), the authoritative masters the Commons defers to, and every file containing example-like content; the audit fails the build on anything unregistered. Shown on `build.html#provenance` (D-PROV-01). Routine "Provenance audit".
### Changed
- Metadata Weaver examples replaced with real public records (Defra road noise round 3, Environment Agency flood-monitoring API, DfT NaPTAN, DfE school capacity) with sources; the ODCS example is labelled illustrative.
- Research finding F-03 restated as an untested assumption.
- Home page links to the new page and to connectors. Diagram styles added to `base.css`.

## 2.13.0 — 2026-11-07
### Added
- `dqkit/weaves.py` and `DQ.weaves` in `engine.js` (identical output, checked by the parity check): one rules file to 11 native formats — SQL rule pack, Snowflake data metric functions, Databricks Lakeflow expectations, AWS Glue DQDL, Google Knowledge Catalog (Dataplex) rules, dbt data tests, SodaCL, PyDeequ, OpenMetadata test cases, DataHub assertions, Monte Carlo monitors-as-code. Rules with no equivalent are listed, never dropped. `weaves.crosswalk()` derives the check-by-platform matrix from the weaves (D-WEAVE-01).
- Page `connectors.html` (Apply) and `knowledge/vendors.yaml`: 27 vendors and platforms from the 2026 Gartner Magic Quadrant for Augmented Data Quality Solutions (all 13 named vendors), the Forrester Wave Data Quality Solutions Q1 2026, and the catalogues and platforms they connect to; analyst positions only where publicly confirmed; GitHub repositories confirmed; AI agent and MCP offerings for cataloguing and metadata with sources (D-VEND-01).
- `dqkit export --to <platform>`; `weave_rules` tool in the Commons MCP server.
- `scripts/check_vendor_repos.py`, run by the monthly link check. Routines "Vendor and analyst facts" and "Weave parity". `tests/test_weaves.py`.

## 2.12.1 — 2026-11-06
### Fixed
- Global menu bar: one set of breakpoints replaces seven scattered ones. The full menu shows from 1200 pixels (was 1440, which hid it on most laptops); between 1200 and 1919 pixels search and what's new become icon-only and the tour button says "Tour"; below 1200 the menu collapses into "Menu". Every bar control is 40 pixels high and pill-shaped; the bar is 60 pixels at every width; labels hidden for space stay in the accessible name; open menus sit above the floating buttons (D-NAV-04).

## 2.12.0 — 2026-11-05
### Added
- Page `getinvolved.html` (Contribute) and `knowledge/participation.yaml`: three routes in (contribute, join, champion), five working groups with terms of reference, champion and ambassador roles, a communications kit for email, Teams, Slack, Viva Engage, intranet, newsletters and meetings, and seven badges (D-PART-01). `scripts/make_badges.py` writes badges to `portal/src/badges/` (SVG and PNG); `ambassador_kit()` writes `downloads/getinvolved/` (Word, .eml, text files, zip). GitHub forms `8-badge-claim.yml` and `9-join-working-group.yml`; contact topics for working groups, champions and badges.
- Page `governance.html` (Learn) and `knowledge/governance-bodies.yaml`: 20 bodies in seven layers (decide, advise, regulate, communities, devolved and Crown Dependency, your organisation, the Commons) with purpose, aims, outcomes, rules of engagement, decision rights, cadence, terms-of-reference and activity status; question routes; how a standard is agreed (D-GOV-01).
- Shell: display options (BL-27, D-DISP-01); source labels on outside links (BL-26, D-SRC-01); journey bar for cross-portal journeys (BL-34, D-JRN-01).
- `scripts/import_code_evidence.py` and `knowledge/code-evidence.yaml`: evidence from public code on wheel areas and standards (BL-29, D-CODE-01).
- DAM requirement ids per playbook stage and in `api/xref.json` (BL-33); feedback routes to the sister portals on every page (BL-30); System Usability Scale on the research page and in the session guides (BL-32); learning progress (BL-28); draft Jersey and Isle of Man packs (BL-15); `downloads/weaver-uk-mem-mapping.csv` (BL-12).
- Routines: strategy watch, code evidence refresh, cross-portal feedback themes. `tests/test_participation_governance.py`.
### Changed
- Menu and bar: the full menu shows from 1440 pixels wide (was 1300) so the new Aa button fits; the phone bar is tighter.
- Body text is sized in rem so it follows the text size option.
### Fixed
- Reflow at 150% text with wide spacing: chips, tags, buttons, filter labels and the Ask box wrap instead of overflowing (WCAG 1.4.4, 1.4.10).
- `{{REPO}}` placeholders inside pages are now replaced (the capability model's source link).

## 2.11.0 — 2026-11-05
### Added
- Page `research.html` (Contribute) and `knowledge/research.yaml`: introduction for prospective consumers and their teams, research panel sign-up (Microsoft Form when configured; otherwise the contact form with no contact details), 10 research questions (6 tactical, 4 strategic) linked to backlog items, 10 methods, 3 planned rounds, inclusion quotas, findings ("You said, we did"), synthesis steps, participant information and consent (D-UR-02).
- Research bundle built into `downloads/research/`: invitation pack (.docx), invitation email (.eml with no sender or recipients), participant information and consent (.docx), sign-up questions for Microsoft Forms Quick import (.docx), session guides (.docx), README and one zip (`research_bundle()`, `research_email()`).
- Page `roadmap.html` (Contribute) and `knowledge/roadmap.yaml`: idea-to-release pipeline, 6 delivery objectives (3 tactical, 3 strategic), Now/Next/Later with capacity, transparent scoring (user need, inclusion, strategic alignment, feasibility, effort factor) with your-own-weights what-if and CSV download, item tracing, wishes awaiting assessment, 8 government strategy anchors with coverage counts, capacity and governance (D-RM-01).
- Backlog items BL-25 to BL-34; contact topics "Take part in user research" and "Suggest an idea for the roadmap" (the contact form pre-selects a topic from `?topic=`).
- `tests/test_research_roadmap.py`.
### Changed
- Triage: BL-22 could → should, BL-27 should → must, BL-29 should → could, to match their scores (tested rule).
- Help us build this links to the open roadmap and research; Three portals, one journey adds join-up actions X8 (estate compass) and X9 (research and roadmap in the open).

## 2.10.0 — 2026-11-05
### Added
- `knowledge/standards-catalogue.yaml` and a Standards catalogue section on `interop.html`: 57 standards across data, digital, cyber and technology with GOV.UK status (19 mandated, 4 recommended, 9 UK guidance, 25 widely used), publisher, specification link, Rosetta concepts, Weaver support and links to the repos asset catalogue and the DAM playbooks. Public facts only (D-STD-01).
- Metadata Weaver writes W3C DQV (`to_dqv` in `dqkit/weaver.py`, `W.toDqv` in `engine.js`, `dqkit weave --to dqv`, DQV tab on `weaver.html`); `weave()` returns `quality` (D-DQV-02). Two-engine parity covers it.
- Page `ecosystem.html` (Apply) and `knowledge/ecosystem.yaml`: comparison of the three portals, what each could gain, lineage map (keyboard operable; scrolls sideways on phones), trace one thing, five journeys, seven join-up actions, live check of the playbooks' cross-reference manifest (D-ECO-01).
- `api/xref.json` cross-reference manifest; "Continue in a sister portal" asides on 13 pages; wheel and role panels link to the same area or role in the DAM playbooks.
- `tests/test_ecosystem_standards.py`. Icon `network`.
### Changed
- Rosetta Stone: eleven standards (adds schema.org, CKAN, ODCS); vocabulary and knowledge graph exports regenerated.
- The knowledge link test skips pages that belong to a sister portal.

## 2.9.0 — 2026-11-05
### Added
- Page `wheel.html` (Check and assess) and `knowledge/dama-wheel.yaml`: an original wheel of the 11 DAMA-DMBOK knowledge areas, seven audience views, DAM policy actions, mappings to the Commons maturity themes and the DMA for Government's 10 topics, maturity overlay from the visitor's own answers, data and records lifecycle, records frameworks, ten join-up actions with CSV plan download, communities (D-WHEEL-01).
- `knowledge/change-delivery.yaml` and a "Data quality in change programmes and projects" section on `roles.html`: assessment of 14 change roles, lifecycle with GDS phases and assurance gates, RACI (13 activities, one accountable each), service blueprint, proto-personas and journeys (D-ROLE-02).
- 10 change and delivery roles in `knowledge/stakeholders.yaml` (`group: change`); the role picker groups everyday and change roles.
- `knowledge/feedback.yaml`: Microsoft Form route (configurable link and pre-filled link), question set, settings and set-up steps; feedback strip on every page; Give feedback section on `build.html`; `downloads/dq-commons-feedback-form-questions.docx` (D-FB-01).
- `tests/test_wheel_change_feedback.py` (14 tests). Icons `wheel`, `feedback`.
### Changed
- Striped table rows use a theme-aware overlay, fixing dark-mode contrast on pages with their own colour tokens.
- Maturity page links to the wheel; Community adds the KIM profession and The National Archives' information management; supplier and information governance roles gain change duties; privacy notice covers the Microsoft Form; user guide tasks and tour list; operating model, FTIR spec, equality and data protection screening, user research bundle.

## 2.8.0 — 2026-11-05
### Added
- Pages `sitemap.html` (Start), `ask.html` (Start) and `reuse.html` (Apply); knowledge files `knowledge/reuse.yaml` and `knowledge/acronyms.yaml` (D-NAV-03, D-AI-02, D-REUSE-01).
- Open data API built with the portal: `api/index.json`, `api/pages.json`, `api/search.json`, `api/passages.json`, `api/releases.json`, `api/acronyms.json`, `api/mcp-tools.json`, `api/knowledge/*.json`; `feed.xml` (Atom releases feed), `sitemap.xml`, `ask-index.js`.
- Shell: Share this page on every page; embed mode (`?embed=1&accent=RRGGBB`) with height messages for the host page; `?search=` deep link; tooltips (data-tip, acronyms on first use, icon-only buttons, level badges); reading progress bar; Top button; previous and next page navigation with position dots (D-SHARE-01, D-NAV-03).
- Footer links to the site map, Ask the Commons, reuse, API and feed. Icons `sitemap`, `share`, `copy`.
### Changed
- Visual layer (D-VIS-01): accessible 8-hue palette for light and dark; group colours on menu panels, page labels and page navigation; section hues on heading icons, cards, disclosures and the On this page list; KPI accents.
- Tables: content-fitted columns (narrow for short codes and numbers, more room for long text, scaled to fit on wide screens), wrapping headers tinted by section, striped and highlighted rows, wide tables extend beside the reading column on large screens, scroll shadows and a sideways hint, sticky headings on long tables.
- Guided tours end with shared steps for tables, tooltips and previous and next. User guide: Finding your way and six tutorials; tour list includes the new pages.
- Search dialog links to Ask the Commons with the same words, and to the site map.
### Fixed
- Easy read summaries added for the catalogues and models pages (found by the new navigation tests in `tests/test_reuse_nav.py`).

## 2.7.0 — 2026-11-05
### Added
- `knowledge/catalogue-integration.yaml` and page `catalogues.html` (Manage and improve): integration patterns, integration depth levels, 20 products with sources, open standards, 16 lock-in risks, 32 RFI and RFP questions, a 10-test proof-of-concept script, exit checklist, buying route and UK procurement resources (D-COM-02).
- `tests/test_catalogues.py`.
### Changed
- `commercial.html` accepts `#add=C03,C12` to add clauses to the schedule; links from Tooling and the tender questions.
- Capabilities C3 and C12 link to the new page (model version 1.1.0 exports regenerated).

## 2.6.0 — 2026-11-04
### Fixed
- Menu panels: positioned to stay on screen (`placePanel` in the shell); groups with more than 6 pages show in two columns; full menu from 1300px, compact Menu button below; brand no longer shrinks or overlaps the menu; no sideways scrolling from 320px up.
- Target size: buttons, selects, summaries, chips and file pickers at least 24px (WCAG 2.2, 2.5.8); chips wrap under 480px.
### Added
- Interactive models page: capability map with detail panel, workflow player (play, step, role highlight, list view, deep links `#wf-P2-s3`), record explorer (`#ent-Issue`), capability deep links (`#cap-C7`).
- Model navigation fields: `pages` on capabilities, `page` and `stage` on steps, `lanes` role mapping; validated against portal pages, playbook stages and roles (model version 1.1.0).
- Home: "Find your way by capability". Roles: "Your steps in the data quality workflows". Playbook: workflow steps per stage.
- Search entries for capabilities, records and workflow steps; knowledge graph classes `Capability`, `Workflow`, `RecordType` and properties `guidedBy`, `keepsRecord`, `realisedBy`, `performedBy`, `createsRecord`, `linksTo`.

## 2.5.0 — 2026-11-04
### Added
- `models/dq-capability.yaml` and `scripts/build_models.py` (D-MOD-01): ArchiMate 3.1 exchange XML and Archi CSV, UML 2.5.1 XMI, PostgreSQL DDL, JSON Schema 2020-12, OWL Turtle, data dictionary, capability-guidance matrix, Mermaid ERD and SVG, Visio `.vsdx` process map and PDF, BPMN 2.0 workflows P1 to P5.
- Portal page `models.html`; downloads in `downloads/models/` and `dq-capability-models.zip`.
- `tests/test_models.py`; CI runs `build_models.py --check`.
- Metadata Weaver profile `uk-gemini`; value checks for `accessRights`, `securityClassification` and `publisher` (`value_issues`).
- `scripts/apply_settings.sh` for owner-only repository settings and release tags.
### Changed
- Every `uses:` in `.github/workflows` pinned to a full commit SHA with the version in a comment.

## 2.4.0 — 2026-11-04
### Added
- `docs/CONFORMANCE.md`; frameworks `uk-identify-cda`, `uk-data-ownership-model`; requirements IDC-1, IDC-2, DO-1, DQAP-8, IF-5.
- DQAP workbook tabs `Communication plan` and `Checklist`; new columns in Issues log, Causes and Actions; new Details rows.
- CDA return columns `gds_purposes`, `gds_dataowner`, `gds_datasteward`, `gds_iao`, `gds_providedto`, `gds_sourcedataset`, `gds_dqmeasurementfrequency`, `gds_metadatalastreview`, `gds_metadatanextreview` (appended).
- Workflows: Dependency review, Label pull requests, Welcome; release SBOM and build provenance. `CITATION.cff`, `.github/SUPPORT.md`.
### Fixed
- Playbook rule template scales (1 to 4, as the issues framework); UK CDA profile must and should lists.

## 2.3.0 — 2026-11-04
### Changed
- The portal has no claude.ai dependency (D-GH-02). All submissions use GitHub issue forms pre-filled by the portal; results are read from GitHub when the portal is built.
- Rules assistant uses fixed, published patterns in the browser instead of an AI model; optional "copy as a prompt" for an approved AI tool.
- Publish workflow also runs daily and when the `published` or `withdrawn` label changes.
### Added
- `scripts/gen_issue_forms.py` and generated forms `6-maturity-share.yml`, `70`–`73-survey-*.yml`.
- `community()` in the portal build: published contributions, survey totals and the maturity benchmark (counts under 5 hidden).
- Tests: no claude.ai calls in any page; issue forms current; survey forms carry no free text.
### Removed
- claude.ai shared store, sign-in, downloads, in-portal moderation and inbox, the AI model behind the assistant, and the `--artifact` build options.

## 2.2.0 — 2026-11-03
### Added
- `github.html#map-h`: portal-to-GitHub feature map. `window.DQP_GITHUB` helper in the shell.
- Roadmap computed from backlog statuses; GitHub milestones and `needs-people` label kept in step (`scripts/backlog_to_issues.py --sync`).
- Build-time GitHub data (issue numbers, states, votes, wishlist) on Help us build this.
- `.github/DISCUSSION_TEMPLATE/` (ideas, q-a, show-and-tell); `.github/inclusion-review.md`.
- `scripts/sample_facts.py` and the Fact sampling workflow; source diffing (`check_links.py --diff`).
### Changed
- Portal form fallbacks open pre-filled GitHub forms; the contribution form covers events, blogs, videos and podcasts and has a details field.
- Commissions no longer ask for contact details; survey privacy notice updated.
- Releases attach the offline portal and open an inclusion review.
- `knowledge/build.yaml`: static roadmap removed; routines and GitHub links updated.

## 2.1.0 — 2026-11-03
### Added
- Portal search (`/` or Ctrl+K), an "On this page" drawer with collapsible sections and New or Updated flags, a contextual icon on each section heading, and reduced-motion-safe reveal motion.
- "In short" plain English summary on every page (`knowledge/easy-read.yaml`); offline zip (`downloads/dq-commons-offline.zip`); per-page change history in the footer.
- Toolkit: `outlier` check; `dqkit/numbers.py`; `dqkit/linkage.py`; value sets `gss_uk_groupings`, `english_regions`, `gss_entity_codes` and library rules G05, G06.
- Weaver: CSVW and Frictionless Data Package readers; GeoDCAT-AP and StatDCAT-AP writers; profile checks (`profiles` in the weave result).
- `0-contact.yml` contact form; `docs/transparency/ATRS-AI-ASSISTANT.md`; `docs/MODERATION.md`; `docs/research/RESEARCH-KIT.md`; `docs/accessibility/AUDIT-BRIEF.md`; `docs/translation/README.md` and `scripts/export_strings.py`; `docs/community/CO-DESIGN.md`; `integrations/fabric/` and `integrations/http-api/`.
- Workflows: Triage (daily), Repository health (weekly); Internet Archive snapshots in the link check; `scripts/check_settings.py`, `scripts/section_baseline.py`.
### Changed
- Contact by form only everywhere; no email fields or addresses (tests enforce it). Case study template asks for a contact route.
- pandas cap lifted to `<4` (numbers no longer depend on pandas).
- Link check keeps one tracked issue (opened, updated, closed) instead of opening a new one each month.
### Fixed
- Accessibility statement: contact route, axe-core testing, offline and plain English options.
- Search anchors use each heading's own id.

## 2.0.0 — 2026-11-03
### Breaking
- Removed `dqkit survey`, `docs/GUIDANCE-CROSSWALK.md`, `docs/SURVEY-REVIEW.md`, `docs/outreach/`, the CDO Council brief (`roles.html#brief`) and the guidance page's comparison sections. Links to them no longer work.
### Added
- `github.html`: a plain-English introduction to GitHub and how the portal and repository connect.
- `professions.html` and `knowledge/professions.yaml`: 12 data quality capabilities mapped to 26 frameworks (Civil Service professions, UK nations, sectors, international), each checked at source on 3 November 2026, with personas and a levels crosswalk.
- About page: background, rationale, goals and desired outcomes.
- Home page journey strip (Beginner, Intermediate, Advanced).
### Changed
- Menu in journey order: 1 Start, 2 Learn, 3 Check, 4 Improve, 5 Apply, 6 Contribute; level badges on every page; breadcrumbs follow the group.
- README organised for beginner, intermediate and advanced readers.
- Baseline effort: user-set deadline (default 12 weeks), example CDA count and capacity; England and Wales bank holidays 2026 to 2028.
- GDaD framework address and skill names corrected (no standalone data quality skill exists).
- Issues framework page rebuilt on published GOV.UK sources only.
### Removed
- Unconfirmed dates and the home page countdown; advice framed for the CDO Council and GDS; content drawn from unpublished documents; two unpublished framework entries.
### Fixed
- No third-party loads: js-yaml 4.2.0 bundled (MIT), Google Fonts removed.
- Source verification re-audited: every source read at source (BL-04 done).

## Repository go-live fixes — 2026-11-02 (released in 2.0.0)
### Fixed
- CI: pandas capped below 3.1 (the browser engine matches pandas 3.0 number parsing); `odfpy` and `requests` declared; workflow test no longer breaks on action updates.
- Accessibility: keyboard access to scrollable tables, 24-pixel minimum targets, contrast on the learn page, roles for labelled elements.
- GitHub now detects the MIT licence; the OGL content licence is in `docs/CONTENT-LICENCE.md`.
### Changed
- GitHub Actions moved to Node 24 releases; Node 22 for checks.
### Added
- Dependabot, CODEOWNERS, CodeQL scanning and OpenSSF Scorecard workflows.

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
- `control_point` on every rule (source, pipeline or reporting) (source, pipeline or reporting).
- Issue operations (`dqkit/operations.py`): defect volume, control failure rate, cycles open, overdue issues with escalation, and recurrence. A new Operations tab in the workbook.
- Workbook Issues log: control point, cycles open, escalation, recurring, source system and immediate risk. Actions tab: action type (containment, corrective, preventive) and how success will be checked.
- `--case-study`: drafts the GDS case study template (.md and .docx) from results. The NDL charts each get one.
- Illustrative escalation example (`examples/illustrative-escalation/`).

## 0.2.0 — 2026-10-14
### Added
- Filled-in DQAP Excel workbook (`--workbook`) and run history (`--history`).
- IOPC-style trust level and decision-tree DQAP route in every check summary.
- ESS "plus" dimensions, and `trust_level` in the metadata model.
- Issues framework page with a live calculator.
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


