#!/usr/bin/env python3
"""Provenance audit: find illustrative, placeholder or invented content and check it is registered.

Scans knowledge files, portal pages, rule templates and examples for markers such as example domains,
"illustrative", "made up", "invented", "dummy", "synthetic" and "placeholder". Every file with a marker must
be listed in knowledge/provenance.yaml (items[].where, a file or a folder), with a class and how it is shown.
Exit 1 if anything is unregistered, or if a registered item no longer exists.

    python scripts/audit_provenance.py            # report
    python scripts/audit_provenance.py --json     # machine-readable
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
SCAN = [("knowledge", "*.yaml"), ("portal/src/pages", "*.html"), ("rules/library", "*.yaml"), ("examples", "**/*.md")]
MARKER = re.compile(r"example\.(org|com)\b|\billustrative\b|made[- ]up|\binvented\b|\bdummy\b|\bsynthetic\b|\bplaceholders?\b|\blorem\b|\bfake\b", re.I)
# Text that mentions these words without being example content (markup attributes, the honesty rules themselves).
IGNORE = re.compile(r'placeholder="|::placeholder|nothing is invented|never invent|not invented|no invented|invented facts|'
                    r'"placeholder"|\.placeholder|placeholder:', re.I)
SKIP_FILES = {"knowledge/provenance.yaml"}


def scan() -> dict:
    hits: dict[str, list] = {}
    for folder, pattern in SCAN:
        base = ROOT / folder
        if not base.exists():
            continue
        for f in sorted(base.glob(pattern)):
            rel = f.relative_to(ROOT).as_posix()
            if rel in SKIP_FILES:
                continue
            for n, line in enumerate(f.read_text(encoding="utf-8").splitlines(), 1):
                clean = IGNORE.sub("", line)
                m = MARKER.search(clean)
                if m:
                    hits.setdefault(rel, []).append({"line": n, "marker": m.group(0)})
    return hits


def audit() -> dict:
    reg = yaml.safe_load((ROOT / "knowledge" / "provenance.yaml").read_text(encoding="utf-8"))
    items = reg["items"]
    wheres = [i["where"].rstrip("/") for i in items]
    hits = scan()
    covered = lambda rel: any(rel == w or rel.startswith(w + "/") for w in wheres)
    unregistered = {k: v for k, v in hits.items() if not covered(k)}
    missing = [w for w in wheres if not (ROOT / w).exists()]
    bad_class = [i["where"] for i in items if i["class"] not in reg["classes"]]
    counts: dict[str, int] = {}
    for i in items:
        counts[i["class"]] = counts.get(i["class"], 0) + 1
    return {"hits": hits, "unregistered": unregistered, "missing": missing, "bad_class": bad_class, "counts": counts,
            "ok": not unregistered and not missing and not bad_class}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    r = audit()
    if a.json:
        print(json.dumps(r, indent=2))
    else:
        print(f"Provenance audit: {len(r['hits'])} files with markers, {len(r['unregistered'])} unregistered, "
              f"{len(r['missing'])} registered paths missing.")
        for k, v in r["unregistered"].items():
            print(f"  unregistered: {k} (lines {', '.join(str(h['line']) for h in v[:8])}) - add it to knowledge/provenance.yaml")
        for w in r["missing"]:
            print(f"  missing: {w} is registered but no longer exists")
        for w in r["bad_class"]:
            print(f"  unknown class: {w}")
    return 0 if r["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
