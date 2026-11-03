"""Compare the repository's GitHub settings with .github/settings-baseline.json and report drift.

Usage: GITHUB_TOKEN=... python scripts/check_settings.py [--repo owner/name] [--out settings-report.md]
Reads settings only; never changes them (only an owner should, in Settings). Settings the token can't read
are reported as "couldn't read", not as drift. Exit code 1 if anything has drifted.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def api(path: str, token: str):
    req = urllib.request.Request(f"https://api.github.com{path}", headers={
        "Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28", "User-Agent": "dq-commons-settings-check",
        **({"Authorization": f"Bearer {token}"} if token else {})})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read() or b"null")
    except urllib.error.HTTPError as e:
        return {"_error": e.code}


def compare(base: dict, repo: dict, pvr, rulesets, labels) -> list:
    rows = []
    for k, (want, why) in base["repo"].items():
        rows.append((f"repo.{k}", want, repo.get(k, "?"), why))
    sa = repo.get("security_and_analysis") or {}
    for k, (want, why) in base["security"].items():
        have = (pvr or {}).get("enabled", "?") if k == "private_vulnerability_reporting" else (sa.get(k) or {}).get("status", "?")
        rows.append((f"security.{k}", want, have, why))
    if isinstance(rulesets, list):
        have = any(r.get("target") == "branch" and r.get("enforcement") == "active" for r in rulesets)
    else:
        have = "?"
    want, why = base["rulesets"]["main_protected"]
    rows.append(("rulesets.main_protected", want, have, why))
    want, why = base["labels"]["required"]
    have_labels = {l["name"] for l in labels} if isinstance(labels, list) else None
    rows.append(("labels.required", "all present", "?" if have_labels is None else
                 ("all present" if set(want) <= have_labels else "missing: " + ", ".join(sorted(set(want) - have_labels))), why))
    return rows


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--repo", default=os.environ.get("GITHUB_REPOSITORY", "cyberdudeuk/dq-commons"))
    ap.add_argument("--out", default="")
    a = ap.parse_args(argv)
    token = os.environ.get("GITHUB_TOKEN", "")
    base = json.loads((ROOT / ".github" / "settings-baseline.json").read_text(encoding="utf-8"))
    r = f"/repos/{a.repo}"
    rows = compare(base, api(r, token), api(f"{r}/private-vulnerability-reporting", token),
                   api(f"{r}/rulesets", token), api(f"{r}/labels?per_page=100", token))
    drift = [x for x in rows if x[2] != "?" and x[1] != x[2]]
    unread = [x for x in rows if x[2] == "?"]
    lines = [f"# Repository settings: {len(drift)} drifted, {len(unread)} couldn't read", "",
             "Only an owner can change these, in the repository's Settings. Nothing was changed by this check.", "",
             "| Setting | Expected | Now | Why |", "|---|---|---|---|"]
    lines += [f"| {k} | {w} | {'couldn' + chr(39) + 't read' if h == '?' else h} | {why} |" for k, w, h, why in rows if (k, w, h, why) in drift + unread]
    report = "\n".join(lines) + ("\n\nEverything matches the baseline.\n" if not drift and not unread else "\n")
    if a.out:
        Path(a.out).write_text(report, encoding="utf-8")
    print(report)
    return 1 if drift else 0


if __name__ == "__main__":
    sys.exit(main())
