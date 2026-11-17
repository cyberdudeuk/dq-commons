# Secrets scan audit

Scanned on 17 November 2026 with detect-secrets 1.5.0 over every tracked file (excluding `node_modules`,
`vendor` and lock files). The results are recorded in [`.secrets.baseline`](../../.secrets.baseline).

- Candidates found: 100
- Audited as real secrets: 0

Each candidate was read in context and judged not to be a secret:

12-character section fingerprints; secret *names* (not values) in `integrations/config.yaml`; synthetic NHS number and National Insurance test values in tests and parity checks; repository names in `portal/src/pages/tooling.html`.

New commits are checked by the detect-secrets pre-commit hook against this baseline. If the hook flags a
new string, read it, and either remove it or audit it into the baseline with `detect-secrets audit .secrets.baseline`.
Never audit a real credential as a false positive: remove it and rotate it.
