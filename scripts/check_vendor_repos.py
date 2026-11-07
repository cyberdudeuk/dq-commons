#!/usr/bin/env python3
"""Check that every GitHub repository named in knowledge/vendors.yaml still exists and is not archived.

Uses the GitHub search API (works without a token; set GITHUB_TOKEN for higher rate limits).
Writes a Markdown report and exits 1 if any repository is missing or archived, so the monthly
link check can raise one tracked issue.

    python scripts/check_vendor_repos.py --out repo-report.md
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.request
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent


def lookup(repo: str) -> dict | None:
    req = urllib.request.Request(f"https://api.github.com/search/repositories?q=repo:{repo}",
                                 headers={"Accept": "application/vnd.github+json", "User-Agent": "dq-commons-repo-check"})
    if os.environ.get("GITHUB_TOKEN"):
        req.add_header("Authorization", f"Bearer {os.environ['GITHUB_TOKEN']}")
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            items = json.load(r).get("items", [])
    except Exception:  # a 422 means the repository does not exist or is private
        return None
    return items[0] if items else None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="repo-report.md")
    a = ap.parse_args()
    v = yaml.safe_load((ROOT / "knowledge" / "vendors.yaml").read_text(encoding="utf-8"))
    rows, bad = [], 0
    for vendor in v["vendors"]:
        for g in vendor.get("github", []):
            info = lookup(g["repo"])
            if info is None:
                bad += 1
                rows.append(f"| {vendor['name']} | `{g['repo']}` | Not found |")
            elif info.get("archived"):
                bad += 1
                rows.append(f"| {vendor['name']} | `{g['repo']}` | Archived |")
            time.sleep(2.5)  # stay well inside the search rate limit
    report = "## Vendor GitHub repositories\n\n"
    report += ("Every repository listed in knowledge/vendors.yaml exists and is active.\n" if not bad else
               f"{bad} repositories need attention. Update knowledge/vendors.yaml and the connectors page.\n\n"
               "| Vendor | Repository | Problem |\n|---|---|---|\n" + "\n".join(rows) + "\n")
    Path(a.out).write_text(report, encoding="utf-8")
    print(report)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
