---
artefact:id: P04-HLD-001
artefact:version: 1.0.0
artefact:as-of: 2026-11-20
artefact:review-date: 2027-02-20
project: P04 Public Sector Data Quality Commons
grade: G3
profile: public sector > personal public good
---

# High-level design (HLD): Public Sector Data Quality Commons

> **How to read this.** Facts marked V were read from this repository on 20 November 2026. Assumptions, measures and risks are proposals written for this kit, not findings. U means unconfirmed. Where another document in this repository already covers a topic, this one links to it rather than repeating it.

## Building blocks
Derived from the repository's top-level structure (V: git tree, 20 Nov 2026).

| Part | Role | Files |
|---|---|---|
| `assessments/` | Assessments | 150 |
| `portal/` | Portal source | 94 |
| `.github/` | Workflows, issue forms and repository health files | 42 |
| `knowledge/` | Knowledge base | 40 |
| `tests/` | Automated tests | 34 |
| `models/` | Models | 32 |
| `dqkit/` | Data quality kit | 30 |
| `docs/` | Documentation and registers | 29 |
| `scripts/` | Build, check and routine scripts | 29 |
| `packs/` | Packs | 16 |
| `rules/` | Data quality rules | 14 |
| `vocab/` | See README | 12 |
| `examples/` | Examples | 9 |
| `integrations/` | Integration kits | 6 |

## How it fits together
1. Content and data live in the source folders above. They are the single source of truth.
2. The build and check commands in [07-lld.md](07-lld.md) generate the published output from those sources. Generated folders are never edited by hand. (D-KIT-02: an earlier draft named the first command as 'the build', which was wrong for repositories whose first command is a test run.)
3. Checks and tests run locally and in CI before anything is published.
4. Publication happens through the repository's workflow (pages.yml, release.yml).
5. People change things through pull requests and GitHub issue forms. Routines report; a person decides anything irreversible.

## Integrations
- **NDL PubSec MCP:** Federation (Listed)
- **DAM capability playbooks:** Quality rules (Live)
- **Confluence:** docs-to-confluence workflow (Live)

## Environments
- **Local:** run the build and checks below.
- **CI:** GitHub Actions. Note: on 20 November 2026 no Actions jobs could start on this account because of a billing block; local checks are the evidence until that is fixed.
- **Live:** https://cyberdudeuk.github.io/dq-commons/

For the architecture rationale, see [docs/ARCHITECTURE.md](../../docs/ARCHITECTURE.md).
