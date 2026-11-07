# Decision log (this repository)

## 2026-11-07 · D-JRN-02 · One journey-bar script for all three portals
- **Decision:** publish the journey bar as `js/journey-bar.js`, a self-contained script that sets its styles on its own elements, and add the same file to the DAM capability playbooks and the GitHub repos catalogue.
- **Why:** BL-34 left the sister portals to adopt the bar; both are maintained alongside the Commons, so adopting it directly closes the item. The playbooks' Content-Security-Policy blocks inline style sheets, which hid a first version, so styles are set through the DOM instead.
- **Alternatives considered:** each portal writing its own bar (three copies drift); a shared CDN file (the portals make no third-party requests).

## 2026-11-07 · D-PROV-01 · A provenance register and audit instead of silent examples
- **Decision:** every file that contains something that looks like an example, placeholder or invented detail is registered in `knowledge/provenance.yaml` with its class and how the page labels it; `scripts/audit_provenance.py` fails the build otherwise. Where another body masters the real thing (GOV.UK organisations, data.gov.uk, ONS geography, Ordnance Survey, the Environment Agency, DfT, DfE), the register links to it. Invented records attributed to real organisations were replaced with real public records.
- **Why:** the user asked to find inferred, dummy and made-up content, replace it with authoritative content where it is mastered elsewhere, and set routines to keep checking it.
- **Kept as illustrative:** content that is illustrative by nature (model contract clauses, worked AI examples with invented figures, the escalation example's simulated dates, the ODCS skeleton), because no authentic equivalent can be published; each is labelled on the page.
- **Alternatives considered:** deleting all examples (the features become hard to understand); live pulls from data.gov.uk on page load (breaks offline use and the no-tracking stance).

## 2026-11-07 · D-DIAG-01 · Pictures first, derived from the model, in the style of a Morgan Map
- **Decision:** a small in-house SVG diagram kit (no libraries) and a "Data quality at a glance" page as a picture-first way in. Workflow steps are placed on two axes, who does it against how much it matters to trust, adapting Tom Wynne-Morgan's Morgan Map (automation against criticality). Positions come from the capability model by published rules (step type and guidance cited), never hand-placed scores. Every diagram has a list equivalent and keyboard access.
- **Why:** the user asked for friendlier, diagram-based views of lineage, traceability and entity relationships that bring in a less technical audience while keeping every feature.
- **Alternatives considered:** Mermaid (a large dependency and its output is hard to make accessible); copying the Morgan Map tool's interface (it is someone else's work; we adapted the idea, not the code).
- **Next:** apply the kit to more pages (ecosystem lineage, knowledge graph, roadmap) and test with users in research round 1.

## 2026-11-07 · D-WEAVE-01 · Weave rules into each platform's own format, derived crosswalk
- **Decision:** add 11 weaves that write Commons rules in each platform's native rule language, mirrored in the browser and held to byte-for-byte parity; derive the crosswalk by running each weave on a one-rule sample per check, so the matrix can never disagree with the code.
- **Why:** the user asked for connectors, add-ons and crosswalks to the data quality solutions of the major vendors. A one-way export people can paste is the lowest-friction connector and keeps rules portable (avoids lock-in, see the catalogues page).
- **Proprietary suites:** Informatica, Ataccama, Qlik, IBM, Precisely, Collibra and others accept SQL-defined rules but publish no open import format, so they get the SQL rule pack plus the crosswalk rather than a guessed proprietary file.
- **Alternatives considered:** live API connectors per vendor (needs credentials and tenants we don't have, and would break silently); hand-written mapping tables (drift from the code).

## 2026-11-07 · D-VEND-01 · Vendor directory with sourced facts only
- **Decision:** `knowledge/vendors.yaml` starts from the 2026 Gartner Magic Quadrant (vendor list from Gartner's public abstract) and the Forrester Wave Q1 2026; shows a position only when the vendor or analyst has announced it publicly; lists only first-party GitHub repositories, each confirmed through the GitHub API; states "no first-party MCP server found" with the date rather than "none"; tones down any product detail without a source.
- **Why:** the user asked for vendors' data quality repositories and their AI agent and MCP features for cataloguing and metadata. Analyst graphics and texts are copyright, and vendor facts change quickly, so every line carries a source and a checked date, and a routine rechecks them.
- **Alternatives considered:** copying Magic Quadrant positions from third-party sites (unverifiable); listing community MCP servers (not the vendor's offer, variable quality).

## 2026-11-06 · D-NAV-04 · One responsive rule set for the global bar
- **Decision:** replace the bar's scattered breakpoints with one set: full menu from 1200 pixels, compact right-hand buttons from 1200 to 1919 pixels (icon-only search and what's new, "Tour"), full labels from 1920, "Menu" below 1200; every control 40 pixels high; the bar 60 pixels; hidden labels clipped rather than removed so screen readers still hear them.
- **Why:** after 2.12.0 added the Aa button, the full menu only showed from 1440 pixels, so most laptops (1280 to 1366) saw "Menu" with empty space, and controls had five different heights. The user asked for the bar to be fixed.
- **Alternatives considered:** shortening group names (they carry the numbered journey); moving display options into the footer (harder to find for the people who need it).

## 2026-11-05 · D-PART-01 · Three ways in, five working groups, champions and badges
- **Decision:** `getinvolved.html` and `knowledge/participation.yaml` set out three routes (contribute, join, champion), five working groups (standards and metadata, accessibility and inclusion, user research, sector and nation packs, data quality practice) with published terms (open membership, 1 to 2 hours a month, consensus, published notes, rotating convenor, yearly review), champion and ambassador roles, a communications kit and seven badges. Supporter is self-declared; other badges are confirmed by a maintainer and recorded with the person's agreement.
- **Why:** the user asked for routes to collaborate and participate, ways for people to engage others in their organisations, ready-made artefacts and a recognition scheme.
- **Privacy:** sign-ups and claims go through public GitHub forms that ask for a GitHub name only, or the private Microsoft Form; the kit's messages name no one and carry no tracking; `mailto:` links have no address.
- **Honest status:** the working groups are "forming" until they have members; badges are recognition, not qualifications or government endorsement.
- **Alternatives considered:** a hosted badge platform such as Open Badges with a backend (new processor and accounts); points and leaderboards (reward volume over quality and exclude people with less time).

## 2026-11-05 · D-GOV-01 · A guide to governance bodies from public facts
- **Decision:** `governance.html` lists 20 bodies in seven layers with purpose, aims, outcomes, rules of engagement, decision rights, cadence, terms-of-reference status (published, described, not found) and activity (active, unclear). Facts come from each body's own page, paraphrased; contact details are not repeated. The Commons' own governance is listed alongside.
- **Why:** the user asked for the boards, committees, councils and forums associated with the capability, with their terms of reference where available.
- **Honesty:** the Open Standards Board shows "activity unclear" (latest minutes March 2023); in-organisation governance is described as a typical pattern because the DAM Policy names roles, not a board.
- **Alternatives considered:** an org chart diagram (implies hierarchy that doesn't exist between advisory and regulatory bodies).

## 2026-11-05 · D-DISP-01 · Display options in the shell
- **Decision:** an Aa button opens display options (text size 100 to 150%, wider spacing, an easier-to-read system font, light, dark or high contrast, reduced movement, source labels on or off), applied before the page draws and saved in the browser. The full menu now shows from 1440 pixels so the bar fits; body text uses rem; shell CSS makes chips, tags, buttons and filters wrap at large sizes.
- **Why:** BL-27 (must, inclusion 3). Browser zoom remains the primary route; these options help people who don't know it or need spacing and contrast too.
- **Alternatives considered:** loading a dyslexia font (an outside request and weight; evidence for special fonts is mixed); per-page settings (inconsistent).

## 2026-11-05 · D-SRC-01 · Source labels by kind of source
- **Decision:** the shell labels every outside link in page content by its address: Official, Standard, International, Code, News or blog (government blogs included), Supplier or Other. A legend sits in the user guide. Facts checked at source keep their "verified" marking.
- **Why:** BL-26, learned from the DAM capability playbooks: readers need to judge how far to rely on each statement.
- **Limits:** classification is by domain, so a label describes the publisher, not whether a particular statement is right.
- **Alternatives considered:** labelling every sentence by hand (thousands of statements; would go stale).

## 2026-11-05 · D-JRN-01 · Journeys across portals through a shared browser key
- **Decision:** "Follow this journey" stores the journey in the browser under `dqp-journey`. All three portals are on the same github.io origin, so any of them can read it and show the same bar; the Commons shows it now.
- **Why:** BL-34. Keeps people's place without accounts or tracking.
- **Alternatives considered:** query strings carried between portals (lost on the first link the portal doesn't control).

## 2026-11-05 · D-CODE-01 · Evidence from public code, imported as aggregates
- **Decision:** `scripts/import_code_evidence.py` reads the repos catalogue's open edition (refusing any other edition) and writes counts and up to five example public repositories per wheel area and standard. Re-run when the catalogue publishes new data.
- **Why:** BL-29. Shows that a practice or standard is really used, without copying the catalogue.
- **Alternatives considered:** fetching live from the catalogue (the page is 13 MB; no API).

## 2026-11-05 · D-RM-01 · An open roadmap where the score sets the priority
- **Decision:** `roadmap.html` and `knowledge/roadmap.yaml` publish how the order is decided. Every open backlog item is scored 0 to 3 on user need, inclusion, strategic alignment and feasibility (weights 3, 3, 2, 2), multiplied by an effort factor (S 1.0, M 0.9, L 0.8). The score's band sets the MoSCoW priority in `knowledge/build.yaml` (2.2 must, 1.6 should, 1.0 could, below that won't), a test enforces it, so the open roadmap, the build page and the GitHub milestones cannot disagree. Next fills in score order up to the quarter's volunteer capacity; the rest is shown as waiting. Anyone can try their own weights; our published order uses ours.
- **Alignment:** eight strategy anchors, led by A roadmap for modern digital government 2025 to 2030 (GDS, 19 January 2026) and the strategic roadmap for public sector data it committed for April 2026. We could not confirm the latter has been published, so it is marked "committed" and BL-31 re-scores everything when it is.
- **Why:** the user asked for a requirements backlog and roadmap users can contribute to and navigate, in GDS-style working in the open, linked to the wishlist, votes and an internal assessment of feasibility, capacity and alignment with government strategy.
- **Triage outcomes recorded:** BL-22 to should, BL-27 to must, BL-29 to could.
- **Alternatives considered:** RICE or WSJF scoring (needs reach and cost-of-delay estimates we don't have; harder to explain in plain English); votes alone (favours people with GitHub accounts, which the equality screening flagged); a separate tool such as a project board only (not navigable without GitHub).

## 2026-11-05 · D-UR-02 · Research with prospective consumers: a panel, a public plan and an emailable bundle
- **Decision:** `research.html` introduces the Commons to teams and recruits a research panel; `knowledge/research.yaml` holds the plan (10 questions split tactical and strategic, methods, rounds, quotas, findings, consent). The build generates an emailable bundle in `downloads/research/`. Sign-up uses a Microsoft Form in the Commons team's tenant once its link is set; until then people use the contact form and give only their organisation type and role, because contact messages are public GitHub issues.
- **Why:** the user asked for a bundle to introduce users and their teams to the portal and recruit for testing, delivered by email and integrated in the portal for ongoing research that sets tactical and strategic direction.
- **Privacy and inclusion:** contact details are never on GitHub or the portal (tested: one screener question collects them, no email addresses anywhere in the bundle, the .eml has no sender or recipients). Quotas include assistive technology users, people with little data experience, Welsh speakers, every nation and the voluntary sector. Access support is arranged and paid for by the team.
- **Builds on:** BL-01 and the research kit (`docs/research/RESEARCH-KIT.md`), which stays the detailed guide for facilitators.
- **Alternatives considered:** a GitHub issue form for sign-up (public, so it can't hold contact details); a third-party recruitment platform (new processor and cost).

## 2026-11-05 · D-ECO-01 · Link the three portals, do not merge them; one cross-reference manifest per portal
- **Decision:** DQ Commons, the DAM capability playbooks and the GitHub repos asset catalogue stay separate sites with separate owners and release cycles. They join up through shared keys (the 11 DAMA areas as DM-GOV … DM-DQ, role codes, standard names and page paths), a published manifest per portal (`api/xref.json` here, `data/xref.json` in the playbooks), "Continue in a sister portal" asides on the pages where a journey naturally moves on, and a page (`ecosystem.html`) with a like-for-like comparison, a lineage map, a trace tool, five journeys and seven join-up actions. A live check compares this portal's keys with the playbooks' manifest in the visitor's browser.
- **Why:** the user asked how the portals could work better together, with lineage and traceability and journeys that start in one and continue in another. Each portal answers a different question (what the policy needs; how to do data quality; what already exists in code); merging would blur ownership and break links people rely on.
- **Comparison method:** each portal's own public pages and repository were read on 5 November 2026; anything not found is marked "not seen in our review" rather than "none", and the page says so.
- **Alternatives considered:** one merged site (ownership and release clash); iframes of each other's pages (inaccessible, fragile); a shared database (none of the portals has a backend, by design).

## 2026-11-05 · D-STD-01 · A standards catalogue from public facts only
- **Decision:** `knowledge/standards-catalogue.yaml` lists 57 standards used across UK government and the wider public sector for data, digital, cyber and technology. Each entry holds public facts only: name, publisher, a link to the specification, its status in GOV.UK guidance (Mandated or Recommended open standard, UK guidance, or Widely used), the Rosetta concepts it expresses, Weaver support and its name in the repos asset catalogue. The structure and wording are the Commons' own.
- **Why:** the user supplied two internal workbooks (a crosswalk and a draft classification) to guide the work and chose "public facts only": standard names, publishers, links and W3C or ISO mappings may be used; workbook text, the draft taxonomy and the workbook names are not published (tested).
- **Status:** DQV is "Widely used": a W3C Group Note that GOV.UK names alongside DCAT in its recommended profile for describing data assets in a catalogue, not itself a selected open standard.
- **Alternatives considered:** importing the workbooks (they are marked OFFICIAL and one is a draft); linking only to the GOV.UK list (no mapping to concepts or tools).

## 2026-11-05 · D-DQV-02 · The Metadata Weaver writes metadata quality as DQV (builds on D-014)
- **Decision:** the Weaver adds a DQV output: a `dqv:QualityMetadata` graph with measurements for critical data asset property coverage, coverage per output format and conformance to each profile, all in the Commons `metadata` dimension, plus a quality annotation listing missing CDA properties. Python and JavaScript produce identical output (parity checked).
- **Why:** D-014 chose DQV to carry data quality results; metadata quality is the part the Weaver can measure itself, and publishing it as DQV lets a catalogue show how complete a record is.
- **Alternatives considered:** a bespoke score (not interoperable); SHACL validation reports (heavier, and describe violations rather than measurements).

## 2026-11-05 · D-WHEEL-01 · An original data management wheel, mapped to maturity, the DAM policy and records management
- **Decision:** add `wheel.html` in Check and assess, next to the maturity self-assessment, drawing the 11 DAMA-DMBOK knowledge areas as an original Commons diagram (our own groupings into four lifecycle groups, colours and text; DAMA's names only, with attribution). Each area carries seven audience views, the DAM policy action, mappings to the Commons maturity themes and the DMA for Government topics, lifecycle stages, the records management overlap and Commons pages. The visitor's own maturity answers (kept in their browser) can shade the wheel.
- **Why:** the user asked for a DAMA-related view linked to the maturity model, showing each audience how to shape enterprise data management, the lifecycle, DAM policy adoption and the join-up with records and information management. A wheel is the recognised mental model; putting it beside maturity turns results into a capability map.
- **Copyright:** DAMA's wheel graphic and DMBOK text are not reproduced. Mappings are labelled as the Commons' judgement, for review with DAMA UK, the Data Management Community and the KIM profession.
- **Alternatives considered:** a section inside the maturity page (too long, and the wheel serves other journeys too); adopting DAMA's own maturity levels (the government already uses the DMA's five levels).

## 2026-11-05 · D-ROLE-02 · Ten change and delivery roles join the Commons' roles, with a lifecycle, RACI and service blueprint
- **Decision:** after assessing 14 programme and project roles, add 10 (SRO, programme or delivery manager, PMO, business change and transition lead, business analyst, product or service owner, architects and design authority, data migration lead, test lead, records and information manager) to `knowledge/stakeholders.yaml` with `group: change`. Supplier, information governance, commercial and assurance reviewers are covered elsewhere. `knowledge/change-delivery.yaml` holds the assessment, a six-phase lifecycle mapped to GDS phases and gateway-style assurance gates (now NISTA-led for major projects), a RACI with exactly one accountable role per activity, a service blueprint and four proto-personas with journeys.
- **Why:** data quality is mostly made or broken during change; the everyday roles cannot fix decisions programmes have already taken. Assurance reviewers need concrete gate questions.
- **Note:** the role id `bizchange` avoids clashing with the `#change` section anchor on the roles page (tested).
- **Alternatives considered:** a separate programme page (splits the role picker); folding change duties into existing roles (hides who is accountable during delivery).

## 2026-11-05 · D-FB-01 · A Microsoft Form as an extra feedback route, configured by link
- **Decision:** add a Microsoft Form route in `knowledge/feedback.yaml`. The portal shows it only when the form's share link (or a pre-filled link with the word PAGE) is pasted in; until then it says the form is being set up. The build publishes the question set as a Word document for Quick import. Every page ends with a feedback strip.
- **Why:** many public servants use Microsoft 365 and have no GitHub account; the GitHub form alone excluded them (noted in the equality screening since v1.0.0).
- **Privacy:** no names, emails or sign-in; "Record name" off; responses in the Commons team's tenant, exported monthly and deleted after 12 months. No email address is shown anywhere, in line with the contact-by-form rule.
- **Alternatives considered:** a hosted form service (new processor, cost); embedding the form in an iframe (third-party content inside every page).

## 2026-11-05 · D-VIS-01 · One accessible visual layer in the shell: group and section colours, fitted tables, tooltips
- **Decision:** the shell (not each page) carries an 8-hue palette, each with a soft tint, defined for light and dark themes. Each menu group has a fixed hue (Start teal, Learn purple, Check blue, Improve orange, Apply green, Contribute pink); top-level sections on a page take turns from the group's hue. Tables are fitted by a script that measures each column's text: short columns shrink to fit, long-text columns get a minimum width, scaled down step by step until the table fits on screens 700px and wider; phones keep readable columns and scroll sideways. Zebra and hover use zero-specificity selectors so page-specific cell colours (heatmaps, verdicts) always win. Acronyms are explained on first use from `knowledge/acronyms.yaml`; tooltips follow WCAG 1.4.13 (hoverable, persistent, dismissible with Escape).
- **Why:** the user asked for easier tables, more colour and signposting with less cognitive load. Doing it once in the shell reaches all pages, including the four that carry their own tokens.
- **Accessibility:** every text colour meets 4.5:1 on its tint and on the page background in both themes (checked in the build log); colour is never the only signal (labels, numbers and words carry the meaning); motion respects reduced motion; print hides the aids.
- **Alternatives considered:** fixed column widths per table (fragile, 60+ tables, breaks when content changes); `table-layout: fixed` (truncates long text); a CSS framework (adds weight and a dependency).

## 2026-11-05 · D-NAV-03 · A site map page and previous / next links in menu order
- **Decision:** `sitemap.html` draws the menu as data (`__K_SITEMAP__`, also `api/pages.json`), with a level filter, text filter and suggested routes. The build adds previous and next links in menu order to every page, with dots for the pages in the current group. `sitemap.xml` is generated for search engines.
- **Why:** gives a single overview and a linear path through the Commons without changing the six-group menu people already know.

## 2026-11-05 · D-AI-02 · Ask the Commons is retrieval, not generative AI
- **Decision:** the question box ranks passages (BM25-style scoring over every page section and knowledge item, with a small synonym list) and quotes the best one word for word with its source link. It loads `ask-index.js` and runs entirely in the browser.
- **Why:** answers stay traceable and checkable, nothing is sent to a third party, there is no running cost and no claude.ai or other AI dependency (D-POL-01). Organisations that want generative answers can connect their own approved assistant through the MCP server or `api/passages.json`.
- **Alternative considered:** a hosted language model. Rejected for now: needs a service, budget, a DPIA, and risks unsourced answers.

## 2026-11-05 · D-REUSE-01 · Reuse through static, read-only files: API, feed, embed mode and white-label
- **Decision:** the open data API is a set of JSON files written by the build (`api/`), served by GitHub Pages like the rest of the portal: no key, no tracking, versioned in `api/index.json`. Embed mode is a query string (`?embed=1&accent=RRGGBB`, hex only) that hides the shell and keeps a link to the source; the host can size the frame from a `dqp-height` message. White-label is a fork plus documented edits.
- **Why:** nothing new to run or secure; works on closed networks from the offline zip; matches the open standards and reuse principles in the Technology Code of Practice.
- **Alternatives considered:** a live API service (needs hosting and support); an embeddable script widget (runs Commons code inside the host page, harder to approve).

## 2026-11-05 · D-SHARE-01 · Share without third-party scripts
- **Decision:** Share this page uses the device share sheet where available, the clipboard, a `mailto:` link with no address, and plain share links for Microsoft Teams and LinkedIn opened in a new tab. No share widgets or tracking scripts are loaded.
- **Why:** no cookies or trackers (privacy notice), no email address shown anywhere, and it works offline for copy and email.

## 2026-11-05 · D-COM-02 · Guidance on catalogue and quality tools is vendor-neutral, sourced and dated, and favours standards-first
- **Decision:** a new page sets out how catalogues and quality tools connect, a product landscape with each claim sourced to the vendor's own documentation or official notices and dated, five integration patterns ranked by lock-in, a five-level integration depth scale, a lock-in checker, an RFI and RFP question bank, a proof-of-concept script and an exit checklist. Standards-first (ODCS, OpenLineage, DCAT and DQV, Iceberg) is the recommended target whatever is bought. Risks link to existing contract clauses (C03, C04, C12 to C20) through a deep link into the clause builder.
- **Why:** organisations are buying catalogues and quality tools now, often bundled, while the market consolidates (Salesforce and Informatica, ServiceNow and data.world) and Parliament and the CMA have highlighted lock-in. Buyers need questions and tests, not rankings.
- **Safeguards:** no rankings or endorsements; product facts carry sources and a checked date and a three-monthly review; analyst reports are flagged as paid research; an AI-generated vendor profile found during research to contain a false acquisition claim was not used, and the page warns buyers to check facts at source.
- **Alternatives considered:** a scored vendor comparison (rejected: not neutral, quickly stale, and the Commons cannot test every product); leaving it to the existing tender questions (rejected: they cover data quality duties, not tool integration, portability or bundling).

## 2026-11-04 · D-NAV-02 · The capability model is the Commons' map: every capability, step and role links to where the work is done
- **Decision:** the model gains navigation fields (`pages`, `page`, `stage`, `lanes`). The models page becomes interactive (capability map, workflow player, record explorer, deep links), and the home, roles, playbook, search and knowledge map pages link into it. The generator refuses links to pages, stages or roles that don't exist.
- **Why:** people arrive with a job to do ("I'm a data owner", "we need to prioritise issues"). The model already says who does what and with which records; using it as the map turns 36 pages into one joined-up route, and keeps the links honest because they are tested.
- **Accessibility:** every diagram has a text equivalent (workflow list view, record list, keyboard operation with Tab, Enter and arrow keys); nothing is dimmed or animated on load; Play respects reduced motion.
- **Alternatives considered:** a separate navigation file (rejected: would drift from the model); embedding a BPMN viewer library (rejected: a third-party script, larger pages and weaker keyboard support than drawing the SVG ourselves).

## 2026-11-04 · D-NAV-01 · Menus stay on screen; full menu from 1300px
- **Decision:** dropdown panels open under their tab and shift to stay inside the window, with height capped to the space below the bar; groups with more than six pages use two columns; the full menu shows from 1300px wide (it needs about 1,260px), the Menu button below that.
- **Why:** the first menu was anchored to its right edge and ran off the left of the screen; between 1001 and 1140px the bar was wider than the window, and the brand overlapped the menu.
- **Alternatives considered:** shorten menu labels (rejected: the group names carry meaning); a mega-menu across the full width (rejected: a bigger change to a pattern people already know).

## 2026-11-04 · D-MOD-01 · One YAML source for the capability, data model and workflows; generated exports for each tool family
- **Decision:** `models/dq-capability.yaml` describes the enterprise data quality capability (12 capabilities, 22 record types, 5 workflows) with the guidance each part implements. `scripts/build_models.py` generates ArchiMate 3.1 Open Exchange XML and an Archi CSV set, UML 2.5.1 XMI, PostgreSQL DDL, JSON Schema 2020-12, OWL in Turtle, a data dictionary and capability-guidance matrix, a Mermaid ERD, a Visio `.vsdx` process map and BPMN 2.0 files with diagram layout. Outputs are deterministic and CI fails if they drift from the YAML. The Visio file is written directly as an Open Packaging file (no Visio licence or template needed) and checked by rendering it in LibreOffice.
- **Why:** architects use different tools (Archi, Sparx EA, BiZZdesign, Visio, Camunda, erwin, Protégé); one source keeps every view consistent and reviewable as text, and open formats avoid locking anyone into one product.
- **Overlay:** each capability is coloured by the GDQF principle it mainly serves; each workflow step carries DAM, DQAP, issues framework and other codes and is coloured the same way. Swimlanes are roles from the data ownership model and DQAP guide.
- **Privacy:** the model holds roles, not people's contact details; contact routes are forms (D-REPO-02). A test refuses email, phone or address fields.
- **Alternatives considered:** a LinkML model as the source (rejected for now: it covers data, not capabilities or processes; `model/cda-quality.linkml.yaml` stays for the DQV proposal); drawing in Visio by hand (rejected: needs a licence, can't be diffed, drifts from the data model); a hosted modelling tool (rejected: licences and another supplier).
- **Limits, stated openly:** files were not opened in Microsoft Visio, Archi, Sparx EA or Camunda in this environment, and the official XSDs were unreachable; structural tests check every reference instead. Users are asked to report import problems through the contact form.

## 2026-11-04 · D-CONF-01 · Templates follow the GOV.UK guidance's "must record" lists; the stated rule wins over a table
- **Decision:** the DQAP workbook, playbook templates, CDA return and Weaver profile record every item the DQAP implementation guide, the critical data asset guidance, the data ownership model and the metadata guidance ask for (assessment in `docs/CONFORMANCE.md`). Where the issues framework's table 4 (96.75% for a 97.5% target) contradicts its stated rule (halfway, giving 96.25%), the Commons follows the rule and records the discrepancy for the GDS data quality team. Personal names asked for by the ownership guidance are recorded only in an organisation's own workbook or return, never in the Commons.
- **Why:** the DAM policy says a DQAP, or an existing mechanism, must cover all 7 steps; a template that misses a step makes users non-compliant without knowing.
- **Alternatives considered:** follow the table (rejected: it breaks the method for other targets and disagrees with the worked examples); leave name fields out (rejected: the ownership model requires names; they belong in the organisation's records).

## 2026-11-04 · D-GH-03 · Adopt GitHub's supply-chain and contribution features
- **Decision:** add dependency review on pull requests, area labels, a first-time welcome, signed build provenance and an SBOM on releases, a citation file, a support file and a Q&A link in the issue chooser. Recommend to the owner: a main-branch ruleset, secret scanning validity checks and generic patterns, immutable releases, a GitHub Project for the roadmap, and pinning actions to commit SHAs.
- **Why:** these are free on public repositories, raise the OpenSSF Scorecard and make downloads verifiable, which public bodies increasingly ask for.
- **Alternatives considered:** third-party bots (rejected: more permissions, more suppliers); a stale-issue bot (rejected: closing people's issues automatically conflicts with the moderation service levels).

## 2026-11-04 · D-GH-02 · No claude.ai dependency: the Commons runs on GitHub and its own code
- **Decision:** remove every use of claude.ai from the portal: the shared store, sign-in, in-portal moderation, claude.ai downloads, the AI model behind the assistant, and the claude.ai build mode. Submissions go through GitHub issue forms pre-filled by the portal (surveys and maturity sharing get generated forms, `scripts/gen_issue_forms.py`); moderators publish with the `published` label; the portal build counts and shows results (published items, survey totals, the maturity benchmark, votes) with counts under 5 hidden, and republishes daily and on publish or withdraw. The assistant drafts rules with fixed, published patterns in the browser, with an optional "copy as a prompt" for an AI tool the person's organisation has approved.
- **Why:** the project lead's instruction: most target users have no government or corporate claude.ai licence, so anything that needs it excludes them. GitHub is free, already used across government, and offers forms, reactions, labels, Actions and Pages.
- **Trade-offs, stated openly:** GitHub issues are public at once and show the submitter's username, so survey and maturity answers are no longer anonymous to GitHub; the forms say so plainly, free text is never sent, totals hide counts under 5, and a colleague can submit for a team. Results update daily rather than instantly. The assistant recognises fewer phrasings than a language model, and lists what it doesn't recognise.
- **Alternatives considered:** a hosted backend such as a database or forms service (rejected: cost, another service to secure, and third-party data processing); keep claude.ai as an optional extra (rejected: two ways of doing everything, and an unfair experience for people without a licence); private survey collection by email (rejected: D-REPO-02, contact by form only).

## 2026-11-03 · D-GH-01 · GitHub is the working system behind every portal feature
- **Decision:** each portal feature maps to a GitHub feature (map on `github.html`). Forms that save on claude.ai open the matching GitHub issue form or discussion, pre-filled, everywhere else (`window.DQP_GITHUB` in the shell). The roadmap is computed from backlog statuses and mirrored as milestones by `scripts/backlog_to_issues.py --sync` with the same rule. The portal build reads public issue data once (issue numbers, states, thumbs-up votes, wishlist) with a read-only token; visitors' browsers never call GitHub (D-POL-01). Release tags stay a person's decision: the release workflow runs when a maintainer pushes a tag.
- **Why:** the portal described processes (roadmap, votes, co-design, releases) that only fully worked on claude.ai or existed only on paper. GitHub already offers forms, reactions, milestones, discussions, releases and Actions, so the Commons uses them rather than building its own.
- **Alternatives considered:** GitHub Projects board (left for later: user-owned projects need a personal token, which the Commons doesn't hold); calling the GitHub API from the browser (rejected: third-party requests and rate limits); creating tags automatically from the release record (rejected: releasing stays a deliberate human step).

## 2026-11-03 · D-REPO-01 · No decks or films in the repository unless explicitly allowed
- **Decision:** slide decks and video files are ignored by `.gitignore` and refused by `tests/test_repo_policy.py`, unless their path is listed in `.media-allowlist`.
- **Why:** the project lead's standing rule. They are large, hard to review and hard to make accessible, and they belong where they are presented.
- **Alternatives considered:** Git LFS (rejected: the content still doesn't belong here); a size limit only (rejected: small decks would slip through).

## 2026-11-03 · D-REPO-02 · Contact by form only, everywhere
- **Decision:** the only way to reach the Commons is the contact form (a GitHub issue form, `0-contact.yml`, pre-filled from the portal). No email address appears in any page, document, data file or template; the case study template asks for a contact route, not a name and email. A test fails on any email address other than GitHub's no-reply addresses.
- **Why:** the project lead's standing rule; publishing addresses invites spam and exposes people; one route is easier to moderate and measure.
- **Alternatives considered:** a shared team inbox (rejected: still an address to publish and a single person's burden); a third-party form service (rejected: D-POL-01, no third-party requests).

## 2026-11-03 · D-REPO-03 · Scan for credentials, private links and marking banners, with a self-test
- **Decision:** `tests/test_repo_policy.py` refuses tokens and keys, links to private claude.ai chats, projects or artifacts, and protective marking banners, and plants one example of each to prove the scan works. A weekly Repository health workflow compares settings with `.github/settings-baseline.json` and reports drift without changing anything.
- **Why:** adapted from the GitHub Repos Asset Catalogue, which uses the same patterns; the repository is public, so prevention must be automatic.
- **Alternatives considered:** rely on GitHub secret scanning alone (kept as well, but it doesn't cover private links or markings).

## 2026-11-03 · D-TK-02 · The toolkit reads numbers with its own rule
- **Decision:** `dqkit/numbers.py` reads numbers from text (optional spaces and sign, digits with optional point, optional exponent, "inf"), giving the correctly rounded value; `engine.js` uses the same rule. pandas is no longer used for this, so the `<3.1` cap (D-CI-01) is lifted to `<4`.
- **Why:** pandas 3.1 changed its parser, which made results depend on the installed pandas version and broke parity. Owning the rule makes Python and the browser agree on every pandas version. Issue #25.
- **Alternatives considered:** copy pandas 3.1's parser into JavaScript (rejected: results would differ again for anyone on pandas 3.0, and again at the next change).

## 2026-11-03 · D-UX-01 · Page drawer, collapsible sections, change flags and portal search
- **Decision:** every page gets an "On this page" drawer built from its headings, collapsible sections, and New or Updated flags for sections that differ from the previous release (fingerprints in `portal/section-baseline.json`, regenerated at each release by `scripts/section_baseline.py`). Search covers pages, sections and named items in the knowledge base; its index (`search-index.js`) loads only when search is first opened. Motion is used only for content coming into view, never hides content already on screen, and is off for anyone who prefers reduced motion.
- **Why:** pages are long; the menu helps across the portal but not within a page. Flags show returning readers what changed without reading release notes.
- **Alternatives considered:** a server-side search service (rejected: D-POL-01 and cost); flags typed by hand (rejected: they would be forgotten); a fixed side table of contents (rejected: takes width from tables on smaller screens).

## 2026-11-03 · D-WV-02 · Application profiles in the Weaver are simplified shapes, not full SHACL
- **Decision:** the Weaver checks the DCAT output against simplified must/should property lists for DCAT-AP 3, GeoDCAT-AP, StatDCAT-AP and the UK critical data asset properties, plus ISO 8601 dates, in both engines. It says plainly to validate with the official SHACL shapes before publishing.
- **Why:** a full SHACL engine in the browser is heavy; the common gaps are missing properties and bad dates, which these checks catch. Issues #11 and #13.
- **Alternatives considered:** bundle a SHACL validator (rejected for now: size and a third-party dependency); skip the check (rejected: users asked to know if they meet a profile).

## 2026-11-03 · D-OPS-02 · Weekly maintenance by a scheduled task, with people-dependent work kept open
- **Decision:** a weekly scheduled task (Monday mornings, London time) reviews CI, open issues, Dependabot pull requests, content health and settings drift, fixes what it safely can, and reports the rest. Backlog items that need people (user research, independent audit, translation, live co-design, tenant trials, checks with statistics offices) are prepared in full and kept open.
- **Why:** the project lead handed over ongoing maintenance; closing items that need people would overstate what is done.
- **Alternatives considered:** close prepared items (rejected: misleading); daily runs (rejected: too noisy for the volume).

## 2026-11-03 · D-POL-03 · Version 2.0.0, not 1.7.0
- **Decision:** release as 2.0.0.
- **Why:** the release policy treats removing files, links or commands people rely on as a major change; this release removes `dqkit survey`, two documents and some page anchors.

## 2026-11-03 · D-POL-02 · Keep the public repository to published or original material; hold the rest privately
- **Decision:** remove from the public repository and portal: content drawn from documents shared privately and not published by their owners; internal tooling work and our critique of it; unsent draft messages; unconfirmed dates from an internal timeline; advice framed for the CDO Council and GDS; figures from the internal register prototype. The removed material is kept in a private bundle for a private repository, and the public git history is rewritten to drop it.
- **Why:** the repository became public on 2 November. Republishing or critiquing others' unpublished work in public breaks trust and handling expectations; unconfirmed dates presented as fact mislead; advice to a governance body should reach it first, privately.
- **Kept, with credit and flagged for the owners' permission:** the trust level (adapted from the IOPC's approach), the DQAP route for data you produce or receive (from a community decision tree), the case study drafter and the workbook's suggested RACI. These embody general methods rather than reproduce documents, and removing them would break the CDA return format.
- **Alternatives considered:** remove everything derived from those sources (rejected for this release: breaks outputs people use; revisit once owners respond); keep all and add caveats (rejected: does not address handling).

## 2026-11-03 · D-POL-01 · No third-party requests from the portal
- **Decision:** bundle js-yaml (4.2.0, MIT) into the build and remove Google Fonts; pages use system fonts.
- **Why:** many government networks block CDNs, which broke the check page's rules reader with a misleading error; and font and script CDNs see every visitor's IP address, which conflicts with the privacy promise that nothing leaves the device.
- **Alternatives considered:** self-host the web fonts (possible later; adds files and licences to manage).

## 2026-11-03 · D-IA-01 · Menu in journey order with levels
- **Decision:** six groups in the order people work: 1 Start, 2 Learn, 3 Check, 4 Improve, 5 Apply, 6 Contribute. Every page carries a level (Beginner, Intermediate, Advanced) shown as a badge; the breadcrumb follows the group automatically. The home page and README offer three journeys.
- **Why:** the old groups (Start, Do, Know, Govern, Scenarios, Community) mixed task types with topics, so newcomers had no obvious path and experts had to hunt. Levels match the three-level scales used by APS, Canada, JNCC and others (see professions.html).
- **Alternatives considered:** persona-first menu (kept as routes on Home and For your role); level-first menu (splits related pages apart).

## 2026-11-03 · D-PRO-01 · Map data quality across professions from sources read on the day
- **Decision:** `knowledge/professions.yaml` records, for each profession or framework, only what its source says (checked 3 November 2026), plus the Commons' mapping to 12 capabilities, marked as an interpretation.
- **Why:** senior audiences will rely on it; each claim needs to stand up. The research found no standalone data quality skill in the GDaD framework, which is itself a useful finding.

## 2026-11-02 · D-CI-04 · Security scanning and a public health score
- **Decision:** add CodeQL (Python, JavaScript, Actions; security-and-quality queries) and OpenSSF Scorecard workflows. Add Dependabot for pip and GitHub Actions, grouped into one weekly pull request each, plus CODEOWNERS.
- **Why:** the repository is now public and meant for reuse across government. Departments assessing it need visible, independent evidence that it is maintained securely. Automation keeps it current without manual checking.
- **Dependabot range rule:** `increase-if-necessary` for pip. The default raised every minimum to the newest release (PR #28), which would lock out departments on older, centrally managed environments with no benefit, since CI already installs the newest allowed versions.
- **Alternatives considered:** GitHub's one-click CodeQL "default setup" (equivalent, but needs a settings change this session cannot make, and is less visible in the repository).

## 2026-11-02 · D-CI-03 · Root LICENSE is the exact MIT text; OGL statement moves to docs/CONTENT-LICENCE.md
- **Decision:** remove the appended OGL paragraph from `LICENSE`; state the content licence in `docs/CONTENT-LICENCE.md` and link it from the README.
- **Why:** GitHub showed the licence as "NOASSERTION" (unknown), because it only recognises an exact licence text. An unlabelled licence discourages reuse and hides the repo from licence-filtered searches.
- **Alternatives considered:** keeping one combined file (rejected: GitHub cannot detect it); a second root LICENSE-OGL file (rejected: two root licence files can also confuse detection).

## 2026-11-02 · D-CI-02 · Move GitHub Actions to Node 24 releases
- **Decision:** checkout, setup-python, setup-node, upload-artifact v7; upload-pages-artifact and deploy-pages v5; github-script v8 (same scripting interface as v7); Node 22 for the checks. Dependabot keeps them current from now on.
- **Why:** every run warned that Node 20 actions are deprecated and being forced onto Node 24; Node 20 itself is end of life.

## 2026-11-02 · D-CI-01 · Cap pandas below 3.1 until the browser engine is re-aligned
- **Decision:** `pandas>=2.0,<3.1` in `requirements.txt` and `pyproject.toml`; Dependabot ignores pandas 3.1+. Add `odfpy` (OpenDocument spreadsheets) as a declared dependency.
- **Why:** on the first GitHub run, CI installed pandas 3.1.0, which parses numbers precisely (for example "0.30000000000000004" stays as written). The portal's JavaScript engine is verified to match pandas 3.0 exactly, so the parity test failed (536 differences in one micro-test, 10 in the finance fixture). `odfpy` was installed on the build machine but never declared, so `.ods` tests failed on a clean runner.
- **Alternatives considered:** change the JavaScript engine to the pandas 3.1 behaviour now (rejected for this fix: then results would differ for anyone on pandas 3.0; needs its own change with both versions tested). Follow-up tracked as a GitHub issue.

## 2026-10-30 · D-077 · One effort model, two front ends
- **Decision:** activities and defaults live in `knowledge/effort.yaml`; the baseline page and `dqkit/effort.py` both read it, and a test checks they agree on a known case.
- **Why:** the CDO Council brief needs the same numbers as the interactive page; a second copy would drift.

## 2026-10-30 · D-076 · Q-FAIR rated from evidence, missing fields lower the rating
- **Decision:** Q is rated from measured results; F, A, I and R only from fields in the asset record. A missing field is reported as missing and lowers the rating; nothing is inferred. Scale and "indicator, not an absolute measure" follow the Geospatial Commission's 2022 benchmark.
- **Why:** the user asked how far the baseline aligns with Q-FAIR. Rating from evidence makes the gap visible (the illustrative NDL portfolio is Good on quality but needs attention on A, I and R because those fields aren't recorded).
- **Alternatives considered:** a numeric FAIR score (rejected: false precision; the benchmark itself is qualitative).

## 2026-10-30 · D-075 · A role-based front door and a public gap register
- **Decision:** a "For your role" page for 13 stakeholder roles, a CDO Council brief built on every release, and a gap register with status, severity and owner of the response. Open gaps name the decision needed and who makes it.
- **Why:** different stakeholders need different things from the same evidence; listing gaps openly (including those the Commons can't fix) is more useful to the Council and GDS than silence.

## 2026-10-30 · D-074 · Publish from GitHub Actions; releases come from the release record
- **Decision:** `pages.yml` builds and publishes the portal (and bundle) on every push to `main`; `release.yml` creates a GitHub release when a `vX.Y.Z` tag is pushed, refusing tags not in `knowledge/releases.yaml`. Package, toolkit and MCP versions are read from or tested against that file.
- **Why:** the user asked to publish to the repository. Automation means the public copy always matches `main`, and release notes can't drift from the drawer and changelog.
- **Alternatives considered:** a `gh-pages` branch (rejected: a second copy of built files in history); publishing only weekly from the pipeline (rejected: content changes would wait up to a week).

## 2026-10-30 · D-073 · Playbook progress is judged from evidence files, never from people
- **Decision:** `dqkit playbook status` marks a stage "done" only when its evidence file exists with content (register row, rules, results, action plan, owned actions, statement or DQV, history, review) and every checklist item in the workspace README is ticked.
- **Why:** self-reported ticks alone overstate progress; files alone miss judgement. Both together are honest, and nothing about individuals is recorded.

## 2026-10-30 · D-072 · Horizon scans add only sources read at source
- **Decision:** each scan (this one: October 2026) adds items only after reading the primary page; trade-press items are used only when they report a primary statement (for example a written parliamentary answer). Paid standards are listed by catalogue record and say so. Drafts and bills are labelled as such.
- **Why:** keeps the library 100% "read in full" and stops hype or unconfirmed claims entering the Commons.

## 2026-10-30 · D-071 · Frameworks with no public document are "Not publicly available", not "partly verified"
- **Decision:** a third verification state, `unpublished`, for frameworks we were told about but which have no public source. They stay listed, with an explanation and an empty link, and can be filtered.
- **Why:** "partly verified" implied a check was still to do. Hiding them would lose useful mappings; labelling them is honest.

## 2026-10-30 · D-070 · One playbook source, generated document, generic terms
- **Decision:** the data quality management playbook lives in `knowledge/playbook.yaml`; the portal page and `docs/DQ-MANAGEMENT-PLAYBOOK.md` are both generated from it (`--check` in CI). UK DAM policy and DQAP clauses are attached to each stage, but each stage is written as a plain job, with a terms table for other mandates.
- **Why:** the user asked for a playbook for CDAs under the DAM policy that works anywhere. One source keeps page and document in step; plain jobs let devolved, local, international and non-government users adopt it without the UK mandate.
- **Alternatives considered:** a separate playbook per jurisdiction (rejected: duplicates the same eight stages); a Word document (rejected: drifts from the toolkit and can't be ticked off).

## 2026-10-30 · D-069 · Inclusion is a check in every stage, not a separate chapter
- **Decision:** every playbook stage carries an inclusion check, results are broken down by group where lawful, and the issues framework weighs who is affected, not only how many.
- **Why:** averaging hides poor quality for small groups, which is how data excludes people. Putting the check in each stage makes it routine.

## 2026-10-15 · D-068 · One release record drives the version, the drawer and the change log
- **Decision:** `knowledge/releases.yaml` holds every release; the build takes the version from it; a test checks each release is in CHANGELOG.md.
- **Why:** version numbers and release notes drifted between files. One source keeps the portal, repository and docs in step.

## 2026-10-15 · D-067 · A standalone build bundle generated from the docs
- **Decision:** `scripts/build_bundle.py` renders the mandated documents into one page, with no extra packages; CI fails if the committed bundle is stale.
- **Why:** reviewers want one place to read everything; generating it means it can't drift from the documents.

## 2026-10-15 · D-066 · The Commons mark
- **Decision:** three overlapping circles (the many organisations that hold public data) sharing one space (the commons), with a tick at the centre (quality). Line art in the brand teal and gold, drawn for the project, no stock or AI imagery.
- **Why:** distinctive, explains the idea, works as a favicon, in one colour, and in dark mode.

## 2026-10-15 · D-065 · Events and training are verified, linked and honest about accessibility and cost
- **Decision:** curated entries are read on the organiser's page before listing; cost and accessibility are what the organiser states, or "not stated". Members add events through moderation. Free options come first.
- **Why:** trust, and fairness to people for whom cost or access decides whether they can take part.

## 2026-10-15 · D-064 · One ontology and knowledge graph behind the glossary, thesaurus, dictionary and taxonomies
- **Decision:** `knowledge/ontology.yaml` defines classes, relationships, thesaurus links, the data dictionary and lineage; `dqkit/graph.py` builds one connected graph from all knowledge files and exports SKOS and OWL.
- **Why:** separate lists drift and can't show how things relate. One graph gives every view (and machines) the same answer, with each node traced to its source file.
- **Alternatives considered:** a graph database or an external graph library. Rejected for now: the graph is small, must run offline in a browser and on government laptops, and must be easy to replicate.

## 2026-10-15 · D-063 · Retire stale news rather than relabel it
- **Decision:** when the content health check flags a news slide as over 6 months old and no newer source confirms the story, remove it from the carousel. The topic stays on its page.
- **Why:** relabelling old news as "knowledge" would hide staleness instead of fixing it.

## 2026-10-15 · D-062 · Show content provenance on every page
- **Decision:** each page shows the oldest review date and the owning roles of the knowledge files it uses, computed at build time.
- **Why:** readers can judge currency; roles, not names, keep personal data out.

## 2026-10-15 · D-061 · International frameworks as packs, with manual items stated
- **Decision:** add `un-nqaf` and `imf-dqaf` packs. Requirements about integrity and the institutional environment are marked "needs a person to confirm"; headings are paraphrased and link to the source.
- **Why:** small statistics offices in the Crown Dependencies, Overseas Territories and Commonwealth often work to these frameworks. Automated evidence only where the toolkit can measure it.

## 2026-10-15 · D-060 · No personal details in the colophon, commits or contact routes
- **Decision:** the footer colophon names the project, version, commit, build date and stack, not people. Git commits use a GitHub no-reply address. Contact is by form only.
- **Why:** the repository is public. Personal emails attract spam and impersonation, and the Commons credits organisations, not individuals (D-013).
- **Alternative considered:** a shared team mailbox. Rejected for now: it would still be harvested by spammers.

## 2026-10-15 · D-059 · The Commons checks itself
- **Decision:** `scripts/self_check.py` runs on every change and weekly. It fails on errors (personal or sensitive data, claims that don't match the data, overdue reviews) and reports warnings and notes.
- **Why:** content goes stale quietly. Recounting claims from data and scanning for personal data stops two common failures reaching readers.
- **Planned next:** axe-core in CI, source archiving, source diffing, fact sampling (see the routines on Help us build this).

## 2026-10-15 · D-058 · Contact without an email address
- **Decision:** messages go into the sender's own moderation queue item; moderators reply there and the sender sees the reply on Help us build this. Elsewhere, GitHub discussions and issues; security through private vulnerability reporting.
- **Why:** prevents spam and impersonation, and needs no personal data to reply.
- **Alternative considered:** an obfuscated email address. Rejected: easily scraped, and still personal data.

## 2026-10-15 · D-057 · The backlog lives in the repository and becomes issues
- **Decision:** `knowledge/build.yaml` is the source; a workflow creates one GitHub issue per item, found again by its `[BL-nn]` prefix. Items already in Jira get `jira-linked` so the Jira sync skips them.
- **Why:** one source of truth, visible to everyone, without duplicates in Jira.

## 2026-10-15 · D-056 · Consolidate roadmap, backlog, wishlist and co-design in one page
- **Decision:** a new Help us build this page replaces the roadmap on About and the wishlist on Community. Both old places point to it.
- **Why:** people looked in three places to see what's planned and how to influence it.

## 2026-10-15 · D-055 · Build a Metadata Weaver, not just a bigger crosswalk
- **Decision:** add `dqkit/weaver.py` (with a browser port checked for parity) that reads and writes DCAT, schema.org, CKAN and ODCS through one canonical record tied to the Metadata Rosetta, and reports gaps and CDA coverage.
- **Why:** a crosswalk explains mappings; teams still retype records and only find gaps after publishing. A weaver keeps one source and shows gaps first. It is deterministic and runs offline, so any organisation can replicate it. See `docs/METADATA-WEAVER.md`.
- **Alternative considered:** RML or SPARQL-based mapping. Rejected for now: heavier to run and harder for non-specialists; it remains an option for a later profile layer.

## 2026-10-15 · D-054 · Scope includes the Crown Dependencies, Overseas Territories, Commonwealth and international partners
- **Decision:** add them as audiences, survey options, a scenario and a page, with principles that respect each jurisdiction's own laws.
- **Why:** UK public data work depends on partners beyond UK government, and small jurisdictions benefit most from a free, offline toolkit.
- **Safeguard:** nothing assumes UK law or frameworks apply outside the UK.

## 2026-10-15 · D-053 · Icons drawn for the Commons instead of imagery
- **Decision:** one inline SVG sprite of simple line icons, decorative (`aria-hidden`), themed by colour tokens.
- **Why:** no licensing risk, no extra requests, works in dark mode, and meaning is always carried by text. Photos would need stock or AI generation with licence and representation checks.

## 2026-10-15 · D-052 · Repository name: cyberdudeuk/dq-commons
Chosen by the project lead. The local repository will be pushed there once it exists and a working GitHub login is available in the build session (the current token is invalid). Alternative: an organisation repository (co-cddo, gds-dtx); can be transferred later without losing history.

## 2026-10-15 · D-051 · Link checking runs where the internet is reachable
The build sandbox can't reach outside websites, so the checker reports "network unavailable" instead of 79 false failures. A monthly GitHub workflow runs it and opens an issue for real breaks.

## 2026-10-15 · D-050 · Every knowledge file has an owning role and a review date
A test fails any file not reviewed in 12 months. Named people are never recorded; roles are.

## 2026-10-15 · D-049 · Benchmarks are opt-in, anonymous and published by editors
Maturity levels are shared only by choice, with organisation type and nation, never a name. Editors publish averages; groups under 5 are hidden. Alternative: live averages (rejected: small groups identifiable).

## 2026-10-15 · D-048 · Media items need captions or a transcript; external media is linked, not hosted
Accessibility and copyright: the Commons links to sources and requires captions or transcripts before listing videos and podcasts. No invented items: "Not yet reviewed" marks anything found but not read in full.

## 2026-10-15 · D-047 · Front page carousel follows the WAI-ARIA carousel pattern
Pause control, holds on hover and focus, no autoplay with reduced motion, 24px targets, hidden slides removed from the tab order. Content is real news with sources, or Commons' own work, labelled.

## 2026-10-15 · D-046 · Migration reconciliation in both engines
dqkit/reconcile.py and DQ.reconcile give identical results (parity-checked): counts, missing and new keys, duplicates, totals, changed values.

## 2026-10-15 · D-045 · Model contract clauses are illustrative, with supplier burden of proof
20 clauses (MoSCoW) put measurement, remediation cost and exit readiness on the supplier. Clearly labelled as not legal advice. Grounded in the Procurement Act 2023 KPI duty (contracts over £5 million) and the Technology Code of Practice.

## 2026-10-15 · D-044 · Built-in spreadsheet reader instead of a library
Excel and ODS are read with the browser's own decompression and XML parser: no third-party code, nothing uploaded. Tested against files written by pandas and LibreOffice formats. Alternative: SheetJS from a CDN (about 900 KB, licence and supply-chain review needed).

## 2026-10-15 · D-043 · Data contracts in open standards, with parity
ODCS v3.1, Frictionless Table Schema and CSVW export and import, plus Great Expectations and R validate exports, in Python and the browser with identical output. Rules that can't be expressed are kept as an extension or listed, never dropped.

## 2026-10-15 · D-042 · Accessibility checks run in a real browser with our own rules
Context: the standard axe scanner couldn't be installed (package registry not reachable from the build session). Decision: a Playwright check for unlabelled controls, unnamed buttons and links, duplicate ids, heading skips, WCAG contrast (4.5:1 and 3:1), sideways scroll and hidden panels leaking, on all 19 pages at 1280 px light and 390 px dark. Alternative: skip until axe is available (rejected). Still needed: an independent audit (XDMH-213).

## 2026-10-15 · D-041 · Survey privacy by design: totals only, under 5 hidden, editors publish
Each person's answers are stored under their own id, readable only by editors. Editors count and publish totals; counts under 5 are hidden; free text is never published. No names or emails are asked for. Alternative: open live totals (rejected: small organisations could be identified).

## 2026-10-15 · D-040 · Community data in the artifact's shared store, with GitHub forms as the fallback
Contributions, wishlist suggestions and commissions go to a per-member moderation queue only editors can read; published items are copied to an editor-only `library`. Votes: each member writes only their own. Where the shared store isn't available (for example GitHub Pages), every form links to the matching GitHub issue form. Alternative: a separate backend such as Supabase (deferred until volume needs it).

## 2026-10-15 · D-039 · The AI assistant drafts; the toolkit's engine judges
The assistant (artifact `sample` capability) calls page tools that run the same parity-checked engine. Any rules file it returns is validated, and a failing draft goes back with the error up to twice. Only column names go to the model unless the user ticks to share 5 examples per column. A deterministic suggester works with no AI. Alternative: free-form chat (rejected: unverifiable output).

## 2026-10-15 · D-038 · Requests flow GitHub to Jira; docs flow repository to Confluence
Issues labelled `backlog` become Jira stories under XDMH-210 with the key commented back. Docs listed in `integrations/config.yaml` publish to Confluence space ARCHITECTU on merge. Both are dry runs until secrets are set. Source of truth: the GitHub repository. Alternative: manual copying (rejected: drifts).

## 2026-10-15 · D-037 · Grouped navigation and an accessible guided tour on every page
19 pages in five groups (Start, Do, Know, Scenarios, Community). The tour is a non-modal dialog that moves focus, supports arrow keys and Escape, respects reduced motion, and can be started from a link (`?tour=1`).

## 2026-10-15 · D-036 · One knowledge base in YAML and CSV drives the portal, toolkit and AI tools
`knowledge/` (frameworks, communities, learning, maturity, surveys, requirements, AI-for-DQ) is injected at build time, read by the MCP server and the assistant. A test guards against values silently lost to unquoted commas (4 such losses found and fixed).

## 2026-10-15 · D-035 · Framework packs, a registry of 30 frameworks and crosswalk conversion
Each framework maps its dimensions to the toolkit's, so results convert between frameworks. 19 of 30 entries are marked "partly verified" until checked clause by clause (XDMH-221).

## 2026-10-15 · D-034 · Renamed to the Public Sector Data Quality Commons, a general hub
Chosen by the project lead. The toolkit applies to any data quality purpose; the NDL and DAM policy become two of 14 scenarios. Alternatives considered: "Government Data Quality Hub" (clashes with the ONS hub's name), keeping the NDL name (too narrow).

Newest first. These continue the portal decision log (D-001 to D-014) in the claude.ai project.

## 2026-10-15 · D-033 · Old copies of merged pages say where the live version is
- **Decision:** the four standalone data quality pages, and their copies in the Unified Data Asset Portal, keep their content but carry a banner pointing to the NDL Data Quality Portal. The main portal gains a tile linking to it.
- **Why:** one source of truth without breaking links people may already have shared.
- **Alternative considered:** deleting the old copies. Rejected: links in the wild would break, and deletion is the owner's call.

## 2026-10-15 · D-032 · The CDA return is produced by the pipeline
- **Decision:** every run writes `cda-return.csv`: one row per asset in the proposed Dataverse column layout (gds_* columns), with mean performance per dimension, issue counts by priority, trust level and route. Unmeasurable values stay blank.
- **Why:** the January baseline should be filled from measured results, not re-keyed. The columns are a proposal until GDS publishes the return schema.

## 2026-10-15 · D-031 · The browser checker uses a line-by-line port of the Python engine, proved by a parity check
- **Decision:** `portal/src/js/engine.js` reimplements the kit in JavaScript. `scripts/parity_check.py` runs 30 cases (all 15 checks, the 8 NDL charts, a 3,000-point scoring grid, ageing over 4 cycles, and micro-cases for numbers, dates, regex and CSV parsing) through both and fails on any difference.
- **Why:** people can try the kit without installing anything, and their data never leaves the browser. Two engines are only safe if they are proved identical. The parity check already found one real Python bug (empty columns) and one inconsistency (error wording).
- **Alternative considered:** Pyodide (Python in the browser). Rejected: a 10+ MB download and slow first load, which is poor for low-bandwidth users.

## 2026-10-15 · D-030 · A separate NDL Data Quality Portal, built from the pipeline results
- **Decision:** all data quality pages live in one separate portal with one top bar: home, pipeline status, check your data, NDL assurance, January baseline, guidance, tooling, and share and learn. `scripts/build_dq_portal.py` builds it from `portal/src/` and the latest results, so every number comes from the same run. GitHub Pages publishes it after each pipeline run; a claude.ai artifact copy is published by hand.
- **Why:** the project lead chose a separate portal. Generating pages from results removes hand-copied figures, which had already gone stale (test counts, "today" dates).
- **Alternative considered:** a data quality hub inside the Unified Data Asset Portal. Not chosen by the project lead.

## 2026-10-15 · D-029 · Operationalise the kit as a scheduled GitHub Actions pipeline
- **Decision:** a portfolio file (`portfolio.ndl.yaml`) lists the assets and schedules. `dqkit run` measures what is due, keeps history and writes the outputs. A weekly workflow tests, measures, commits changed results, opens, updates or closes one GitHub issue per escalation, and publishes the portal.
- **Why:** the project lead chose GitHub Actions: free for public repositories, open, repeatable and reviewable. It turns the DQAP's "repeat measure over time" step into something that happens without anyone remembering.
- **Alternatives considered:** Power Automate or Fabric (most departments' platform; documented as a follow-on), and cron on a server (nobody to run it).

## 2026-10-14 · D-028 · (Withdrawn in 2.0.0) Survey analysis
- **Status:** the survey analyser was removed from the public repository in 2.0.0 (D-POL-02) and is held privately.

## 2026-10-14 · D-027 · Draft case studies from results; people write the rest
- **Decision:** `--case-study` drafts a case study from rules, results and history. It leaves the trigger, lessons, permissions and responder details as "[To complete]". It adds 3 proposed fields: CDA identifier, a before-and-after table, and inclusion.
- **Why:** most of "what did you do" and "what changed" is already measured. Drafting it lowers the effort of contributing case studies. Permissions and personal details must be the organisation's own choice.

## 2026-10-14 · D-026 · Issue ageing and escalation use the issues framework timescales
- **Decision:** an issue is overdue when it has been open for more consecutive measurement cycles than its priority allows: Critical 1 (the framework says "immediately"; the next cycle is the first point you can tell), High 1, Medium 3, Low 6. Overdue Critical and High issues escalate to the data owner and governance board; others to the data owner.
- **Why:** escalation of overdue remediation needs a rule. The framework's own timescales are the obvious, consistent basis.
- **Alternative considered:** calendar days. Rejected because measurement cycles differ by asset.

## 2026-10-14 · D-025 · Every rule records where its control belongs
- **Decision:** add `control_point` (source, pipeline or reporting) to rules, defaulting by check type: validity and completeness checks at source; uniqueness, totals, freshness and gaps in the pipeline; measure labelling and group disparity in reporting.
- **Why:** a controls model (source, pipeline, reporting) shows that fixing at source prevents recurrence. Showing it per rule points stewards to the right fix and helps the external-data route say what to ask the supplier.

## 2026-10-14 · D-024 · A filled-in DQAP workbook, with a history of each run
- **Decision:** `--workbook` writes a filled-in Excel DQAP with 10 tabs, using the tab structure of the GOV.UK DQAP template. `--history` keeps every run, so the Results tab shows trends.
- **Why:** stewards already work in these templates. Producing them directly removes copying and re-keying.
- **Alternative considered:** CSV only. Kept as well, but it is less usable for owners.

## 2026-10-14 · D-023 · DQAP route for data you produce or receive
- **Decision:** the `source` and `influence` asset fields choose a route: internal (fix at source), external with influence (work with the supplier), or external without influence (measure, caveat and communicate). The NDL charts use the external route without influence.
- **Why:** the GOV.UK DQAP steps assume you own the data. Critical data assets are shared, and the NDL republishes others' data.

## 2026-10-14 · D-022 · Suggest an IOPC-style trust level for every assessed asset
- **Decision:** `trust.py` suggests Untrustworthy, Requires improvement, Useable or Trustworthy from the worst open priority. It applies IOPC's personal data accuracy rule (below 90% can't be Trustworthy; below 100% needs an action plan). It caps the level at Useable when fewer than 3 core dimensions are measured. The level is a suggestion that the owner confirms, because IOPC uses no fixed formula. A `trust_level` field is added to the metadata model.
- **Why:** no GOV.UK source links quality to how data may be shared.

## 2026-10-14 · D-021 · Default targets at the low end of each framework range (replaces D-016)
- **Decision:** the default target policy is "low": 75, 90, 97.5 and 99.9. "mid" (the old defaults 85, 95, 99, 100) and "high" can be chosen per asset.
- **Why:** the low end of each range is the least burdensome starting point. The owner still confirms each target.
- **Effect on the NDL assessment:**
  - "Geography stated" goes from High to Low priority.
  - "No factual errors" now meets its target. The one error is still reported.
  - No other results change.

## 2026-10-14 · D-019 · Treat NDL page checks as rules measured across the portfolio
- **Decision:** each of the 20 checks is scored as one data quality rule across all 84 pages, using the issues framework, with importance 3.
- **Why:** this uses the government's own prioritisation method rather than an invented one, and it ranks fixes that can be made once in the page template.
- **Alternative considered:** a bespoke weighted scorecard. Rejected because it isn't comparable with DQAP outputs.

## 2026-10-14 · D-018 · Assess what the NDL page shows, not the source publisher's page
- **Decision:** checks use only what is on the data.gov.uk page.
- **Why:** the NDL is the front door. Users decide there. Methodology on a publisher site one click away isn't visible at the point of choice.
- **Known effect:** this lowers the methodology and caveats scores. The report says so.

## 2026-10-14 · D-017 · Add "representativeness" as a seventh dimension
- **Decision:** add representativeness, an inclusion extension, alongside the six DAMA UK dimensions, plus a "metadata" dimension for catalogue checks.
- **Why:** overall completeness can hide groups of people who are missing or misrecorded. The research found only 2 of 21 public DQ repos test for this.
- **Alternative considered:** fold it into completeness. Rejected because that hides the result.

## 2026-10-14 · D-016 · Default targets inside each framework range: 85, 95, 99, 100 (superseded by D-021)
- **Decision:** when a rule has no target, use these defaults. The framework gives ranges and leaves the choice to the owner. Its own example uses 95 for combined score 4.
- **Why:** this keeps scoring predictable. Owners can override per rule.

## 2026-10-14 · D-015 · Pure Python with pandas, plus exporters, instead of depending on Great Expectations
- **Decision:** the kit runs its own engine and exports to Great Expectations and R validate.
- **Why:**
  - Departments use different tools.
  - Fewer dependencies make it easier to approve on government laptops.
  - One rules file serves Python and R users.
- **Alternative considered:** a Great Expectations-only kit. Rejected because it locks out R users and makes the setup heavier.

## 2026-10-14 · D-014 · Use W3C DQV to carry CDA quality results in metadata (proposed)
- **Decision:** see the project decision log. Implemented here as `model/cda-quality.linkml.yaml` with JSON Schema and SHACL.
- **Status:** a proposal to GDS metadata owners has been drafted but not sent.
