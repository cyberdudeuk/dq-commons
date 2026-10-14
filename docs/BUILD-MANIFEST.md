# Build manifest — v0.3.0 (2026-10-14)

| Path | Purpose | Generated? |
|---|---|---|
| dqkit/framework.py | GOV.UK issues framework | No |
| dqkit/rules.py | Rules engine (15 checks) | No |
| dqkit/metadata.py | Catalogue record assessment (20 checks, 13 CDA properties) | No |
| dqkit/dqv.py | DQV JSON-LD writer | No |
| dqkit/exporters.py | GX, R validate, DQAP CSV | No |
| dqkit/cli.py, `__main__.py` | Command line | No |
| dqkit/trust.py | IOPC-style trust level | No |
| dqkit/pathway.py | Decision-tree DQAP route | No |
| dqkit/workbook.py | Filled-in DQAP workbook (11 tabs) and run history | No |
| dqkit/operations.py | Issue ageing, overdue escalation, recurrence | No |
| dqkit/casestudy.py | Draft case study in the GDS template | No |
| dqkit/survey.py | DQ tooling survey analysis (personal data removed) | No |
| docs/SURVEY-REVIEW.md | Pre-launch review of the survey | No |
| assessments/ndl/results/case-studies/*.md | Draft case studies for 8 NDL charts | Yes |
| examples/illustrative-escalation/ | Illustrative 3-cycle history showing escalation | Yes |
| docs/GUIDANCE-CROSSWALK.md | Comparison of 15 guidance sources, 18 findings | No |
| assessments/ndl/results/dqap-workbooks/*.xlsx | DQAP workbooks for 8 NDL charts | Yes |
| vocab/dimensions.csv, issue-types.csv | Vocabulary source | No |
| vocab/dq-vocab.ttl, dq-vocab.jsonld | SKOS / JSON-LD | Yes (scripts/build_vocab.py) |
| model/cda-quality.linkml.yaml | Metadata extension proposal | No |
| model/cda-quality.schema.json, .shacl.ttl | Schema and shapes | Hand-written (regenerate with LinkML) |
| rules/ndl/*.yaml | 8 rule files, 49 rules | No |
| assessments/ndl/harvest.jsonl | 84 NDL page records (14 Oct 2026) | Harvested |
| assessments/ndl/chart-data/*.csv | 8 NDL chart files (plus 1 sample) | Harvested |
| assessments/ndl/results/* | Results, DQV, DQAP CSVs, GX suites, R rules, summary | Yes (scripts/run_ndl_assessment.py) |
| assessments/ndl/REPORT.md | Findings | No |
| tests/test_dqkit.py | 34 tests | No |
| .github/workflows/ci.yml | CI | No |
| docs/* | Product, architecture, delivery and outreach documents | No |

Runtime dependencies: pandas ≥ 2.0, PyYAML ≥ 6.0, jsonschema ≥ 4.0, openpyxl ≥ 3.1. Python ≥ 3.10.
