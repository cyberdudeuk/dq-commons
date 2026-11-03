# Build journal

## 2026-11-03 — v2.0.0: journey-ordered portal, GitHub introduction, professions, privacy clean-up

**Asked for:** final verification and polish; a GitHub introduction for newcomers, linked to the Commons' background and aims; a more intuitive page order for beginners to experts; connections to personas, the GDaD framework and every profession's framework, the UK nations and international frameworks; a README for three audiences; remove the CDO Council brief and anything else that should be private; check any partly verified sources in full.

**Built**
- `github.html` (Get started) and About page background, rationale, goals and outcomes.
- `professions.html` from `knowledge/professions.yaml`: 12 capabilities, 26 frameworks read at source (GDaD, Analysis Function, GSG, GES, GORS, GSR, Policy, Finance, Commercial, Project Delivery, Counter Fraud, GKIM, Civil Service Skills Taxonomy, the Introduction to Data Quality course, LGA, NHS England, Scotland, Wales, NISRA, JNCC, SFIA 9, ISO 8000-150, APS, Canada, Stats NZ, US Federal Data Strategy), personas and a levels crosswalk.
- Journey menu with level badges and automatic breadcrumbs; home page journey strip; shorter header brand.
- README for beginner, intermediate and advanced readers.

**Fixed:** the check page's rules reader failed when a CDN was blocked (js-yaml now bundled); Google Fonts removed; target sizes for sliders, date fields and heading links; GDaD links and skill names (the framework moved address; no standalone data quality skill exists); framework counts.

**Removed (D-POL-02):** CDO Council brief; unconfirmed dates and the countdown; Council and GDS advice; the internal CDA count; unpublished framework entries; the guidance crosswalk, survey review, tooling comparison and draft messages; `dqkit survey`. Kept in a private bundle.

**Verified:** no source is marked partly verified or not yet reviewed; BL-04 closed.

**Checked:** all tests pass; content health clean; a local probe (target size, contrast, ARIA, keyboard scrolling) is clean on all 35 pages; screenshots reviewed at desktop and phone sizes.


## 2026-11-02 — repository goes live on GitHub: CI fixed, accessibility fixed, maintenance automation

**Context:** the v1.6.0 history was pushed to `cyberdudeuk/dq-commons`, made public, and GitHub Pages turned on. The first automatic runs showed 4 of 6 workflows failing.

**Fixed**
- **Tests (also blocked the portal publish and content health):** CI installed pandas 3.1.0, which parses numbers differently from the version the browser engine copies; capped below 3.1 (D-CI-01). `odfpy` added to the declared dependencies.
- **Accessibility (24 serious axe findings):**
  - scrollable tables could not be reached by keyboard on phones: the portal build now makes every table wrapper focusable, with a role and a name (WCAG 2.1.1)
  - 13-pixel tick boxes and 17–23-pixel stacked links: now at least 24 × 24 pixels, in the shared page shell so it applies to every page (WCAG 2.5.8)
  - learn page: modules outside your pathway were faded to 55% opacity, which failed contrast on 35 elements; now a dashed card on a tinted background with a visible "Outside your pathway" label, so the difference is not shown by styling alone (WCAG 1.4.3, 1.4.1)
  - labels on plain `div` and `span` elements (rating bar, ticks and crosses, vote tallies, trail, example requests) now carry a role (WCAG 4.1.2)
- **Licence detection:** GitHub showed "NOASSERTION"; root `LICENSE` is now the exact MIT text and the OGL statement lives in `docs/CONTENT-LICENCE.md` (D-CI-03).
- **Actions:** moved off deprecated Node 20 actions (D-CI-02). The weekly pipeline's Pages publish now queues behind the main publish instead of colliding.

**Added:** Dependabot (weekly, grouped), CODEOWNERS, CodeQL security scanning, OpenSSF Scorecard (D-CI-04).

**Checked:** 145 tests pass locally. All workflow files parse. A local Playwright probe for target size, contrast and ARIA rules finds no problems on the pages axe flagged; the full axe run is confirmed by CI on push.

**Could not do from this session (proxy policy):** push version tags; change repository settings (description, website, topics, branch and tag rules). Steps are in the session summary and `docs/OPERATIONS.md`.

## 2026-10-30 — v1.6.0: for your role, CDO Council brief, gap register and Q-FAIR

**Built:** For your role page (13 roles, key dates, CDO Council brief, gap register of 20); Q-FAIR ratings in the toolkit and CDA return (11 new columns); shared effort model (`knowledge/effort.yaml`, `dqkit effort`, MCP `estimate_effort`); Q-FAIR fields and self-rating on the baseline page.

**Research used:** the DAM policy (checked 30 October: requires a DQAP or equivalent, no minimum metrics, no FAIR or Q-FAIR); the Q-FAIR blog and 2022 benchmark (six partner bodies, three-level qualitative scale, sector-wide ratings); Victoria's 2025 audit of critical data assets.

**Findings shown honestly:** the illustrative NDL portfolio rates Good on quality (8 of 8) but Attention required on accessible, interoperable and reusable, because those fields aren't recorded.

**Checked:** all tests pass; Python and portal effort model agree (7,465 person-days on the default 56-day case); new pages have no errors, no sideways scroll and no accessibility findings on desktop light and phone dark.

## 2026-10-30 — v1.5.0: playbook in the toolkit, automatic publishing and releases

**Built:** `dqkit playbook init | status | guide` and the MCP tool `playbook`; a progress report download and toolkit commands on the playbook page; GitHub Pages and release workflows; `scripts/release_notes.py`; `tests/test_playbook.py` (6 tests).

**Fixed:** three playbook steps showed as "[object Object]" because "word: text" in YAML became a mapping (found by the new CLI); version numbers in `pyproject.toml`, `dqkit/__init__.py` and the MCP server had drifted (1.1.0, 0.1.0, 1.2.0) and now match the release record.

**Checked:** 137 tests pass; parity 37 of 37; content health clear; browser checks on all 32 pages.

**GitHub:** the repository exists with a starter LICENSE commit; local history was joined to it with a normal merge (no force push). Pushing was refused because the repository isn't yet in this session's authorised sources.

## 2026-10-30 — v1.4.0: data quality management playbook, horizon scan, every source verified

**Built:** Data quality management playbook for critical data assets (page, YAML source, generated document, 6 CSV templates, knowledge graph lineage flow). `scripts/build_playbook_doc.py` with a CI check. A third verification state ("Not publicly available") with a filter on the frameworks page and dates on every card.

**Research:** 86 previously unverified sources read at source and corrected where needed (9 links replaced, 5 dimension maps re-keyed, 2 frameworks marked not publicly available, 1 substitute source explained). October 2026 horizon scan: 10 new library items and 2 home page slides, each read at source. ODCS v3.1.0 confirmed as the version the toolkit already writes and validates.

**Fixed:** the content health counter missed single-quoted YAML values, so it under-reported verification (it now reports 154 of 154 sources read in full); duplicate library title; empty-link warnings.

**Checked:** all tests pass; parity 37 of 37; content health 0 errors, 0 warnings; browser checks on all 32 pages in desktop light and phone dark, with the playbook's checklist, stage navigation and jurisdiction finder exercised; graph is one connected component (468 nodes, 1,092 relationships).

**Not yet possible here:** the external link checker and the axe-core CI run need network access this sandbox doesn't have (both run in GitHub Actions on push). GitHub push still waiting for access.

## 2026-10-15 — v1.3.0: knowledge map, events, skills and training, releases, logo, build bundle

**Built:** Knowledge map (glossary, thesaurus, data dictionary, taxonomies, ontology, interactive graph with trail, path finder, lineage and traceability); knowledge graph module, CLI and MCP tool, with SKOS/OWL exports; Events page; Skills and training page; Commons logo, favicon and "What is a Commons?" panel; What's new drawer and menu flags driven by `knowledge/releases.yaml`; the standalone solution build and development bundle.

**Research:** 5 upcoming events and 13 training entries checked against providers' pages where marked; organisers' contact emails seen during research were not copied.

**Checked:** all tests pass; parity 37 of 37; content health clear; browser checks on all 31 pages in desktop light and phone dark; graph has no dangling links and is one connected component.


## 2026-10-15 — v1.2.1: international packs, provenance, freshness issues, accessibility CI

**Built:** UN NQAF and IMF DQAF packs (14 packs now); a "content last reviewed" line on every page; the weekly content health run now opens and closes a GitHub issue; an axe-core accessibility workflow; the v1.2 architecture section with a diagram. Retired one stale news slide.

**Checked:** 118 tests pass; parity 37 of 37; content health 0 errors, 0 warnings.

**Not yet possible here:** the axe-core workflow couldn't be run in this sandbox (the npm registry is unreachable); it runs on the first push. GitHub push still waiting for access.


## 2026-10-15 — v1.2.0: weaver, world, help us build this, self-checks

**Built**
- Metadata Weaver in Python and the browser, with a portal page, CLI, MCP tool and parity cases. Contract validation and change control with breaking-change detection.
- UK and the world page: Crown Dependencies, Overseas Territories, Commonwealth and 18 international partners.
- Help us build this page: roadmap, backlog, wishlist and votes, co-design, charter, rules, safeguards, contributors, GitHub resources, trust routines and a contact form with no published email.
- Backlog-to-issues script and workflow; charter and contributors docs generated from the same YAML; code of conduct.
- Content health self-check and workflow; GOV.UK blog features; icon set; new footer with licences, notices and colophon.

**Checked:** 116 tests pass; parity 37 of 37. Content health: no errors after fixes.

**Privacy scan:** repository, history and built portal scanned for emails, phone numbers, identifiers, tokens, keys and security markings. Found: a personal email as the git author on every commit (rewritten to a no-reply address before the first push) and an Atlassian site address (replaced with a placeholder). Test data uses example.org addresses and published specimen identifiers only.


## 2026-10-15 — v1.1.0: contracts, suppliers, legacy, front page, library and media

**Asked for:** close the gaps; data contracts and exports; older pages to v1.0; benchmarking; merge related work; commercial barriers, contract clauses and supplier obligations so the burden isn't on the public sector; legacy and technical debt with MoSCoW; integration, interoperability, standards, guardrails and measures; then a front page with a hero carousel and spotlight, a curated content library with community publishing, a knowledge base and a media centre (blog, vlog, podcasts).

**Built**
- **Data contracts:** `dqkit contract` and the checker export and import ODCS, Table Schema, CSVW; GX and R validate exports in the browser; data profile; Excel, ODS, JSON and JSON Lines in the browser.
- **Govern pages:** Buying and suppliers (12 barriers, 8 principles, 20 clauses with a builder, tender scoring, RACI, lifecycle); Legacy and modernisation (data debt patterns, self-assessment, migration gates, MoSCoW, reconciliation tool); Interoperability and standards (6 layers, metadata Rosetta of 61 concepts, guardrails, requirements checklist, measures, related capabilities).
- **Front page:** news and insights carousel, spotlight (capability, case study, theme, workflow, topic, domain), latest items.
- **Library and knowledge base:** curated resources (64), 10 knowledge base articles with a reader, members' publishing through moderation.
- **Media centre:** blog (3 Commons posts), vlog and podcasts, with captions or transcript required.
- **Older pages:** context banners, group labels and tours on all six.
- **Accessibility statement and privacy notice** page.
- **Benchmarking:** opt-in anonymous maturity sharing; editors publish averages with groups under 5 hidden.
- **Content governance:** owner role and review date on every knowledge file; monthly link checker.
- **Merged work:** Standards Rosetta, DDaT role mapping, xAPI learning record export, MCP domain manifest for the NDL Civic Tech platform.

**Fixed along the way:** a comma silently split a value in the new interoperability file (caught by the guard test); banner colours invisible in one theme on older pages; library and media headings skipped a level; carousel Pause didn't pause after keyboard focus; slide dots below the 24px target size; survey saves could overwrite a shared maturity result.

**Checked:** all unit tests pass; parity 35 of 35 (now including contracts, exports and reconciliation); all 25 pages pass browser, layout and accessibility checks at desktop (light) and phone (dark).

**Not done here:** the GitHub push (the session's GitHub token is invalid), and live link checking (no internet from the sandbox).

## 2026-10-15 — v1.0.0: the Public Sector Data Quality Commons

**Asked for:** make it a general data quality hub for the whole public sector, not NDL or DAM specific; add international standards and crosswalks, tours, tutorials, a user guide, a wishlist, GitHub/Jira/Confluence links and an operating model, communities, surveys and commissions, member contributions, AI guidance with worked examples and case studies, and an AI assistant; fully accessible and inclusive.

**Built**
- **Rename and scope:** Public Sector Data Quality Commons v1.0.0. Mission, aims, 6 objectives, priorities and roadmap on a new About page.
- **Portal, 19 pages** in 5 groups, with a guided tour on 13 pages. New: About, User guide, Maturity self-assessment, AI assistant, Frameworks and standards, Learn, AI for data quality, Scenarios (14), Community, Surveys and commissions, Operating model.
- **Toolkit:** identifier checks (10 schemes), value sets, 9 data sources, 12 packs, 30-framework registry, crosswalk conversion, MCP server for AI agents.
- **Checker:** identifier and value set options in the rule builder; rule library templates; takes drafts from the assistant.
- **Shared store** (artifact database) for contributions, wishlist votes, survey answers and commissions, with access rules; wishlist seeded with backlog stories XDMH-211 to 222.
- **Integrations:** issue forms, PR template, CONTRIBUTING, SECURITY; backlog sync to Jira; docs to Confluence; `docs/OPERATING-MODEL.md`, `docs/USER-GUIDE.md`.

**Fixed along the way**
- 4 GitHub issue forms had invalid YAML (GitHub would have rejected them).
- 4 knowledge entries lost text after a comma (for example principle P1's title). A test now guards this.
- Panels marked hidden (editor-only moderation, survey admin, maturity results) were visible because page styles overrode `hidden`. Fixed globally and now tested.
- The crosswalk table caused sideways scroll on phones.
- Some new text said the browser checker reads Excel and ODS; it reads CSV (the Python toolkit reads the rest). Corrected.

**Checked:** all Python tests pass; parity 33 of 33; all 19 pages render with no script errors, no sideways scroll and no findings from the accessibility checks at desktop (light) and phone (dark); access rules tested at viewer and contributor level.

## 2026-10-15 — v0.4.0: one data quality portal, run by a pipeline

**Asked for:**
- Merge all the data quality artefacts into one portal (the project lead chose a separate portal).
- Run the kit as a workflow (the project lead chose GitHub Actions).
- Find and fix the remaining gaps.

**What was built**
- **Pipeline:**
  - The portfolio runner and starter-rules suggester (started in the previous session) were finished and tested.
  - New: the CDA return export.
  - The weekly workflow now has a portal to publish.
- **NDL Data Quality Portal:** 8 pages with one top bar, skip link and footer, built from `portal/src/` by `scripts/build_dq_portal.py`.
  - **New pages:**
    - home: role routes, live deadline, status
    - pipeline status: trust mix, assets with trend, issues, changes, escalations, catalogue, downloads
    - check your data: in-browser checker, rule builder, copy to DQV or DQAP
    - share and learn: case studies
  - **Merged in:** NDL assurance (now rebuilt from pipeline outputs, identical to before), January baseline, guidance and tooling.
- **Other changes:**
  - The old standalone pages and the main portal copies now point to the new portal.
  - The main portal has a tile for it.

**Checked and fixed**
- **Parity check:** 30 of 30 cases pass. It found and fixed:
  - a crash on empty columns under pandas 3
  - inconsistent error wording
- **Rendering:** every page renders at desktop (light) and phone (dark) widths with no overflow and no script errors. The checker runs the example end to end.
- **Stale content fixed:**
  - test counts
  - a fixed "today" date and working-day count on the baseline page
  - the home page layout (a CSS specificity bug)
- **Tests:** 59 pass.

**Pending**
- GitHub push: no repository is attached, so the workflow and Pages are untested on GitHub.

## 2026-10-14 — v0.3.0 tooling and adoption material built in

**What came in:** further tooling and adoption material, shared privately (details held in the private repository).

**What was built**
- Control points per rule. Issue ageing, overdue escalation and recurrence, with a new Operations tab.
- Containment, corrective and preventive action types.
- A case study drafter (`--case-study`).
- Tests: 30 → 34, all passing.

**What was found:** 9 findings, shared privately with the material's owners.

**NDL results:** unchanged (no rules or data changed). Each chart now also has a draft case study.

**Pending:** GitHub push (no repository attached).

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
- **Documentation:** PRD, theory of change, architecture, FTIR spec, user research bundle, screening and decisions.
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
**Trigger:** existing guidance, some of it shared privately (details held in the private repository).

**Built**
- **An issues framework page** with a live calculator.
- **`framework.py`:**
  - target policies low, mid and high, with low as the default (D-021)
  - error rates in words ("1 in 40 records")
  - tests for the band calculation
- **`trust.py`:** IOPC-style trust level (D-022). **`pathway.py`:** decision-tree route (D-023).
- **`workbook.py`:** a filled-in 10-tab DQAP workbook, plus run history (D-024). The Causes tab has an addressability column.
- **Vocabulary:** 3 ESS "plus" dimensions (relevance, coherence and comparability, accessibility and clarity). **Model:** `trust_level`.
- **NDL rule files:** marked as external data with no influence. Assessment re-run; DQAP workbooks written for all 8 charts.
- **Portal v2.2.0:** new issues framework page; NDL assurance page shows trust levels.

**Checked:** 30 tests pass. The model schema and example are valid. New pages have no errors and no sideways scroll at 1280 px or 400 px.

**Privacy:** the source documents name individuals. No names are copied into any output (D-013).
