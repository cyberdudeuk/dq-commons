# Public Sector Data Quality Commons: operating model and support

Status: proposed, prototype stage. Version 1.0, October 2026. Licence: OGL v3 (text), MIT (code).

This page says who the Commons is for, how people get help, who does what, and how ideas move from a request to a released feature. It is written so any team could run the Commons, not only the team that built it.

## 1. Who it is for

Anyone working with data in or for the public sector:

- central government departments, agencies and arm's length bodies
- devolved governments in Scotland, Wales and Northern Ireland, and their public bodies
- local authorities, fire, police, health and care, and education bodies
- voluntary and community organisations and private suppliers delivering public services
- universities and researchers using public sector data

Roles we design for: data owners, data stewards, analysts and engineers, statisticians, governance leads, chief data officers, service owners, and AI and data science teams. Nobody needs to code: every task has a no-install route in the portal.

## 2. How people get help (support tiers)

| Tier | What it is | Who answers | Target response |
|---|---|---|---|
| 0. Self-service | Portal: user guide, guided tours, tutorials, learning pathway, rule library, frameworks, FAQ | Nobody needed | Instant |
| 1. Community | Discussion in the Commons community space and the networks listed on the Community page; contributions library | Other members | Best effort |
| 2. Commons team | Questions, bugs, commissions and access needs through the service desk (Jira project SUP) or a GitHub issue form | Commons team (rota) | Acknowledge in 2 working days; plan in 5 |
| 3. Specialist | Anything needing an official decision (policy wording, the official DQMI, statistics regulation, data protection) | The owning government team, with the requester's agreement | As that team sets |

Accessibility requests (for example an alternative format, or a problem with assistive technology) always go to tier 2 and are acknowledged in 1 working day.

## 3. Roles

| Role | Does | Time |
|---|---|---|
| Service owner | Owns the roadmap, priorities and the operating model; chairs triage | 0.2 FTE |
| Product and delivery | Runs the backlog (Jira XDMH, epic XDMH-210), releases, user research | 0.5 FTE |
| Maintainers (2 or more, from different organisations) | Review pull requests, keep the kit, packs and engine in parity, run the release checklist | 0.1 FTE each |
| Content stewards | Keep the framework registry, crosswalks, learning and community lists current; verify "partly" entries | 0.1 FTE each |
| Moderators | Review member contributions and survey free text before publication | Rota, 1 hour a week |
| Accessibility champion | Checks every release against WCAG 2.2 AA; runs testing with assistive technology users | 0.1 FTE |
| AI assurance lead | Owns the AI-for-DQ route: evaluations, ATRS records, human review rules | 0.1 FTE |

Named people are kept in the team's own records, not in this repository.

## 4. How work flows

1. **Idea or request.** Anyone raises it: a portal wishlist item, a GitHub issue form (feature, bug, rule or pack, commission, contribution) or a SUP service desk ticket.
2. **Weekly triage** (30 minutes, open notes). Each item gets one label: `backlog`, `answered`, `community`, `specialist` or `declined` (with the reason).
3. **Backlog.** The `backlog` label mirrors the issue to Jira automatically (`.github/workflows/backlog-sync.yml`): a story is created under epic XDMH-210 and its key is commented back on the issue. GitHub stays the place for discussion; Jira is the plan.
4. **Prioritisation** (monthly). Score = user value x reach x inclusion benefit / effort. Items that help people who are often left out of data, or that fix accessibility, go first when scores tie.
5. **Build.** A pull request using the template. It must pass tests, the Python and browser parity check, and the accessibility checks. Docs change in the same pull request.
6. **Release.** Merge to main runs the pipeline, rebuilds the portal, and publishes the operating model, user guide, decision log and runbook to Confluence (`.github/workflows/docs-to-confluence.yml`, space ARCHITECTU). The Jira story moves to Done.
7. **Tell people.** Changelog entry; a short note to the networks on the Community page.

Until the Jira and Confluence secrets are added to the repository, both workflows run as dry runs and log what they would do. See `integrations/config.yaml`.

## 5. Contributions and moderation

- Members can add case studies, insights, resources, guidance and training to the library.
- Every contribution is checked before it is public: no personal data, no named individuals without consent, accurate source links, plain English, and nothing that would identify an organisation's unpublished problems without its agreement.
- Moderators publish, ask for changes or decline within 10 working days, and always say why.
- Contributions are OGL v3 unless the contributor chooses otherwise.
- Contributors keep credit as their organisation, or anonymously if they prefer.

## 6. Surveys and commissions

- Any organisation can run a survey through the Commons. Each one shows the privacy notice first, never asks for names or emails, and shows results only as totals, with totals under 5 hidden.
- Commissions (for example assessing a data asset, writing rules, a peer review of a data quality action plan, training or incident help) are triaged weekly. Anything needing an official decision goes to tier 3 with the requester's agreement.
- The Commons tooling survey does not replace any official survey.

## 7. AI in the Commons

- The portal assistant drafts rules, explains results and finds frameworks. A person always reviews what it produces before it is used.
- Every AI component follows the route in the AI-for-DQ guidance: evaluate, assure (DPIA where personal data is involved, Algorithmic Transparency Recording Standard record), pilot, then reuse.
- The rule-drafting evaluation (`knowledge/ai-eval/`) is rerun before any change to prompts or models is released.

## 8. Measures of success

- Organisations using the kit or portal, by type and nation (from opt-in surveys, never tracking)
- Critical assets with a measured baseline
- Time from request to first answer; commissions completed
- Accessibility issues open and their age
- Share of contributions from outside central government
- Portal task completion and ease scores from the feedback survey

## 9. Risks

| Risk | Mitigation |
|---|---|
| Depends on a few people | At least two maintainers from different organisations; everything in the open repository |
| Mistaken for official guidance | Clear "prototype, not official" labels; official sources always linked first |
| Personal data in contributions or surveys | Moderation; privacy-by-design forms; suppression under 5 |
| Unverified framework content | `verified` flags shown on the page; stewards verify "partly" entries (XDMH-221) |
| AI output trusted without review | Human review required; evaluation before release; ATRS record |
