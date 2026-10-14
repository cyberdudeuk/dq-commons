# NDL data quality assurance kit

Tools and open standards for measuring, reporting and publishing the data quality of
critical data assets (CDAs) and National Data Library (NDL) assets, in line with the GOV.UK
[data asset management (DAM) policy](https://www.gov.uk/government/publications/data-asset-management-policy-in-government/data-asset-management-policy-in-government)
and [data quality action plan (DQAP) guidance](https://www.gov.uk/government/publications/implement-a-data-quality-action-plan/data-quality-action-plan-implementation-guide).

**Status:** alpha prototype (v0.1.0). MIT-licensed code, OGL v3.0 content. Not an official GDS product.

## What is in it

| Folder | What it is | Who it is for |
|---|---|---|
| `dqkit/` | Python kit: runs quality rules on data, scores them with the GOV.UK issues framework, checks catalogue records against GOV.UK requirements | Data stewards, analysts, engineers |
| `vocab/` | 8 quality dimensions and 43 cross-government issue types (CSV, SKOS Turtle, JSON-LD) | Anyone logging data quality issues |
| `model/` | Proposed quality extension to the cross-government metadata exchange model (LinkML, JSON Schema, SHACL) | GDS metadata standards owners |
| `rules/ndl/` | Example rule files for 8 NDL chart datasets | People writing their own rules |
| `assessments/ndl/` | A full test of the NDL's 84 curated data pages against GOV.UK requirements | NDL team, CDO Council |
| `docs/` | PRD, theory of change, architecture, specs, decisions, build log, outreach drafts | Everyone |

## Quick start (no coding knowledge needed beyond copy and paste)

1. Install Python 3.10 or later.
2. In a terminal, in this folder, run: `pip install -r requirements.txt`
3. Check the kit works: `python -m unittest discover -s tests`
   You should see `OK` at the end (21 tests).
4. Check a data file against a rules file:
   `python -m dqkit check assessments/ndl/chart-data/people__births.csv rules/ndl/births.yaml --out my-results`
   You get a plain summary on screen, plus these files in `my-results/`:
   - `*.results.json`: every rule, pass rate, and priority
   - `*.dqv.jsonld`: results as W3C Data Quality Vocabulary metadata, ready for a catalogue
   - `*.dqap-rules.csv` and `*.dqap-issues.csv`: rows to paste into the GOV.UK DQAP template
5. Turn the same rules into another tool's format:
   - Great Expectations: `python -m dqkit export rules/ndl/births.yaml --to gx`
   - R `validate`: `python -m dqkit export rules/ndl/births.yaml --to r-validate`
6. Re-run the NDL assessment: `python scripts/run_ndl_assessment.py`

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
- Strong: every page was reviewed in the last 12 months. 91% name the provider and link to authoritative sources.
- Weak: no page shows an accountable owner role or a security classification. Only 1 links a methodology, and 56 of 84 give
  no quality information at all. 32% state an update frequency. 11% declare a schema.
- 8 chart data files were checked with 49 rules. Main issues: air quality chart missing 2025, unclear
  measures (vaccinations, council tax), and missing context columns (election, social mobility).
- One factual error found: the Driving tests page says "Driver and Vehicle Standards Agency (DVLA)".

Full report: [`assessments/ndl/REPORT.md`](assessments/ndl/REPORT.md).

## Related work

- Public Sector DQ Tooling Atlas (research behind this kit)
- CDA Quality Baseline Effort model (January 2027 baseline return)
- Unified Data Asset Portal (GDS/OCDO DAM portal prototype)

## Contributing

Issues and pull requests are welcome. Please read `docs/DECISIONS.md` first. Every change should
update `docs/BUILD-LOG.md` and `CHANGELOG.md` in the same commit.
