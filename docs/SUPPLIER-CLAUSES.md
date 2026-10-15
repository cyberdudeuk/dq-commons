# Data quality obligations for suppliers: model clauses

**Status:** illustrative drafting, not legal advice and not approved government terms. Source of truth: knowledge/commercial.yaml in the repository; this page is generated from it.

## Why

Most public sector data now lives in, or passes through, systems run by suppliers. When quality obligations are vague, public bodies pay twice: once for the service, and again to find and fix poor data, to work around it, or to exit.

- UK public sector digital and data spend was about £26 billion in 2023, of which about £21 billion went to third parties.
- Only 28% of leaders believe they have enough capability to monitor supplier performance; only 40% say third parties perform as expected.
- Actual spend with managed service providers exceeded contract value by more than 50% in 2023.
- 70% of survey respondents said their data landscape is not well co-ordinated or interoperable.
- Contracts over £5 million under the Procurement Act 2023 must have at least three KPIs, assessed and published at least once every 12 months.

## Principles

- **The supplier proves quality.** The supplier measures and reports the quality of the data its service creates, holds or changes, using agreed rules, at its own cost.
- **We own our data, metadata and rules.** Public bodies own the data, the metadata about it, and the quality rules and results, in open formats, at no extra charge.
- **Quality is a KPI.** At least one KPI measures data quality, so it appears in published contract performance notices for contracts over £5 million.
- **Fix at source, at the supplier's cost.** Defects caused by the supplier's system or process are fixed by the supplier, within agreed timescales, without a change request.
- **Exit-ready from day one.** Data and documentation are kept ready to hand over at any time, in open formats, with quality evidence.
- **Open standards by default.** Open standards for data, metadata, identifiers, contracts and APIs, as the Technology Code of Practice expects.
- **Include everyone.** Systems can record people, places and characteristics accurately, without forced defaults, and quality is measured across groups.
- **Transparent automation.** Any AI or automated processing that changes data is documented, tested and switchable, with human review for high-impact changes.

## Clauses

### C01 Data quality standard of performance (must)

*Theme:* Quality obligations

The Supplier shall ensure that Authority Data created, received, stored, transformed or provided by the Services meets the Data Quality Rules in Schedule [X] at or above the target for each rule. The Data Quality Rules shall be set out in an open, machine-readable format agreed with the Authority (for example the Open Data Contract Standard, a Frictionless Table Schema or the Commons rules format) and may be updated by agreement without a change in the Charges.

- Why: Makes quality a stated part of the service, not an assumption.
- Supplier evidence: Rules file agreed at mobilisation; measurement results for every reporting period.
- Measure: Share of rules meeting target each period.

### C02 Data quality rules and targets set with the Authority (must)

*Theme:* Quality obligations

During mobilisation the Supplier shall work with the Authority to identify the critical data items in the Services and agree a rule, dimension and target for each, using the Government's data quality issues framework (importance of purpose x impact of the issue) unless the Parties agree otherwise.

- Why: Targets follow the government method, so scores are comparable across suppliers.
- Supplier evidence: Agreed criticality matrix and rules file.
- Measure: Rules agreed before service commencement.

### C03 Free access to Authority Data in open formats (must)

*Theme:* Ownership and access

The Authority owns all Authority Data, associated metadata, data quality rules and data quality results. The Supplier shall make them available to the Authority on request and through an agreed interface, in open, documented, non-proprietary formats (such as CSV meeting RFC 4180, JSON, or Parquet with a published schema), at no additional charge and without rate limits that prevent routine quality checking.

- Why: Removes the cost and lock-in of reaching your own data.
- Supplier evidence: Interface documentation; test extract during mobilisation.
- Measure: Extract requests met within the agreed time.

### C04 Data model, definitions and lineage documented (must)

*Theme:* Standards and metadata

The Supplier shall maintain and provide to the Authority an up-to-date data dictionary, data model and lineage for Authority Data, including code lists, permitted values, defaults and derivations, and shall notify the Authority at least [30] days before any change that affects them.

- Why: Undocumented data models are a main source of data debt and exit risk.
- Supplier evidence: Data dictionary and model in an open format; change notices.
- Measure: Dictionary completeness; changes notified on time.

### C05 Data quality KPI (must)

*Theme:* Reporting and KPIs

Key Performance Indicator [n] (Data Quality): the percentage of Data Quality Rules meeting their target in the reporting period. Target: [95]%. The Supplier shall report it [monthly], with the results for each rule, in W3C Data Quality Vocabulary (DQV) or another agreed open format.

- Why: Under the Procurement Act 2023, contracts over £5 million need at least three KPIs that are assessed and published; data quality should be one of them.
- Supplier evidence: Monthly quality report; DQV file.
- Measure: The KPI itself.

### C06 Quality report contents (should)

*Theme:* Reporting and KPIs

Each data quality report shall include, for each rule: the measured result, the target, the trend, open data quality issues with their priority and age, root causes identified, and actions taken, and shall state any known limitations of the data.

- Why: Turns a number into something the Authority can act on and explain to users.
- Supplier evidence: Report template agreed at mobilisation.
- Measure: Reports complete and on time.

### C07 Notification of serious data quality incidents (should)

*Theme:* Reporting and KPIs

The Supplier shall notify the Authority within [one] Working Day of becoming aware of a data quality issue rated Critical or High under the issues framework, or any issue likely to affect decisions about individuals, and shall provide a containment plan within [two] Working Days.

- Why: Fast warning limits harm to people and decisions.
- Supplier evidence: Incident log.
- Measure: Notifications on time.

### C08 Fix at source at the Supplier's cost (must)

*Theme:* Remediation

Where a data quality issue is caused by the Supplier's systems, processes, staff or subcontractors, the Supplier shall correct the affected data and the root cause at its own cost, within the resolution timescale for the issue's priority (Critical: immediately; High: within one reporting period; Medium: within three; Low: within six), and shall not treat such work as a Change.

- Why: Stops paying twice for the supplier's defects.
- Supplier evidence: Issue log with root causes and fixes.
- Measure: Issues resolved within timescale.

### C09 Service credits linked to data quality (should)

*Theme:* Remediation

If the Data Quality KPI falls below the [Requires improvement] level for [two] consecutive periods, Service Credits shall apply as set out in Schedule [Y], and the Supplier shall provide a remediation plan for approval.

- Why: Gives the KPI teeth without waiting for a breach.
- Supplier evidence: Remediation plan.
- Measure: Periods below target.

### C10 Recording people and places accurately (must)

*Theme:* Inclusion and equality

The Services shall allow names, addresses, dates and personal characteristics to be recorded accurately and in full (including non-Latin characters, single names, and addresses without a postcode where appropriate), shall not force default or placeholder values, and shall use the Government Statistical Service harmonised standards for characteristics where the Authority specifies them.

- Why: Forced defaults and narrow formats misrecord people, often those already less well served.
- Supplier evidence: Test cases agreed with the Authority, including edge cases.
- Measure: Share of records with defaulted or unknown values.

### C11 Quality measured across groups (should)

*Theme:* Inclusion and equality

Where Authority Data describes people, the Supplier shall report data quality results separately for groups the Authority specifies (for example by age band, sex, ethnic group, disability or nation) and shall flag differences larger than the agreed tolerance.

- Why: Data can pass overall checks while failing particular groups.
- Supplier evidence: Group-level results.
- Measure: Largest gap between groups.

### C12 Exit data pack (must)

*Theme:* Exit and transition

On request, and in any case before expiry or termination, the Supplier shall provide a complete copy of Authority Data with its data dictionary, data model, quality rules, latest quality results and open issues, in open formats, and shall reconcile record counts and key totals with the Authority and any replacement supplier, at no additional charge.

- Why: Clean exit data cuts transition cost and risk.
- Supplier evidence: Exit plan maintained from mobilisation; test exit at least once a year.
- Measure: Successful test exit; reconciliation passed.

### C13 Annual exit rehearsal (should)

*Theme:* Exit and transition

Once a year the Supplier shall carry out a test extract of the exit data pack and the Authority (or a party it nominates) shall load and reconcile it. Defects found shall be fixed under clause [C08].

- Why: An untested exit plan usually fails when it's needed.
- Supplier evidence: Rehearsal report.
- Measure: Rehearsal passed.

### C14 Transparent AI and automated processing (must)

*Theme:* AI and automation

The Supplier shall not use AI or automated processing to create, change, match, enrich or delete Authority Data without the Authority's written approval. For any approved use the Supplier shall document the purpose, model and data used, provide evaluation results (overall and by group), keep a log of changes made, allow the feature to be switched off, route low-confidence or high-impact outputs to human review, and provide the information the Authority needs for an Algorithmic Transparency Recording Standard record and any DPIA.

- Why: AI can quietly change data quality, for better or worse.
- Supplier evidence: Model card, evaluation results, change log.
- Measure: Approved uses documented; changes logged.

### C15 Keep components supported and data debt visible (must)

*Theme:* Legacy and technical debt

The Supplier shall keep all software used for the Services in mainstream support for the term, maintain a register of known data quality debt (for example overloaded fields, hard-coded rules, free text where codes are needed, duplicated master data) with a plan to reduce it, and report progress [quarterly].

- Why: Prevents the next generation of legacy and makes data debt something that is managed.
- Supplier evidence: Support status register; data debt register.
- Measure: Components out of support; data debt items closed.

### C16 Flow-down to subcontractors (must)

*Theme:* Subcontractors

The Supplier shall include obligations equivalent to clauses [C01-C15] in any subcontract under which the subcontractor creates, holds or changes Authority Data, and remains responsible for their performance.

- Why: Obligations must reach whoever actually handles the data.
- Supplier evidence: Subcontract extracts.
- Measure: Subcontracts compliant.

### C17 Right to check quality independently (should)

*Theme:* Assurance

The Authority, or a party it nominates, may independently measure the quality of Authority Data using the agreed rules, through the access in clause [C03], and the Supplier shall co-operate and investigate any material difference from its own reported results.

- Why: Trust, but verify.
- Supplier evidence: Co-operation with checks.
- Measure: Differences explained.

### C18 Open standards and identifiers (should)

*Theme:* Standards and metadata

The Supplier shall use open standards for data and interfaces as the Authority directs, including persistent identifiers (for example UPRN for addresses, GSS codes for geography, Companies House or charity numbers for organisations, ODS codes for health organisations), ISO 8601 dates, UTF-8 text, and OpenAPI 3 descriptions for APIs.

- Why: Shared identifiers and formats are what make data join up.
- Supplier evidence: Interface and data specifications.
- Measure: Share of records with valid identifiers.

### C19 Processor duties for personal data accuracy (must)

*Theme:* Privacy

Where the Supplier processes personal data as a processor, it shall, in addition to the terms required by UK GDPR Article 28, help the Authority keep personal data accurate and up to date, including by correcting inaccurate data promptly on instruction and supporting rectification requests from individuals.

- Why: Accuracy is a legal duty for personal data; the processor holds the levers.
- Supplier evidence: Rectification log.
- Measure: Rectification requests met on time.

### C20 Accessible data quality tools and reports (should)

*Theme:* Accessibility

Any interface the Supplier provides for reviewing data quality results, issues or reports shall meet WCAG 2.2 level AA, so staff who use assistive technology can do this work.

- Why: Data quality work must be open to everyone in the team.
- Supplier evidence: Accessibility statement and audit.
- Measure: Accessibility issues open.

## Tender questions

1. How will you measure and report the quality of the data your service creates or holds? Show an example report. *Good answer:* Named rules for critical items, targets from the issues framework, monthly results in an open format such as DQV, trends and open issues.
2. In what formats can we get all our data, metadata, rules and quality results, and at what cost? *Good answer:* Open, documented formats on demand through an interface, at no extra charge.
3. Describe how you find and fix the root cause of data defects, and who pays. *Good answer:* Root cause analysis, fix at source within priority timescales, at the supplier's cost when the supplier caused it.
4. How does your service record names, addresses and characteristics for people it serves? What defaults does it force? *Good answer:* No forced defaults; supports non-Latin characters, single names, addresses without postcodes; GSS harmonised standards.
5. What AI or automated processing touches our data? How can we test it, see what it changed and switch it off? *Good answer:* Full list, evaluation results by group, change log, off switch, human review route, ATRS support.
6. Show your exit plan for data. When did you last rehearse an exit, and what went wrong? *Good answer:* A tested exit pack with dictionary, rules and reconciliation; honest lessons.
7. Which open standards and identifiers does your service use? *Good answer:* UPRN, GSS, ODS and others as relevant; ISO 8601; UTF-8; OpenAPI 3; ODCS or Table Schema for contracts.
8. Can staff who use assistive technology use your data quality screens? *Good answer:* WCAG 2.2 AA with an accessibility statement and recent audit.

## Who does what

| Activity | Supplier | Public body |
|---|---|---|
| Agree critical data items, rules and targets | Responsible | Accountable |
| Measure quality every period | Responsible and accountable | Informed |
| Independent spot checks | Consulted | Responsible |
| Fix defects the supplier caused | Responsible and accountable (at its cost) | Informed |
| Fix defects in data the authority supplied | Consulted | Responsible |
| Report the data quality KPI | Responsible | Accountable (publishes performance notice) |
| Keep exit pack ready and rehearse it | Responsible | Accountable |
| Approve any AI use on the data | Consulted | Accountable |

## Sources

- [State of digital government review (DSIT, January 2025)](https://www.gov.uk/government/publications/state-of-digital-government-review/state-of-digital-government-review)
- [Procurement Act 2023 guidance: key performance indicators](https://www.gov.uk/government/publications/procurement-act-2023-guidance-documents-manage-phase/guidance-key-performance-indicators-html)
- [Procurement Act 2023, section 52](https://www.legislation.gov.uk/ukpga/2023/54/section/52/enacted)
- [Procurement Act 2023 guidance for Wales: key performance indicators](https://www.gov.wales/procurement-act-2023-guidance-key-performance-indicators-html)
- [The Technology Code of Practice](https://www.gov.uk/guidance/the-technology-code-of-practice)
- [The Digital, Data and Technology Playbook](https://www.gov.uk/government/publications/the-digital-data-and-technology-playbook)
- [ICO: contracts between controllers and processors](https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/accountability-and-governance/guide-to-accountability-and-governance/contracts/)
- [Open Data Contract Standard (Bitol)](https://bitol-io.github.io/open-data-contract-standard/latest/)
