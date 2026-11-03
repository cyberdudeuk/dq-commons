"""Fact sampling (quarterly routine): pick a random 5% of sourced claims for a person to re-check.

Usage: python scripts/sample_facts.py [--share 0.05] [--seed 2026Q4] [--out fact-sample.md]
Writes a checklist: each sampled item, the file it lives in and its source link. The quarterly workflow
opens it as a GitHub issue; the person checking ticks each item, notes any error, and the error rate is
recorded in the issue when it is closed. The seed defaults to the year and quarter, so a quarter's
sample can be reproduced.
"""
from __future__ import annotations

import argparse
import datetime as dt
import random
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
NAME = ("name", "title", "term", "label")


def claims() -> list:
    out = []
    def walk(node, f):
        if isinstance(node, dict):
            url = node.get("url") or node.get("source_url") or node.get("link")
            name = next((node[k] for k in NAME if isinstance(node.get(k), str)), None)
            if isinstance(url, str) and url.startswith("https://") and name:
                out.append((f, name, url))
            for v in node.values():
                walk(v, f)
        elif isinstance(node, list):
            for v in node:
                walk(v, f)
    for f in sorted((ROOT / "knowledge").glob("*.yaml")):
        walk(yaml.safe_load(f.read_text(encoding="utf-8")), f"knowledge/{f.name}")
    return out


def main(argv=None) -> int:
    today = dt.date.today()
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--share", type=float, default=0.05)
    ap.add_argument("--seed", default=f"{today.year}Q{(today.month - 1) // 3 + 1}")
    ap.add_argument("--out", default="")
    a = ap.parse_args(argv)
    all_claims = claims()
    n = max(5, round(len(all_claims) * a.share))
    pick = random.Random(a.seed).sample(all_claims, min(n, len(all_claims)))
    lines = [f"# Fact sampling {a.seed}: {len(pick)} of {len(all_claims)} sourced items", "",
             "For each item: open the source, check that what the Commons says matches it today, and tick it. If it doesn't,",
             "write what is wrong under the item and fix it in a pull request. When done, comment the error rate",
             "(items wrong ÷ items checked) and close this issue. The rate is reported in the next release notes.", ""]
    lines += [f"- [ ] **{name}** ({f}): {url}" for f, name, url in sorted(pick)]
    report = "\n".join(lines) + "\n"
    if a.out:
        Path(a.out).write_text(report, encoding="utf-8")
    print(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
