# Algorithmic transparency record: AI Data Quality Assistant

This record follows the structure of the UK government's **Algorithmic Transparency Recording Standard (ATRS)**
(Tier 1 summary, then the Tier 2 sections). The Commons is not a public body, so publishing it is voluntary.
We publish it because the public bodies who use the Commons are expected to publish one for algorithmic
tools that affect people, and we should meet the same bar (backlog BL-03, issue #3).

A public body that adopts the assistant for its own work should publish its own record in the ATRS
repository on GOV.UK, and may reuse this one as a starting point.

| | |
|---|---|
| Record version | 1.0 |
| Last updated | 3 November 2026 |
| Next review | With every change of model, prompt or tools, and at least every 6 months |
| Owner (role) | Commons maintainers (AI and data ethics lead role) |
| Contact | The Commons [contact form](https://github.com/cyberdudeuk/dq-commons/issues/new?template=0-contact.yml) (choose "Something else"). We never publish an email address. |

---

## Tier 1: summary

**Name:** AI Data Quality Assistant (portal page `assistant.html`).

**Description:** A chat assistant that turns a plain English description of data quality expectations into a
rules file for the Commons toolkit, explains results, and finds the frameworks that apply. It uses the toolkit's
own engine as tools, so every rules file it shows has already been validated. It drafts; people decide. It
never measures data itself: measuring is always done by the rules engine.

**Website:** <https://cyberdudeuk.github.io/dq-commons/assistant.html>

**Why it is used:** writing rules files by hand is slow and needs technical skill, which keeps many data
owners and stewards out of data quality work. The assistant lowers that barrier while keeping a person in charge.

**How it affects people:** it does not make or support decisions about individual members of the public. It
supports staff who write checks on datasets. A poor rule could lead to a dataset being judged better or worse
than it is, so every draft must be reviewed before use (see "Human decisions and review").

---

## Tier 2

### 1. Owner and responsibility

- **Organisation:** Public Sector Data Quality Commons, an open community project (not an official government service).
- **Team:** Commons maintainers.
- **Senior responsible owner (role):** lead maintainer.
- **Supplier involvement:** the language model is provided by Anthropic through claude.ai. It is only available
  when the portal is opened on claude.ai, where the person's own claude.ai account and its terms apply. On
  GitHub Pages and in the offline copy the assistant is switched off and says so.

### 2. Description and rationale

- **Detailed description:** the person types a request (for example "every claim needs a valid National Insurance
  number, one claim per person per month"). The model may call these tools, all run in the person's browser by the
  toolkit's JavaScript engine: `validate_rules`, `run_rules`, `list_checks`, `describe_data`, `find_frameworks`,
  `crosswalk` and `score_issue`. It must call `validate_rules` before showing a rules file. The page shows which tools
  were used for each answer.
- **Scope:** drafting and explaining rules files; looking up frameworks; explaining scores. Out of scope: judging
  individual people, records about people, or making decisions on anyone's behalf.
- **Benefit:** faster, more consistent rules; more people able to take part in data quality work.
- **Previous process:** rules written by hand from the rule library templates (still available and recommended for
  anyone who prefers not to use AI).
- **Alternatives considered:** template-only drafting (kept as the default route); a rules wizard without AI (on the
  roadmap); a model hosted by the Commons (rejected: cost, and data would leave the person's control).

### 3. Decision-making process

- **Integration:** the output is a draft rules file. Nothing runs on a real dataset until the person loads it into
  Check your data or the toolkit themselves.
- **Information provided to the person:** the draft, the validation result, the tools used, and the warning that
  the AI drafts and the rules decide.
- **Frequency and scale:** on demand; individual users. No batch or automated use.
- **Human decisions and review:** the person must read every rule before use. The playbook and the issues framework
  page explain how to test rules on a sample first. A data owner signs off the rules for a critical data asset.
- **Training:** the Learn page's rules module and the user guide tour for the assistant.
- **Appeals and challenge:** anyone can report a wrong or harmful answer through the contact form. Reports feed the
  evaluation set (below).

### 4. Tool specification

- **Architecture:** a static web page; the model is reached through claude.ai's in-page interface (`claude.use("sample")`);
  tools are JavaScript functions from `portal/src/js/engine.js`, which matches the Python toolkit case for case
  (`scripts/parity_check.py`).
- **Phase:** pilot.
- **Maintenance:** prompt, tool list and evaluation set are in the public repository. Any change to the prompt, model or tools
  must re-run the evaluation (`scripts/eval_rule_drafting.py` against `knowledge/ai-eval/rule_drafting.yaml`); a drop in
  score blocks release.
- **Model:** a general-purpose large language model chosen by claude.ai. The Commons does not train or fine-tune any model.

### 5. Data specification

- **What is sent to the model:** the person's messages; the column names of a file they load; example values only if they
  tick the box to allow it; tool results (summaries, not rows).
- **What is never sent:** the full dataset. Files are read in the browser and never uploaded to the Commons.
- **Personal data:** the page tells people not to type personal data. The Commons stores nothing from the conversation.
- **Training data:** none from the Commons. The provider's own policies apply to the model.
- **Representativeness:** the evaluation set covers identifiers from all four UK nations, inclusion checks
  (unknown or defaulted characteristics, gaps between groups) and plain-language requests. It is small and will grow
  from real reports.

### 6. Risks, mitigations and impact assessments

| Risk | Mitigation |
|---|---|
| A wrong or incomplete rule makes a dataset look better or worse than it is | Every rules file is validated by the engine before it is shown; people must review; test on a sample first; data owner sign-off for critical data assets |
| Made-up frameworks or references | Framework answers come from the `find_frameworks` tool over the Commons registry, not from the model's memory |
| Personal data typed into the chat | Warning on the page; example values off by default; nothing stored by the Commons |
| Bias against groups (for example, checks that ignore "unknown" ethnicity or gaps between groups) | Evaluation cases include inclusion checks; the rule library offers `not_unknown` and `group_disparity` |
| Over-reliance on AI | The page states "the AI drafts, the rules decide"; the template route stays available and is described first in the guide |
| Model or provider changes behaviour | Re-run the evaluation with every change we know of; reports from users trigger a re-run |
| Excluding people without a claude.ai account | All features work without AI; the assistant is optional |

**Assessments:** the Commons equality and data protection screening (`docs/EQUALITY-AND-DATA-PROTECTION-SCREENING.md`)
covers the assistant. No data protection impact assessment is needed by the Commons because it processes no personal
data; an adopting public body should do its own screening.
