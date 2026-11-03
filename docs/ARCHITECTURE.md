# Architecture: solution, high-level and low-level design

## 1. Solution architecture (SAD)

### Context
```mermaid
flowchart LR
  subgraph Dept[Department or ALB, where the data lives]
    D[(Critical data asset)] --> K[dqkit rules engine]
    R[Rules file YAML] --> K
    K --> O1[DQAP template rows]
    K --> O2[DQV JSON-LD]
    K --> O3[GX suite / R validate rules]
  end
  O2 --> C[Departmental catalogue / Purview]
  C --> RET[Annual CDA return to GDS]
  RET --> NDL[National Data Library catalogue]
  H[NDL page metadata] --> M[dqkit metadata assessment] --> NDL
  NDL --> U[Data users]
  V[Shared vocabulary: dimensions + 43 issue types] -.-> K
  V -.-> M
```

### Principles
1. **Data stays with its owner.** The kit runs locally. Only results and metadata move.
2. **One rules file, many outputs.** Steward effort is spent once. Exporters serve other tools.
3. **Standards first:** DCAT, DQV, SKOS, LinkML, JSON Schema, SHACL, ISO 8601, and the GOV.UK issues framework.
4. **Explainable.** Every score carries its evidence, rule and source requirement.
5. **Inclusion by design.** Representativeness is a first-class dimension.

### Fit with the target platform
The recommended production stack (Dataverse, then Fabric, then Purview) can consume DQV JSON-LD as
custom metadata, or map it to Purview data quality rules. The departmental return workspace's Dataverse
table can take the extension's fields as columns (see the LLD mapping).

## 2. High-level design (HLD)

| Component | Responsibility | Interfaces |
|---|---|---|
| `framework.py` | GOV.UK issues framework: targets, bands, priority, resolution | `assess(importance, impact, performance, target)` |
| `rules.py` | Load and validate rule files; run 15 check types on a DataFrame; summarise | `load_rules`, `run(df, spec, as_of)` |
| `metadata.py` | 20 requirement checks on catalogue records; 13 CDA properties; portfolio scoring | `assess_record`, `assess_portfolio` |
| `dqv.py` | Results to W3C DQV JSON-LD | `result_to_dqv` |
| `exporters.py` | Great Expectations, R validate, DQAP CSVs | `to_great_expectations`, `to_r_validate`, `to_dqap_csv` |
| `cli.py` | Plain command line | `check` (with `--workbook`, `--history`), `export`, `assess-metadata`, `run`, `suggest` |
| `portfolio.py` | Run many assets from one portfolio file (`portfolio.schema.json`): per-asset outputs, schedule (due or carried forward), changes since the last run, escalations, merged DQV catalogue, run summary | `run(portfolio_path, as_of, out_dir)`, `validate`, `build_escalations`, `compare` |
| `profile.py` | Profile a data file and draft a starter rules file for a steward to review | `profile(df)`, `suggest(df, asset)`, `to_yaml(spec)` |
| `.github/workflows/dq-pipeline.yml` | Weekly pipeline: tests, `dqkit run`, commit results, GitHub issues per escalation, portal to GitHub Pages | GitHub Actions (schedule, manual run with `as_of`) |
| `portfolio.py`, `cdareturn.py` | Portfolio runner; CDA return rows in the proposed Dataverse columns | `dqkit run`; `cda-return.csv` |
| `portal/src/` and `scripts/build_dq_portal.py` | NDL Data Quality Portal: 8 page templates, shared shell, base CSS; built from the run's results | Static site in `portal/dist/` (GitHub Pages); artifact copy |
| `portal/src/js/engine.js` | Browser port of the kit (checks, scoring, trust, route, ageing, DQV, DQAP CSV) | `DQ.run(table, spec, asOf)`; parity-checked against Python (`scripts/parity_check.py`) |
| `trust.py` | IOPC-style trust level, with reasons | `classify(result)` |
| `pathway.py` | DQAP route from the 2023 decision tree | `route(asset)` |
| `workbook.py` | Filled-in DQAP workbook (11 tabs) and run history | `build`, `append_history` |
| `operations.py` | Issue ageing, overdue escalation (issues framework timescales), recurrence | `assess(result, history_dir)` |
| `casestudy.py` | Draft case study from results | `draft`, `to_markdown`, `to_docx` |
| `vocab/` | Dimensions and issue types (CSV source; SKOS and JSON-LD generated) | `scripts/build_vocab.py` |
| `model/` | Proposed metadata extension (LinkML, JSON Schema, SHACL) | For GDS metadata model owners |

## 3. Low-level design (LLD)

### Scoring flow for one rule
1. Pass rate = records passing ÷ records checked × 100.
2. Combined score = asset importance (1–4) × rule impact (1–4). The impact defaults from the issue type.
3. Target = the rule's own target, or the default for the framework range: 85, 95, 99 or 100.
4. If below target, find the band:
   - Middle band starts at 100 − 2 × (100 − target).
   - High band starts halfway between the middle-band start and the target.
   - Score: Low 3, Middle 2, High 1, and 4 when the target is 100.
5. Priority score = importance × impact × band score:
   - 1–7 Low
   - 8–16 Medium
   - 17–32 High
   - 33–64 Critical
6. Resolution comes from Table 8.

### Control points and escalation
- Each rule has a `control_point`: source (capture), pipeline, or reporting. It defaults by check type.
- An issue's age is the number of consecutive measurement cycles below target, read from the history.
- An issue is overdue when its age exceeds its priority's window: Critical 1, High 1, Medium 3, Low 6 (D-026).

### Dataset-level checks
`freshness`, `sum_max` and `group_disparity` give one pass or fail (checked = 1). `freshness` treats a year
label as covering the whole year. It passes when (as_of − end of the latest period) ≤ expected frequency + lag.

### Reading numbers and outliers
Numbers are read by `dqkit/numbers.py` (mirrored by `pdNumber` in `engine.js`), not by pandas, so results do not
change with the pandas version (D-TK-02). `outlier` counts only cells that are numbers; blanks and text are left to
`not_null` and `type`. With `method: iqr` a value fails outside Q1 − k·IQR to Q3 + k·IQR (numpy's linear quantile,
written out in both engines); with `method: zscore` it fails more than `threshold` sample standard deviations from
the mean. Fewer than 4 numbers: nothing to compare, so every value passes.

### Mapping to the Dataverse return table (proposed new columns)

| Extension slot | Dataverse column | Type |
|---|---|---|
| dqap_status | `gds_dqapstatus` | Choice: none, in_progress, in_place, equivalent |
| data_quality_action_plan | `gds_dqapurl` | URL |
| quality_assessment_date | `gds_dqbaselinedate` | Date |
| quality_measurements (per dimension, mean) | `gds_dq_completeness` … `gds_dq_accuracy` | Decimal (0–100) |
| quality_issues (counts by priority) | `gds_dqissues_critical`, `_high`, `_medium`, `_low` | Whole number |
| inclusion_assessed | `gds_dqinclusionassessed` | Yes/No |

### Operations

The kit runs as a scheduled pipeline (runbook: [`OPERATIONS.md`](OPERATIONS.md)).

```mermaid
flowchart LR
  P[portfolio.ndl.yaml] --> R[dqkit run]
  H[(history CSVs)] <--> R
  R --> PJ[portfolio.json] --> PORTAL[Web portal on GitHub Pages]
  R --> ES[escalations.json] --> GI[GitHub issues, label dq-escalation]
  R --> CAT[catalogue.dqv.jsonld] --> C[Catalogue]
  R --> RS[run-summary.md]
```

- **Portfolio file**: one YAML file lists each asset's rules and data files, with an optional
  schedule and tags. It is checked against `dqkit/portfolio.schema.json` (JSON Schema 2020-12).
- **Determinism**: results depend only on the data, the rules and `--as-of`. `run_at` is the only
  clock value (fixed by `SOURCE_DATE_EPOCH` if set). `fingerprint` hashes what was measured, so the
  pipeline commits only when results change.
- **History**: one CSV per asset. Re-running a date replaces that date's rows (no double counting of cycles).
- **Schedule**: an asset that is not due is carried forward from the last run, without adding a cycle.
- **Changes**: `new`, `resolved` and `still_open` issues compare this run's `portfolio.json` with the previous one in the same folder.
- **Escalation**: priorities in `notify.escalate_priorities` (default Critical, High) that are overdue
  under the issues framework windows (D-026). Who acts comes from the DQAP route.
- **Merged catalogue**: DQV graphs are merged by `@id`. A chart file and its NDL page share an IRI, so
  their measurements sit on one `dcat:Dataset` node.

### Security and privacy
- The kit reads files locally and makes no network calls.
- Failing examples include up to 5 row values. For personal data, set the rule's columns carefully or strip
  `examples` before sharing results. The recommendation is to share only `dqv.jsonld` and the DQAP CSVs.

## 4. v1.0.0 additions (15 October 2026)
- **Knowledge layer:** `knowledge/*.yaml|csv` is the single source for frameworks, clauses, communities, learning, maturity, surveys and AI guidance. The portal build injects it as `__K_NAME__` placeholders; the MCP server and assistant read the same data.
- **Portal:** 19 static pages from `portal/src/pages`, shared shell (grouped navigation, guided-tour engine), parity-checked browser engine.
- **Runtime services (claude.ai artifact):** `db` with 9 access rules (library, wishlist, results readable by all, written by editors; per-member `queue/{self}`, `responses/{self}`, `votes/{self}`); `user` (opaque id only, no names); `sample` for the assistant. On GitHub Pages these resolve to null and the pages fall back to GitHub issue forms.
- **Integration:** GitHub (source of truth) to Jira (`backlog-sync.yml`, `scripts/sync_backlog.py`) and Confluence (`docs-to-confluence.yml`, `scripts/publish_confluence.py`); configuration in `integrations/config.yaml`; secrets only in repository secrets.
- **Agent interface:** `dqkit/mcp_server.py` (stdio JSON-RPC, read-only, root-restricted).

## 5. v1.1.0 additions (15 October 2026)
- **Toolkit:** `dqkit/contracts.py` (ODCS, Table Schema, CSVW), `dqkit/reconcile.py`; both mirrored in `portal/src/js/engine.js` and parity-checked with the exporters.
- **Browser file reading:** `portal/src/js/sheets.js` reads xlsx and ods with DecompressionStream and DOMParser; no third-party code.
- **Knowledge layer:** adds `commercial.yaml`, `legacy.yaml`, `interop.yaml`, `rosetta.yaml`, `articles.yaml`, `media.yaml`; every file carries `review: {last_reviewed, owner_role}`.
- **Shared store:** adds a `media` collection (read by all, written by editors); maturity benchmarks are stored per member under `responses/{self}` and published to `results/maturity`.
- **Operations:** `link-check.yml` monthly; `scripts/mcp_manifest.py` generates `integrations/ndl-mcp-domain.json`.

## 6. v1.2.0 design (15 October 2026)

### 6.1 Solution view (SAD)

- **Scope widened:** users now include the Crown Dependencies, Overseas Territories, Commonwealth partners and international bodies. Nothing in the toolkit assumes UK law; frameworks are chosen per jurisdiction through packs (now 14, including `un-nqaf` and `imf-dqaf`).
- **Quality attributes added:** self-assurance (the content health check fails the build on personal data, mismatched claims and overdue reviews), provenance (every page states when its content was last reviewed and by which role), and privacy by default for contact (no email address published or required).
- **Source of truth:** the GitHub repository. Jira (XDMH) and Confluence (ARCHITECTU) are mirrors, updated by workflows or by hand with the sync status recorded in the build log.

### 6.2 High-level design (HLD)

```mermaid
flowchart LR
  subgraph Repo[GitHub repository: source of truth]
    K[knowledge/*.yaml] --> B[scripts/build_dq_portal.py]
    T[dqkit Python toolkit] --> B
    E[portal/src/js/engine.js] --> B
    S[scripts/self_check.py] --> B
    BL[knowledge/build.yaml backlog] --> I[scripts/backlog_to_issues.py]
    BL --> G[scripts/gen_community_docs.py] --> CD[CHARTER.md, CONTRIBUTORS.md]
  end
  B --> P[Portal: 28 static pages]
  P --> GHP[GitHub Pages]
  P --> ART[claude.ai artifact: shared store for votes, queue, contact]
  T --> CLI[CLI: weave, contract-check, run, check]
  T --> MCP[MCP server: weave_metadata, check_contract and 9 more]
  I --> GHI[GitHub issues]
  GHI -- backlog label, not jira-linked --> J[Jira XDMH]
  Repo -- docs-to-confluence --> C[Confluence ARCHITECTU]
  T <-. parity: 37 cases .-> E
```

### 6.3 Low-level design (LLD)

**Metadata Weaver (`dqkit/weaver.py`, `DQ.weaver`).**
1. `detect(record)`: ODCS if `kind: DataContract` or `apiVersion`; DCAT if a `dcat:` type, context or key; schema.org if `@type: Dataset`; CKAN if package keys (also inside an API `result`).
2. `read_<format>` fills a canonical record of 22 fields (`FIELDS`: key, label, Rosetta concept, CDA property, which outputs carry it). Lists are de-duplicated; nothing is inferred.
3. `to_dcat`, `to_schema`, `to_ckan`, `to_odcs` write only filled fields. DCAT uses `dqc:` for security classification and expiry. ODCS needs an id and version, so it uses visible placeholders (`dataset`, `1.0.0`).
4. `coverage()` lists filled, missing and "not carried" fields per output; `cda_check()` scores the 13 CDA properties (description needs 40 characters; distributions need a format) with half credit for partial.

**Contract change control (`dqkit/contracts.py`).**
- `validate_odcs`: errors for missing required fields, wrong kind, unnamed schema objects or properties, repeated property names; warnings for non-v3, unknown status, non-semantic version, no schema, unknown metrics, rules without thresholds, no team, no SLA.
- `diff_odcs`: columns keyed by (object, property). Breaking: removed column, changed type, lost `required` or `unique`, removed quality rule, looser threshold, status moved to deprecated or retired. Suggests major, minor or patch; `version_ok` says whether the stated version is a big enough bump.

**Content health (`scripts/self_check.py`).** Eight checks, each finding an error, warning or note; writes `health.json` and `health.md`; exit 1 on errors (or warnings with `--strict`). The build embeds a summary in Help us build this. The weekly workflow keeps one GitHub issue open while there are findings.

**Contact and moderation.** The sender's message is an item of kind `contact` in their own `queue/{uid}` document (rules: owner read and write, editors read all). Moderators reply in place (`status: answered`, `reply`), which the sender sees on Help us build this. No email field exists.

**Provenance.** At build time each page's `__K_NAME__` placeholders are mapped to knowledge files; the oldest `review.last_reviewed` and the owning roles are printed above the colophon.

**Backlog to issues.** Idempotent: existing issues are matched by `[BL-nn]`. Items with a Jira key get `jira-linked`, which the Jira sync workflow skips.

## 7. v1.3.0 design (15 October 2026)

**Knowledge graph (`dqkit/graph.py`).** Builds nodes (`Type:slug`) and named edges from every knowledge file, the vocabulary CSVs, packs and the Rosetta. Every edge's property is declared in `knowledge/ontology.yaml` with a domain and range (a test enforces this), so the graph is self-describing. Bridging links come only from the data: glossary terms that name a dimension, role or standard are `sameAs` it; lineage stages `involve` the concepts they use; places are `inScope` of the Commons. Result: 460 nodes, about 1,060 edges, one connected component, no dangling links. Exports: JSON for the portal, JSON-LD and Turtle (SKOS concepts, OWL classes and object properties, `owl:sameAs` to the published vocabulary IRIs). Questions: `find`, `neighbours`, `path` (breadth-first, either direction).

**Knowledge map page.** Radial neighbourhood view (SVG, no libraries) with keyboard-focusable nodes and a full relationship list as the accessible equivalent; trail; path finder; glossary A to Z; ISO 25964 thesaurus (SN, UF, BT, NT, RT, USE); data dictionary with an entity relationship diagram; taxonomies as nested disclosures; ontology class diagram; lineage diagrams laid out by longest-path layering; framework-to-evidence traceability.

**Events.** Curated events plus published community events (`events/{id}`, moderated from each member's queue). RFC 5545 calendar files generated in the browser.

**Releases.** `knowledge/releases.yaml` drives the version, the What's new drawer (a non-modal dialog that keeps focus, closes on Escape and remembers the last version seen in local storage) and New or Updated flags in menus.

**Bundle.** `scripts/build_bundle.py` converts the mandated Markdown documents with a small built-in converter into one standalone page; `--check` keeps the committed copy current.

## 8. v1.4.0 design (30 October 2026)

**Playbook.** `knowledge/playbook.yaml` is the single source. The portal build exposes it as `__K_PLAYBOOK__`; the page joins it with `__K_REQUIREMENTS__` (clause text) and `__K_FRAMEWORKS__` (jurisdiction finder) in the browser. `scripts/build_playbook_doc.py` renders the same data as Markdown for the build bundle. The playbook cycle is a lineage flow in `knowledge/ontology.yaml`, so the graph links each stage to the toolkit stages and glossary terms it uses.

**Verification states.** `verified`/`checked` now take `yes`, `partly`, `listed` or `unpublished`; `checked_on` records the date read. The health check counts `yes` and `unpublished` as read in full.

## 9. v1.5.0 design (30 October 2026)

**Playbook in the toolkit.** `dqkit/playbook.py` reads `knowledge/playbook.yaml`. A workspace is a plain folder: six CSV templates named by stage, a README checklist and `playbook-status.yaml` (asset ID, rules file, results folder). `status()` checks evidence per stage and parses README ticks. The CLI and MCP tool are thin wrappers; MCP confines workspace paths with the existing `_inside()` guard.

**Publishing and releases.** `pages.yml` (push to main) and the weekly pipeline both build `portal/dist` and copy `docs/bundle/index.html` to `/bundle/` before deploying. `release.yml` runs the tests, renders notes with `scripts/release_notes.py` and creates the release with a `git archive` zip.

## 10. v1.6.0 design (30 October 2026)

**Stakeholders and brief.** `knowledge/stakeholders.yaml` (roles, dates, gaps) is joined at build time with `dqkit.effort.scenarios()` and a summary of `assessments/portfolio/cda-return.csv` into `__K_STAKEHOLDERS__`. The brief is therefore regenerated on every build and release.

**Q-FAIR.** `dqkit/qfair.py` rates five areas from the run result and the asset record; `cdareturn.row()` adds the record fields, ratings and baseline confidence. New optional asset fields in rules files: `description`, `access_route`, `classification`, `conforms_to`, `identifiers`, `licence`, `provenance`, `baseline_confidence`.

**Effort.** `knowledge/effort.yaml` holds activities and defaults; the baseline page reads it through `__K_EFFORT__`; `dqkit/effort.py` ports the same formula.
