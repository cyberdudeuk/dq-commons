# Build manifest — v0.4.0 (2026-10-15)

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
| tests/ | 60 tests: kit, pipeline, portal build, JavaScript parity | No |
| dqkit/portfolio.py, portfolio.schema.json | Portfolio runner and its file format | No |
| dqkit/profile.py | Starter rules from a data file (`dqkit suggest`) | No |
| dqkit/cdareturn.py | CDA return rows (proposed Dataverse columns) | No |
| portfolio.ndl.yaml | The NDL portfolio: 8 assets and the page metadata | No |
| assessments/portfolio/* | Latest pipeline run: portfolio.json, run summary, escalations, DQV catalogue, CDA return, per-asset files, history | Yes (`dqkit run`) |
| portal/src/ | Portal templates, shell, base CSS, browser engine | No |
| scripts/build_dq_portal.py | Builds the portal into portal/dist/ | No |
| portal/dist/ | The built portal (not committed) | Yes |
| scripts/parity_check.py, .mjs | Python–JavaScript parity check (30 cases) | No |
| .github/workflows/dq-pipeline.yml | Weekly pipeline | No |
| docs/OPERATIONS.md | Pipeline runbook | No |
| pyproject.toml | Packaging (`pip install -e .`) | No |
| .github/workflows/ci.yml | CI | No |
| docs/* | Product, architecture, delivery and outreach documents | No |

Runtime dependencies: pandas ≥ 2.0, PyYAML ≥ 6.0, jsonschema ≥ 4.0, openpyxl ≥ 3.1. Python ≥ 3.10.

## v1.0.0 (15 October 2026)
| Component | Path |
|---|---|
| Portal pages (19) | `portal/src/pages/*.html` |
| Shell, tour engine, base styles | `portal/src/shell.html`, `portal/src/base.css` |
| Knowledge base | `knowledge/` |
| Packs (12) | `packs/` |
| Rule library | `rules/library/` |
| Value sets | `vocab/valuesets/` |
| MCP server | `dqkit/mcp_server.py` |
| Data sources | `dqkit/sources.py` |
| Integrations | `integrations/config.yaml`, `scripts/sync_backlog.py`, `scripts/publish_confluence.py`, `.github/workflows/backlog-sync.yml`, `.github/workflows/docs-to-confluence.yml` |
| Community templates | `.github/ISSUE_TEMPLATE/`, `.github/PULL_REQUEST_TEMPLATE.md`, `CONTRIBUTING.md`, `SECURITY.md` |
| Operating model, user guide | `docs/OPERATING-MODEL.md`, `docs/USER-GUIDE.md` |
| AI evaluation | `knowledge/ai-eval/`, `scripts/eval_rule_drafting.py` |

## v1.1.0 (15 October 2026)
| Component | Path |
|---|---|
| Data contracts | `dqkit/contracts.py`, `DQ.contracts` in `portal/src/js/engine.js` |
| Reconciliation | `dqkit/reconcile.py`, `DQ.reconcile` |
| Spreadsheet reader | `portal/src/js/sheets.js` |
| New pages (6) | `commercial`, `legacy`, `interop`, `library`, `media`, `accessibility` |
| New knowledge | `knowledge/{commercial,legacy,interop,rosetta,articles,media}.yaml` |
| Link checker | `scripts/check_links.py`, `.github/workflows/link-check.yml` |
| MCP manifest | `scripts/mcp_manifest.py`, `integrations/ndl-mcp-domain.json` |

## v1.2.0 additions

| Path | What |
|---|---|
| `dqkit/weaver.py` | Metadata Weaver |
| `knowledge/global.yaml`, `knowledge/build.yaml` | Scope extension; roadmap, backlog, charter, routines |
| `portal/src/pages/weaver.html`, `global.html`, `build.html` | New pages (28 in total) |
| `portal/src/icons.svg` | Icon sprite |
| `scripts/self_check.py`, `scripts/backlog_to_issues.py`, `scripts/gen_community_docs.py` | Self-checks, backlog issues, community docs |
| `.github/workflows/content-health.yml`, `backlog-issues.yml` | New workflows |
| `CHARTER.md`, `CODE_OF_CONDUCT.md`, `CONTRIBUTORS.md`, `.all-contributorsrc` | Community docs |
| `docs/METADATA-WEAVER.md`, `docs/ASSURANCE-ROUTINES.md` | Assessment and routines |
