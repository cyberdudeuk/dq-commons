# Contributing to the Public Sector Data Quality Commons

Everyone is welcome: central and local government, devolved administrations, the wider public
sector, and private and voluntary organisations. You don't need to write code to contribute.

## Ways to contribute

| You want to | Do this |
|---|---|
| Share a case study, insight or resource | Use the portal's Community page (Library), or open a "Contribute to the library" issue |
| Ask for help | Use the portal's Commission form, or open a "Commission help" issue |
| Suggest a feature | Add it to the portal's wishlist, or open a "Feature request or wish" issue |
| Add a rule, identifier, value set, framework or pack | Open a "Add a rule, value set or framework pack" issue, or a pull request |
| Fix or improve code | Open a pull request (see below) |

## Ground rules

- **No personal data, anywhere:** code, tests, examples, issues or screenshots. Use made-up data.
- **Cite authoritative sources** for frameworks, standards, identifiers and value sets. Summarise in
  your own words. Don't copy text from paid standards.
- **Plain English** in everything people read. Follow GOV.UK style.
- **Accessible by default.** Portal changes must work with a keyboard, a screen reader, at 400px
  wide, and in dark mode.
- **Deterministic results.** Measuring is done by rules, not models. AI may draft; rules decide.
  New AI components follow the route in `knowledge/ai-for-dq.yaml` (7 stages and a checklist).
- **Two engines, one answer.** A change to `dqkit/rules.py` needs the same change in
  `portal/src/js/engine.js`, and `python scripts/parity_check.py` must pass.

## Pull requests

1. Fork, then branch from `main`.
2. Make the change, with tests.
3. Run `python -m unittest discover -s tests` and, if relevant, `python scripts/parity_check.py`.
4. Update the docs in the same pull request.
5. Fill in the pull request checklist. A maintainer reviews within 10 working days.

## How work is tracked

GitHub issues are the public front door. Issues labelled `backlog` are mirrored to the Jira
project (key set in `integrations/config.yaml`) by the backlog sync workflow, and the Jira key is
written back as a comment. Support and operating model pages live in Confluence
(see `docs/OPERATING-MODEL.md`).

## Licence

Code: MIT. Content: Open Government Licence v3.0. By contributing you agree your contribution is
published under these licences.
