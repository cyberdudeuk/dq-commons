#!/usr/bin/env bash
# Apply the repository settings in .github/settings-baseline.json, and tag the releases, in one go.
#
# Why this script exists: repository settings and release tags need an owner's permission, so automation
# (and the Claude maintenance task) can't change them. Run it once from your own computer:
#
#   1. Install the GitHub CLI (https://cli.github.com) and sign in:  gh auth login
#   2. In a copy of the repository:                                   git pull
#   3. Run:                                                           bash scripts/apply_settings.sh
#
# It prints each step. Nothing is deleted. Re-running it is safe.
set -euo pipefail
REPO="${REPO:-cyberdudeuk/dq-commons}"
say() { printf '\n== %s\n' "$*"; }

say "1. Features: keep Issues, Discussions and Projects on; turn the wiki off (docs live in docs/)"
gh api -X PATCH "repos/$REPO" -F has_wiki=false -F has_issues=true -F has_discussions=true \
  -F delete_branch_on_merge=true -F web_commit_signoff_required=true >/dev/null && echo "done"

say "2. Code security: secret scanning, push protection, validity checks, generic patterns, Dependabot fixes"
gh api -X PATCH "repos/$REPO" --input - >/dev/null <<'JSON' && echo "done"
{"security_and_analysis": {
  "secret_scanning": {"status": "enabled"},
  "secret_scanning_push_protection": {"status": "enabled"},
  "secret_scanning_validity_checks": {"status": "enabled"},
  "secret_scanning_non_provider_patterns": {"status": "enabled"},
  "dependabot_security_updates": {"status": "enabled"}}}
JSON
gh api -X PUT "repos/$REPO/private-vulnerability-reporting" >/dev/null && echo "private vulnerability reporting: on"

say "3. Protect main: the 'tests' check must pass; no force pushes; main can't be deleted"
# Pull requests are not required, so the weekly maintenance task can still push small fixes after tests pass.
# To require pull requests too, add {"type": "pull_request"} to the rules list below.
if gh api "repos/$REPO/rulesets" -q '.[].name' | grep -qx "Protect main"; then
  echo "ruleset already exists"
else
  gh api -X POST "repos/$REPO/rulesets" --input - >/dev/null <<'JSON' && echo "done"
{"name": "Protect main", "target": "branch", "enforcement": "active",
 "conditions": {"ref_name": {"include": ["~DEFAULT_BRANCH"], "exclude": []}},
 "rules": [{"type": "deletion"}, {"type": "non_fast_forward"},
           {"type": "required_status_checks", "parameters": {"strict_required_status_checks_policy": false,
             "required_status_checks": [{"context": "test"}]}}]}
JSON
fi

say "4. Immutable releases: a published release can't be changed afterwards"
gh api -X PUT "repos/$REPO/immutable-releases" >/dev/null 2>&1 && echo "done" || echo "not available on this account yet: turn it on in Settings, General, Releases"

say "5. Tag every release from 2.0.0 that has no tag yet (each tag makes a GitHub Release)"
git fetch --tags --quiet
for v in $(python3 -c "import yaml;print(' '.join(str(r['version']) for r in yaml.safe_load(open('knowledge/releases.yaml'))['releases']))"); do
  major=${v%%.*}; [ "$major" -ge 2 ] || continue
  if git rev-parse -q --verify "refs/tags/v$v" >/dev/null; then echo "v$v already tagged"; continue; fi
  sha=$(git log --format=%H -S"version: \"$v\"" -- knowledge/releases.yaml | tail -1)
  [ -n "$sha" ] || { echo "v$v: commit not found, skipped"; continue; }
  git tag -a "v$v" "$sha" -m "Release v$v" && git push origin "v$v" && echo "v$v tagged at ${sha:0:7}"
done

say "All done. Check: Settings, Rules; Settings, Code security; and the Releases page."
