# Public Sector Data Quality Commons

A free, open hub and toolkit for everything about data quality in the public sector: check data,
find the frameworks and standards that apply, learn, use AI safely, and share what works. For
central and local government, the devolved governments, the wider public sector, the voluntary
and private bodies that deliver public services, and the Crown Dependencies, Overseas Territories,
Commonwealth and international partners the UK works with.

[![tests](https://github.com/cyberdudeuk/dq-commons/actions/workflows/ci.yml/badge.svg)](https://github.com/cyberdudeuk/dq-commons/actions/workflows/ci.yml)
[![Accessibility](https://github.com/cyberdudeuk/dq-commons/actions/workflows/accessibility.yml/badge.svg)](https://github.com/cyberdudeuk/dq-commons/actions/workflows/accessibility.yml)
[![publish portal](https://github.com/cyberdudeuk/dq-commons/actions/workflows/pages.yml/badge.svg)](https://github.com/cyberdudeuk/dq-commons/actions/workflows/pages.yml)
[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/cyberdudeuk/dq-commons/badge)](https://scorecard.dev/viewer/?uri=github.com/cyberdudeuk/dq-commons)

**Use it now, no install:** [cyberdudeuk.github.io/dq-commons](https://cyberdudeuk.github.io/dq-commons/)

**Status:** prototype (v2.0.0). [MIT-licensed code](LICENSE), [OGL v3.0 content](docs/CONTENT-LICENCE.md). Not an official government product.

## Choose your path

| You are… | Start here | You'll need |
|---|---|---|
| **Beginner**: new to data quality, to the Commons, or to GitHub | [For beginners](#for-beginners) | A web browser |
| **Intermediate**: managing data quality for an asset, a team or a return | [For intermediate users](#for-intermediate-users) | A browser; optionally Python on your computer |
| **Advanced**: automating, integrating, adapting or contributing code | [For advanced users and contributors](#for-advanced-users-and-contributors) | Python, Git and a GitHub account |

## For beginners

**What it is.** One shared place to check whether data is good enough to use, learn how to
improve it, and see which frameworks and standards apply to you. Read why it exists, its aims
and desired outcomes on the [About page](https://cyberdudeuk.github.io/dq-commons/about.html).

**What GitHub is, and why the Commons lives here.** This page is the project's repository:
the files the portal is built from, with every past version and an open noticeboard. You don't
need to code. Our [plain-English introduction to GitHub](https://cyberdudeuk.github.io/dq-commons/github.html)
explains the words you'll see (issue, pull request, release) and what you can do at each level.

**Things you can do today, in your browser:**
1. [Check a CSV file](https://cyberdudeuk.github.io/dq-commons/check.html) against quality rules. Nothing is uploaded.
2. Follow the [learning pathway for your role](https://cyberdudeuk.github.io/dq-commons/learn.html).
3. See where data quality sits in [your profession's skills framework](https://cyberdudeuk.github.io/dq-commons/professions.html).
4. Find [frameworks and standards](https://cyberdudeuk.github.io/dq-commons/frameworks.html) for your nation or sector.

**Report a problem or suggest an idea:** [open an issue](https://github.com/cyberdudeuk/dq-commons/issues/new/choose)
(a free GitHub account is needed), or use the [help routes](https://cyberdudeuk.github.io/dq-commons/operate.html)
if you'd rather not. Never post personal data or anything sensitive: everything here is public.

## For intermediate users

The portal follows a journey: **1 Start, 2 Learn, 3 Check, 4 Improve, 5 Apply, 6 Contribute**,
with every page marked Beginner, Intermediate or Advanced. Useful next steps:
- Prioritise issues with the government [issues framework calculator](https://cyberdudeuk.github.io/dq-commons/guidance.html).
- Work through the eight-stage [data quality management playbook](https://cyberdudeuk.github.io/dq-commons/playbook.html).
- Size a [critical data asset baseline](https://cyberdudeuk.github.io/dq-commons/baseline.html) to your own deadline.
- Read the [user guide](docs/USER-GUIDE.md) and the [operating model](docs/OPERATING-MODEL.md).

### Quick start on your own computer (copy and paste, no coding)

1. Install Python 3.10 or later.
2. In a terminal, in this folder, run: `pip install -r requirements.txt`
3. Check the kit works: `python -m unittest discover -s tests`
   You should see `OK` at the end (131 tests at the time of writing). `python scripts/parity_check.py` also proves the browser version gives the same answers (37 cases).
4. Check a data file against a rules file:
   `python -m dqkit check assessments/ndl/chart-data/people__births.csv rules/ndl/births.yaml --out my-results`
   You get a plain summary on screen, plus these files in `my-results/`:
   - `*.results.json`: every rule, pass rate, and priority
   - `*.dqv.jsonld`: results as W3C Data Quality Vocabulary metadata, ready for a catalogue
   - `*.dqap-rules.csv` and `*.dqap-issues.csv`: rows to paste into the GOV.UK DQAP template
   Add `--workbook` to also get a filled-in DQAP Excel workbook. It has 11 tabs: Start here, Details,
   Criticality matrix, Metrics, Results, Issues log, Causes, Actions, Operations, RACI and Steps.
   Add `--history my-history` to keep every run, so the Results tab shows the trend over time,
   and the Issues log shows how long each issue has been open and which are overdue (escalate).
   Add `--case-study` to draft a case study (.md and .docx).
   The summary also gives a suggested **trust level** (adapted from the IOPC's data trust scales: Untrustworthy, Requires
   improvement, Useable, Trustworthy) and the **DQAP route** for internal or external data.
5. Turn the same rules into another tool's format:
   - Great Expectations: `python -m dqkit export rules/ndl/births.yaml --to gx`
   - R `validate`: `python -m dqkit export rules/ndl/births.yaml --to r-validate`
6. Re-run the NDL assessment: `python scripts/run_ndl_assessment.py`
7. Measure a whole portfolio of assets in one go (what the weekly automated pipeline does):
   `python -m dqkit run portfolio.ndl.yaml --out assessments/portfolio`
   Read `assessments/portfolio/run-summary.md` for a plain-English digest. It also writes
   `portfolio.json` (for the web portal), `escalations.json` (overdue Critical and High issues),
   one merged DQV catalogue file, and every asset's workbook, CSVs and case study.
   Add `--as-of YYYY-MM-DD` to measure as if on a date, and `--fail-on-escalation` to finish with
   exit code 2 when something needs escalating. See [`docs/OPERATIONS.md`](docs/OPERATIONS.md).
8. Start a rules file for a new data file:
   `python -m dqkit suggest my-data.csv --title "My data" --owner "My Department" --out rules.yaml`
   This drafts rules from what the data looks like. A data steward must review every rule.
9. Build the portal from the latest results: `python scripts/build_dq_portal.py` (writes `portal/dist/`).
   Every page is a static file; open `portal/dist/index.html` in a browser.
10. Install the `dqkit` command (optional): `pip install -e .` then run `dqkit check ...` instead of `python -m dqkit check ...`.

### Writing a rules file

```yaml
asset:
  id: my-asset            # short, unique
  title: My critical data asset
  owner: My Department
  importance: 3           # GOV.UK issues framework: 1 Low, 2 Medium, 3 High, 4 Critical
rules:
  - {id: R1, check: not_null, column: nhs_number}
  - {id: R2, check: unique, columns: [nhs_number]}
  - {id: R3, check: regex, column: postcode, pattern: '[A-Z]{1,2}\d[A-Z\d]? ?\d[A-Z]{2}'}
  - {id: R4, check: freshness, column: extract_date, expected: P1M, lag: P7D}
  - {id: R5, check: not_unknown, column: ethnicity}            # inclusion check
  - {id: R6, check: group_disparity, group: sex, tolerance: 5,
     inner: {check: not_null, column: nhs_number}}            # is quality equal across groups?
```

Optional asset fields:
- `source` (internal or external) and `influence` (true or false): choose the decision-tree route.
- `target_policy` (low, mid or high): sets default targets.
- `personal_data_columns`: used by the personal data accuracy rule in the trust level.
- `primary_use`, `secondary_uses` and `steward`: fill the Details tab.

Optional rule fields:
- `purpose`, `requirement`, `method` and `notes`: fill the Metrics tab, matching the Defra and DQAP rule templates.
- `personal_data: true`: marks a personal data field.
- `control_point` (source, pipeline or reporting): where the control that prevents this failure belongs.
  The default comes from the check type.

Checks available: `not_null`, `required_columns`, `unique`, `type`, `regex`, `in_set`, `range`,
`not_future`, `compare`, `sum_max`, `freshness`, `no_gaps`, `header_has_unit`, `not_unknown`,
`group_disparity`, `identifier` and `outlier` (valid but implausible numbers: `method: iqr` with `k`, default
1.5, or `method: zscore` with `threshold`, default 3). Each maps to an issue type in `vocab/issue-types.csv`. You can override a rule's
`impact` (1 to 4), `target` (%), `dimension` or `issue_type`.

### How scoring works

The kit applies the published [data quality issues framework](https://www.gov.uk/government/publications/implement-a-data-quality-action-plan/data-quality-issues-framework) exactly:
importance × impact sets a target range; performance below target falls into a band;
importance × impact × band gives the priority (Low, Medium, High, Critical) and the time to fix.
The tests check the kit against the framework's own worked example.

## For advanced users and contributors

### Repository map

| Folder | What it is | Who it is for |
|---|---|---|
| `dqkit/` | Python kit: runs quality rules on data, scores them with the GOV.UK issues framework, checks catalogue records against GOV.UK requirements, suggests a trust level, picks the DQAP route, and writes a filled-in DQAP workbook | Data stewards, analysts, engineers |
| `vocab/` | 8 quality dimensions and 43 cross-government issue types (CSV, SKOS Turtle, JSON-LD) | Anyone logging data quality issues |
| `model/` | Proposed quality extension to the cross-government metadata exchange model (LinkML, JSON Schema, SHACL) | GDS metadata standards owners |
| `rules/ndl/` | Example rule files for 8 NDL chart datasets | People writing their own rules |
| `assessments/ndl/` | A full test of the NDL's 84 curated data pages against GOV.UK requirements | NDL team, data leaders |
| `portfolio.ndl.yaml`, `assessments/portfolio/` | The NDL portfolio (8 chart assets and the page metadata), and the results of the latest pipeline run | NDL team, portal |
| `.github/workflows/` | Tests on every change, and the weekly data quality pipeline | Maintainers |
| `portal/src/`, `scripts/build_dq_portal.py` | The NDL Data Quality Portal: page templates, shared top bar, and the browser version of the kit (`portal/src/js/engine.js`) | Everyone |
| `knowledge/` | The knowledge base behind every portal page, each file with an owning role and review date | Content stewards |
| `docs/` | PRD, theory of change, architecture, specs, decisions and build log | Everyone |

### Architecture, automation and releases
- How it fits together: [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md); decisions: [`docs/DECISIONS.md`](docs/DECISIONS.md).
- What runs automatically (tests, accessibility, security scanning, Dependabot, the weekly pipeline,
  publishing) and the maintainer routine: [`docs/OPERATIONS.md`](docs/OPERATIONS.md) section 10.
- Releases: add an entry to `knowledge/releases.yaml`, then push a `vX.Y.Z` tag; the release
  workflow checks the tests and publishes notes and a source zip.
- Agents and tools: `dqkit/mcp_server.py` exposes the kit as read-only MCP tools.

### Contributing
Read [`CONTRIBUTING.md`](CONTRIBUTING.md) and the [charter](CHARTER.md). Every change updates
`docs/BUILD-LOG.md` and `CHANGELOG.md` in the same commit, and must pass the tests, the
accessibility check and the content health check.

## Background and evidence

### Headline findings from the NDL assessment (14 October 2026)

- 84 curated data pages in 7 collections were tested against 20 checks drawn from the DAM policy,
  CDA metadata guidance, DQAP guidance, NDL curation criteria, FAIR principles and inclusion.
- Average score: **50.9%**. 1 page green, 47 amber, 36 red.
- Average coverage of the 13 CDA metadata properties: **46.4%**.
- Strong: every page was reviewed in the last 12 months. Only one factual error was found. 91% name the provider and link to authoritative sources.
- Weak: no page shows an accountable owner role or a security classification. Only 1 links a methodology, and 56 of 84 give
  no quality information at all. 32% state an update frequency. 11% declare a schema.
- 8 chart data files were checked with 49 rules. Main issues: air quality chart missing 2025, unclear
  measures (vaccinations, council tax), and missing context columns (election, social mobility).
- One factual error found: the Driving tests page says "Driver and Vehicle Standards Agency (DVLA)".

Full report: [`assessments/ndl/REPORT.md`](assessments/ndl/REPORT.md).

### How this kit lines up with existing guidance

The kit follows the published GOV.UK guidance: the [data quality action plan guide and issues
framework](https://www.gov.uk/government/publications/implement-a-data-quality-action-plan/data-quality-action-plan-implementation-guide)
(2026), the [Government Data Quality Framework](https://www.gov.uk/government/publications/the-government-data-quality-framework/the-government-data-quality-framework)
(2020) and the [data asset management policy](https://www.gov.uk/government/publications/data-asset-management-policy-in-government/data-asset-management-policy-in-government).
The portal's [frameworks page](https://cyberdudeuk.github.io/dq-commons/frameworks.html) maps 28 other
published frameworks and standards onto the same dimensions.

### Conformance

How the templates meet the DAM policy, the critical data asset guidance, the data ownership model, the DQAP
implementation guide, the issues framework, the Government Data Quality Framework and domain guidance:
[`docs/CONFORMANCE.md`](docs/CONFORMANCE.md).

### Related work

- Public Sector DQ Tooling Atlas (research behind this kit)
- CDA Quality Baseline Effort model (first baseline return)
- Unified Data Asset Portal (GDS/OCDO DAM portal prototype)
- [GitHub Repos Asset Catalogue](https://github.com/cyberdudeuk/github-repos-asset-catalogue): every UK public sector code project on GitHub, findable by topic,
  organisation, question or capability, in plain English. Use it to find data quality code to reuse before
  building your own. The Commons borrows its contact-form-only policy, three-level README and checks against
  personal data and credentials in the repository.

## What's new

The latest release (2.1.0) adds search across the portal (press `/`), an "On this page" drawer that
flags new and changed sections, a plain English summary at the top of every page, an offline copy,
outlier and record linkage checks, and Metadata Weaver support for CSVW, Frictionless, GeoDCAT-AP and
StatDCAT-AP. Contact is by form only. Every release is in [`CHANGELOG.md`](CHANGELOG.md) and the
portal's What's new panel.
