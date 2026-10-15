"""Check every external link in the knowledge base and portal pages, and report broken ones.

Usage: python scripts/check_links.py [--out link-report.md] [--workers 8]
Exit code 1 if any link is broken (4xx/5xx or unreachable), so a scheduled workflow can raise an issue.
Some sites refuse automated requests (403/405); those are reported as "check by hand", not broken.
"""
from __future__ import annotations

import argparse
import concurrent.futures as cf
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
URL = re.compile(r"https://[^\s\"'<>)\]]+")
SKIP = ("https://fonts.googleapis.com", "https://fonts.gstatic.com", "https://cdnjs.cloudflare.com", "https://example.", "https://github.com/x/")


def collect() -> dict:
    found: dict = {}
    files = list((ROOT / "knowledge").rglob("*.yaml")) + list((ROOT / "knowledge").glob("*.csv")) + list((ROOT / "portal" / "src" / "pages").glob("*.html"))
    for f in files:
        for u in URL.findall(f.read_text(encoding="utf-8")):
            u = u.rstrip(".,;:`")
            if "${" in u or u.startswith(SKIP):
                continue
            found.setdefault(u, set()).add(str(f.relative_to(ROOT)))
    return found


def check(url: str) -> tuple:
    headers = {"User-Agent": "Public-Sector-DQ-Commons-link-checker/1.0 (+https://github.com/cyberdudeuk/dq-commons)"}
    for method in ("HEAD", "GET"):
        try:
            req = urllib.request.Request(url, method=method, headers=headers)
            with urllib.request.urlopen(req, timeout=20) as r:
                return url, r.status, "ok"
        except urllib.error.HTTPError as e:
            if method == "HEAD" and e.code in (403, 405, 429, 501):
                continue
            return url, e.code, "check by hand" if e.code in (401, 403, 429) else "broken"
        except Exception as e:  # noqa: BLE001 - network errors of any kind
            if method == "GET":
                return url, 0, f"unreachable ({type(e).__name__})"
    return url, 0, "unreachable"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="")
    ap.add_argument("--workers", type=int, default=8)
    a = ap.parse_args(argv)
    links = collect()
    with cf.ThreadPoolExecutor(a.workers) as ex:
        results = sorted(ex.map(check, links), key=lambda r: (r[2] == "ok", r[0]))
    if results and all(r[2].startswith("unreachable") for r in results):
        print(f"Network unavailable: none of the {len(results)} links could be reached, so this run can't tell broken links "
              "from a blocked network. Run it where the internet is reachable (the monthly GitHub workflow does).")
        return 0
    bad = [r for r in results if r[2] not in ("ok", "check by hand")]
    lines = [f"# Link check: {len(results)} links, {len(bad)} broken or unreachable", "", "| Status | Code | Link | Used in |", "|---|---|---|---|"]
    lines += [f"| {s} | {c} | {u} | {', '.join(sorted(links[u]))} |" for u, c, s in results if s != "ok"]
    report = "\n".join(lines) + "\n"
    if a.out:
        Path(a.out).write_text(report, encoding="utf-8")
    print(report)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
