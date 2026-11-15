# Theory of change

**Long-term outcome:** People and services can rely on government data because its quality is known,
published and improving. Gaps that affect particular groups are visible and fixed.

| Inputs | Activities | Outputs | Short-term outcomes (first year) | Medium-term outcomes (years 2 to 3) | Impact |
|---|---|---|---|---|---|
| GOV.UK DAM policy and DQAP guidance; public sector DQ code (27 repos reviewed); NDL collections | Build open kit, vocabulary and metadata extension; assess the NDL; share with departments | dqkit; 43 issue types; DQV extension; NDL assessment; effort model | Departments submit comparable baselines; NDL fixes its page template; shared issue language | Quality shown on every NDL and CDA record; issues tracked to closure; inclusion checks routine | Better decisions and services; less duplicated effort; fewer people excluded by poor data |

**Assumptions** (to test):
1. Departments will adopt a free shared kit rather than build their own. Risk: tool habits and procurement.
2. GDS will accept DQV fields in the metadata model.
3. Data owners will act on priorities that the framework produces.
4. Publishing quality openly builds trust rather than discouraging use.

**Risks:**
1. Low capacity before January. Mitigation: proportionate baseline.
2. Inclusion checks need protected-characteristic data that some assets don't hold. Mitigation: report "not assessable" honestly.
3. Overconfidence in automated scores. Mitigation: every result shows its evidence and source.

## Update for v1.0.0 (15 October 2026)
- **Inputs (added):** a shared knowledge base, framework packs (12 at v1.0, 14 at v1.2), rule library, community store, AI assistant, operating model.
- **Activities:** organisations check data, assess maturity, learn by role, contribute and ask for help; requests flow into an open backlog.
- **Outputs:** baselines for critical assets in any sector; translated results across frameworks; moderated case studies; survey totals.
- **Outcomes:** common language and methods across sectors and nations; fewer duplicated tools; inclusion checks routine for personal data; AI used with evaluation and transparency.
- **Impact:** public services and decisions rest on data people can trust, including for groups data often leaves out.
- **Assumptions to test:** non-central organisations will use a hub that started in central government (XDMH-212); moderation capacity matches demand (XDMH-217).

## Sustainable Development Goals

The Commons supports the UN Sustainable Development Goals through the quality of the data public services rely on.

**Main target: 17.18.** Target 17.18 asks for capacity-building support "to increase significantly the availability of
high-quality, timely and reliable data disaggregated by income, gender, age, race, ethnicity, migratory status,
disability, geographic location and other characteristics relevant in national contexts". The Commons contributes
through features that exist in this repository:
- **Disaggregation tested, not assumed.** The `not_unknown` check measures how often a characteristic such as
  ethnicity is missing or defaulted, and `group_disparity` tests whether quality is equal across groups rather than
  only overall (the representativeness dimension).
- **Shared quality frameworks for statistics offices.** Packs map results to the UN National Quality Assurance
  Framework (`packs/un-nqaf.yaml`), the IMF Data Quality Assessment Framework (`packs/imf-dqaf.yaml`) and ISO 8000
  (`packs/iso-8000-8.yaml`), so offices of any size, including Crown Dependencies, Overseas Territories and
  Commonwealth partners, can use the same free kit.
- **Quality published openly.** Results are written as W3C Data Quality Vocabulary (DQV) metadata
  (`dqkit/dqv.py`), ready for a catalogue, so users can see how reliable data is before they use it.

**Secondary target: 16.6** ("Develop effective, accountable and transparent institutions at all levels"). Every issue
the kit finds is logged with a priority, a resolution timescale, a responsibility and a named owner (the DQAP issues
log, `*.dqap-issues.csv`), so accountability for fixing data is visible and can be tracked to closure.

**Limits, stated honestly:**
- Target 17.18 is framed around capacity-building support to developing countries, least developed countries and
  small island developing states. The Commons is UK-first: it was built for UK public bodies, and its international
  packs are an offer, not evidence of use in those countries. It has not been tested with any developing-country
  statistics office.
- The link to 16.6 is to the target, not to its official indicators. Indicator 16.6.1 measures primary government
  expenditures against the approved budget, and 16.6.2 the proportion of the population satisfied with their last
  experience of public services. The Commons measures neither.
- No SDG outcome has been measured. These are intended contributions, to be tested like the assumptions above.

Sources: target and indicator wording from the UN SDG indicator framework, as published by national SDG reporting
platforms (for example sdg.data.gov and the National Statistics Office Malta), checked 15 November 2026.
