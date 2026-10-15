# Build journal

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
    - share and learn: case studies, survey fixes, outreach status
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
- Outreach drafts: not sent.

## 2026-10-14 — v0.3.0 tooling and adoption material built in

**What came in:** 6 more documents from the project lead:
- the GDS Data Quality Tooling Review
- the Cross-Government DQ Solutions Survey design
- a brief research note on DQ tools
- the GDS case study template
- two "Adopting DQAPs in Practice" decks (a Scottish Government session and DQ Week)

**What was built**
- Control points per rule. Issue ageing, overdue escalation and recurrence, with a new Operations tab.
- Containment, corrective and preventive action types.
- A case study drafter (`--case-study`) and a survey analyser (`dqkit survey`). The survey analyser drops personal data on load.
- Tests: 30 → 34, all passing. The survey test uses entirely made-up data.

**What was found:** 9 new findings (F10–F18), including:
- The survey collects personal data with no privacy notice.
- The survey can't segment by organisation type or link to CDAs.
- The tooling review leaves out open-source and government-built tools.
- The brief research omits uniqueness from the GDQF dimensions.
- One deck describes the DAM policy as an organisation's internal policy.
- The Shared Learning Library is members-only.

**NDL results:** unchanged (no rules or data changed). Each chart now also has a draft case study.

**Pending:** GitHub push (no repository attached). Outreach drafts not sent.

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
