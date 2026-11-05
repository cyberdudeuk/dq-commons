# User research bundle

**Status: no primary research has been done yet.** Everything below is a hypothesis drawn from
published guidance, the public sector code review, and the NDL assessment. Validate it before
treating it as evidence.

## Proto-personas

| Persona | Context | Goal | Pain point (hypothesis) |
|---|---|---|---|
| Sam, data steward at an arm's length body | Spreadsheets and SQL; no budget for tools | Get the January baseline done | Doesn't know where to start; template feels abstract |
| Priya, senior data owner | Accountable for 6 CDAs | Know what to fix first | Gets long issue lists with no priority |
| Alex, NDL catalogue officer | Curates collection pages | Show users whether data is trustworthy | No standard fields for quality |
| Jordan, data user with a visual impairment | Uses a screen reader | Download and analyse data | PDF-only and dashboard-only data is hard to use |
| Morgan, analyst in Northern Ireland | Looks for UK-wide comparisons | Find equivalent NI data | England-only pages don't signpost NI sources |

### Change and delivery proto-personas (v2.9.0)

| Persona | Context | Goal | Pain point (hypothesis) |
|---|---|---|---|
| Dami, SRO of a benefits system replacement | Accountable for a three-year programme | Go live on time without harming claimants | Data readiness reported green until the last rehearsal fails |
| Chris, data migration lead at a supplier | Moving 12 million records with legacy codes | A clean, reconciled switch-over | No agreed rules, or owner to accept "good enough" |
| Leah, records manager in a department | Holds the information asset register and retention schedule | New systems keep and dispose of records properly | Brought in after the design is fixed |
| Tom, business analyst on an alpha | Writing requirements for a new data collection | Acceptance criteria testers and suppliers can use | Business rules live in people's heads |

Journeys for each are on the For your role page (`knowledge/change-delivery.yaml`).

## Hypotheses to test
1. A rules file in YAML is usable by stewards with spreadsheet skills, given examples. (If not, build the web form, F-09.)
2. Framework-based priorities change what owners fix first.
3. Users trust NDL pages more when quality and owner information is shown.
4. Signposting other UK nations increases successful finds for devolved-nation users.
5. Programmes that use the gate questions and RACI find data readiness problems earlier (test with two live programmes and an assurance reviewer).
6. Records managers and data stewards who share one asset register and lifecycle duplicate less work (test with two departments).
7. People without GitHub accounts give more feedback when a Microsoft Form is offered.

## Research plan
1. **Sample:** 8 to 10 stewards from at least 5 organisations, including 2 ALBs and 1 devolved administration. Include at least 2 disabled participants and 2 people who have little experience with data tools.
2. **Methods:** task-based usability sessions (run a baseline on a sample file); interviews with 4 data owners; unmoderated tests of NDL page variants.
3. **Ethics:** informed consent, no personal data in the test files, and accessible materials (Easy Read summary, BSL interpreter on request).
4. **Outputs:** findings report, updated personas, prioritised backlog.

## Secondary evidence already gathered
- Public Sector DQ Tooling Atlas (27 repos): teams build their own engines; few inclusion checks.
- NDL assessment (84 pages): consistent metadata gaps; 27 pages without an open machine-readable format.
- CDA effort model: capacity is the main constraint for January.

## Research questions added for v0.4.0

1. **Rules without the command line:** can a data steward with no coding background write a working rules file using only the portal's rule builder? Measure task completion and time.
2. **Owners and escalation:** do data owners understand an escalation ticket well enough to act, without opening the workbook?
3. **Assistive technology:** does the checker work with a screen reader and keyboard only? This includes the file inputs, results table and copy buttons.
4. **Trust levels:** which portal page do CDOs read first, and is the trust level understood as a suggestion rather than a decision?

## Research plan for v1.0.0 (XDMH-212)
**Recruit 5 organisation types:** a local authority, a devolved government body, an NHS trust, a voluntary organisation, a central department; at least 2 participants who use assistive technology; at least 1 Welsh speaker.
**Tasks to test:** find the frameworks that apply to you; check a CSV with an identifier rule; complete the maturity self-assessment; draft rules with the assistant and judge whether you trust them; contribute a resource; take a survey.
**Questions:** Does "Commons" read as for everyone, or as central government? Is the menu grouping clear? Do tours help or get in the way? What would stop you contributing? How do you feel about AI drafting rules? Is anything missing for your nation or sector?
**Built-in feedback:** the "Tell us about the Commons" survey (no names, totals only).

## Additions for v1.1.0
**Recruit also:** a commercial or procurement lead, a supplier delivering a public service, a programme team mid-migration.
**Tasks:** build a data quality schedule for a contract; score a tender answer; reconcile two extracts; export rules as a data contract and load it in another tool; publish a resource; find a knowledge base article from the front page.
**Questions:** Is the clause wording usable as a starting point by commercial teams? Would suppliers accept the burden of proof? Does the carousel help or distract? Is "Not yet reviewed" understood?
