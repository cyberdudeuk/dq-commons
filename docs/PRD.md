# Product requirements: NDL data quality assurance kit

## Problem
Departments must report a data quality baseline for every critical data asset (CDA) in their first
return under the data asset management policy. The GOV.UK DAM policy also requires a DQAP or equivalent for each asset. But:
- departments mostly build their own checking tools (Public Sector DQ Tooling Atlas, October 2026)
- there is no shared issue vocabulary
- the cross-government metadata model has no field for quality
- the NDL's own pages don't yet show the metadata the policy asks for (assessment, 14 October 2026)

## Users and needs

| User | Need |
|---|---|
| Data steward in a department or ALB | Measure the quality of my asset quickly, in a way GDS will accept, without buying a tool |
| Data owner (senior) | See which issues matter most and how fast they must be fixed |
| GDS / NDL catalogue team | Receive quality results in a standard, machine-readable form; show them to users |
| CDO Council | See quality across government and where help is needed |
| Data user (public, researcher, journalist) | Know whether data is fit for my purpose, and for which groups of people |

## Requirements (MoSCoW)

**Must:**
1. Apply the GOV.UK issues framework exactly (importance, impact, targets, bands, priority, timescale).
2. Cover the six DAMA UK dimensions, plus inclusion (representativeness).
3. Output rows for the GOV.UK DQAP template.
4. Output W3C DQV metadata.
5. Assess catalogue records against the DAM policy and CDA metadata guidance, with every check citing its source.
6. Run without paid software; MIT licence.
7. Explain results in plain English.

**Should:**
1. Export to Great Expectations and R validate.
2. Offer a shared issue vocabulary as SKOS.
3. Propose a quality extension to the metadata model.
4. Run in CI.

**Could:**
1. Connectors for databases and Spark.
2. A web form for non-technical stewards.
3. Publish to Purview or Dataverse.

**Won't (this release):**
1. Store or process personal data centrally.
2. Replace departmental tools.

## Success measures
- A steward with no prior experience can run a first baseline in under one hour (to test in user research).
- 100% of the issues framework's published examples are reproduced by the tests (achieved: tests pass).
- The NDL page template gains the missing metadata fields, and the average NDL score rises from 50.9% to over 75%.
- At least 3 departments use the vocabulary or kit for the January return.

## Out of scope / constraints
- Data stays with its owner. The kit runs where the data is.
- Only OFFICIAL data, matching DAM policy scope.

## Scope update: v0.4.0 (15 October 2026)

**Now in scope:**
- **Operating the kit, not just running it once:**
  - a portfolio of assets measured on a schedule
  - escalation of overdue issues as tickets
  - rows produced for the CDA return
- **One NDL Data Quality Portal for every audience:**
  - a status page for owners and CDOs
  - an in-browser checker for stewards
  - reference pages for architects and policy teams

**Success measures added:**
- Every number on the portal comes from the latest run. Hand-copied figures in portal pages: 0.
- An asset can be added by a steward with one line in the portfolio file.
- Time from an issue going overdue to a ticket existing: one pipeline run (at most a week).

## Scope update: v1.0.0 (15 October 2026)
**Mission:** a free, open, shared place where anyone working with public sector data can check it, improve it, learn how, and help each other, so public services and decisions rest on data people can trust.
**Users added:** local authorities, devolved governments, NHS and care, policing and justice, education, voluntary sector, suppliers, researchers; roles include statisticians, AI and data science teams and service owners.
**Must (added):** general scope beyond NDL and DAM; framework registry, crosswalks and packs; clause-by-clause comparison with devolved and international equivalents; learning pathway; maturity self-assessment; guided tours and user guide; surveys and commissions any organisation can use; moderated member contributions; wishlist; GitHub, Jira and Confluence linkage; AI-for-DQ guidance; AI assistant with deterministic validation; WCAG 2.2 AA.
**Should:** Welsh version; outlier and linkage checks; Fabric connector.
**Success measures added:** organisations using the Commons by type and nation (opt-in); share of contributions from outside central government; accessibility issues open and their age; AI components evaluated and recorded under ATRS.

## Scope update: v1.1.0 (15 October 2026)
**Must (added):** suppliers carry explicit, measurable responsibility for data quality (clauses, KPIs, tender questions, exit); data quality in legacy modernisation (data debt, gates, reconciliation, MoSCoW); interoperability layers, guardrails and measures; data contracts in open standards; a front page with news, insights and a spotlight; a curated library, knowledge base and media centre with moderated community publishing; an accessibility statement and privacy notice.
**Should:** benchmarking by sector and nation; xAPI learning records; metadata Rosetta.
**Success measures added:** share of supplier contracts with a published data quality KPI; data contract coverage of interfaces; share of migrations with a passed reconciliation; contributions published per month by sector and nation.

## v1.2 additions (2026-10-15)

- **Metadata Weaver and contract change check** (Do). User need: "As a publisher, I need to describe a dataset once and publish it in every catalogue, so that I don't retype records and miss fields."
- **UK and the world** (Scenarios). User need: "As a statistics office in a Crown Dependency or Overseas Territory, I need tools and frameworks that respect my own laws, so I can improve data quality without UK-specific assumptions."
- **Help us build this** (Community). User need: "As a member, I need to see and influence what's planned, and contact the team without sharing personal data."
- **Self-checking content.** User need: "As a reader, I need to trust that what I read is current and checked."
- Success measures: share of records with full CDA coverage after weaving; backlog items picked up by contributors; content health errors at zero on main.

## v1.3 additions (2026-10-15)

- **Knowledge map.** User need: "As a new data steward, I need to understand the terms and how frameworks, rules and evidence connect, so I can apply them with confidence."
- **Events and training.** User need: "As a manager, I need to find affordable, accessible training and events that match my team's gaps."
- **What's new.** User need: "As a returning user, I need to see what changed since my last visit."
- **Build bundle.** User need: "As an assurer or reviewer, I need every design and delivery document for a version in one place."

## v1.4 additions (2026-10-30)
- **Playbook (must):** a data quality management playbook for critical data assets under the DAM policy, usable under any mandate: stages, checklists, RACI, templates, escalation, measures, inclusion checks and a jurisdiction finder. Success: a steward can run the first cycle on one asset using only the playbook and toolkit.
- **Verification (must):** every listed source read at source, with the date shown. Success: content health reports 100% read in full.
- **Horizon scan (should):** a dated scan of new guidance, standards and news each release.

## v1.6 additions (2026-10-30)
- **Role-based entry (must):** each stakeholder role sees its needs, decisions, risks, measures and routes. Success: a CDO or data owner reaches their next action in two clicks.
- **CDO Council brief:** withdrawn from the public product in 2.0.0 and held privately (D-POL-02).
- **Gap register (must):** every known gap with who it affects, severity, status and response.
- **Q-FAIR (should):** ratings in the CDA return and a self-rating, aligned to the Geospatial Commission scale.

## v2.10 and v2.11 additions (2026-11-05)
- **Standards and join-up (2.10):** a catalogue of open standards with GOV.UK status; DQV output from the Metadata Weaver; Three portals, one journey with the DAM capability playbooks and the GitHub repos asset catalogue.
- **User research with prospective consumers (2.11):** an introduction for teams, a research panel and an emailable research bundle. Success: two research rounds by March 2027 with every quota met, findings published and linked to backlog changes.
- **Open roadmap (2.11):** published scores, objectives, capacity and alignment with government strategy (the Roadmap for modern digital government; the strategic roadmap for public sector data once published). Success: every open item scored and traceable; challenges answered within 10 working days.
