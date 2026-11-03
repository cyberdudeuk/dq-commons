# How the Commons keeps itself current, accurate and trustworthy

The portal and toolkit check themselves. This is the list of routines, what each one catches, and what's planned.
The same list is shown on the portal's Help us build this page (from `knowledge/build.yaml`).

## Running now

| Routine | Catches | Where |
|---|---|---|
| Unit and integration tests | Broken code, invalid knowledge files, pages missing parts | `tests/`, `.github/workflows/ci.yml` |
| Two-engine parity | The browser and Python giving different answers | `scripts/parity_check.py` |
| Content health report | Overdue reviews, stale news, unverified sources, personal or sensitive data, duplicates, numbers that no longer match the data, non-https links, words to avoid | `scripts/self_check.py`, `.github/workflows/content-health.yml` |
| Link checker | Broken external links | `scripts/check_links.py`, `.github/workflows/link-check.yml` |
| Review dates | Knowledge with no owner or not reviewed for 12 months | `tests/test_knowledge.py` |
| Community docs in sync | The charter or contributors list drifting from the portal | `scripts/gen_community_docs.py --check` |
| Backlog to issues | Backlog items without a GitHub issue | `scripts/backlog_to_issues.py` |
| Privacy guards | Email addresses or internal site addresses in anything people read | `tests/test_weaver.py` (Privacy) |
| Moderation | Personal data, poor sources or unlicensed material in contributions | Community page |

## Recommended next (on the backlog)

1. **Accessibility in CI:** axe-core on every page, light and dark, desktop and phone (BL-18).
2. **Freshness issues:** stale news or overdue reviews open a GitHub issue for the owning role (BL-19).
3. **Source archiving:** keep an archived copy of each cited source (BL-20).
4. **Source diffing:** notice when an official source changes after we summarised it.
5. **Fact sampling:** a person re-checks 5% of claims each quarter and the error rate is published.
6. **Provenance on every page:** last reviewed, by which role, from which commit (BL-21).
7. **AI evaluation gate:** the assistant's evaluation set must pass before any AI change ships.
8. **Inclusion review:** each release, check that content and examples include all nations, jurisdictions and groups.
9. **Dependency and secret scanning:** turn on Dependabot and secret scanning when the repository is public.
10. **Search analytics without tracking:** count failed site searches in the browser only, and let users choose to send them, to find missing content.
