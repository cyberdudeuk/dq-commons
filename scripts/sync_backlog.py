"""Mirror a GitHub issue to the Jira backlog, and write the Jira key back to the issue.

Run by .github/workflows/backlog-sync.yml when an issue gets the backlog label. It can also be
run by hand: python scripts/sync_backlog.py --title "..." --body "..." --url https://github.com/...

Needs JIRA_BASE_URL, JIRA_EMAIL and JIRA_API_TOKEN in the environment. Without them it prints
what it would do and exits 0 (a dry run), so the workflow never fails just because it isn't set up.
"""
from __future__ import annotations

import argparse
import base64
import json
import os
import sys
import urllib.request
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent


def config() -> dict:
    return yaml.safe_load((ROOT / "integrations" / "config.yaml").read_text(encoding="utf-8"))


def jira_payload(cfg: dict, title: str, body: str, url: str) -> dict:
    j = cfg["jira"]
    text = (body or "").strip()[:20000]
    return {"fields": {
        "project": {"key": j["project"]},
        "issuetype": {"name": j.get("issue_type", "Story")},
        "summary": title[:250],
        "parent": {"key": j["epic"]},
        "labels": ["dq-commons", "from-github"],
        "description": {"type": "doc", "version": 1, "content": [
            {"type": "paragraph", "content": [{"type": "text", "text": text or "(no description)"}]},
            {"type": "paragraph", "content": [{"type": "text", "text": "GitHub issue: " + url,
                                               "marks": [{"type": "link", "attrs": {"href": url}}]}]}]}}}


def create(payload: dict, opener=urllib.request.urlopen) -> str:
    base = os.environ["JIRA_BASE_URL"].rstrip("/")
    auth = base64.b64encode(f"{os.environ['JIRA_EMAIL']}:{os.environ['JIRA_API_TOKEN']}".encode()).decode()
    req = urllib.request.Request(f"{base}/rest/api/3/issue", data=json.dumps(payload).encode(), method="POST",
                                 headers={"Authorization": f"Basic {auth}", "Content-Type": "application/json",
                                          "Accept": "application/json"})
    with opener(req, timeout=30) as r:
        return json.loads(r.read())["key"]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--title", required=True)
    ap.add_argument("--body", default="")
    ap.add_argument("--url", default="")
    a = ap.parse_args(argv)
    cfg = config()
    payload = jira_payload(cfg, a.title, a.body, a.url)
    if not all(os.environ.get(k) for k in ("JIRA_BASE_URL", "JIRA_EMAIL", "JIRA_API_TOKEN")):
        print("Dry run (Jira secrets not set). Would create:", json.dumps(payload)[:500])
        return 0
    key = create(payload)
    print(key)
    out = os.environ.get("GITHUB_OUTPUT")
    if out:
        with open(out, "a", encoding="utf-8") as f:
            f.write(f"jira_key={key}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
