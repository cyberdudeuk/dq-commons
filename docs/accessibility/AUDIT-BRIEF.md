# Brief: independent WCAG 2.2 AA accessibility audit (BL-02, issue #2)

A ready-to-send statement of work. The audit needs an independent supplier and disabled testers, so the issue
stays open until the audit report is in and its fixes are planned.

## Why

The Commons is checked automatically on every change (our own browser checks and axe-core), and states that it is
**partially compliant** with WCAG 2.2 AA because it has not been independently audited. Public bodies that use it need
to know it meets the Public Sector Bodies (Websites and Mobile Applications) (No. 2) Accessibility Regulations 2018.

## Scope

- **Standard:** WCAG 2.2 level A and AA, all success criteria.
- **Pages (sample of 12 covering every template and interaction):** Home; New to GitHub; Learn; Across the professions;
  Check your data (with a file loaded); Maturity self-assessment; AI assistant (as shown on GitHub Pages, AI off);
  Data quality management playbook; Frameworks (comparison view); Metadata Weaver (with results); Help us build this
  (contact form and backlog); Accessibility and privacy.
- **Shared components:** global menu, "On this page" drawer and collapsible sections, search dialog, What's new panel,
  guided tours, carousel, tabs, data tables, file inputs, downloads, dark mode, print.
- **Assistive technology and browsers (minimum):** JAWS with Chrome, NVDA with Firefox, VoiceOver with Safari on macOS and iOS,
  TalkBack with Chrome on Android, Dragon or Voice Control, Windows magnifier or ZoomText at 400%, keyboard only, high contrast mode.
- **Testing with disabled people:** at least 5 participants with different access needs, on 4 tasks from
  `docs/research/RESEARCH-KIT.md`.

## Deliverables

1. Report listing every failure with the success criterion, page, steps to reproduce, severity, and a suggested fix.
2. Findings from the sessions with disabled participants, in their words where they agree.
3. A retest of fixes within 3 months.
4. Wording the Commons can use to update its accessibility statement.

## How we will act on it

Failures become GitHub issues labelled `area:accessibility`, fixed in order of severity. Blocking issues are fixed
before the next release. The accessibility statement is updated in the same change.

## Practical

- Budget: to be agreed by the sponsoring organisation. A sample this size usually takes 5 to 10 supplier days plus sessions.
- Route: any public sector framework that covers accessibility testing, or a direct award under the threshold.
- Supplier must not have built the Commons. Testers with lived experience of disability should be paid.
- Contact for the supplier: the Commons contact form. We never publish an email address.
