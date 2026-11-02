# Decision log (this repository)

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

## 2026-10-14 · D-028 · Survey analysis removes personal data on load
- **Decision:** `dqkit survey` drops name, role and email columns as it reads the Forms export, and never writes them out. Summaries warn about counts under 5.
- **Why:** the analysis needs no personal data (data minimisation, UK GDPR Article 5). Small counts by solution can identify an organisation.
- **Alternative considered:** keep emails for follow-up. Rejected: follow-up is GDS's job, through the Forms record, not the analysis file.

## 2026-10-14 · D-027 · Draft case studies from results; people write the rest
- **Decision:** `--case-study` fills the GDS case study template from rules, results and history. It leaves the trigger, lessons, permissions and responder details as "[To complete]". It adds 3 proposed fields: CDA identifier, a before-and-after table, and inclusion.
- **Why:** most of "what did you do" and "what changed" is already measured. Drafting it lowers the effort of contributing to the Shared Learning Library. Permissions and personal details must be the organisation's own choice.

## 2026-10-14 · D-026 · Issue ageing and escalation use the issues framework timescales
- **Decision:** an issue is overdue when it has been open for more consecutive measurement cycles than its priority allows: Critical 1 (the framework says "immediately"; the next cycle is the first point you can tell), High 1, Medium 3, Low 6. Overdue Critical and High issues escalate to the data owner and governance board; others to the data owner.
- **Why:** the GDS DQ Week material asks for escalation of overdue remediation but gives no rule. The framework's own timescales are the obvious, consistent basis.
- **Alternative considered:** calendar days. Rejected because measurement cycles differ by asset.

## 2026-10-14 · D-025 · Every rule records where its control belongs
- **Decision:** add `control_point` (source, pipeline or reporting) to rules, defaulting by check type: validity and completeness checks at source; uniqueness, totals, freshness and gaps in the pipeline; measure labelling and group disparity in reporting.
- **Why:** the brief research's controls model shows that fixing at source prevents recurrence. Showing it per rule points stewards to the right fix and helps the external-data route say what to ask the supplier.

## 2026-10-14 · D-024 · A filled-in DQAP workbook, with a history of each run
- **Decision:** `--workbook` writes a filled-in Excel DQAP with 10 tabs, using the tab structure of the Implementation Guide v2.0 and the Defra "Start here" annexes. `--history` keeps every run, so the Results tab shows trends, as Defra's monitoring template does. Cells for stewards to complete are grey.
- **Why:** stewards already work in these templates. Producing them directly removes copying and re-keying.
- **Alternative considered:** CSV only. Kept as well, but it is less usable for owners.

## 2026-10-14 · D-023 · DQAP route from the 2023 decision tree
- **Decision:** the `source` and `influence` asset fields choose a route: internal (fix at source), external with influence (work with the supplier), or external without influence (measure, caveat and communicate). The NDL charts use the external route without influence.
- **Why:** the GOV.UK DQAP steps assume you own the data. Critical data assets are shared, and the NDL republishes others' data.

## 2026-10-14 · D-022 · Suggest an IOPC-style trust level for every assessed asset
- **Decision:** `trust.py` suggests Untrustworthy, Requires improvement, Useable or Trustworthy from the worst open priority. It applies IOPC's personal data accuracy rule (below 90% can't be Trustworthy; below 100% needs an action plan). It caps the level at Useable when fewer than 3 core dimensions are measured. The level is a suggestion that the owner confirms, because IOPC uses no fixed formula. A `trust_level` field is added to the metadata model.
- **Why:** no GOV.UK source links quality to how data may be shared (crosswalk F6).

## 2026-10-14 · D-021 · Default targets at the low end of each framework range (replaces D-016)
- **Decision:** the default target policy is "low": 75, 90, 97.5 and 99.9. "mid" (the old defaults 85, 95, 99, 100) and "high" can be chosen per asset.
- **Why:** Issues Framework v1.0 builds its own band tables on the low end of each range. Defra sets thresholds by business need (for example 75% for descriptive fields). The owner still confirms each target.
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
