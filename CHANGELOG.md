# Changelog

## 0.3.0 — 2026-10-14
### Added
- `control_point` on every rule (source, pipeline or reporting), from the controls model in the brief research note.
- Issue operations (`dqkit/operations.py`): defect volume, control failure rate, cycles open, overdue issues with escalation, and recurrence. A new Operations tab in the workbook.
- Workbook Issues log: control point, cycles open, escalation, recurring, source system and immediate risk. Actions tab: action type (containment, corrective, preventive) and how success will be checked.
- `--case-study`: drafts the GDS case study template (.md and .docx) from results. The NDL charts each get one.
- `dqkit survey`: reshapes and summarises the Cross-Government DQ Solutions Survey export, with personal data removed.
- `docs/SURVEY-REVIEW.md` (12 fixes before launch). Crosswalk extended to 15 sources and 18 findings.
- Illustrative escalation example (`examples/illustrative-escalation/`).

## 0.2.0 — 2026-10-14
### Added
- Filled-in DQAP Excel workbook (`--workbook`) and run history (`--history`).
- IOPC-style trust level and decision-tree DQAP route in every check summary.
- ESS "plus" dimensions, and `trust_level` in the metadata model.
- Guidance crosswalk of 9 sources, with 9 findings.
### Changed
- Default targets now use the low end of each framework range (D-021). The previous defaults are available as `target_policy: mid`.
- The Issues log now shows plain-English error rates.

## 0.1.0 — 2026-10-14
### Added
- `dqkit` rules engine, the GOV.UK issues framework, a metadata assessment, and DQV, DQAP, GX and R validate outputs.
- A cross-government issue vocabulary (43 types) and an inclusion dimension.
- A proposed DQV quality extension for the cross-government metadata exchange model.
- The NDL collections assessment (84 pages, 8 chart files) and its report.
- Documentation set and CI.
