# Data quality guidance crosswalk

How published government guidance, and the ways organisations have applied it, line up with one
another and with this kit. Prepared 14 October 2026 from 15 sources: the 2026 GOV.UK pages, plus 13
documents shared by the project lead (7 guidance documents, then 6 tooling and adoption documents). Named individuals in the source documents are not reproduced
here (decision D-013).

## Sources

| ID | Source | Organisation | Date | What it is |
|---|---|---|---|---|
| S1 | The Government Data Quality Framework | Government Data Quality Hub | 2020 | Principles, the 6 DAMA UK dimensions, and the DQAP idea |
| S2 | Implement a data quality action plan, with the data quality issues framework | GDS (GOV.UK) | Apr 2026 | 7-step DQAP guide, scoring method, DQAP template |
| S3 | DQAP Implementation Guide v2.0 (pilot) | Cross-government (DQ Hub community) | 2024–25 | 9-step guide with RACI, templates, training links and further content (R04, R08, R17, R23, R26, R41, R42) |
| S4 | Data Quality Issues Framework v1.0 | Cross-government | pre-2026 | Full scoring method, with an issue priority calculator |
| S5 | Data Quality Action Plans: Start here! v1.0 | Defra | 2024 | 4-step minimum DQAP for first-timers, with 3 annex templates |
| S6 | Data Quality Trust Scales | Independent Office for Police Conduct (IOPC) | 2023, updated 2024 | 4-level trust scale that decides internal or external use |
| S7 | Data Quality Assessment Decision Tree | Government data quality community (publisher not named in the file) | Jul 2023 | Routes internal and external data through DQAP steps |
| S8 | Quality Framework for Data Science | NHS England | Sep 2024 | Analytical QA framework: 5 pillars, 20 areas, log with RAG and evidence |
| S9 | DQ Guidance and Training note | Cross-government DQ community | 2024 | Background, training links, and organisations' practice |
| S10 | Data Quality Tooling Review (revised) | GDS Data Management Team | Oct 2026 | Market overview using Gartner's 2026 Magic Quadrant: 5 use cases, 8 core and 7 advanced features, 18 vendors |
| S11 | Cross-Government Data Quality Solutions Survey (Forms design) | GDS Data Management Team | Oct 2026 | 109 questions: organisation once, then 33 questions repeated for up to 3 solutions |
| S12 | Brief research on data quality tools in UK government | Not stated (prepared for DSIT) | 2025–26 | Tool landscape, capability matrix, controls model (source, pipeline, reporting), options paper |
| S13 | Data Quality Case Study Template | GDS Data Management Team | 2026 | Case study form for the Shared Learning Library, structured on the 7 DQAP steps |
| S14 | Adopting DQAPs in Practice (Scottish Government session) | GDS Data Management Team | 2026 | 7 steps with roles per step, a worked rule example, the Shared Learning Library |
| S15 | Adopting DQAPs in Practice (DQ Week) | GDS Data Management Team | 2026 | Owner and steward roles, issue intake and triage, containment and corrective action, metrics and escalation |

## 1. Process steps

| This kit | S2 (7 steps) | S3 (9 steps) | S5 (Defra, 4 steps) | S6 (IOPC) | S7 (tree) |
|---|---|---|---|---|---|
| `asset:` block, Criticality matrix tab | 1 Identify critical data | 1 Identify critical data | Data owner and steward named (Annex 1) | Set up: consult owners and users | Define use cases and stakeholders |
| `rules:` in the YAML; Metrics tab | 2 Identify rules | 2 Identify rules | 1 Define rules (Annex 2) | Document production and usage | Assess structure; define parameters |
| `dqkit check`; Results tab | 3 Assess current quality | 3 Initial assessment; 4 Document findings | 2 Measure and record (Annex 3) | Assess: basic dimensions, then plus dimensions | Measure against parameters |
| Issues framework scoring; Issues log | 4 Prioritise and set goals | 5 Prioritise; 6 Define goals | 3 Prioritise (impact, addressability) | Classify on the trust scale | Is the assessment meeting its aims? |
| Causes and Actions tabs | 5 Root cause and action | 7 Root cause and action | 4 Plan response, escalate | Action log | Make changes where appropriate |
| DQV JSON-LD, trust level, dashboards | 6 Report | 8 Report | Communicate with users; update catalogue metadata | Publish and share | Store, visualise, communicate |
| `--history`; trend columns | 7 Repeat | 9 Repeat | Commit to repeat | Review; plan the next trust scale | Repeat at the required frequency |

**Note:** S2 and S3 number their steps differently, because S3 splits two steps. The kit labels outputs with S3's 9 steps in the RACI tab. It doesn't depend on either numbering.

## 2. Dimensions

| Dimension | S1/S2/S3/S5 | S6 IOPC | S8 NHS England | This kit |
|---|---|---|---|---|
| Completeness, uniqueness, consistency, timeliness, validity, accuracy | ✓ (DAMA UK) | ✓ basic | Part of "verification and validity" | ✓ |
| Relevance; coherence and comparability; accessibility and clarity | — | ✓ "plus" (from the ESS) | Partly (documentation, presentation) | ✓ added to the vocabulary (qualitative) |
| Representativeness and fairness | — | Personal data accuracy only | ✓ "Ethics and fairness", bias checks | ✓ representativeness dimension and checks |
| Metadata quality | Step 6 mentions metadata | Accessibility and clarity | Documentation and transparency | ✓ 20 metadata checks |

## 3. Targets and prioritisation

| Topic | S4 / S2 issues framework | S5 Defra | S6 IOPC | S9 practice | This kit |
|---|---|---|---|---|---|
| Target | From importance × impact ranges | Set per business need (for example 100% for mandatory, 75% for descriptive) | No formula | — | Rule target, or a policy default: low end of the range (D-021) |
| Priority | Importance × impact × band | Impact plus addressability | Expert judgement | NHSBSA uses the organisation's risk framework | Exact framework method, tested |
| Timescales | Measured in measurement cycles | — | Action log | HMRC: 10-step remediation | Shown on each issue |

## 4. Roles

| Role | S2/S3 | S5 | S6 | S8 | This kit |
|---|---|---|---|---|---|
| Accountable | Data owner A(Quality); IAO A(Risk). The IAO role is "under review" (S3). | Data owner | Data owner decides, advised by the DQ team | Analytical assurer | `owner` in the asset block; RACI tab from S3 |
| Doing | Steward, custodian, analyst | Steward | DQ team | Lead analyst, quality lead | `steward` |

## 5. What each source adds that the others lack

1. **S5 Defra "Start here":** the smallest workable DQAP. It accepts estimates and ad hoc evidence at first. This supports a proportionate January baseline.
2. **S6 IOPC trust scale:** turns quality results into a usage decision (internal only, or external). It also sets a firm rule: personal data accuracy below 90% can't be Trustworthy, and anything below 100% needs an action plan. Built into `dqkit/trust.py`.
3. **S7 decision tree:** the only source that deals with data you receive but don't control. That is common for critical data assets, which are by definition shared, and for the NDL, which republishes others' data. Built into `dqkit/pathway.py`.
4. **S8 NHS England:** quality of the analysis around the data, such as commissioning, peer review, version control and uncertainty. It complements the DQAP. It doesn't replace it.
5. **S9:**
   - Lists the W3C Data Quality Vocabulary as future metadata guidance. That supports D-014.
   - Records organisations' own practices:
     - Home Office: a DQ policy, and an investigation of shared tooling
     - NHSBSA: risk-based selection of critical data elements
     - HMRC: 10-step remediation
     - NHS England: a merged DQ framework

## 6. Contradictions and errors found

| # | Finding | Effect | How the kit handles it |
|---|---|---|---|
| F1 | S4 Tables 7 and 8 give the High band start for a 97.5% target as **96.75%**. The rule in the same document ("halfway between Middle band start and target") gives **96.25%**. | Departments copying the table set the band 0.5 points too high, so issues can score one priority level too low | Follows the stated rule. A unit test documents the slip. |
| F2 | S4 lists band scores as "1 – Low, 2 – Middle, 3 – High". Its own worked example gives 1 to performance just below target, which is the upper band. | The opposite reading inverts priorities | Follows the worked example and the 2026 GOV.UK page: closest band 1, furthest band 3 |
| F3 | S2 has 7 steps and S3 has 9 | Confusion in training and reporting | Mapped in table 1 |
| F4 | S3, S9 and the GOV.UK template file names still say "Essential Shared Data Assets". The 2026 policy says "critical data assets". | Mixed terminology in returns | The kit uses CDA. Templates should be renamed. |
| F5 | S3 says the IAO role is under review, while its RACI makes the IAO accountable for risk | Unclear accountability | The workbook RACI shows both A(Risk) and A(Quality) |
| F6 | No GOV.UK source says how quality should decide whether data can be shared | Inconsistent sharing decisions | Adds the IOPC trust level, and a `trust_level` field in the model |
| F7 | GOV.UK DQAP steps assume you own the data | CDAs and the NDL often don't | Adds the decision tree route |
| F8 | Inclusion is almost absent: only S8 (fairness) and S6 (personal data accuracy) touch it | Gaps for under-recorded groups stay hidden | Adds the representativeness dimension and checks |
| F9 | Several targets used in practice (S5: "75% might be good enough") sit at the very bottom of the framework range | Inconsistent strictness | Default target policy "low", stated openly. Owners can choose mid or high. |
| F10 | S10 leaves out open-source and government-built tools. These include Great Expectations, Soda Core, dbt tests, R `validate` and `pointblank`, MoJ `data_linter`, NHS England's DQMI and MHCLG's digital-land checks. S10 gives them one line ("SQL, Python, R, Excel"). It also leaves out Microsoft Fabric and Purview data quality, although Purview is a survey option and is part of the CDA return platform. | Smaller bodies with little or no tooling budget see no affordable route. The review is not reproducible openly, because the Gartner report is paywalled. | The Tooling Atlas covers these. This kit is itself an open, tool-agnostic option. |
| F11 | S10 has no criteria for accessibility for staff using assistive technology, open-standards export (DQV, portable rules) or exit and lock-in | Tool choices can exclude disabled staff and lock quality results into one vendor, against the Technology Code of Practice (open source, open standards) | The Atlas adds these 3 criteria. The kit exports DQV and portable rules. |
| F12 | S11 and S13 collect name, role and email without a privacy notice, lawful basis or retention period | UK GDPR transparency risk. It also puts some people off responding. | Survey analysis drops personal fields on load (`dqkit survey`). Case study drafts leave them blank. |
| F13 | S11 can't answer 3 of S10's own questions. It has no organisation type or size, although S10 asks how usage differs by scale. It doesn't ask how widely a tool is used, although S10 says it will. It has no link to CDAs, DQAP steps or the CDA return. Its maturity scale doesn't match the Data Maturity Assessment for Government (Beginning, Emerging, Learning, Developing, Mastering). Q32 runs 1 = easy to 5 = hard, the opposite direction to the other ratings. | Results can't be segmented or tied to the DAM policy. Ratings are easy to misread. | See `docs/SURVEY-REVIEW.md` for 12 fixes. Analysis flags the reversed scale. |
| F14 | S12 lists 5 GDQF dimensions and leaves out uniqueness (S1 and GOV.UK list 6). Its citations are bare footnote numbers with no reference list. It predates the DAM policy, CDAs and DQAPs. | Can't be checked or reused as evidence as it stands | One claim checked and confirmed: NHSBSA bought a Datactics profiling tool (Contracts Finder, 2023). Its recommendation matches this kit's approach: shared rules, common measures, reusable reporting, tool-agnostic. |
| F15 | S13 has no structured before-and-after measures, no CDA identifier and no inclusion question. Its maturity stages don't match the Data Maturity Assessment. | Case studies can't be compared or linked to the CDA register | `--case-study` drafts the template from results and adds these 3 fields as proposals |
| F16 | S14 and S15 contain errors: they write "EDSA" for ESDA (now CDA). S15 slide 17 describes the "DAM policy" as an organisation's internal data policy (its own domains, systems and exceptions), not the cross-government policy. S15 also uses US spellings ("standardization", "prioritizes", "program"). | Confuses the mandate with local policy. Doesn't follow GOV.UK style. | Flag to GDS (outreach draft) |
| F17 | The Shared Learning Library (S14), with the MoJ case study, framework and playbook, sits in a members-only Knowledge Hub group | Not discoverable by local government, devolved administrations, the third sector or the NDL. This works against the DAM policy's own discoverability aim. | Recommend mirroring on GOV.UK or GitHub under OGL, and cataloguing it in the NDL |
| F18 | S14 notes the DAM policy is not mandatory for the Scottish Government | Four-nations gaps in CDAs mirror the NDL finding that 45 of 48 partial-UK pages don't signpost every other nation | Tools, templates and case studies should be usable by devolved administrations as they are |

### What S10 to S15 add (built into the kit in v0.3.0)

| Source | Idea | Where it is in the kit |
|---|---|---|
| S12 | Controls at source, in the pipeline, or in reporting | `control_point` on every rule (default per check type). Shown in Metrics and the Issues log. |
| S15 | Metrics: defect volumes, ageing of open issues, recurrence, control failure rate | `dqkit/operations.py` and the workbook's Operations tab |
| S15 | Escalation for overdue remediation and repeated failures | Issues log "Escalation" column, using issues framework timescales |
| S15 | Containment versus corrective action; validation criteria | Actions tab: action type (Containment, Corrective, Preventive) and "How we will know it worked" |
| S15 | Intake details: source system, immediate risk | Issues log input columns |
| S13 | Case study template | `--case-study` writes a draft (.md and .docx) |
| S11 | Survey | `dqkit survey` reshapes the Forms export to one row per organisation and solution, and summarises it |
| S14 | Roles per step | Already in the workbook RACI (from S3). Matches S14. |
| S14 | Worked rule: NI number present and valid in at least 98% of claims | Consistent with the issues framework: 98% sits in the 97.5–99.9 range for combined score 8–9 |

## 7. Recommendations

1. **Ask GDS to correct S4 Table 7 and 8 (F1) and clarify the band labels (F2).** These are small fixes with a real effect on priorities.
2. **Publish one numbering of the DQAP steps (F3).** Rename the ESDA templates to CDA (F4).
3. **Adopt a trust scale in the CDA guidance (F6).** Record the result in metadata (`trust_level`).
4. **Add an "external data" route to the DQAP guide (F7).** Use the decision tree as the basis.
5. **Make representativeness checks expected for CDAs holding personal data (F8).**
6. **Offer Defra's "Start here" as the official proportionate entry point** for the January baseline.
7. **Point DQAP users to NHS England's framework** for the quality of analysis built on the data.
8. **Fix the survey before it launches (F12, F13).** Add a privacy notice, organisation type and size, CDA and DQAP links, open-source options and DMA levels, and make the rating directions consistent. See `docs/SURVEY-REVIEW.md`.
9. **Widen the tooling review (F10, F11).** Add open-source and government-built tools, and criteria for accessibility, open standards and exit.
10. **Add before-and-after measures, a CDA identifier and inclusion to the case study template (F15).** Accept kit-drafted case studies.
11. **Publish the Shared Learning Library openly (F17).**
12. **Put S15's operational metrics and the containment, corrective and preventive distinction into the GOV.UK DQAP guide.** Correct the deck errors (F16).
