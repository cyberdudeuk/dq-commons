---
artefact:id: P04-LLD-001
artefact:version: 1.0.0
artefact:as-of: 2026-11-20
artefact:review-date: 2027-02-20
project: P04 Public Sector Data Quality Commons
grade: G3
profile: public sector > personal public good
---

# Low-level design (LLD): Public Sector Data Quality Commons

> **How to read this.** Facts marked V were read from this repository on 20 November 2026. Assumptions, measures and risks are proposals written for this kit, not findings. U means unconfirmed. Where another document in this repository already covers a topic, this one links to it rather than repeating it.

## Build and check commands (V: README)
```
python3 -I -m pytest
python3 scripts/build_dq_portal.py
```

## Scripts (V: file tree)
- `scripts/a11y_check.mjs`
- `scripts/apply_settings.sh`
- `scripts/audit_provenance.py`
- `scripts/backlog_to_issues.py`
- `scripts/build_bundle.py`
- `scripts/build_dq_portal.py`
- `scripts/build_models.py`
- `scripts/build_playbook_doc.py`
- `scripts/build_vocab.py`
- `scripts/check_links.py`
- `scripts/check_settings.py`
- `scripts/check_vendor_repos.py`
- `scripts/eval_rule_drafting.py`
- `scripts/export_strings.py`
- `scripts/gen_community_docs.py`
- `scripts/gen_issue_forms.py`
- `scripts/import_code_evidence.py`
- `scripts/make_badges.py`
- `scripts/mcp_manifest.py`
- `scripts/parity_check.mjs`
- `scripts/parity_check.py`
- `scripts/portal_add_pages.py`
- `scripts/publish_confluence.py`
- `scripts/release_notes.py`
- `scripts/run_ndl_assessment.py`

## Tests (V: file tree)
- `tests/test_ai_eval.py`
- `tests/test_backlog_done.py`
- `tests/test_catalogues.py`
- `tests/test_community_questions.py`
- `tests/test_contracts.py`
- `tests/test_dqkit.py`
- `tests/test_ecosystem_standards.py`
- `tests/test_fuzz.py`
- `tests/test_integrations.py`
- `tests/test_knowledge.py`
- `tests/test_knowledge_graph.py`
- `tests/test_mcp.py`
- `tests/test_mcp_manifest.py`
- `tests/test_models.py`
- `tests/test_moderation_sla.py`
- `tests/test_owner_rules.py`
- `tests/test_packs.py`
- `tests/test_parity.py`
- `tests/test_participation_governance.py`
- `tests/test_pipeline.py`

## Workflows (V: .github/workflows)
- `accessibility.yml`
- `backlog-issues.yml`
- `backlog-sync.yml`
- `ci.yml`
- `codeql.yml`
- `content-health.yml`
- `dependency-review.yml`
- `docs-to-confluence.yml`
- `dq-pipeline.yml`
- `fact-sampling.yml`
- `labeler.yml`
- `link-check.yml`
- `pages.yml`
- `release.yml`
- `repo-health.yml`
- `scorecard.yml`
- `triage.yml`
- `welcome.yml`

## Repository size
561 files tracked on 20 November 2026.

## Documentation kit
- `docs/artefacts/manifest.yaml` lists every core document, where it is, and its review date.
- `tools/artefact_check.py` checks the kit (rules AC-01 to AC-08, each with a negative test). Run `python3 tools/artefact_check.py --self-test` then `python3 tools/artefact_check.py .`.

## Handover
Someone new can rebuild and verify with the commands above, then read [docs/PRD.md](../../docs/PRD.md) and [docs/ARCHITECTURE.md](../../docs/ARCHITECTURE.md).
