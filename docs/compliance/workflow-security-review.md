# Workflow security review

Reviewed on 17 November 2026 against the GDS Way guidance on
[using GitHub Actions and workflows](https://gds-way.digital.cabinet-office.gov.uk/standards/source-code/using-github-actions.html),
which lists `issues` among the triggers to avoid unless they have had a rigorous security review.

For each workflow below the review checked: who can start it; whether untrusted text can reach a shell
(script injection); whether code from a pull request or fork is checked out and run; and whether the
token's permissions are the least the job needs.

## `backlog-sync.yml:issues`

Runs on `issues: labeled`, and only when the label is `backlog`; only people with triage rights can label, so outsiders cannot start it. Issue title and body reach the script through `env:` and quoted shell variables, never `${{ }}` inside `run:`. It does not check out or run code from a pull request. Token: `issues: write`, `contents: read`. Jira secrets are scoped to this workflow.

**Outcome:** accepted. Re-review whenever the workflow changes; a code owner must approve any change to `.github/workflows`.

## `pages.yml:issues`

Runs on `issues: labeled/unlabeled`, and the build job only proceeds for the moderator labels `published` or `withdrawn`. It builds from `main`, never from issue content as code; issue data is read through the API as data. Token: `contents: read`, `issues: read`, plus `pages: write` and `id-token: write` for the deploy.

**Outcome:** accepted. Re-review whenever the workflow changes; a code owner must approve any change to `.github/workflows`.

## `welcome.yml:issues`

Runs on `issues: opened` and posts a fixed welcome comment. It reads only the author's login, type and labels from the event payload inside `actions/github-script` (JavaScript, no shell). Token: `issues: write`, `pull-requests: write`. The pull request trigger was changed from `pull_request_target` to `pull_request` in this change.

**Outcome:** accepted. Re-review whenever the workflow changes; a code owner must approve any change to `.github/workflows`.

