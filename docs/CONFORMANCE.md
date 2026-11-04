# Conformance of the Commons' templates with government data quality policy and guidance

Assessed 4 November 2026 against the published GOV.UK pages, each read in full on that day. The machine-readable
version of this assessment is `knowledge/requirements.csv` (the requirements register), shown on the portal's
Frameworks page.

**Key:** ✅ conforms · 🟡 partly: what is missing is listed · ➖ not applicable to a template (an organisational duty)

## 1. Sources

| Source | Status | Published or updated |
|---|---|---|
| [Data asset management policy in government](https://www.gov.uk/government/publications/data-asset-management-policy-in-government/data-asset-management-policy-in-government) | Mandatory for central government departments and ALBs | 16 April 2026 |
| [Identifying and recording critical data assets](https://www.gov.uk/government/publications/identify-and-record-critical-data-assets/identifying-and-recording-critical-data-assets) | Mandatory, as above | 16 April 2026 |
| [Recording metadata to describe critical data assets](https://www.gov.uk/government/publications/record-metadata-to-describe-critical-data-assets/recording-metadata-to-describe-critical-data-assets) | Supports the policy | 16 April 2026 |
| [Data ownership model](https://www.gov.uk/government/publications/data-ownership-in-government/data-ownership-model) | Supports the policy | 16 April 2026 |
| [Data quality action plan: implementation guide](https://www.gov.uk/government/publications/implement-a-data-quality-action-plan/data-quality-action-plan-implementation-guide) | The 7 steps every DQAP, or equivalent, must cover | 11 November 2025, updated 16 April 2026 |
| [Data quality issues framework](https://www.gov.uk/government/publications/implement-a-data-quality-action-plan/data-quality-issues-framework) | Method for scoring and prioritising issues | 11 November 2025 |
| [The Government Data Quality Framework](https://www.gov.uk/government/publications/the-government-data-quality-framework/the-government-data-quality-framework) | Principles, lifecycle and dimensions | 3 December 2020 |

## 2. Data asset management policy

| Requirement | Where the Commons meets it | Status |
|---|---|---|
| Every identified asset has a named data owner | DQAP workbook Details; register entry template; CDA return `gds_dataowner` | ✅ |
| Every asset has a DQAP, or equivalent covering all 7 steps | DQAP workbook (every step, with a Checklist tab); playbook plan template organised by step | ✅ (changed in v2.4.0: Communication plan tab, review and resolution dates, options and costs added) |
| Metadata recorded and reviewed every 12 months | Metadata Weaver; annual review note template; CDA return review dates | ✅ |
| Assets reported to GDS | CDA return (`cda-return.csv`) | 🟡 GDS has not published a return format; the Commons' column names are a proposal |
| Minimum standards for quality, discoverability and interoperability | Rules and issues framework; metadata checks; identifier and value set checks | 🟡 the policy page sets no measurable thresholds, so none can be checked against |
| CDO accountable; CDO Council oversight; annual ministerial letter | — | ➖ |

## 3. Identifying and recording critical data assets, and the data ownership model

| Requirement | Where | Status |
|---|---|---|
| Designate by purpose: one or more of the 7 GOV.UK purposes | Register entry template; CDA return `gds_purposes` | ✅ (added in v2.4.0). The values are recorded as given, not yet checked against the list |
| Named data owner or IAO; successor named when an owner leaves | DQAP Details (owner, steward, custodian, IAO); annual review note | ✅ (added in v2.4.0) |
| Designate the source data set, not only a distribution | Register entry template; CDA return `gds_sourcedataset` | ✅ (added in v2.4.0) |
| Owner, steward and custodian roles; names and roles kept in metadata | RACI tab; DQAP Details | ✅ Names stay in the organisation's own records; the public Commons never stores them |
| Contact details for the asset (the guidance suggests a team mailbox) | Weaver "Contact point (a team or role)" | ✅ Compatible: a team mailbox is a team contact. The Commons itself still never publishes an email address |
| Enterprise data ownership model, asset registers, sharing agreements | — | ➖ |

## 4. Recording metadata for critical data assets

| Property | Guidance | Weaver and the UK CDA profile check | Status |
|---|---|---|---|
| creator, dateCreated, title, description, expires, supersededBy, temporalCoverage, conformsTo, accessRights, securityClassification, licence | Mandatory | Checked as "must" (changed in v2.4.0: expires and supersededBy moved to must; identifier moved to should) | ✅ |
| identifier, mediaType | Recommended | Checked as "should" | ✅ |
| alternativeTitle | Optional | Not carried | 🟡 low priority |
| Dates in ISO 8601 | Required | Date check in every profile | ✅ |
| accessRights values (open, commercial, internal); creator from a list of organisations | Required vocabularies | accessRights and securityClassification values checked (v2.5.0); creator flagged if it looks like an email address | 🟡 creator not yet matched to the organisations list |
| DCAT as the main standard; GEMINI or INSPIRE for geospatial; IANA media types | Required | DCAT and GeoDCAT-AP outputs; media types carried | ✅ (UK GEMINI profile added in v2.5.0, alongside GeoDCAT-AP) |

## 5. DQAP implementation guide: what each step must record

| Step | Must record | DQAP workbook | Status |
|---|---|---|---|
| 1. Identify critical data | Critical data items, known issues, whether a DQAP exists and where | Criticality matrix, Issues log, Details (status and link) | ✅ (link added in v2.4.0) |
| 2. Identify rules | Users and needs; rules, measures, methods, targets and percentage thresholds | Details (users and needs), Metrics | ✅ (users and needs added in v2.4.0) |
| 3. Assess current quality | Baseline, issues with priorities, targets per measure | Results, Issues log | ✅ |
| 4. Prioritise and set goals | Priorities, actions, timeframes, owners, review dates, goals and target percentages | Issues log, Actions (review date and goal added) | ✅ |
| 5. Root cause and action | Root causes, systemic or one-off, options, costs and benefits, owners, target dates | Causes (options, cost and benefit added), Actions | ✅ |
| 6. Report | Stakeholder list, communication plan, target and actual resolution dates | Communication plan tab (new), Issues log (dates added) | ✅ |
| 7. Repeat over time | Frequency, results over time, trends, issue progress | Details, Results (history), Operations, Issues log | ✅ |
| Roles | Owner, steward, custodian, analyst, IAO, process owner, user | RACI tab | ✅ |
| Dimensions | DAMA UK core six, adaptable | All six measured; representativeness added for inclusion | ✅ |

## 6. Data quality issues framework

| Element | Commons | Status |
|---|---|---|
| Definition of an issue (fails a rule target) | Issues are rules below target | ✅ |
| Importance and impact 1 to 4; combined score 1 to 16 | `dqkit/framework.py` and the browser engine, tested against GOV.UK examples | ✅ (playbook rule template corrected in v2.4.0: it said 1 to 5) |
| Target ranges 75–90, 90–97.5, 97.5–99.9, 99.9–100 | Exact | ✅ |
| Performance bands; 100% target graded Critical (4) | Exact | ✅ |
| Priority levels 1–7, 8–16, 17–32, 33–64; resolution within 0, 1, 3, 6 measurements | Exact | ✅ |
| **Finding:** GOV.UK table 4 gives 96.75% as the High band start for a 97.5% target, but the framework's own rule ("halfway between the Middle band start and the target") gives 96.25% | The Commons follows the stated rule | Raise with the GDS data quality team |

## 7. Government Data Quality Framework

| Principle or practice | Where | Status |
|---|---|---|
| 1. Commit: governance, capability, continuous improvement (DQAPs) | Operating model, Learn, Skills and training, DQAP workbook | ✅ |
| 2. Know your users and their needs | DQAP Details (users and needs), portal feedback survey | ✅ |
| 3. Assess throughout the lifecycle; communicate across it | Control points (source, pipeline, reporting); playbook stages; Communication plan | ✅ |
| 4. Communicate quality clearly; documentation and metadata | Data quality statement template; trust levels; DQV output; Weaver | ✅ |
| 5. Anticipate change: root cause analysis, build quality into new systems | Causes tab (5 whys); Legacy and modernisation; data contracts | ✅ |
| Lifecycle (plan, collect, prepare, use, share, archive) | Playbook stages and control points | 🟡 archive or destroy is covered by the playbook, not by a separate template |
| Six dimensions (completeness, uniqueness, consistency, timeliness, validity, accuracy) | All measured by checks | ✅ |

## 8. Domain, sector and capability guidance

Each has an entry in `knowledge/frameworks.yaml` and, where measurable, a pack in `packs/`.

| Area | Guidance | How the Commons supports it | Status |
|---|---|---|---|
| Official statistics | Code of Practice for Statistics 3.0; QAAD; Welsh and Scottish quality policies | uk-statistics pack; QAAD level field; supplier QA route | ✅ (confirm standard-by-standard wording against the full Code) |
| Analysis | AQuA Book; Analysis Function quality questions | Frameworks, crosswalk, Learn | ✅ guidance only: the Commons measures input data, not models |
| Personal data | UK GDPR accuracy principle, ICO guidance | uk-personal-data-accuracy pack; identifier checks; inclusion checks | ✅ |
| Health | NHS Data Quality Maturity Index | nhs-dqmi-style pack (indicative) | 🟡 approximates the official DQMI |
| Geospatial | ISO 19157-1; Q-FAIR; GEMINI and INSPIRE | iso-19157 pack; Q-FAIR ratings; GeoDCAT-AP; UK GEMINI profile | 🟡 positional accuracy needs reference data |
| AI and analytics | ISO/IEC 5259 | ai-ml-readiness pack; AI for data quality guidance | 🟡 label quality and drift need model-side evidence |
| International | ESS QAF, UN NQAF, IMF DQAF, FCSM, Canada, ABS, NAA | Packs or crosswalks | ✅ |
| Devolved nations | Scotland data standards; Welsh quality strategy | Frameworks, scenarios | ✅ (the DAM policy is not mandatory there) |

## 9. What changed in v2.4.0 because of this assessment

1. DQAP workbook: Communication plan tab; Checklist tab for the 7 steps; review dates, target and actual resolution
   dates (target date worked out from the priority and the measurement cycle), options considered, costs and benefits,
   goals; Details rows for the DQAP link, users and needs, SMEs, custodian, IAO and next review.
2. Playbook templates: issues framework scales corrected to 1 to 4; register entry, issue log, action plan and annual
   review fields brought into line with the guidance.
3. CDA return: purposes, data owner, steward, IAO, provided to, source data set, measurement frequency and review dates.
4. UK CDA profile in the Weaver: must and should lists match the metadata guidance.
5. Registers: two GOV.UK sources added (identifying critical data assets; data ownership model) and five requirements.

## 10. Closed in v2.5.0

- `accessRights` must start Open, Commercial or Internal; `securityClassification` must start OFFICIAL (the DAM policy's scope); a publisher that looks like an email address is flagged. Both engines, parity tested.
- UK GEMINI profile for geospatial assets in the Metadata Weaver (the critical data asset guidance asks for GEMINI for geospatial data).
- The capability, data model and workflows that carry out these requirements are published as models (`models/`, D-MOD-01); each step cites the clause it implements.

## 11. Still open

- `creator` (the publisher) is flagged if it looks like an email address, but not yet matched against the GOV.UK organisations register, which changes often and isn't available offline; planned as a build-time list.
- A published GDS return schema, when there is one, to replace the proposed CDA return columns.
- The issues framework table discrepancy (section 6): a note for the GDS data quality team is drafted; the project lead sends it through GDS's own channel.
