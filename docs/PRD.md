# Product requirements: NDL data quality assurance kit

## Problem
Departments must report a data quality baseline for every critical data asset (CDA) in the January 2027
return. The GOV.UK DAM policy also requires a DQAP or equivalent for each asset. But:
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
