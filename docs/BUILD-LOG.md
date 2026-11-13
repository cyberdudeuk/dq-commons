# Build journal

## 2026-11-09 — Weekly maintenance check (no release)
- **Checked:** GitHub Actions for the last 7 days (every workflow green on the latest commit; the earlier failures, last on 5 November, were fixed by later commits); open issues (no contact, content health, broken link or repository settings issues); Dependabot pull request #39; locally, 253 tests, 37 of 37 parity cases, content health (0 errors, 0 warnings, 1 note) and the portal build (48 pages).
- **Changed (documentation only):** the operations runbook and the FTIR spec no longer say the workflows are untested on GitHub; they now say which workflows run there and that the weekly data quality pipeline's first scheduled run is due on 9 November 2026. Build bundle regenerated.
- **Needs people:** a decision on pull request #39, which includes a major version of `actions/github-script` (8 to 9).

## 2026-11-13 — v2.16.0: questions answered, reference and master data group, Semarchy, Person standard

- From a sweep of mail, Teams, Knowledge Hub and Slack for questions on reference and master data: four questions are answered on the community page, and a special interest group was proposed in the Data Management Community.
- Semarchy opens a Master and reference data group under Connectors, with its public sector use from published notices. A new test makes sure every vendor group has a heading, so a vendor in a new group can't silently disappear.
- The Person data standard (alpha) joins the standards catalogue; Zingg and dedupe join the open tools list.

## 2026-11-13 — v2.15.1: catalogue links, Croissant and LinkML, hash changes

- Found by a review of how the three portals join up: two links into the repos asset catalogue named a view it does not have, its standards count was out of date, and the catalogue tracks Croissant and LinkML which the standards catalogue lacked.
- Every one of the 34 shared keys in `api/xref.json` was opened in a browser on the live site: all select the right area or role on load. Changing the address on an open page did not update it; now it does.
- Checks: unit tests, two-engine parity (37 of 37), content health, link check, and axe-core on 48 pages in two modes, all pass.

## 2026-11-07 — v2.15.0: priorities picture, Morgan layers, journey bar in all three portals, sync
- **Built:** Priorities at a glance on the roadmap; Morgan Map layers on the at-a-glance map; label spacing in the diagram kit; the shared journey-bar script, adopted by the two sister portals (both pushed).
- **Follow-ups closed:** sister portals' journey bar (BL-34); Confluence and Jira synced through the Atlassian connector (Architecture space, epic XDMH-210) for v2.13 to v2.15; review requests drafted for the Data Standards Authority (Weaver mapping, BL-12) and the Jersey and Isle of Man statistics offices (packs, BL-15), left unaddressed in the owner's email drafts.
- **Checked:** full tests, parity, provenance audit; roadmap and map pictures at 1366 and 390 pixels; the journey bar in both sister portals in a browser; the catalogue's distribution checks.
- **Needs people:** Microsoft Forms links, release tags, participants and reviewers' replies.

## 2026-11-07 — v2.14.0: data quality at a glance, real examples, provenance register
- **Built:** diagram kit (constellation, flow, columns); Data quality at a glance page (workflow constellation, flow, record relationships, rule lineage, placement rules); provenance register, audit script and build-page section; home page links.
- **Replaced:** invented Metadata Weaver records with real Defra, Environment Agency, DfT and DfE records (sources found and checked by search); F-03's untraceable evidence restated as an assumption.
- **Checked:** full tests; parity; provenance audit (18 files registered, none unregistered); new page at 1366 and 390 pixels in light and dark; all 48 pages at 150% text with high contrast (one overflow on the connectors page found and fixed); internal links and anchors (one broken link in the register found and fixed).
- **Not yet done:** applying the diagram kit to the other pages, and a full visual refresh of all 48 pages; these are on the backlog for testing with users first.

## 2026-11-07 — v2.13.0: connectors, weaves and AI
- **Built:** 11 platform weaves in Python and the browser; the Connectors, weaves and AI page (generator, directory of 27 vendors and platforms, crosswalk, AI and MCP table, analyst reports); `dqkit export --to <platform>`; `weave_rules` MCP tool; monthly repository check.
- **Researched:** 2026 Gartner Magic Quadrant vendor list (13) from Gartner's abstract; positions announced by Informatica, Ataccama, Qlik, IBM (Leaders), DQLabs (Visionary), CluedIn (Niche Player); Forrester Wave Q1 2026 Leaders (Ataccama, Informatica, Qlik) and Experian (Strong Performer); MCP and agent offerings from vendor documentation; 30 GitHub repositories confirmed live.
- **Checked:** full tests (including 11 new), two-engine parity 37 of 37 with the weaves added, content health, the new page at 1366 and 390 pixels in light and dark (a phone overflow and a badge style clash found and fixed).

## 2026-11-06 — v2.12.1: global menu bar fixed
- **Fixed:** the full menu shows from 1200 pixels again with compact buttons; uniform 40-pixel controls in a 60-pixel bar at every width; accessible names kept for icon-only buttons; open menus above floating buttons.
- **Checked:** bar measured at 390, 768, 1024, 1280, 1366, 1440, 1536 and 1920 pixels (no overflow, constant height); every menu group opens inside the screen and closes with Escape; collapsed menu on phone and tablet; accessible names; accessibility checks.

## 2026-11-05 — v2.12.0: get involved, governance bodies, display options, and the backlog executed
- **Built:** Get involved (routes, working groups, champions and ambassadors, communications kit, badges and an ambassador kit); Governance boards and forums (20 bodies, routes, how a standard is agreed); display options; source labels; cross-portal journey bar; evidence from public code; DAM requirement links per playbook stage; feedback routes to sister portals; usability benchmark; learning progress; draft Jersey and Isle of Man packs; Weaver mapping to the Metadata Exchange Model for review.
- **Backlog:** BL-26, 27, 28, 29, 30, 32, 33, 34 done. BL-12, 15, 31 advanced and waiting on others (DSA review, statistics offices, publication of the strategic roadmap for public sector data). BL-01, 02, 06, 09, 17, 22, 23, 25 need people (participants, an auditor, translators, a live tenant, testers).
- **Checked:** full tests; every internal link and anchor on all 46 pages (hash routes confirmed by hand); four-size inspection; accessibility names; every page at 150% text, wide spacing and high contrast at 390 and 1280 pixels (8 overflows found and fixed); screenshots of new pages in light and dark.
- **Fixed:** an unreplaced `{{REPO}}` placeholder on the capability model page; reflow at large text.

## 2026-11-05 — v2.11.0: user research with your team, and an open roadmap
- **Built:** Take part in user research (introduction for teams, research panel, questions, methods, rounds, quotas, findings, consent) and Open roadmap and priorities (pipeline, objectives, Now/Next/Later with capacity, scores with your-own-weights, tracing, strategy anchors, governance); the research bundle generated with the portal (invitation, email file, consent, sign-up questions, session guides, zip); ten backlog items; two contact topics.
- **Sister repositories (same session):** DAM capability playbooks 1.8.3 signposts the Commons' new pages and fixes a CI break test; the GitHub repos asset catalogue links back from its wheel and standards views and footer (RM-27, first part).
- **Checked:** new tests (research links, privacy of sign-up, every open item scored, MoSCoW matches score band, bundle has no addresses); full suite; accessibility names and roles; four-size inspection; screenshots of both pages at 1366 and 390 pixels.
- **Research:** the Roadmap for modern digital government (19 January 2026) and its commitment to a strategic roadmap for public sector data in April 2026, the data.gov.uk now/next/later roadmap and the DAM policy informed the anchors.

## 2026-11-05 — v2.10.0: standards catalogue, DQV from the Weaver, three portals as one journey
- **Built:** a catalogue of 57 open standards on the interoperability page (filters, status, Rosetta concepts, Weaver support, links into the repos asset catalogue and the DAM playbooks); DQV output from the Metadata Weaver in Python, JavaScript and the command line; the Rosetta grows to 11 standards; a new page, Three portals, one journey, with a comparison, an interactive lineage map, trace one thing, journeys and a join-up plan; `api/xref.json`; sister-portal links on 13 pages and in the wheel and role panels.
- **Sister repositories:** the DAM capability playbooks and the GitHub repos asset catalogue gain matching links back (see their changelogs).
- **Checked:** full test suite; two-engine parity (37 cases); four-size visual inspection (no new findings; the lineage map scrolls sideways on phones by design); accessibility names and roles; screenshots at 1366 and 390 pixels in light and dark.
- **Inputs:** two internal workbooks guided the coverage; only public facts are used (D-STD-01).

## 2026-11-05 — v2.9.0: data management wheel, data quality in change, Microsoft Form feedback

**Built**
- **Data management wheel** (`wheel.html`, `knowledge/dama-wheel.yaml`): interactive SVG wheel (keyboard: Tab, Enter, arrow keys; list view, used by default under 600px); seven audience views; panel with DAM policy action, maturity themes and DMA topics, lifecycle stages, records overlap and Commons pages; maturity overlay from the visitor's own answers; maturity matrix; DMA topic table; audience cards; data and records lifecycle; 11 frameworks (data, records, both); ten join-up actions with a downloadable CSV plan; communities; sources (D-WHEEL-01).
- **Change and delivery roles** (D-ROLE-02): assessment of 14 roles, 10 added to the role picker under "Change and delivery roles"; lifecycle cards with gate questions; RACI with phase filter and role highlight; service blueprint (5 lanes by 6 phases); four proto-personas with journeys. Supplier and information governance roles gained change duties.
- **Feedback** (D-FB-01): `knowledge/feedback.yaml`; feedback strip on every page; Give feedback section on Help us build this with the form status, questions, settings and set-up steps; Word question set in downloads; privacy notice updated.
- **Research:** checked the DMA for Government structure (10 topics, 6 themes, five levels), the DAMA-DMBOK2 revised edition (2024), NISTA replacing the IPA (April 2025), the KIM profession, The National Archives' IMA and the section 46 Code, and Microsoft Forms pre-filled links.
- **Community:** added the Government Knowledge and Information Management Profession and The National Archives' information management.
- **Docs:** decisions, changelog, README, user guide (page and Markdown), FTIR spec, operating model, equality and data protection screening, user research bundle (personas and hypotheses 5 to 7), architecture section 12.
- **Fixed after the CI accessibility check:** striped table rows used a light fallback colour on the two pages that carry their own colour tokens, so dark mode had light-on-light rows (baseline, NDL assurance). Stripes now use a theme-aware overlay defined in the shell. Also fixed in this release: two YAML values lost to unquoted commas and colons (caught by the knowledge tests), and tables no longer hyphenate words.

## 2026-11-05 — v2.8.0: easier tables and signposting, site map, Ask the Commons, sharing and reuse

**Built**
- **Visual layer in the shell (D-VIS-01):** 8-hue palette for light and dark; group colours on menu panels, page labels and page navigation; section hues on heading icons, cards, disclosures, callouts and the On this page list; KPI accents.
- **Tables:** column fitting script (tight, medium, wide, extra-wide), scaled to fit on wide screens; tinted wrapping headers; zebra and hover rows; wide tables extend beside the reading column at 1260px and up; scroll shadows and a sideways hint; sticky headings for tables over 25 rows.
- **Navigation aids:** reading progress bar, Top button, previous and next links with group dots (D-NAV-03), site map page, `sitemap.xml`.
- **Tooltips:** shared accessible tooltip; acronyms on first use (`knowledge/acronyms.yaml`, 43 entries); icon-only buttons; level badges and New/Updated flags; `title` attributes converted.
- **Ask the Commons (D-AI-02):** retrieval over 1,300 passages in the browser, synonym list, answers quote the source with links; "not found" goes to the contact form.
- **Use the Commons your way (D-REUSE-01):** `knowledge/reuse.yaml` (8 routes, 4 AI options, guardrails, customisation); route finder; comparison table; embed code builder with contrast check; API list read live from `api/index.json`; MCP set-up and tools read from `dqkit.mcp_server.TOOLS` at build time.
- **Share this page (D-SHARE-01)** on every page; embed mode; `?search=` deep links; footer links.
- **Docs:** user guide page (Finding your way, six tutorials, tour list), `docs/USER-GUIDE.md`, CHANGELOG, README, releases, architecture section 10.

**Checked**
- Palette contrast: every hue on its tint 4.9:1 or more (light) and 5.8:1 or more (dark); on page backgrounds 5.3:1 or more.
- 191 tests pass (11 new in `tests/test_reuse_nav.py`); two-engine parity 37 of 37; content health 0 errors, 0 warnings.
- Visual inspection of all 40 pages at 1366, 1100, 768 (dark) and 375px; per-page probe in light and dark: no script errors, no sideways page scroll. Fixed during inspection: site map tiles squeezed by a shared link rule; share button insertion on pages whose title is nested; links in card headings now at least 24px tall; easy read summaries missing on two pages. After the first CI accessibility run: tooltip conversion no longer adds names to table cells and other non-interactive elements (axe aria-prohibited-attr), the New/Updated count uses hidden text instead of a label on a span, and the Ask conversation can be scrolled by keyboard.
- Tours: every tour runs to the end and adds the shared steps where the page has them; tooltip shows on hover and focus, closes with Escape.
- Remaining inspection notes (not faults): output areas that stay empty until you run a tool; a few links in lists and survey checkboxes under 24px that meet WCAG 2.5.8 by spacing; the models swimlane diagram and home carousel scroll inside their own frames.

## 2026-11-05 — v2.7.0: catalogues and quality tools, integration and buying

**Asked for:** content and guidance on integrating data catalogue software with data quality software (same or different vendors), resources for finding out more, help for RFI, RFP and wider procurement, and avoiding vendor lock-in through bundles and commercial barriers.

**Researched (5 November 2026):** vendor documentation and announcements for Alation, Atlan, Collibra, Informatica, Ataccama, IBM, Precisely, Qlik Talend, Microsoft Purview, Google Knowledge Catalog, AWS Glue Data Quality and SageMaker Catalog, Databricks Unity Catalog, Snowflake Horizon, DataHub, OpenMetadata, data.world, Great Expectations, Soda and observability tools; ODCS v3.1, OpenLineage, Iceberg REST, Polaris and Unity Catalog open source; Procurement Act 2023, G-Cloud 15 and the Government Commercial Agency, Technology Code of Practice, Open Standards principles, DDaT Playbook, CMA cloud investigation and March 2026 actions, EU Data Act switching rules, the Commons Science, Innovation and Technology Committee report of 3 June 2026, EDM Council CDMC. One false claim (an acquisition that did not happen) was found in an AI-generated vendor profile and excluded.

**Built:** `knowledge/catalogue-integration.yaml`; `catalogues.html` with pattern explorer, depth ladder, filterable product table with side-by-side comparison, lock-in checker (statements, score, risks, clauses, questions), question builder (CSV and Markdown downloads), proof-of-concept and exit checklists, buying route and resources; clause builder deep links; links from Tooling, Buying and suppliers, home capability map and capabilities C3 and C12; search entries.

**Checked:** knowledge tests (6), full suite, browser tests of every control and the hand-off to the clause builder, phone width (long links now wrap), page probe on every page.

## 2026-11-04 — v2.6.0: menu fixed, visual inspection, models made interactive and joined up across the Commons

**Asked for:** fix the first menu running off screen; run a general visual inspection; update the Commons with the new capability, data model and workflow content, as intuitive, dynamic and interactive as possible, with visual navigation.

**Fixed**
- The "1 Start" panel was anchored to the right of its tab and ran off the left edge. Panels now open under their tab and shift to stay on screen (a name clash with the tour's own `place` function first stopped this working; renamed `placePanel`).
- The top bar was wider than the window between 1001 and 1140px, and the brand name shrank to nothing on desktop (a lone "D" on phones). The bar row is now 1360px wide, the full menu shows from 1300px, the brand doesn't shrink, and phones show the logo only (still named for screen readers).
- Visual inspection of all 36 pages at 4 sizes (1366, 1100, 768 dark, 375): sideways scrolling at 320px from an unwrappable chip; controls under 24px. Fixed with shared rules in `base.css`.

**Built**
- Models page: clickable capability map with principle filter and detail panel; workflow player (Play, Previous, Next, role highlight, fit to width, list view, keyboard); record explorer with link lines and fields; deep links for capabilities, workflows, steps and records.
- Home "Find your way by capability"; roles "Your steps in the data quality workflows"; playbook stages link to workflow steps; search and the knowledge graph include capabilities, records and steps.
- Model 1.1.0: navigation fields, validated; Visio shape data and BPMN documentation carry the Commons page and playbook stage.

**Checked:** full test suite, model tests (20), page probe on every page, visual inspection rerun, browser tests of every new link. Axe runs in CI (npm was unreachable locally).

## 2026-11-04 — v2.5.0: capability and data models, Visio process map, BPMN workflows; open actions closed

**Asked for:** act on all recommendations and close open actions; create the data models behind the end-to-end data quality capability, importable into enterprise architecture tools; describe the capability overlaid with the Government Data Quality Framework and other guidance as a downloadable Visio process map; and the underlying workflows.

**Built**
- `models/dq-capability.yaml`: 12 capabilities (36 sub-capabilities), 22 record types with 177 fields and 17 reference lists, 5 workflows (54 steps), all traced to the DAM policy, critical data asset and metadata guidance, ownership model, DQAP steps 1 to 7, issues framework, GDQF principles, Code of Practice, QAAD and ICO.
- `scripts/build_models.py`: ArchiMate exchange XML and Archi CSV, UML XMI, PostgreSQL DDL, JSON Schema, OWL Turtle, data dictionary, capability-guidance matrix, Mermaid ERD (and SVG), an 8-page Visio map (capability map with GDQF overlay and lifecycle band, 5 swimlane workflows, information model, guidance key; shape data on every shape; glued connectors), 5 BPMN 2.0 files with lanes, data objects and diagram layout, plus a PDF of the map.
- Portal page *Capability and data models* (Manage and improve): downloads by tool, capability map with principle filter, map previews, text version of every workflow, searchable information model, import steps, guidance key; one zip of everything.
- `tests/test_models.py` (19 tests) and `build_models.py --check` in CI.
- Recommendations closed: every GitHub Action pinned to a commit SHA (Scorecard); Metadata Weaver checks access rights, security classification and publisher values; new UK GEMINI profile for geospatial assets; `scripts/apply_settings.sh` for the settings only the owner can change (ruleset, secret scanning options, private vulnerability reporting, immutable releases, release tags).

**Found and fixed while building:** unquoted commas in the YAML silently split step names; the generator now refuses unexpected fields. Mermaid HTML labels didn't show outside browsers; the SVG now uses plain text.

**Checked:** model tests, the full test suite, two-engine parity, content health, the portal build and a browser check of the new page; the Visio file rendered page by page in LibreOffice.

## 2026-11-04 — v2.4.0: conformance with government guidance; GitHub supply-chain features

**Asked for:** which other GitHub features and workflows should be enabled; whether the portal's templates conform fully to the Government Data Quality Framework, the DQAP implementation guide, the DAM policy and other relevant guidance.

**Found and fixed**
- DQAP workbook missed parts of steps 1, 2, 4, 5 and 6 (DQAP link, users and needs, review dates, goals, resolution options, costs, communication plan, target and actual resolution dates). All added, with a 7-step checklist tab.
- Playbook rule template used 1 to 5 scales (the issues framework uses 1 to 4); register, issue log, plan and annual review templates lacked purposes, IAO, source data set, successor and review fields. Fixed.
- CDA return lacked purposes, ownership and review fields; UK CDA profile had expires and supersededBy as recommended rather than mandatory. Fixed in both engines (parity 37 of 37).
- GOV.UK issues framework table 4 contradicts its own band rule for a 97.5% target: recorded (IF-5) for the GDS data quality team.
- Added dependency review, PR labels, first-time welcome, release SBOM and signed provenance, CITATION.cff, SUPPORT.md, Q&A link; settings baseline extended.
- `docs/CONFORMANCE.md` written; two GOV.UK sources and five requirements added to the registers.

## 2026-11-04 — v2.3.0: no claude.ai needed; the Commons runs on GitHub alone

**Asked for:** remove the portal's dependency on claude.ai, because most target users have no licence for it; the Commons must be self-sufficient on GitHub's features combined with the portal's own.

**Built**
- Removed every claude.ai call (shared store, sign-in, downloads, model) from 16 pages, the shell and the build; removed the claude.ai build mode; a test now fails if any page calls claude.ai.
- GitHub issue forms for each survey and for maturity sharing, generated from the knowledge base (`scripts/gen_issue_forms.py`, checked by a test); survey forms carry no free text.
- Build-time reading of published contributions, survey answers and maturity shares (`community()`), with totals and the benchmark computed at build time and counts under 5 hidden; the publish workflow runs daily and when the `published` or `withdrawn` label changes.
- Community, Library, Media and Events show published contributions; their forms finish on GitHub. Build page: votes are 👍 reactions; wishes and contact are GitHub forms; the in-portal inbox and moderation queue are gone.
- Rules assistant: plain English to rules with fixed patterns (identifiers, future dates, uniqueness, ranges, allowed values, inclusion, freshness, outliers, required fields), framework and scoring look-ups, and an optional prompt to copy for an approved AI tool.
- Privacy notice, known problems, user guide, architecture, screening and the transparency record (now version 2.0: no model) updated.

**Checked:** tests, parity, browser checks of the assistant, survey hand-off (opens the right pre-filled form), benchmark, and every changed page with no script errors.

## 2026-11-03 — v2.2.0: portal connected to GitHub, outstanding portal items closed

**Asked for:** deal with any remaining outstanding, open or pending items described in the portal and its roadmap, and connect them and every other portal feature to the matching GitHub features and workflows.

**Built**
- Map of every portal feature to its GitHub counterpart (`github.html#map-h`); `window.DQP_GITHUB` helper; pre-filled GitHub fallbacks on Community, Library, Media, Events, wishlist and commissions; contribution form extended (events, blogs, videos, podcasts, details).
- Roadmap computed from the backlog and mirrored as milestones with a needs-people label (`backlog_to_issues.py --sync`); backlog rows show issue, state and votes; GitHub wishlist with thumbs-up votes away from claude.ai.
- Discussion forms (ideas, Q&A, show and tell); co-design and case studies point to them.
- Routines: fact sampling (quarterly workflow), source diffing (monthly link check with cached fingerprints), inclusion review on every release, release assets include the offline portal; routine list updated (17 running, 1 on demand).
- Stale text fixed: operating model (GitHub live; Jira and Confluence are dry runs until secrets are added), pipeline status, Weaver next steps, videos note. Commission contact field removed.

## 2026-11-03 — v2.1.0: search, page drawer, plain English summaries, backlog cleared where it can be

**Asked for:** deal with every issue in the backlog; contact by form only, everywhere, never an email address; no decks or films in any repository unless asked; act on every recommendation that needs no intervention, and take over ongoing maintenance; a retractable page drawer with collapsible sections and flags for new or changed content; search across the portal; more contextual icons, visual elements and motion; link to and learn from the GitHub Repos Asset Catalogue.

**Built**
- Shell: "On this page" drawer (sections from each page's headings, scroll position highlighted, expand or collapse all), collapsible sections, New and Updated flags measured against v2.0.0, a contextual icon on every section heading, search dialog (`/` or Ctrl+K, arrow keys, highlighted matches) over 1,000+ entries, gentle reveal motion for content coming into view (off with reduced motion).
- "In short" plain English summary on every page (`knowledge/easy-read.yaml`); offline zip of the whole portal; page footers show the last change with a link to its history.
- Toolkit: `outlier` check (IQR or z-score) in Python and JavaScript; `dqkit/numbers.py` so numbers read the same whatever the pandas version (pandas cap lifted); `dqkit/linkage.py` for record linkage quality and fairness; GSS geography value sets.
- Weaver: CSVW and Frictionless inputs; GeoDCAT-AP and StatDCAT-AP outputs; profile checks for DCAT-AP, GeoDCAT-AP, StatDCAT-AP and the UK CDA properties.
- Contact: `0-contact.yml` issue form, pre-filled from the portal; email fields and references removed everywhere; tests enforce it. Decks and films blocked by `.gitignore` and a test.
- Operations: ATRS record for the AI assistant; moderation guide and daily Triage workflow; Internet Archive snapshots in the link check; freshness checks for events; Repository health workflow and settings baseline; credential, private-link and marking scan with a self-test; Fabric notebook and HTTP service for Power Automate.
- Prepared and kept open (need people): research kit, accessibility audit brief, translation pack and exporter, co-design time zone planner, Crown Dependency packs, UK metadata model alignment, live tenant trial.
- Linked the GitHub Repos Asset Catalogue from the README, the GitHub page and the tooling page.

**Checked:** full test suite; two-engine parity (37 of 37 cases, including new outlier, number, CSVW, Frictionless and profile cases); self-check; browser probes of the drawer, search, collapsing, the planner and the Weaver profiles with no script errors.

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
