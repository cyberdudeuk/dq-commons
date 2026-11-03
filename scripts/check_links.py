"""Check every external link in the knowledge base and portal pages, and report broken ones.

Usage: python scripts/check_links.py [--out link-report.md] [--workers 8] [--archive 40] [--diff .cache/source-hashes.json]
Exit code 1 if any link is broken (4xx/5xx or unreachable), so a scheduled workflow can raise an issue.
Some sites refuse automated requests (403/405); those are reported as "check by hand", not broken.

Archive snapshots (issue #20): every broken link in the report comes with its Internet Archive address,
so readers and maintainers can still reach the evidence. With --archive N, the run also asks the
Internet Archive to save up to N working links, a different slice each run, so over a few months every
source has a recent archived copy. Only public pages are sent; nothing personal is in the knowledge base.

Source diffing (routine "Source diffing"): with --diff FILE, the run keeps a fingerprint of each source's
visible text in FILE and lists the sources whose text changed since the last run, so the summaries that
cite them can be re-read. Pages that change constantly (news, search results) will show up often; the list
is a prompt to look, not proof that a summary is wrong.
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


ARCHIVE_VIEW = "https://web.archive.org/web/*/"
ARCHIVE_SAVE = "https://web.archive.org/save/"


def archive(urls: list, limit: int) -> str:
    """Ask the Internet Archive to save a rotating slice of working links. Best effort: failures are listed, not fatal."""
    import datetime
    import time
    if not urls or limit <= 0:
        return ""
    urls = sorted(urls)
    start = (datetime.date.today().toordinal() // 7 * limit) % len(urls)  # a different slice each week
    batch = (urls[start:] + urls[:start])[:limit]
    saved, failed = 0, []
    for u in batch:
        try:
            req = urllib.request.Request(ARCHIVE_SAVE + u, headers={"User-Agent": "Public-Sector-DQ-Commons-archiver/1.0 (+https://github.com/cyberdudeuk/dq-commons)"})
            with urllib.request.urlopen(req, timeout=60):
                saved += 1
        except Exception as e:  # noqa: BLE001 - the archive rate-limits; try again next run
            failed.append(f"{u} ({type(e).__name__})")
        time.sleep(6)
    out = f"## Archive snapshots\n\nAsked the Internet Archive to save {len(batch)} of {len(urls)} working links: {saved} accepted."
    if failed:
        out += " Not accepted this time (tried again on a later run): " + "; ".join(failed[:10]) + ("…" if len(failed) > 10 else "")
    return out


def fingerprint(url: str) -> tuple:
    import hashlib
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Public-Sector-DQ-Commons-link-checker/1.0 (+https://github.com/cyberdudeuk/dq-commons)"})
        with urllib.request.urlopen(req, timeout=20) as r:
            text = r.read(2_000_000).decode("utf-8", "ignore")
    except Exception:  # noqa: BLE001
        return url, None
    text = re.sub(r"<(script|style|noscript)\b.*?</\1>|<[^>]+>", " ", text, flags=re.S | re.I)
    return url, hashlib.sha256(re.sub(r"\s+", " ", text).strip().encode()).hexdigest()[:16]


def diff_sources(urls: list, path: str, workers: int) -> str:
    import json
    f = Path(path)
    old = json.loads(f.read_text(encoding="utf-8")) if f.exists() else {}
    with cf.ThreadPoolExecutor(workers) as ex:
        now = {u: h for u, h in ex.map(fingerprint, urls) if h}
    changed = sorted(u for u, h in now.items() if u in old and old[u] != h)
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(json.dumps({**old, **now}, indent=0, sort_keys=True), encoding="utf-8")
    if not old:
        return f"## Source diffing\n\nFirst run: recorded fingerprints for {len(now)} sources. Changes are reported from the next run."
    return (f"## Source diffing\n\n{len(changed)} of {len(now)} sources changed since the last run. Re-read the summaries that cite them:\n\n"
            + "\n".join(f"- {u} (used in {', '.join(sorted(LINKS[u]))})" for u in changed[:60]))


LINKS: dict = {}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="")
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--archive", type=int, default=0, help="ask the Internet Archive to save up to N working links")
    ap.add_argument("--diff", default="", help="file of source fingerprints to compare with and update")
    a = ap.parse_args(argv)
    links = collect()
    LINKS.update(links)
    with cf.ThreadPoolExecutor(a.workers) as ex:
        results = sorted(ex.map(check, links), key=lambda r: (r[2] == "ok", r[0]))
    if results and all(r[2].startswith("unreachable") for r in results):
        print(f"Network unavailable: none of the {len(results)} links could be reached, so this run can't tell broken links "
              "from a blocked network. Run it where the internet is reachable (the monthly GitHub workflow does).")
        return 0
    bad = [r for r in results if r[2] not in ("ok", "check by hand")]
    lines = [f"# Link check: {len(results)} links, {len(bad)} broken or unreachable", "",
             "| Status | Code | Link | Archived copies | Used in |", "|---|---|---|---|---|"]
    lines += [f"| {s} | {c} | {u} | [Internet Archive]({ARCHIVE_VIEW}{u}) | {', '.join(sorted(links[u]))} |" for u, c, s in results if s != "ok"]
    if a.archive:
        lines += ["", archive([u for u, c, s in results if s == "ok"], a.archive)]
    if a.diff:
        lines += ["", diff_sources([u for u, c, s in results if s == "ok"], a.diff, a.workers)]
    report = "\n".join(lines) + "\n"
    if a.out:
        Path(a.out).write_text(report, encoding="utf-8")
    print(report)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
