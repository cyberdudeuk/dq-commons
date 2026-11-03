#!/usr/bin/env python3
"""Print release notes for one version from knowledge/releases.yaml (used by the release workflow).

Usage: python3 scripts/release_notes.py 1.5.0
Exits 1 if the version isn't in the file, so a tag can't be released without notes.
"""
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
LABEL = {"new": "New", "changed": "Changed", "fixed": "Fixed", "removed": "Removed"}


def notes(version: str) -> str:
    rel = yaml.safe_load((ROOT / "knowledge" / "releases.yaml").read_text(encoding="utf-8"))["releases"]
    r = next((x for x in rel if str(x["version"]) == version), None)
    if r is None:
        raise SystemExit(f"Version {version} is not in knowledge/releases.yaml")
    out = [f"## {r['title']}", "", f"Released {r['date']}.", ""]
    for t in ("new", "changed", "fixed", "removed"):
        items = [i for i in r["items"] if i["type"] == t]
        if items:
            out += [f"### {LABEL[t]}", ""] + [f"- {i['text']}" for i in items] + [""]
    out += ["Full history: CHANGELOG.md. Code: MIT licence. Content: Open Government Licence v3.0."]
    return "\n".join(out)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    print(notes(sys.argv[1].lstrip("v")))
