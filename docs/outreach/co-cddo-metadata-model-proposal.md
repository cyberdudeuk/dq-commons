**Title:** Proposal: add data quality properties (W3C DQV) so critical data assets can carry their DQAP and baseline

**Body:**

The data asset management policy (May 2026) requires a data quality action plan (DQAP), or equivalent,
for every critical data asset. Departments will report quality baselines from January 2027.

The model has no properties for quality today. A search of `src/model/` finds "quality" only in
organisation names. That means quality results can't travel with an asset's metadata.

**Proposal.** Add an optional mixin to DataSet and DataService, using W3C DQV, which is designed to sit
alongside DCAT:

- `data_quality_action_plan` (URI)
- `dqap_status` (none, in_progress, in_place, equivalent)
- `quality_assessment_date`
- `quality_measurements` (dqv:QualityMeasurement: dimension, value %, target, measured date)
- `quality_issues` (dqv:QualityAnnotation: issue type, priority from the GOV.UK issues framework, resolution timescale)
- `inclusion_assessed` (boolean)

A worked LinkML draft, JSON Schema, SHACL shapes and an example are available in the
ndl-dq-assurance repository (model/), with a 43-term issue vocabulary (vocab/). Both are MIT/OGL.

**Questions for maintainers:**
1. Mixin, or a separate QualityStatement class?
2. Should the dimension list be the six DAMA UK dimensions only, or include representativeness?
3. Should issue types be a controlled vocabulary hosted by GDS?

Happy to open a pull request once the approach is agreed.
