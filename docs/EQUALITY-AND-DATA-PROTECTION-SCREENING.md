# Equality and data protection screening

## Data protection (DPIA screening)
- **Personal data processed by this repository:** none.
  - The NDL harvest holds page metadata only, with organisation names.
  - Chart data is aggregate statistics.
  - The kit itself runs where the data lives and stores nothing centrally.
- **When departments use the kit on personal data:**
  - Failing-row examples (up to 5 values per rule) may contain personal data.
  - Keep results inside the department, or share only the DQV and DQAP outputs, which hold rates, not records.
  - The department's existing DPIA for the asset covers this processing.
- **Conclusion:** a full DPIA is not needed for this repository. Review this if a hosted service is built.

## Equality (public sector equality duty, Equality Act 2010 s.149)

**Who could be affected:**
- people under-recorded in data, such as some ethnic groups, disabled people, people with no fixed address and digitally excluded people
- users of assistive technology
- people in the devolved nations

**Positive measures built in:**
- **Representativeness dimension and 4 inclusion issue types.** Covers characteristic missing or defaulted, group disparity and undercoverage.
- **`not_unknown` and `group_disparity` checks.** These test whether quality is equal across groups, not only overall.
- **NDL checks INC-1 (breakdowns stated) and INC-2 (other nations signposted).** FAIR-1 also flags data that isn't machine-readable, because it is harder for assistive technology users.

**Risks and mitigations:**
- **Risk:** inclusion checks need protected-characteristic fields, and collecting more such data has its own risks.
  **Mitigation:** the kit measures what exists. It doesn't require new collection. GSS harmonised standards are recommended where data is collected.
- **Risk:** scores may be read as judgements about groups of people.
  **Mitigation:** results describe data quality only. Reports use neutral language.

**Accessibility of outputs:**
- Plain-English summaries.
- HTML artefacts built to WCAG 2.2 AA intent (contrast, keyboard focus, reduced motion).
- Not yet tested with assistive technology users. That testing is in the research plan.

## Update for v0.3.0 (14 October 2026)

**Survey analysis and case studies:**
- **Survey analysis:** `dqkit survey` drops name, role and email on load and never writes them out (D-028).
- **Case study drafts:** responder fields are left blank (D-027).
- **Small numbers:** summaries warn that counts under 5 can identify an organisation.

**Findings passed to GDS:**
- **Privacy notice:** the survey and case study template collect personal data without one (F12).
- **Accessibility in tool choice:** the tooling review has no criterion for staff who use assistive technology (F11).
- **Members-only library:** the Shared Learning Library is in a members-only space. That excludes local government, devolved administrations and the third sector without accounts (F17).
