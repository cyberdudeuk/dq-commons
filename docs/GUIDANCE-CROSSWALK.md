# Data quality guidance crosswalk

How published government guidance, and the ways organisations have applied it, line up with one
another and with this kit. Prepared 14 October 2026 from 9 sources: the 2026 GOV.UK pages, plus 7
documents shared by the project lead. Named individuals in the source documents are not reproduced
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

## 7. Recommendations

1. **Ask GDS to correct S4 Table 7 and 8 (F1) and clarify the band labels (F2).** These are small fixes with a real effect on priorities.
2. **Publish one numbering of the DQAP steps (F3).** Rename the ESDA templates to CDA (F4).
3. **Adopt a trust scale in the CDA guidance (F6).** Record the result in metadata (`trust_level`).
4. **Add an "external data" route to the DQAP guide (F7).** Use the decision tree as the basis.
5. **Make representativeness checks expected for CDAs holding personal data (F8).**
6. **Offer Defra's "Start here" as the official proportionate entry point** for the January baseline.
7. **Point DQAP users to NHS England's framework** for the quality of analysis built on the data.
