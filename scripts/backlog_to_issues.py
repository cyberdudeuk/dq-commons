"""Turn the backlog in knowledge/build.yaml into GitHub issues, once each.

Usage:
    python scripts/backlog_to_issues.py [--repo OWNER/REPO] [--apply]

In plain English:
- Every backlog item (BL-01, BL-02, ...) becomes one GitHub issue titled "[BL-01] ...", labelled
  "backlog", its area and its MoSCoW priority.
- It is safe to run again and again: it looks for an existing issue with the same [BL-nn] prefix
  first, and only creates what is missing. It never edits or closes issues people have worked on.
- Items that already have a Jira key get the label "jira-linked", so the GitHub-to-Jira sync
  doesn't create a duplicate story.
- Without --apply, or without a GITHUB_TOKEN (or GH_TOKEN), it prints what it would do (a dry run).

It uses the GitHub REST API directly, so it needs nothing beyond the Python standard library and PyYAML.
"""
from __future__ import annotations

import argparse
import json
import os
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
API = "https://api.github.com"
COLOURS = {"backlog": "0e8a16", "jira-linked": "5319e7", "moscow:must": "b60205", "moscow:should": "d93f0b",
           "moscow:could": "fbca04", "moscow:wont": "cccccc"}


def items() -> list:
    return yaml.safe_load((ROOT / "knowledge" / "build.yaml").read_text(encoding="utf-8"))["backlog"]


def issue_for(b: dict) -> dict:
    labels = ["backlog", f"area:{b['area']}", f"moscow:{b['moscow']}"] + (["jira-linked"] if b.get("jira") else [])
    body = (f"**Why it matters:** {b['why']}\n\n**Priority (MoSCoW):** {b['moscow']}  \n**Area:** {b['area']}  \n"
            f"**Status:** {b['status']}" + (f"  \n**Jira:** {b['jira']}" if b.get("jira") else "") +
            "\n\nFrom the Commons backlog (`knowledge/build.yaml`). Comment here to discuss or to say you're working on it. "
            "Please don't include personal data.")
    return {"title": f"[{b['id']}] {b['title']}", "body": body, "labels": labels}


def _req(method, url, token, data=None):
    req = urllib.request.Request(url, method=method, data=json.dumps(data).encode() if data is not None else None,
                                 headers={"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json",
                                          "X-GitHub-Api-Version": "2022-11-28", "User-Agent": "dq-commons-backlog"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read() or b"null")


def existing(repo, token) -> set:
    found, page = set(), 1
    while True:
        rows = _req("GET", f"{API}/repos/{repo}/issues?state=all&labels=backlog&per_page=100&page={page}", token)
        for r in rows:
            t = r.get("title", "")
            if t.startswith("[BL-"):
                found.add(t.split("]")[0] + "]")
        if len(rows) < 100:
            return found
        page += 1


def ensure_labels(repo, token, labels):
    for name in sorted(labels):
        try:
            _req("GET", f"{API}/repos/{repo}/labels/{urllib.parse.quote(name, safe='')}", token)
        except urllib.error.HTTPError as e:
            if e.code != 404:
                raise
            _req("POST", f"{API}/repos/{repo}/labels", token, {"name": name, "color": COLOURS.get(name, "c5def5")})


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--repo", default=os.environ.get("GITHUB_REPOSITORY", "cyberdudeuk/dq-commons"))
    ap.add_argument("--apply", action="store_true", help="create the issues (otherwise a dry run)")
    a = ap.parse_args(argv)
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    wanted = [issue_for(b) for b in items()]
    if not (a.apply and token):
        for w in wanted:
            print("Would create:", w["title"], w["labels"])
        print(f"Dry run: {len(wanted)} backlog items. Use --apply with GITHUB_TOKEN set to create missing issues.")
        return 0
    have = existing(a.repo, token)
    ensure_labels(a.repo, token, {l for w in wanted for l in w["labels"]})
    made = 0
    for w in wanted:
        if w["title"].split("]")[0] + "]" in have:
            continue
        r = _req("POST", f"{API}/repos/{a.repo}/issues", token, w)
        print("Created", r.get("html_url"))
        made += 1
    print(f"{made} created, {len(wanted) - made} already there.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
