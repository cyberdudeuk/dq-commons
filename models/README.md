# Enterprise data quality capability: models

This folder describes the end-to-end data quality management capability as data: its **capabilities**, its **information model** (the records it keeps) and its **workflows**. Every file is generated from one source, so they always agree.

- **Source:** [`dq-capability.yaml`](dq-capability.yaml). Edit this, never the generated files.
- **Generator:** [`scripts/build_models.py`](../scripts/build_models.py).
- **Portal page:** *Capability and data models* (Manage and improve), with downloads and a text version of every diagram.

## What is in it

| Part | Count | Traced to |
|---|---|---|
| Capabilities (level 1), each with 3 sub-capabilities | 12 | GDQF principles, DAM policy, DQAP guide, data ownership model |
| Record types (entities) | 22 | DAM policy, critical data asset metadata guidance, DQAP steps, issues framework |
| Workflows | 5 | P1 identify and register critical data assets, P2 DQAP lifecycle (7 steps), P3 issue management, P4 scheduled measurement, P5 annual review and return |

Each capability, record type and workflow step carries the codes of the guidance it puts into practice. The capability map is coloured by the Government Data Quality Framework principle each capability mainly serves; that is the "overlay".

## Which file for which tool

| File | Opens in |
|---|---|
| `out/archimate/dq-capability.xml` | ArchiMate 3.1 Open Exchange Format: Archi, Sparx EA, BiZZdesign, ADOIT, ARIS |
| `out/archimate/csv/dq-*.csv` | Archi CSV import |
| `out/uml/dq-data-model.xmi` | UML 2.5.1 XMI: Sparx EA, MagicDraw or Cameo, Visual Paradigm, Papyrus |
| `out/sql/dq-data-model.sql` | PostgreSQL; reverse-engineer in erwin, ER/Studio, DBeaver |
| `out/json/dq-data-model.schema.json` | JSON Schema 2020-12 for APIs, data contracts and validation |
| `out/rdf/dq-data-model.ttl` | OWL in Turtle: Protégé, TopBraid, knowledge graphs |
| `out/dictionary/data-dictionary.csv` | Spreadsheets and catalogues (Purview, Collibra, DataHub) |
| `out/dictionary/capability-guidance-matrix.csv` | Capabilities against principles, guidance, records and workflows |
| `out/erd/dq-data-model.mmd`, `dq-data-model.svg` | Entity relationship diagram (Mermaid source and image) |
| `out/visio/dq-capability-process-map.vsdx` | Microsoft Visio (8 pages); `dq-capability-process-map.pdf` for anyone without Visio |
| `out/bpmn/P1..P5-*.bpmn` | BPMN 2.0 with diagram layout: Camunda Modeler, bpmn.io, Signavio, Bizagi, ARIS |

## How it connects to the rest of the Commons

- `pages` on a capability and `page` on a step name the portal pages where the work is done; `stage` names the playbook stage; `lanes` maps each swimlane to a role on the "For your role" page and a learning pathway.
- The models page uses these for its capability map, workflow player and record explorer; the home page shows the capability map; each role sees its steps; each playbook stage links to its steps; search and the knowledge map include them.
- The generator refuses a link to a page, stage or role that doesn't exist.

## How to change the model

1. Edit `dq-capability.yaml`. Put quotes round any text that contains a comma or ends in a question mark.
2. Run `python3 scripts/build_models.py`. It stops with a plain English message if something refers to a record, list, lane or step that does not exist.
3. To refresh the images too: `python3 scripts/build_models.py --svg --render` (needs mmdc and LibreOffice).
4. Run `python3 -m unittest tests.test_models`. CI runs `build_models.py --check` and fails if a generated file no longer matches the YAML.

## What was checked, and what was not

- **Checked automatically:** the SQL runs (in SQLite, with allowed values enforced); the JSON Schema is valid and accepts and rejects sample records; every reference in the ArchiMate, Archi CSV, UML and BPMN files resolves; every BPMN element has diagram layout; every workflow step can reach an end; the Visio package has every part and every connector is glued to a shape on its page.
- **Checked by eye:** the Visio file opens in LibreOffice Draw and renders all 8 pages (the PDF and previews are made that way).
- **Not checked here:** opening the files in Microsoft Visio, Archi, Sparx EA or Camunda themselves, and validation against the official ArchiMate and BPMN XSD files (their sites were not reachable from the build environment). Please report anything that does not import cleanly through the contact form.

## Guidance codes

| Code | Guidance |
|---|---|
| DAM | [Data asset management policy in government](https://www.gov.uk/government/publications/data-asset-management-policy-in-government/data-asset-management-policy-in-government) |
| IDC | [Identifying and recording critical data assets](https://www.gov.uk/government/publications/identify-and-record-critical-data-assets/identifying-and-recording-critical-data-assets) |
| MD | [Recording metadata to describe critical data assets](https://www.gov.uk/government/publications/record-metadata-to-describe-critical-data-assets/recording-metadata-to-describe-critical-data-assets) |
| DOM | [Data ownership model](https://www.gov.uk/government/publications/data-ownership-in-government/data-ownership-model) |
| DQAP1 to DQAP7 | [Data quality action plan implementation guide](https://www.gov.uk/government/publications/implement-a-data-quality-action-plan/data-quality-action-plan-implementation-guide), steps 1 to 7 |
| IF | [Data quality issues framework](https://www.gov.uk/government/publications/implement-a-data-quality-action-plan/data-quality-issues-framework) |
| GDQF-P1 to P5, GDQF-LC, GDQF-D | [The Government Data Quality Framework](https://www.gov.uk/government/publications/the-government-data-quality-framework/the-government-data-quality-framework): principles, lifecycle, dimensions |
| COP | [Code of Practice for Statistics](https://osr.statisticsauthority.gov.uk/publications/the-code-of-practice-for-statistics/) |
| QAAD | [Quality assurance of administrative data](https://osr.statisticsauthority.gov.uk/guidance/administrative-data-and-official-statistics/) |
| ICO | [UK GDPR accuracy principle](https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/data-protection-principles/a-guide-to-the-data-protection-principles/accuracy/) |
| DCAT, DQV | W3C Data Catalog Vocabulary 3, Data Quality Vocabulary |

MIT licence, like the rest of the repository.
