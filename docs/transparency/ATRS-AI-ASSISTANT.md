# Algorithmic transparency record: Rules assistant

This record follows the structure of the UK government's **Algorithmic Transparency Recording Standard (ATRS)**
(Tier 1 summary, then the Tier 2 sections). The Commons is not a public body, so publishing it is voluntary.
We publish it because the public bodies who use the Commons are expected to be open about algorithmic tools,
and we should meet the same bar (backlog BL-03, issue #3).

| | |
|---|---|
| Record version | 2.0 |
| Last updated | 4 November 2026 |
| Change from version 1.0 | The assistant **no longer uses an AI model**. Version 1.0 (3 November 2026) described a large language model reached through claude.ai. Most of the Commons' audiences have no claude.ai licence, so the model was removed (decision D-GH-02). The assistant now drafts rules with fixed, published patterns that run entirely in the browser. |
| Next review | With every change to the patterns, and at least every 6 months |
| Owner (role) | Commons maintainers (AI and data ethics lead role) |
| Contact | The Commons [contact form](https://github.com/cyberdudeuk/dq-commons/issues/new?template=0-contact.yml). We never publish an email address. |

---

## Tier 1: summary

**Name:** Rules assistant (portal page `assistant.html`).

**Description:** turns a plain English description of data quality expectations into a rules file for the Commons
toolkit. Each phrase it recognises (for example "valid NHS number", "not in the future", "one per person per month",
"between 0 and 100", "one of A, B or C", "ethnic group recorded") maps to one check. The toolkit's engine then
validates the rules file. Anything it doesn't recognise is listed, never guessed. It also answers two kinds of
look-up from the knowledge base: which frameworks apply, and how the government issues framework scores an issue.

**Website:** <https://cyberdudeuk.github.io/dq-commons/assistant.html>

**Why it is used:** writing rules files by hand is slow and needs technical skill. The assistant lowers that barrier
for everyone, with no account, licence or AI service.

**How it affects people:** it does not make or support decisions about individual members of the public. It supports
staff who write checks on datasets. A poor rule could make a dataset look better or worse than it is, so every draft
must be reviewed before use.

---

## Tier 2

### 1. Owner and responsibility
- **Organisation:** Public Sector Data Quality Commons, an open community project (not an official government service).
- **Team:** Commons maintainers. **Senior responsible owner (role):** lead maintainer.
- **Supplier involvement:** none. No third-party service is called.

### 2. Description and rationale
- **How it works:** the text is split into sentences and clauses; each clause is matched against a fixed list of
  patterns in the page's source code; matched words are linked to the loaded file's column names where a file is loaded;
  the resulting rules are validated by `portal/src/js/engine.js`, which matches the Python toolkit case for case.
- **Optional:** a button copies the request as a prompt for an AI tool the person's own organisation has approved. The
  Commons sends nothing; the person decides whether and where to use it, under their organisation's rules.
- **Alternatives considered:** keeping the AI model (rejected: most users have no licence, D-GH-02); a hosted model run by
  the Commons (rejected: cost, and data would leave the person's control); templates only (kept, alongside the assistant).

### 3. Decision-making process
- The output is a draft rules file. Nothing runs on real data until the person loads it into Check your data or the toolkit.
- The person reviews every rule. The playbook and the issues framework page explain how to test rules on a sample first.
  A data owner signs off the rules for a critical data asset.
- Anyone can report a wrong draft, or suggest a new pattern, through the contact form or a pull request.

### 4. Tool specification
- **Architecture:** a static web page; patterns and look-ups in JavaScript; no network requests.
- **Phase:** pilot. **Maintenance:** patterns live in the public repository; changes go through review and the test suite.
- **Model:** none.

### 5. Data specification
- **What is processed:** the text the person types, and the column names of a file they load, in their own browser.
- **What is sent anywhere:** nothing.
- **Personal data:** the page refuses text that looks like an email address, NI number or NHS number.

### 6. Risks, mitigations and impact assessments

| Risk | Mitigation |
|---|---|
| A wrong or incomplete rule | Every rules file is validated; unrecognised phrases are listed, not guessed; people must review; test on a sample first |
| A pattern matches the wrong column | Matched columns are shown in plain English for each rule; with no file loaded, names are marked as made up |
| Some phrasings aren't recognised | Listed back to the person; anyone can propose new patterns; templates remain available |
| Bias against groups | Patterns treat every context alike; phrases about ethnic group, sex, disability and similar add an inclusion check (`not_unknown`) |
| Over-reliance on automation | The page says plainly that people review everything; the template route stays available |

**Assessments:** covered by the Commons equality and data protection screening (`docs/EQUALITY-AND-DATA-PROTECTION-SCREENING.md`).
No data protection impact assessment is needed by the Commons because the assistant processes no personal data.
