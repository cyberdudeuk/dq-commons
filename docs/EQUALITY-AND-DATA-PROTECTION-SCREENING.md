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
- **Case study drafts:** responder fields are left blank (D-027).
- **Small numbers:** summaries warn that counts under 5 can identify an organisation.

**Findings passed to GDS:**

## Update for v0.4.0 (15 October 2026)

**Browser checker:**
- Files are read in the viewer's browser and are never uploaded or stored. There is no server.
- That makes it suitable for trying the kit on sensitive extracts, subject to local rules on where such data may be opened.

**Pipeline:**
- GitHub issues raised for escalations contain rule results. They can also contain up to 3 failing example rows.
- Example rows are left out automatically for any asset that lists `personal_data_columns`.
- Set `notify: {include_examples: false}` in the portfolio file to leave them out for every asset.
- Keep the repository private if the data or its rule results are sensitive.

**Portal accessibility:**
- The portal has a skip link, visible focus, a keyboard-operable menu, labelled form controls, light and dark themes, and reduced motion.
- Charts and bars have text alternatives.
- It has not yet been tested with assistive technology users. That testing is in the research plan.

## Update for v1.0.0 (15 October 2026)
**Data protection**
- New processing: survey answers, contributions, wishlist votes and commission requests in the artifact's store. Linked to an opaque user id only; no names or emails are asked for. Optional contact in commissions only, deleted within 12 months. Editors alone read answers and queues.
- Survey totals published only with counts under 5 hidden; free text never published without moderation.
- Forms block obvious personal data (emails, phone, NI and NHS-number patterns) before saving.
- AI assistant: only messages and column names reach the model; example values only with explicit consent; messages with personal data patterns are blocked. DPIA screening: no high-risk processing identified; a full DPIA is required before the assistant is used with live personal data (XDMH-214).
**Equality**
- Positive: free, no install, no coding; works with keyboard, screen readers and 400% zoom; devolved nations and the voluntary sector have their own scenarios; inclusion checks and an inclusion survey.
- Risks: English only (Welsh version XDMH-216); a free GitHub account is needed to contribute, vote or answer surveys, and GitHub shows who submitted (mitigations: a colleague can submit for a team; free text is never sent to GitHub; totals hide counts under 5; everything else needs no account). The rules assistant uses fixed patterns, not AI, so it treats every context the same way, but it only recognises the phrasings it knows; unrecognised sentences are listed, never guessed.
- Not yet done: independent WCAG 2.2 AA audit (XDMH-213).

## Update for v1.1.0 (15 October 2026)
**Data protection:** new processing is limited to opt-in maturity sharing (organisation type, nation and levels, under an anonymous id) and media submissions (moderated). Reconciliation, profiling and contract conversion run in the browser only. No tracking or analytics.
**Equality:** the clause library requires suppliers' systems to record people accurately (C10) and report quality across groups (C11); media must have captions or transcripts; the carousel can be paused and is static with reduced motion. Remaining gaps: English only; claude.ai or GitHub sign-in needed to contribute.
