# Decision log (this repository)

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
