# Data quality tooling in the UK public sector: research and GitHub analysis

Date: 14 October 2026. Interactive version: the "Public Sector DQ Tooling Atlas" artifact.

## Method
- Broad web research on data quality frameworks, tools and standards in UK government, the NHS, statistics producers and international peers.
- GitHub repository search by name and description across 20+ public sector organisations. Code search was not available because it needs a GitHub sign-in this session didn't have.
- 27 repositories were shallow-cloned and every text and code file was scanned for DQ tools, the six dimensions, standards and inclusion signals. 21 of them are about data quality. 6 turned out to be software QA, infrastructure, empty or unreachable.
- Limits: private repos and commercial platform configurations are not visible.

## Key findings
1. **Teams build their own rule engines.** Examples:
   - Home Office DQ profiler: Scala and Spark, 169 rule modules, MIT. Last commit March 2024.
   - DfE eesyscreener: R, 63 checks.
   - MHCLG digital-land: a YAML expectations engine.
   - PHS: R Shiny dashboards.

   Only ONS pystagegate uses a general framework (Great Expectations). There is no Soda, Pandera, dbt tests, Deequ or DQV in any repo.
2. **Planning data has the most mature model.** `digital-land/specification`:
   - `issue-type.csv` holds 45 issue types, each with a severity, a quality dimension, and whether the council or MHCLG must fix it.
   - `quality.csv` defines a 7-level ladder: none, some, indicative, verifiable, authoritative, usable, trustworthy.
3. **The CDDO metadata exchange model has no quality properties.** `co-cddo/ukgov-metadata-exchange-model` is LinkML, outputs DCAT, JSON Schema and SHACL, and has no quality slots. So CDA baseline scores can't be exchanged in a machine-readable way.
4. **Dimension coverage is uneven.** Repos mentioning each dimension, out of 21:

   | Dimension | Repos |
   |---|---|
   | Uniqueness | 18 |
   | Accuracy | 12 |
   | Consistency | 12 |
   | Validity | 11 |
   | Completeness | 8 |
   | Timeliness | 6 |

   None of the 45 planning issue types measures timeliness.
5. **Central DQ community code has gone quiet.**
   - `dqhub-resources` is nearly empty and was last updated in 2022.
   - The admin data quality framework stopped in 2023, and the question bank in 2024.
   - MoJ `data_linter` and `mojap-metadata` are no longer publicly reachable.
6. **Inclusion checks are rare.** Only two repos encode them:
   - DfE's screener enforces GSS harmonised ethnicity values.
   - NHS England's linkage framework (QAFDL) checks for fairness and uneven error across population groups.

   No repo reports completeness of protected-characteristic fields separately.

## Recommendations
1. Propose DQV-based quality properties for the cross-government metadata exchange model: a measurement per dimension, a link to the DQAP, and the date measured.
2. Adopt the planning issue-type pattern as a cross-government DQ issue vocabulary, mapped to the issues framework's importance × impact scoring.
3. Publish a DQAP starter kit: Great Expectations and Pandera (Python), validate and pointblank (R).
4. Score metadata quality for CDAs in the NDL, modelled on the data.europa.eu metadata quality assessment (DCAT-AP, DQV, SHACL).
5. Make harmonised-standards checks and linkage fairness checks mandatory for CDAs that hold personal data.
6. Ask the DQ Hub to refresh its GitHub presence. Ask MoJ to republish or openly archive data_linter.

## Repositories analysed
- UKHomeOffice/data-quality-profiler-and-rules-engine
- dfe-analytical-services/eesyscreener
- digital-land/digital-land-python, digital-land/specification, digital-land/quality-challenge, digital-land/green-box-data-quality
- ONSdigital/pystagegate, ONSdigital/crvs.pkg
- Public-Health-Scotland/phs-dq-dashboard, Public-Health-Scotland/vacc-dq-reporting, Public-Health-Scotland/phsmethods
- best-practice-and-impact/Data-Quality-Question-Bank, best-practice-and-impact/admin-data-quality-stats, best-practice-and-impact/dqhub-resources, best-practice-and-impact/qa-of-code-guidance
- moj-analytical-services/splink
- nhsengland/quality-assurance-framework-for-data-linkage
- co-cddo/ukgov-metadata-exchange-model
- DFE-Digital/dfe-reference-data
- alphagov/GDS-Accessibility-Monitoring-Platform-Data-Audit-2022
- data-cleaning/validate (Statistics Netherlands)
- Excluded as not data quality: ukhsa-collaboration/standards-qat, DEFRA/rpa-quality-checks, UKHomeOffice/dq-tf-apps, dwp/quality-tool, dwp/miqat (empty)
- Not reachable: moj-analytical-services/data_linter, moj-analytical-services/mojap-metadata

## Status of recommendations (updated 14 October 2026)
1. DQV quality properties: built as a draft extension (LinkML, JSON Schema, SHACL) in ndl-dq-assurance `model/`. The proposal to GDS is drafted, not sent.
2. Issue vocabulary: built, with 43 issue types and 8 dimensions in `vocab/`.
3. Starter kit: built. `dqkit` passes 21 tests and exports to Great Expectations and R validate.
4. NDL metadata scoring: built and run on all 84 NDL pages (see `claude/NDL_ASSURANCE_REPORT.md`).
5. Inclusion checks: built, as the representativeness dimension plus the `not_unknown` and `group_disparity` checks.
6. Outreach: drafts ready for the DQ Hub, MoJ and the NDL team. Not sent.

## How this research compares with the GDS Data Quality Tooling Review (added 14 October 2026)

The GDS Data Management Team's review (October 2026) and a DSIT-facing brief research note were
compared with this research. They are complementary:

| | GDS Tooling Review | Brief research note | This research and Atlas |
|---|---|---|---|
| Lens | Market (Gartner 2026 Magic Quadrant) | Sectors and architecture | Open code and public repos |
| Tools covered | 13 Magic Quadrant vendors plus 5 others | Talend/Qlik, Informatica, Microsoft, Experian, Civica, Datactics, NHS DQMI | 21 public repos, plus open-source frameworks |
| Open source and government-built | One line | Not covered | Main focus |
| Mapped to DQAP steps | In prose | No | Yes |
| Accessibility, open standards, exit | No | No | Yes (added) |
| Evidence from government use | Through the planned survey | Procurement notices (unreferenced) | Code and documentation in public repos |

**Shared conclusion:** all three point to a tool-agnostic approach. That means shared rules,
common measures and reusable reporting patterns, with organisations choosing tools that fit their
estate. The brief research calls this "Option 2 plus Option 3" (standard capabilities and
measures, plus a reference architecture and assured patterns). This kit is a working example of
that pattern.

**Taxonomy alignment:** the review's 8 core features map to this kit as follows:

| Review feature | Kit |
|---|---|
| Connectivity | CSV and pandas only (deliberately small) |
| Profiling and monitoring | 15 checks, history |
| Rule discovery, creation and management | Rules files |
| Alerts, notifications and visualisation | Operations tab and escalation |
| Data transformations | Not in scope |
| Matching | Not in scope |
| Workflow and issue resolution | Issues log, causes, actions |
| Active metadata and lineage | DQV metadata |

Of the advanced features, it covers integration with other tools through its Great Expectations,
R validate and DQV exports.

**Checked claim:** NHSBSA bought a "Self Service Data Quality (Data Profiling Tool)" from Datactics
(Contracts Finder, April 2023, up to £451,500).
