# Data quality management playbook for critical data assets

> Generated from `knowledge/playbook.yaml` by `scripts/build_playbook_doc.py`. Edit the YAML, not this file.
> Last reviewed 2026-10-30. Owner: Data quality lead (Commons). Content licence: OGL v3.0.

A repeatable way to know, prove and improve the quality of the data that matters most. Eight stages, from choosing your critical data to keeping it healthy year after year. Each stage has steps, outputs, a checklist, who does what, an inclusion check and the matching requirement in the UK DAM policy and elsewhere.

**Interactive version:** the portal page `playbook.html` has a checklist you can tick, template downloads and a jurisdiction finder.

## Who it is for

- UK government departments and arm's length bodies with critical data assets (mandatory under the DAM policy)
- Devolved administrations, local government, the NHS, police and the third sector (voluntary adoption)
- Crown Dependencies, Overseas Territories and international partners
- Any organisation with data that many people or services depend on

## Use it anywhere

Use your own words. The playbook works the same whatever your mandate calls things.

| In this playbook | You might call it |
|---|---|
| Critical data asset (CDA) | Critical data, key dataset, master or reference data, high-value dataset (EU), essential shared data asset (older UK term) |
| DAM policy | Your data strategy, data governance policy, statistics code, regulator's rules or contract |
| Data quality action plan (DQAP) | Data quality plan, improvement plan, quality assurance plan (Canada, Australia, US agencies) |
| Data owner | Information asset owner, data custodian, accountable executive, business owner |
| CDA return | Annual data inventory, asset register submission, catalogue record |

If your context has no mandate, start at stage 1 and use the issues framework as your method. Nothing here depends on the UK policy.

## Principles

1. **Fit for purpose.** Quality means good enough for the decisions and services that rely on the data. Agree what 'good enough' means with the people who use it.
2. **Start with what matters.** Focus on the few data items that drive important decisions, not every column.
3. **Measure, don't guess.** Write rules down, test them automatically and keep the results. A score without a rule is an opinion.
4. **Fix causes, not symptoms.** Cleaning data downstream hides the problem. Fix it where the data is created.
5. **Be open about limits.** Publish what you know about quality, including what is wrong. Users trust honest data more than perfect-looking data.
6. **Include everyone.** Check that quality is as good for every group of people the data describes. Missing or wrong data about some groups excludes them from services.
7. **Keep it going.** Quality is a routine, not a project. Measure on a cycle, review every year and hand over cleanly.

## The eight stages

### Stage 1: Identify your critical data

**Goal:** Know which data assets are critical and which data items in them matter most. *Typical effort: 1 to 3 days per asset.*

**Steps**

1. List data assets other teams, services or organisations depend on.
2. Test each against your criteria. Under the DAM policy: shared value across government, open or restricted classification, serving one or more of the policy's purposes.
3. Record each critical asset with an owner, a steward and the standard metadata properties.
4. For each asset, name the 5 to 15 data items that drive the most important decisions (critical data elements).
5. Record who uses the data, for what, and the people or places it describes.

**Outputs:** Critical data asset register; Critical data elements list per asset; User and purpose map.

**Checklist**

- [ ] Every critical asset has a named owner and steward (roles, not just a team).
- [ ] Metadata is complete enough for someone outside your team to find and understand the asset.
- [ ] Critical data elements are agreed with at least two user teams.
- [ ] You know which groups of people, places or organisations the data covers, and which it might miss.

**Who leads:** Data owner (A), Data steward (R).

**UK DAM policy and DQAP:**

- `DAM-1` Identify, record and centrally report shared critical data assets
- `DAM-2` Assign clear ownership and accountability for each data asset
- `DAM-4` Meet minimum standards for discoverability
- `DQAP-1` Identify critical data and the data items that matter most
- `CDA-M` Record 13 metadata properties including creator, identifier, temporal coverage, conformsTo and security classification

**Elsewhere:** Comparable to: ISO 8000-61 (data quality planning), DAMA-DMBOK (critical data elements), Canada GC data quality guidance (identify key data), EU high-value datasets.

**Inclusion check:** Check the user map includes services for disabled people, people on low incomes, Welsh and other language users, and all four UK nations where relevant.

**Toolkit:** Describe the asset once and see gaps against the CDA metadata (`weaver.html`).

### Stage 2: Define quality rules and targets

**Goal:** Turn 'good enough' into rules a computer can test, with agreed targets. *Typical effort: 2 to 5 days per asset.*

**Steps**

1. For each critical data element, choose the dimensions that matter (completeness, uniqueness, consistency, timeliness, validity, accuracy).
2. Write each rule in plain English first, then as a testable rule.
3. Set a target for each rule using the importance of the purpose and the impact of failure (issues framework target ranges).
4. Record the rules as a data contract so suppliers and users see the same promise.
5. Agree targets with the data owner and the main users.

**Outputs:** Rule catalogue; Targets per rule; Data contract (ODCS).

**Checklist**

- [ ] Every critical data element has at least one rule.
- [ ] Every rule names its dimension, owner and target.
- [ ] Targets come from user impact, not from what the data already achieves.
- [ ] Rules are stored as files, not only in a tool, so they survive a change of supplier.

**Who leads:** Data owner (A), Data steward (R), Data quality lead or analyst (R).

**UK DAM policy and DQAP:**

- `DAM-3` Meet minimum standards for data quality through a DQAP or equivalent
- `DAM-5` Meet minimum standards for interoperability
- `DQAP-2` Identify data quality rules, dimensions and agreed thresholds
- `IF-1` Combined score = importance of purpose x impact of the issue
- `IF-2` Target ranges by combined score: 75-90, 90-97.5, 97.5-99.9, 99.9-100

**Elsewhere:** Comparable to: ISO/IEC 25012 (quality characteristics), ODCS v3.1 quality rules, W3C DQV, ESS and UN NQAF quality dimensions.

**Inclusion check:** Add rules for fields that affect fair treatment: completeness of protected characteristics where lawfully collected, valid address formats for all nations, names in all scripts.

**Toolkit:** Write rules in plain English with the assistant, then save them as a data contract (`assistant.html`).

### Stage 3: Measure and set a baseline

**Goal:** Know where you are today. *Typical effort: 1 to 3 days per asset.*

**Steps**

1. Profile the data to see patterns, gaps and outliers.
2. Run every rule and record results with the date and data version.
3. Log every failure as an issue with its dimension, size and affected users.
4. Break results down by group (region, nation, age band, channel) where you lawfully can.
5. Write the baseline into a short data quality statement.

**Outputs:** Baseline results; Issue log; First data quality statement.

**Checklist**

- [ ] Results are reproducible (same rules, same data, same result).
- [ ] Each issue says how many records and which users are affected.
- [ ] You have looked for differences in quality between groups.
- [ ] Results are stored where the next steward will find them.

**Who leads:** Data owner (A), Data steward (R), Data quality lead or analyst (R).

**UK DAM policy and DQAP:**

- `DQAP-3` Assess current quality, log issues and set a baseline

**Elsewhere:** Comparable to: ISO 8000-8 (measurement), IMF DQAF assessment, ABS data quality statements.

**Inclusion check:** If quality is worse for a group, record it as a separate issue so it is not averaged away.

**Toolkit:** Profile and check a file in your browser; nothing is uploaded (`check.html`).

### Stage 4: Prioritise

**Goal:** Fix the issues that hurt most first. *Typical effort: Half a day per cycle.*

**Steps**

1. Score each issue with the issues framework: importance of purpose times impact, then the band below target.
2. Sort by priority. Critical issues are fixed immediately; high in one cycle; medium in three; low in six.
3. Agree the order with the data owner. Record accepted risks explicitly.
4. Turn the top issues into a data quality action plan with goals and dates.

**Outputs:** Prioritised issue list; Data quality action plan; Risk acceptances.

**Checklist**

- [ ] Every issue has a priority score and a resolution timescale.
- [ ] Accepted risks are signed by the data owner, with a review date.
- [ ] The plan has measurable goals (rule X from 82% to 95% by a date).
- [ ] Issues that affect some groups more than others are not ranked down because they are 'small'.

**Who leads:** Data owner (A), Data steward (R).

**UK DAM policy and DQAP:**

- `DQAP-4` Prioritise improvements and set goals using impact and risk
- `IF-3` Bands below target set a band score; priority = combined x band
- `IF-4` Resolution: Critical immediately; High 1 cycle; Medium 3; Low 6

**Elsewhere:** Comparable to: risk-based prioritisation in ISO 31000 and DAMA-DMBOK; US agency data quality plans.

**Inclusion check:** Weight impact by who is affected, not only how many: a small number of wrong records can stop someone getting a service.

**Toolkit:** Score and rank issues with the government method (`guidance.html`).

### Stage 5: Find causes and fix at source

**Goal:** Stop problems coming back. *Typical effort: Varies by cause.*

**Steps**

1. For each priority issue, ask why until you reach the cause (people, process, system, supplier, standard).
2. Choose the fix closest to where the data is created. Prefer prevention (validation at entry, shared identifiers, code lists) over cleaning.
3. Give each action an owner and a date. Put supplier actions into the contract or change request.
4. Re-run the rules to prove the fix worked.

**Outputs:** Root cause records; Actions with owners; Evidence that fixes worked.

**Checklist**

- [ ] Every fix is tested by re-running the rule.
- [ ] Fixes at source are preferred; any downstream cleaning is recorded and temporary.
- [ ] Supplier obligations are in the contract with a KPI.
- [ ] Changes to forms or systems were tested with users, including assistive technology users.

**Who leads:** Data owner (A), Data steward (R), Data producer or system owner (R).

**UK DAM policy and DQAP:**

- `DQAP-5` Identify root causes, choose and own actions

**Elsewhere:** Comparable to: ISO 8000-61 improvement process, Plan-Do-Check-Act, Lean root cause analysis.

**Inclusion check:** Fix forms that force wrong answers (no 'prefer not to say', one-line names, UK-only postcodes). These cause bias at source.

**Toolkit:** Put data quality duties and KPIs into supplier contracts (`commercial.html`).

### Stage 6: Report and be open

**Goal:** Users know how good the data is and what it can safely be used for. *Typical effort: Half a day per cycle.*

**Steps**

1. Update the data quality statement each cycle: scores, trends, known issues and what the data should not be used for.
2. Publish quality metadata with the asset (W3C DQV or the CDA return fields) so catalogues such as the National Data Library can show it.
3. Report the portfolio to your governance board and the centre (for example the CDA return).
4. Rate the asset with Q-FAIR (quality, findable, accessible, interoperable, reusable): record access route, standards, licence and provenance so the ratings can be shown.
5. Tell affected users directly about critical issues.

**Outputs:** Data quality statement; Quality metadata; Portfolio report or CDA return.

**Checklist**

- [ ] The statement is in plain English, accessible (WCAG 2.2 AA) and dated.
- [ ] It says what the data is not fit for, not only what it is fit for.
- [ ] Machine-readable quality metadata is published with the catalogue record.
- [ ] Group differences in quality are reported, not hidden.

**Who leads:** Data owner (A), Data steward (R).

**UK DAM policy and DQAP:**

- `DAM-4` Meet minimum standards for discoverability
- `DQAP-6` Report quality to stakeholders, including limitations

**Elsewhere:** Comparable to: Code of Practice for Statistics (Quality pillar), ESS quality reports, ABS and Statistics Canada quality statements, W3C DQV.

**Inclusion check:** Test the statement with people outside the data team. Offer it in Welsh where required and in Easy Read where the data describes the public.

**Toolkit:** Export results as DQV and CDA return rows (`pipeline.html`).

### Stage 7: Monitor and sustain

**Goal:** Quality stays good without heroics. *Typical effort: Hours per month once set up.*

**Steps**

1. Run checks automatically on every new load or on a fixed cycle (monthly is a good start).
2. Track trends; alert when a rule drops below its target.
3. Escalate using agreed thresholds (see escalation).
4. Build skills: train stewards and producers; share rules and lessons with other teams.
5. Keep rules, results and the plan in version control so they survive staff and supplier changes.

**Outputs:** Automated checks; Trend dashboard; Escalation log; Training record.

**Checklist**

- [ ] Checks run without manual effort.
- [ ] Someone is alerted when quality drops, and knows what to do.
- [ ] The steward role has a named deputy.
- [ ] Rules and results are stored openly where licensing allows (MIT code, OGL content).

**Who leads:** Data owner (A), Data steward (R), Data producer or system owner (R), Data quality lead or analyst (R).

**UK DAM policy and DQAP:**

- `DQAP-7` Repeat measurement, track trends, refine rules

**Elsewhere:** Comparable to: data observability practice, ISO 8000-150 (roles), continual improvement in ISO 9001.

**Inclusion check:** Keep the group breakdowns in the monitoring, not just the baseline.

**Toolkit:** Schedule checks in a pipeline and watch the status (`pipeline.html`).

### Stage 8: Review every year

**Goal:** The asset, rules and targets still match what users need. *Typical effort: 1 day per asset per year.*

**Steps**

1. At least every 12 months, review the asset record, owner, rules, targets and plan.
2. Ask users whether the data still meets their needs; add rules for new uses (for example AI training).
3. Retire rules that no longer matter; raise targets that are now easy.
4. Check maturity and set next year's goals.
5. Submit the updated record or return.

**Outputs:** Annual review note; Updated register entry; Next year's goals.

**Checklist**

- [ ] The review is dated and signed off by the data owner.
- [ ] New uses (such as AI) have been assessed against the AI-ready data guidance.
- [ ] The asset is still correctly classed as critical, or has been retired with a reason.
- [ ] Lessons are shared with the Commons or your community.

**Who leads:** Data owner (A), Data steward (R).

**UK DAM policy and DQAP:**

- `DAM-6` Review asset records at least every 12 months

**Elsewhere:** Comparable to: annual statistical quality reviews, ISO 8000-61 review, management review in ISO 9001.

**Inclusion check:** Ask representatives of groups the data describes whether anything has changed for them.

**Toolkit:** Re-run the maturity self-assessment (`maturity.html`).

## Who does what (RACI)

R = does the work, A = accountable, C = consulted, I = informed.

| Role | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 |
|---|---|---|---|---|---|---|---|---|
| Data owner | A | A | A | A | A | A | A | A |
| Data steward | R | R | R | R | R | R | R | R |
| Data producer or system owner | C | C | C | C | R | I | R | C |
| Data users | C | C | I | C | C | I | I | C |
| Data quality lead or analyst | C | R | R | C | C | C | R | C |
| Data governance board or CDO | I | I | I | I | I | I | I | I |
| People the data describes | I | I | I | C | C | I | I | C |

- **Data owner:** Senior person accountable for the asset and its quality. Signs off targets, accepts risks, funds fixes.
- **Data steward:** Day-to-day lead. Writes rules, runs checks, keeps the issue log and plan.
- **Data producer or system owner:** Team or supplier that creates or changes the data. Fixes causes at source.
- **Data users:** Teams, services and analysts who rely on the data. Say what they need and report problems.
- **Data quality lead or analyst:** Specialist support: methods, tooling, profiling and reporting.
- **Data governance board or CDO:** Sets policy, sees the portfolio, resolves escalations, reports to the centre.
- **People the data describes:** Citizens, communities and their representatives. Help spot exclusion and test whether published quality information is understandable.

## Rhythm

| When | What | Who |
|---|---|---|
| Every load or monthly | Run rules, update the trend, alert on drops | Steward |
| Quarterly | Update the action plan, report to the data owner and governance board | Steward, owner |
| Every 12 months | Annual review, update the register entry or CDA return | Owner, steward |
| On any change | Re-baseline after a system migration, supplier change or new use | Steward, producer |

## Escalation

| Level | Trigger | Action | By |
|---|---|---|---|
| Critical | A rule for a critical data element falls into the lowest band, or wrong data could harm people or break the law | Tell users the same day; owner decides whether to pause use; governance board informed | Immediately |
| High | A rule falls more than one band below target | Owner agrees a fix in the action plan | Within one cycle |
| Medium | A rule falls one band below target | Steward plans a fix | Within three cycles |
| Low | Slightly below target, low impact | Log and monitor | Within six cycles |

## Measures

| Measure | Target |
|---|---|
| Critical assets with a named owner and steward | 100% |
| Critical data elements with at least one rule | 100% |
| Rules meeting target | Rising each quarter |
| Critical issues resolved within timescale | 100% |
| Assets with a current data quality statement | 100% |
| Assets reviewed in the last 12 months | 100% |
| Assets with quality broken down by group where lawful | Rising each year |

## Templates

Use roles and contact forms, not personal names or emails.

### Critical data asset register entry

| Asset name | Identifier | Description | Data owner (role) | Data steward (role) | Classification | Policy purposes served | Users and uses | Critical data elements | Coverage (people, places, period) | Known gaps in coverage | Update frequency | Licence | Catalogue link | Last reviewed |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|

### Data quality rule

| Rule ID | Data element | Plain-English rule | Dimension | Test (data contract or toolkit rule) | Target | Importance of purpose (1-5) | Impact of failure (1-5) | Owner | Date agreed |
|---|---|---|---|---|---|---|---|---|---|

### Issue log entry

| Issue ID | Date found | Rule ID | Description | Records affected | Users or groups affected | Combined score | Band below target | Priority | Resolution timescale | Root cause | Action and owner | Status | Date closed |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|

### Data quality action plan

| Asset | Goals for this period | Issues in scope by priority | Actions | Owners | Dates | Risks accepted and by whom | Resources needed | Review date |
|---|---|---|---|---|---|---|---|---|

### Data quality statement

| Asset and version | Date | Overall summary in plain English | Scores by dimension and trend | Known issues and their effect | Quality by group where lawful | What the data is fit for | What it should not be used for | How to report a problem | Contact (role or form, not a personal email) |
|---|---|---|---|---|---|---|---|---|---|

### Annual review note

| Asset | Date | Still critical? (yes, no and why) | Owner and steward confirmed | Rules added or retired | Targets changed | New uses assessed (including AI) | Maturity level | Goals for next year | Sign-off (role) |
|---|---|---|---|---|---|---|---|---|---|

## Inclusion checks

- [ ] Does the data cover everyone it should? Compare its coverage with an independent count (census, register) by group and place.
- [ ] Is missing data worse for some groups? Break completeness down by group where you lawfully can.
- [ ] Do forms and systems allow people to describe themselves accurately (names, addresses, sex and gender questions following current statistical guidance, 'prefer not to say')?
- [ ] Do rules work for all four UK nations and overseas addresses, not just England?
- [ ] Are quality statements accessible (WCAG 2.2 AA), in plain English, and in Welsh where required?
- [ ] Have people the data describes, or their representatives, had a chance to comment?
- [ ] If the data feeds automated decisions or AI, have you checked for bias against the AI-ready data guidance and ISO/IEC 5259?

## Where it applies

| Where | Basis | Frameworks in the Commons |
|---|---|---|
| UK government (departments and ALBs) | DAM policy (mandatory for CDAs), DQAP and issues framework guidance, CDA metadata guidance, Government Data Quality Framework | Data asset management policy in government; Implement a data quality action plan, and the data quality issues framework; Recording metadata to describe critical data assets; The Government Data Quality Framework |
| UK official statistics | Code of Practice for Statistics 3.0 (Quality pillar) | Code of Practice for Statistics, Edition 3.0 |
| Scotland | Not bound by the DAM policy; Scottish data standards and official statistics quality guidance | Data standards in Scotland's public sector - framework for action: consultation analysis; Producing official statistics - quality management policy (Scottish Government) |
| Wales | Not bound by the DAM policy; Welsh Government statistical quality management | Statistical quality management strategy (Welsh Government) |
| Health (England) | NHS Data Quality Maturity Index | Data Quality Maturity Index (DQMI) |
| Personal data (all UK) | UK GDPR accuracy principle | UK GDPR accuracy principle (Article 5(1)(d)) and ICO guidance |
| European statistics and data spaces | ESS Quality Assurance Framework; CEN/CLC/TS 18331 maturity model; prEN 18352 governance quality framework (draft) | Quality Assurance Framework of the European Statistical System (ESS QAF) |
| Canada | Government of Canada data quality guidance (nine dimensions) | Guidance on Data Quality (Government of Canada) |
| Australia | ABS Data Quality Framework; National Archives data quality guidance | ABS Data Quality Framework; Data quality (National Archives of Australia information management guidance) |
| United States | FCSM data quality framework for federal statistics | A Framework for Data Quality (FCSM 20-04) |
| International | UN National Quality Assurance Frameworks; IMF DQAF; ISO 8000; ISO/IEC 25012; ISO/IEC 5259 for AI | United Nations National Quality Assurance Frameworks Manual for Official Statistics; IMF Data Quality Assessment Framework (DQAF); ISO 8000 Data quality (series), including ISO 8000-8:2015 Information and data quality: Concepts and measuring, and ISO 8000-61 process reference model; ISO/IEC 25012 Data quality model; ISO/IEC 5259 Artificial intelligence - Data quality for analytics and machine learning (ML) (series) |

## Sources

- [Data asset management policy in government](https://www.gov.uk/government/publications/data-asset-management-policy-in-government/data-asset-management-policy-in-government)
- [Implement a data quality action plan (DQAP implementation guide)](https://www.gov.uk/government/publications/implement-a-data-quality-action-plan/data-quality-action-plan-implementation-guide)
- [The Government Data Quality Framework](https://www.gov.uk/government/publications/the-government-data-quality-framework/the-government-data-quality-framework)
- [Guidelines and best practices for making government datasets ready for AI](https://www.gov.uk/government/publications/making-government-datasets-ready-for-ai/guidelines-and-best-practices-for-making-government-datasets-ready-for-ai)
- [Open Data Contract Standard](https://bitol-io.github.io/open-data-contract-standard/latest/)
- [W3C Data Quality Vocabulary](https://www.w3.org/TR/vocab-dqv/)
