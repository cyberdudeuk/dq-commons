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
- With --sync it also keeps the GitHub roadmap in step with the portal's: each backlog issue is put in the
  milestone for its stage (Now, Next, Later or Done, the same stages as the portal's roadmap), its
  "Status:" line is updated, and items that are prepared but wait on people get the label "needs-people".
  It changes only the milestone, that one line and that label: never the rest of the issue, and it
  never closes an issue (commits that say "Closes #n" do that).

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


MILESTONES = {"Now": "Being built now, or prepared and waiting on people",
              "Next": "Must and should items not started yet",
              "Later": "Could items, after Next",
              "Done": "Delivered; see CHANGELOG.md and the portal's What's new"}


def stage(b: dict) -> str:
    """The roadmap stage for a backlog item: the same rule the portal uses (build_dq_portal.py roadmap())."""
    if b["status"] == "done":
        return "Done"
    if b["status"] == "in-progress":
        return "Now"
    return "Next" if b["moscow"] in ("must", "should") else "Later"


def needs_people(b: dict) -> bool:
    return b["status"] == "in-progress" and "needs" in str(b.get("done", "")).lower()


def sync(repo, token) -> int:
    ms = {m["title"]: m["number"] for m in _req("GET", f"{API}/repos/{repo}/milestones?state=all&per_page=100", token)}
    for title, desc in MILESTONES.items():
        if title not in ms:
            ms[title] = _req("POST", f"{API}/repos/{repo}/milestones", token, {"title": title, "description": desc})["number"]
    ensure_labels(repo, token, {"needs-people"})
    by_id = {b["id"]: b for b in items()}
    issues, page = [], 1
    while True:
        rows = _req("GET", f"{API}/repos/{repo}/issues?state=all&labels=backlog&per_page=100&page={page}", token)
        issues += rows
        if len(rows) < 100:
            break
        page += 1
    changed = 0
    for i in issues:
        bid = i.get("title", "")[1:].split("]")[0]
        b = by_id.get(bid)
        if not b:
            continue
        patch = {}
        want = ms[stage(b)]
        if (i.get("milestone") or {}).get("number") != want:
            patch["milestone"] = want
        body = i.get("body") or ""
        line = f"**Status:** {b['status']}" + (f" ({b['done']})" if b.get("done") else "")
        import re
        new_body = re.sub(r"\*\*Status:\*\* [^\n]*?(?=  \n|\n|$)", lambda m: line, body, count=1)
        if new_body != body:
            patch["body"] = new_body
        labels = [l["name"] for l in i.get("labels", [])]
        if needs_people(b) and "needs-people" not in labels:
            patch["labels"] = labels + ["needs-people"]
        elif not needs_people(b) and "needs-people" in labels:
            patch["labels"] = [l for l in labels if l != "needs-people"]
        if patch:
            _req("PATCH", f"{API}/repos/{repo}/issues/{i['number']}", token, patch)
            changed += 1
            print(f"Updated #{i['number']} {bid}: {', '.join(patch)}")
    print(f"Roadmap sync: {changed} issues updated.")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--repo", default=os.environ.get("GITHUB_REPOSITORY", "cyberdudeuk/dq-commons"))
    ap.add_argument("--apply", action="store_true", help="create the issues (otherwise a dry run)")
    ap.add_argument("--sync", action="store_true", help="also set milestones, status lines and needs-people labels")
    a = ap.parse_args(argv)
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    wanted = [issue_for(b) for b in items()]
    if not (a.apply and token):
        for w in wanted:
            print("Would create:", w["title"], w["labels"])
        if a.sync:
            for b in items():
                print(f"Would place {b['id']} in {stage(b)}" + (" (needs-people)" if needs_people(b) else ""))
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
    return sync(a.repo, token) if a.sync else 0


if __name__ == "__main__":
    raise SystemExit(main())
