# NDL data quality assurance kit

Tools and open standards for measuring, reporting and publishing the data quality of
critical data assets (CDAs) and National Data Library (NDL) assets, in line with the GOV.UK
[data asset management (DAM) policy](https://www.gov.uk/government/publications/data-asset-management-policy-in-government/data-asset-management-policy-in-government)
and [data quality action plan (DQAP) guidance](https://www.gov.uk/government/publications/implement-a-data-quality-action-plan/data-quality-action-plan-implementation-guide).

**Status:** alpha prototype (v0.4.0). MIT-licensed code, OGL v3.0 content. Not an official GDS product.

**See it first:** the **NDL Data Quality Portal** brings everything together: pipeline status,
an in-browser checker, the NDL assurance results, the January baseline effort model, guidance,
tooling and case studies. Build it with `python scripts/build_dq_portal.py` and open
`portal/dist/index.html`. Once this repository is on GitHub, the weekly pipeline publishes it to
GitHub Pages.

## What is in it

| Folder | What it is | Who it is for |
|---|---|---|
| `dqkit/` | Python kit: runs quality rules on data, scores them with the GOV.UK issues framework, checks catalogue records against GOV.UK requirements, suggests a trust level, picks the DQAP route, and writes a filled-in DQAP workbook | Data stewards, analysts, engineers |
| `vocab/` | 8 quality dimensions and 43 cross-government issue types (CSV, SKOS Turtle, JSON-LD) | Anyone logging data quality issues |
| `model/` | Proposed quality extension to the cross-government metadata exchange model (LinkML, JSON Schema, SHACL) | GDS metadata standards owners |
| `rules/ndl/` | Example rule files for 8 NDL chart datasets | People writing their own rules |
| `assessments/ndl/` | A full test of the NDL's 84 curated data pages against GOV.UK requirements | NDL team, CDO Council |
| `portfolio.ndl.yaml`, `assessments/portfolio/` | The NDL portfolio (8 chart assets and the page metadata), and the results of the latest pipeline run | NDL team, portal |
| `.github/workflows/` | Tests on every change, and the weekly data quality pipeline | Maintainers |
| `portal/src/`, `scripts/build_dq_portal.py` | The NDL Data Quality Portal: page templates, shared top bar, and the browser version of the kit (`portal/src/js/engine.js`) | Everyone |
| `docs/` | PRD, theory of change, architecture, specs, decisions, build log, outreach drafts, and the guidance crosswalk | Everyone |

## Quick start (no coding knowledge needed beyond copy and paste)

1. Install Python 3.10 or later.
2. In a terminal, in this folder, run: `pip install -r requirements.txt`
3. Check the kit works: `python -m unittest discover -s tests`
   You should see `OK` at the end (59 tests at the time of writing). `python scripts/parity_check.py` also proves the browser version gives the same answers (30 cases).
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
   Add `--case-study` to draft a case study in the GDS Shared Learning Library template (.md and .docx).
   The summary also gives a suggested **trust level** (IOPC scale: Untrustworthy, Requires
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
11. Analyse the Cross-Government DQ Solutions Survey export (names and emails are removed on load):
   `python -m dqkit survey survey-export.xlsx --out survey-results`

## Writing a rules file

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
- `personal_data_columns`: used by the IOPC accuracy rule.
- `primary_use`, `secondary_uses` and `steward`: fill the Details tab.

Optional rule fields:
- `purpose`, `requirement`, `method` and `notes`: fill the Metrics tab, matching the Defra and DQAP rule templates.
- `personal_data: true`: marks a personal data field.
- `control_point` (source, pipeline or reporting): where the control that prevents this failure belongs.
  The default comes from the check type.

Checks available: `not_null`, `required_columns`, `unique`, `type`, `regex`, `in_set`, `range`,
`not_future`, `compare`, `sum_max`, `freshness`, `no_gaps`, `header_has_unit`, `not_unknown`,
`group_disparity`. Each maps to an issue type in `vocab/issue-types.csv`. You can override a rule's
`impact` (1 to 4), `target` (%), `dimension` or `issue_type`.

## How scoring works

The kit applies the published [data quality issues framework](https://www.gov.uk/government/publications/implement-a-data-quality-action-plan/data-quality-issues-framework) exactly:
importance × impact sets a target range; performance below target falls into a band;
importance × impact × band gives the priority (Low, Medium, High, Critical) and the time to fix.
The tests check the kit against the framework's own worked example.

## Headline findings from the NDL assessment (14 October 2026)

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

## How this kit lines up with existing guidance

[`docs/GUIDANCE-CROSSWALK.md`](docs/GUIDANCE-CROSSWALK.md) compares 15 sources. The latest 6 are GDS's tooling
review, the survey, the case study template, two DQAP adoption decks and a brief research note
(review of the survey: [`docs/SURVEY-REVIEW.md`](docs/SURVEY-REVIEW.md)). The first 9 are:
- GOV.UK guidance
- DQAP Implementation Guide v2.0
- Issues Framework v1.0
- Defra "Start here"
- IOPC trust scales
- the 2023 decision tree
- NHS England's framework for data science
- the DQ community note

It shows where each step is in the kit. It also lists 18 findings, including an
arithmetic slip in Issues Framework v1.0 Tables 7 and 8.

## Related work

- Public Sector DQ Tooling Atlas (research behind this kit)
- CDA Quality Baseline Effort model (January 2027 baseline return)
- Unified Data Asset Portal (GDS/OCDO DAM portal prototype)

## Contributing

Issues and pull requests are welcome. Please read `docs/DECISIONS.md` first. Every change should
update `docs/BUILD-LOG.md` and `CHANGELOG.md` in the same commit.
