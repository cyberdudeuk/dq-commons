# Build manifest — v0.1.0 (2026-10-14)

| Path | Purpose | Generated? |
|---|---|---|
| dqkit/framework.py | GOV.UK issues framework | No |
| dqkit/rules.py | Rules engine (15 checks) | No |
| dqkit/metadata.py | Catalogue record assessment (20 checks, 13 CDA properties) | No |
| dqkit/dqv.py | DQV JSON-LD writer | No |
| dqkit/exporters.py | GX, R validate, DQAP CSV | No |
| dqkit/cli.py, `__main__.py` | Command line | No |
| vocab/dimensions.csv, issue-types.csv | Vocabulary source | No |
| vocab/dq-vocab.ttl, dq-vocab.jsonld | SKOS / JSON-LD | Yes (scripts/build_vocab.py) |
| model/cda-quality.linkml.yaml | Metadata extension proposal | No |
| model/cda-quality.schema.json, .shacl.ttl | Schema and shapes | Hand-written (regenerate with LinkML) |
| rules/ndl/*.yaml | 8 rule files, 49 rules | No |
| assessments/ndl/harvest.jsonl | 84 NDL page records (14 Oct 2026) | Harvested |
| assessments/ndl/chart-data/*.csv | 8 NDL chart files (plus 1 sample) | Harvested |
| assessments/ndl/results/* | Results, DQV, DQAP CSVs, GX suites, R rules, summary | Yes (scripts/run_ndl_assessment.py) |
| assessments/ndl/REPORT.md | Findings | No |
| tests/test_dqkit.py | 21 tests | No |
| .github/workflows/ci.yml | CI | No |
| docs/* | Product, architecture, delivery and outreach documents | No |

Runtime dependencies: pandas ≥ 2.0, PyYAML ≥ 6.0, jsonschema ≥ 4.0. Python ≥ 3.10.
