# Decision log (this repository)

Newest first. These continue the portal decision log (D-001 to D-014) in the claude.ai project.

## 2026-10-14 · D-024 · A filled-in DQAP workbook, with a history of each run
- **Decision:** `--workbook` writes a filled-in Excel DQAP with 10 tabs, using the tab structure of the Implementation Guide v2.0 and the Defra "Start here" annexes. `--history` keeps every run, so the Results tab shows trends, as Defra's monitoring template does. Cells for stewards to complete are grey.
- **Why:** stewards already work in these templates. Producing them directly removes copying and re-keying.
- **Alternative considered:** CSV only. Kept as well, but it is less usable for owners.

## 2026-10-14 · D-023 · DQAP route from the 2023 decision tree
- **Decision:** the `source` and `influence` asset fields choose a route: internal (fix at source), external with influence (work with the supplier), or external without influence (measure, caveat and communicate). The NDL charts use the external route without influence.
- **Why:** the GOV.UK DQAP steps assume you own the data. Critical data assets are shared, and the NDL republishes others' data.

## 2026-10-14 · D-022 · Suggest an IOPC-style trust level for every assessed asset
- **Decision:** `trust.py` suggests Untrustworthy, Requires improvement, Useable or Trustworthy from the worst open priority. It applies IOPC's personal data accuracy rule (below 90% can't be Trustworthy; below 100% needs an action plan). It caps the level at Useable when fewer than 3 core dimensions are measured. The level is a suggestion that the owner confirms, because IOPC uses no fixed formula. A `trust_level` field is added to the metadata model.
- **Why:** no GOV.UK source links quality to how data may be shared (crosswalk F6).

## 2026-10-14 · D-021 · Default targets at the low end of each framework range (replaces D-016)
- **Decision:** the default target policy is "low": 75, 90, 97.5 and 99.9. "mid" (the old defaults 85, 95, 99, 100) and "high" can be chosen per asset.
- **Why:** Issues Framework v1.0 builds its own band tables on the low end of each range. Defra sets thresholds by business need (for example 75% for descriptive fields). The owner still confirms each target.
- **Effect on the NDL assessment:**
  - "Geography stated" goes from High to Low priority.
  - "No factual errors" now meets its target. The one error is still reported.
  - No other results change.

## 2026-10-14 · D-019 · Treat NDL page checks as rules measured across the portfolio
- **Decision:** each of the 20 checks is scored as one data quality rule across all 84 pages, using the issues framework, with importance 3.
- **Why:** this uses the government's own prioritisation method rather than an invented one, and it ranks fixes that can be made once in the page template.
- **Alternative considered:** a bespoke weighted scorecard. Rejected because it isn't comparable with DQAP outputs.

## 2026-10-14 · D-018 · Assess what the NDL page shows, not the source publisher's page
- **Decision:** checks use only what is on the data.gov.uk page.
- **Why:** the NDL is the front door. Users decide there. Methodology on a publisher site one click away isn't visible at the point of choice.
- **Known effect:** this lowers the methodology and caveats scores. The report says so.

## 2026-10-14 · D-017 · Add "representativeness" as a seventh dimension
- **Decision:** add representativeness, an inclusion extension, alongside the six DAMA UK dimensions, plus a "metadata" dimension for catalogue checks.
- **Why:** overall completeness can hide groups of people who are missing or misrecorded. The research found only 2 of 21 public DQ repos test for this.
- **Alternative considered:** fold it into completeness. Rejected because that hides the result.

## 2026-10-14 · D-016 · Default targets inside each framework range: 85, 95, 99, 100 (superseded by D-021)
- **Decision:** when a rule has no target, use these defaults. The framework gives ranges and leaves the choice to the owner. Its own example uses 95 for combined score 4.
- **Why:** this keeps scoring predictable. Owners can override per rule.

## 2026-10-14 · D-015 · Pure Python with pandas, plus exporters, instead of depending on Great Expectations
- **Decision:** the kit runs its own engine and exports to Great Expectations and R validate.
- **Why:**
  - Departments use different tools.
  - Fewer dependencies make it easier to approve on government laptops.
  - One rules file serves Python and R users.
- **Alternative considered:** a Great Expectations-only kit. Rejected because it locks out R users and makes the setup heavier.

## 2026-10-14 · D-014 · Use W3C DQV to carry CDA quality results in metadata (proposed)
- **Decision:** see the project decision log. Implemented here as `model/cda-quality.linkml.yaml` with JSON Schema and SHACL.
- **Status:** a proposal to GDS metadata owners has been drafted but not sent.
