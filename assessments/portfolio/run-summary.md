# Data quality run: National Data Library chart data

- **Measured as of:** 2026-10-14 (run at 2026-10-15T06:30:28Z)
- **Owner:** National Data Library team
- **Assets:** 8 (8 measured this run)
- **Rules meeting target:** 43 of 49
- **Open issues:** 6 (5 High, 1 Medium)
- **Overdue issues:** 0. **Escalations:** 0

## Assets

| Asset | Measured on | Rules met | Open issues | Worst priority | Overdue | Trust level | Route |
|---|---|---|---|---|---|---|---|
| NDL People collection: Births chart data | 2026-10-14 | 8/8 | 0 | None | 0 | Trustworthy | External data, no influence: assess, caveat and communicate |
| NDL Early years collection: Childhood vaccinations chart data | 2026-10-14 | 8/9 | 1 | High | 0 | Requires improvement | External data, no influence: assess, caveat and communicate |
| NDL Transport collection: Road traffic chart data | 2026-10-14 | 6/6 | 0 | None | 0 | Trustworthy | External data, no influence: assess, caveat and communicate |
| NDL Environment collection: Air quality chart data | 2026-10-14 | 5/6 | 1 | High | 0 | Requires improvement | External data, no influence: assess, caveat and communicate |
| NDL Government and Parliament collection: Election results chart data | 2026-10-14 | 4/5 | 1 | High | 0 | Requires improvement | External data, no influence: assess, caveat and communicate |
| NDL Transport collection: MOT results chart data | 2026-10-14 | 4/5 | 1 | Medium | 0 | Useable | External data, no influence: assess, caveat and communicate |
| NDL Government and Parliament collection: Council tax chart data | 2026-10-14 | 5/6 | 1 | High | 0 | Requires improvement | External data, no influence: assess, caveat and communicate |
| NDL People collection: Social mobility chart data | 2026-10-14 | 3/4 | 1 | High | 0 | Requires improvement | External data, no influence: assess, caveat and communicate |

## What changed since the last run

Compared with the run measured on 2026-10-14.

### New issues

- None

### Resolved issues

- None

Still open from last time: 6.

## Overdue issues

None. (An issue is overdue when it has been open longer than the issues framework allows: Critical and High 1 cycle, Medium 3, Low 6.)

## Escalations

None this run.

## Catalogue records (metadata assessment)

84 records from `assessments/ndl/harvest.jsonl`: mean score 50.9%, CDA metadata coverage 46.4%. RAG: 1 green, 47 amber, 36 red.

| Check | Performance (%) | Target (%) | Priority |
|---|---|---|---|
| DAM-1 Owner organisation named | 90.5 | 99.9 | Critical |
| DAM-2 Accountable data owner role shown | 0.0 | 99.9 | Critical |
| DAM-3 DQAP or equivalent linked | 17.3 | 99.9 | Critical |
| DAM-4 Reviewed in the last 12 months | 100.0 | 97.5 | Meets target |
| CDA-1 Security classification stated | 0.0 | 75.0 | Medium |
| CDA-2 Time period stated (temporalCoverage) | 70.2 | 90.0 | High |
| CDA-3 Licence stated for the asset | 50.0 | 90.0 | High |
| CDA-4 Schema or standard declared (conformsTo) | 11.3 | 90.0 | High |
| NDL-1 Up to date (checked in the last 6 months) | 65.5 | 97.5 | High |
| NDL-2 Update frequency stated | 32.1 | 90.0 | High |
| NDL-3 Every data link names its publisher | 41.1 | 75.0 | Medium |
| NDL-4 Links go to authoritative public sector sources | 91.1 | 75.0 | Meets target |
| DQ-1 Geography stated | 89.3 | 90.0 | Low |
| DQ-2 Quality caveats stated | 33.3 | 90.0 | High |
| DQ-3 Methodology linked | 1.2 | 90.0 | High |
| FAIR-1 Open machine-readable format offered | 72.6 | 97.5 | High |
| FAIR-2 API offered | 20.2 | 75.0 | Medium |
| INC-1 People breakdowns stated | 28.0 | 90.0 | High |
| INC-2 Other UK nations signposted | 24.0 | 75.0 | Medium |
| QA-1 No factual errors on the page | 98.8 | 97.5 | Meets target |

## Files

- `portfolio.json`: the summary above, for the web portal
- `escalations.json`: one entry per escalated issue, ready to become a ticket
- `catalogue.dqv.jsonld`: all results as W3C Data Quality Vocabulary, for a catalogue
- `assets/`: per-asset results, DQAP workbook, CSVs and draft case study
