"""Record each page's sections at a release, so the portal can flag what is new or changed since.

The page drawer ("On this page") marks a section "New" if it did not exist at the baseline release
and "Updated" if its wording has changed. Run this once each release, after tagging, so the next
release's flags are measured from this one.

Usage:
    python scripts/section_baseline.py --ref v2.0.0 --since 2.0.0   # from a git tag or commit
    python scripts/section_baseline.py --since 2.1.0                # from the working copy
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import build_dq_portal as b  # noqa: E402


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--ref", help="git tag or commit to read the pages from (default: working copy)")
    ap.add_argument("--since", required=True, help="release number shown to readers, e.g. 2.0.0")
    a = ap.parse_args(argv)
    pages = {}
    for stem, _, _ in b.PAGES:
        rel = f"portal/src/pages/{stem}.html"
        if a.ref:
            r = subprocess.run(["git", "show", f"{a.ref}:{rel}"], cwd=ROOT, capture_output=True, text=True)
            if r.returncode != 0:
                continue  # page did not exist at that release: every section on it counts as new
            src = r.stdout
        else:
            src = (ROOT / rel).read_text(encoding="utf-8")
        pages[stem] = b.page_sections(src)
    b.BASELINE.write_text(json.dumps({"since": a.since, "pages": pages}, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Baseline for {len(pages)} pages written to {b.BASELINE.relative_to(ROOT)} (since {a.since})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
