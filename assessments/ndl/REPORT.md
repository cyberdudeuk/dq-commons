# How do the National Data Library's own collections measure up to GOV.UK data asset and data quality requirements?

Assessment date: 14 October 2026. Method, data and code are in this repository, so anyone can re-run it:
`python scripts/run_ndl_assessment.py`.

## Summary

The NDL's curated collections are well chosen and come from authoritative sources. But the pages hold
little of the metadata that the GOV.UK DAM policy and the critical data asset (CDA) metadata guidance
ask for. On average a page scores **50.9%** across 20 checks and covers **46.4%** of the 13 CDA metadata
properties. 1 page is green, 47 amber and 36 red.

The biggest gaps are the same on almost every page, so they can be fixed once in the page template
rather than 84 times.

## What was tested

- **84 curated data pages** across all 7 collections: Business and economy (10), Environment (18),
  Government and Parliament (8), Land and property (11), People (18), Transport (12), Early years (7).
- **20 checks**, each tied to a published source:

| Source | Checks |
|---|---|
| Data asset management policy (May 2026) | Owner named, owner role shown, DQAP or equivalent, reviewed in 12 months |
| CDA metadata guidance (April 2026) | Security classification, time period, asset licence, schema (conformsTo) |
| NDL curation criteria | Up to date, update frequency, publishers named, authoritative sources |
| DQAP guidance | Geography, quality caveats, methodology |
| FAIR principles (as scored by the EU Metadata Quality Assessment) | Open machine-readable format, API |
| Inclusion (this project) | People breakdowns stated, other UK nations signposted |
| Content | No factual errors |

- **8 NDL chart data files** (the NDL's own data downloads) checked with **49 data quality rules**.

Each check is treated as a data quality rule measured across all pages and scored with the GOV.UK
data quality issues framework. Importance is set to 3 (High), because the NDL is the national front
door to public data.

## Results by check

| Check | Pages passing (partial counts half) | Priority | Fix within |
|---|---|---|---|
| Accountable owner role shown (DAM) | 0% | Critical | Immediately |
| DQAP or equivalent linked (DAM) | 17% (1 page links methodology; 27 describe caveats only; 56 have neither) | Critical | Immediately |
| Owner organisation named (DAM) | 90% | Critical | Immediately |
| Methodology linked | 1% | High | 1 cycle |
| Schema declared (conformsTo) | 11% | High | 1 cycle |
| People breakdowns stated (people and early years pages only) | 28% | High | 1 cycle |
| Update frequency stated | 32% | High | 1 cycle |
| Quality caveats stated | 33% | High | 1 cycle |
| Licence stated for the asset | 50% (site-wide only) | High | 1 cycle |
| Up to date (checked in 6 months) | 65% | High | 1 cycle |
| Time period stated | 70% | High | 1 cycle |
| Open machine-readable format | 73% | High | 1 cycle |
| Geography stated | 89% | High | 1 cycle |
| Security classification stated | 0% | Medium | 3 cycles |
| API offered | 20% | Medium | 3 cycles |
| Other UK nations signposted | 24% | Medium | 3 cycles |
| Every link names its publisher | 41% | Medium | 3 cycles |
| No factual errors | 99% | Medium | 3 cycles |
| Reviewed in the last 12 months (DAM) | 100% | Meets target | |
| Links go to authoritative sources | 91% | Meets target | |

"Owner organisation named" scores 90% but is still Critical, because the framework sets a 100% target
when importance and impact are both high. The 8 pages without a named provider are:

- Long term flood risk
- Flood alerts
- Main rivers
- Environmental public registers
- Service assessment reports
- Transparency data
- Deprivation
- Compare school performance

## CDA metadata property coverage

| Property | Coverage | Note |
|---|---|---|
| title, description | 100% | |
| creator | 90% | Provider organisation named |
| mediaType | 80% | Formats mentioned on the page |
| temporalCoverage | 70% | |
| accessRights | 52% | Charged or restricted access is mentioned only sometimes |
| identifier, licence | 50% | Page URL only; site-wide licence only |
| conformsTo | 11% | |
| dateCreated, expires, supersededBy, securityClassification | 0% | Not shown on any page |

## Chart data results

| Chart file | Rules met | Issues |
|---|---|---|
| Births | 8 of 8 | None |
| Road traffic | 6 of 6 | None |
| Childhood vaccinations | 8 of 9 | Column names don't say which vaccine, at what age, or that values are percentages (High) |
| Air quality | 5 of 6 | Latest year is 2024; 2025 statistics would normally be out by spring 2026 (High) |
| Election results | 4 of 5 | No column says which election the vote shares are for (High) |
| Council tax | 5 of 6 | The amount doesn't say it is in pounds per band D dwelling (High) |
| Social mobility | 3 of 4 | No column says what the percentage measures or for which year (High) |
| MOT results | 4 of 5 | Financial years written as "2024", so it is unclear whether that means 2023-24 or 2024-25 (Medium) |

## Content error found

The Driving tests page says "This data is published by the Driver and Vehicle Standards Agency (DVLA)".
The right abbreviation is DVSA. DVLA is the Driver and Vehicle Licensing Agency, a different body.

## Inclusion findings

- Only 7 of the 25 people and early years pages say which groups of people the data can be broken down
  by. Readers can't tell whether they can see results for, for example, disabled people or ethnic groups.
- 48 pages cover only part of the UK. 45 of them don't point users to equivalent data for every other
  UK nation, and 28 point to none. People in Scotland, Wales and Northern Ireland are less well served. The Early years
  collection is the good example to copy: it links to all four nations.
- 27 pages offer no open machine-readable format: 8 only proprietary spreadsheets, and 19 only PDFs, web pages or dashboards, or no stated format. Screen reader users and people using
  low-bandwidth or assistive technology find these formats harder to use than CSV or an API.
- No page describes known gaps in who is covered. For example, survey data excludes people in
  communal establishments, and the family food survey is a household sample.

## Recommendations for the NDL page template (fix once, fixes all 84)

1. Add an "About this data" panel to every data page with:
   - owner organisation and owner role
   - update frequency and next update date
   - time period and geography
   - security classification (OFFICIAL)
   - licence
   - a link to methodology or a DQAP
2. Publish each page's metadata as DCAT with DQV quality measurements. The kit already produces
   this: `assessments/ndl/results/ndl-pages.dqv.jsonld`.
3. Give every chart download a CSV on the Web (CSVW) metadata file that names the measure, the unit
   and the reference period.
4. Add a "Data for other UK nations" line wherever coverage is partial.
5. Say which breakdowns are available on every page about people, and link to GSS harmonised standards.
6. Fix the DVSA abbreviation on the Driving tests page.

## How confident we are

- Page details were gathered on 14 October 2026 by reading each page's text. Links and labels that
  appear only after clicking, or only on the source publisher's site, were not counted. Methodology is
  often one click away on the publisher's site, so DQ-3 measures what the NDL page itself shows.
- The licence, security classification and owner role checks are structural: no page has a field for
  them. They are counted as gaps because the CDA guidance asks for them, but they apply strictly only
  when an asset is designated a CDA.
- Only 8 of 20 chart files were checked, and one (UK house prices) was too large to read whole, so it
  was left out.
