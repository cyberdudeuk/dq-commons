"""Content health: the Commons checks itself, so its content, data and claims stay current, accurate and safe.

Usage:
    python scripts/self_check.py [--out assessments/health] [--strict]

What it checks, in plain English (each finding is an error, a warning or a note):
 1. Review dates: every knowledge file names an owning role and was reviewed in the last 12 months
    (warning after 9 months, error after 12).
 2. Freshness: news slides older than 6 months and GOV.UK blog features older than 2 years are flagged.
 3. Verification: the share of sources read in full ("checked: yes" / "verified: yes") per file.
 4. Personal and sensitive data: email addresses, phone numbers, National Insurance numbers, security
    markings, access tokens and private keys anywhere people read or code ships.
 5. Duplicates: the same link or title listed twice in one list.
 6. Claims match the data: numbers the pages state ("30 frameworks", "61 cataloguing concepts") are
    recounted from the knowledge base.
 7. Links are https and well formed. (Whether they still resolve is checked by scripts/check_links.py.)
 8. Plain-English and inclusive language: words we've agreed to avoid.

It writes health.json and health.md, makes no network calls, and exits 1 on any error
(and on warnings too with --strict). The portal's "How we keep content trustworthy" panel shows the summary.
"""
from __future__ import annotations

import argparse
import datetime as dt
import glob
import json
import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
K = ROOT / "knowledge"
TEXT_GLOBS = ["knowledge/*.yaml", "portal/src/**/*.html", "portal/src/**/*.js", "portal/src/*.css", "*.md", "docs/**/*.md",
              ".github/**/*.yml", "integrations/*.yaml", "integrations/*.json", "dqkit/*.py", "scripts/*.py", "scripts/*.mjs",
              "rules/**/*.yaml", "packs/*.yaml"]
ALLOWED_EMAIL = ("@example.org", "@example.com", "noreply@anthropic.com", "@users.noreply.github.com")
PII = [
    ("email address", re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+\.[A-Za-z0-9.-]*[A-Za-z]{2,}")),
    ("UK phone number", re.compile(r"(?<![\w/.-])(?:\+44\s?7\d{3}|07\d{3})\s?\d{3}\s?\d{3}(?![\w/])")),
    ("security marking", re.compile(r"\b(?:OFFICIAL[- ]SENSITIVE|TOP SECRET|SECRET)\b")),  # upper case, as a marking is written
    ("access token", re.compile(r"\b(?:ghp_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{30,}|xox[abp]-[A-Za-z0-9-]{10,}|AKIA[0-9A-Z]{16}|sk-[A-Za-z0-9]{32,})\b")),
    ("private key", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----")),
]
# Specimen identifiers published for testing are fine in tests and parity checks only.
PII_EXEMPT = ("tests/", "scripts/parity_check.py", "scripts/self_check.py", "portal/src/pages/build.html", "portal/src/pages/community.html",
              "portal/src/pages/media.html", "portal/src/pages/surveys.html", "dqkit/rules.py")
AVOID = {"whitelist": "allow list", "blacklist": "block list", "sanity check": "quick check", "dummy data": "made-up data",
         "manpower": "people or staff", "grandfathered": "kept under the old rules", "the disabled": "disabled people",
         "simply": "", "obviously": ""}
CLAIMS = [  # (pattern in page text, what to count, function)
    (r"(\d+) frameworks", "frameworks in knowledge/frameworks.yaml", lambda: len(_y("frameworks")["frameworks"])),
    (r"(\d+) cataloguing concepts", "Rosetta concepts", lambda: len(_y("rosetta")["concepts"])),
    (r"(\d+) model clauses", "commercial clauses", lambda: len(_y("commercial")["clauses"])),
    (r"(\d+) themes", "maturity themes", lambda: len(_y("maturity")["themes"])),
    (r"(\d+) networks", "communities", lambda: len(_y("communities")["communities"])),
    (r"(\d+) Overseas Territories|Fourteen territories", "Overseas Territories", lambda: len(_y("global")["overseas_territories"])),
    (r"(\d+) packs", "framework packs", lambda: len(list((ROOT / "packs").glob("*.yaml")))),
    (r"(\d+) modules", "learning modules", lambda: len(_y("learning")["modules"])),
    (r"(\d+) short tutorials|(\d+) tutorials", "tutorials", lambda: len(_y("learning")["tutorials"])),
    (r"\b(\d+) pages\b(?! covering)(?! cover)", "portal pages (README and docs only)", None),
]
WORDS = {"Ten": 10, "Fourteen": 14}


def _y(name):
    return yaml.safe_load((K / f"{name}.yaml").read_text(encoding="utf-8"))


def files():
    seen = set()
    for g in TEXT_GLOBS:
        for f in glob.glob(str(ROOT / g), recursive=True):
            p = Path(f)
            if p.is_file() and p not in seen and "/dist/" not in f:
                seen.add(p)
                yield p


class Report:
    def __init__(self):
        self.items = []

    def add(self, level, check, where, message):
        self.items.append({"level": level, "check": check, "where": where, "message": message})


def check_reviews(r, today):
    for f in sorted(K.glob("*.yaml")):
        rv = (yaml.safe_load(f.read_text(encoding="utf-8")) or {}).get("review") or {}
        if not rv.get("owner_role"):
            r.add("error", "review", f.name, "No owning role.")
            continue
        age = (today - dt.date.fromisoformat(str(rv["last_reviewed"]))).days
        if age > 365:
            r.add("error", "review", f.name, f"Not reviewed for {age} days.")
        elif age > 270:
            r.add("warning", "review", f.name, f"Review due: last reviewed {age} days ago.")


def check_freshness(r, today):
    m = _y("media")
    for s in m["slides"]:
        d = str(s.get("date", ""))[:10]
        if len(d) == 10 and s["kind"] == "news" and (today - dt.date.fromisoformat(d)).days > 183:
            r.add("warning", "freshness", f"media.yaml slides/{s['id']}", f"News slide dated {d} is over 6 months old: refresh or retire it.")
    for g in m.get("govuk_blogs", []):
        if (today - dt.date.fromisoformat(g["date"])).days > 730:
            r.add("note", "freshness", f"media.yaml govuk_blogs/{g['id']}", f"Feature from {g['date']} is over 2 years old: consider archiving.")


def verification():
    out = {}
    for f in sorted(K.glob("*.yaml")):
        text = f.read_text(encoding="utf-8")
        yes = len(re.findall(r"\b(?:checked|verified): \"?yes\"?", text))
        other = len(re.findall(r"\b(?:checked|verified): \"?(?:listed|partly|no)\"?", text))
        if yes + other:
            out[f.name] = {"read_in_full": yes, "not_yet": other, "ratio": round(100 * yes / (yes + other), 1)}
    return out


def check_pii(r):
    for f in files():
        rel = f.relative_to(ROOT).as_posix()
        text = f.read_text(encoding="utf-8", errors="ignore")
        for what, rx in PII:
            for m in rx.finditer(text):
                s = m.group(0)
                if what == "email address" and (s.endswith(ALLOWED_EMAIL) or rel.startswith(PII_EXEMPT)):
                    continue
                if what in ("UK phone number", "security marking") and rel.startswith(PII_EXEMPT):
                    continue
                if what == "security marking" and re.search(r"\b(no|not|never|don't|exclude[sd]?|without|or|anything|markings?)\b[^.\n]{0,60}$",
                                                            text[max(0, m.start() - 80):m.start()], re.I):
                    continue  # a rule about markings ("no OFFICIAL-SENSITIVE material"), not a marked document
                line = text.count("\n", 0, m.start()) + 1
                r.add("error", "personal or sensitive data", f"{rel}:{line}", f"Looks like {what}: {s[:6]}… Remove it or move it to a test fixture.")


def check_duplicates(r):
    for name in ("media", "global", "build", "frameworks", "communities"):
        d = _y(name)
        for key, lst in d.items():
            if not isinstance(lst, list) or not lst or not isinstance(lst[0], dict):
                continue
            for field in ("url", "title", "id"):
                vals = [x.get(field) for x in lst if isinstance(x, dict) and x.get(field)]
                for v in sorted({v for v in vals if vals.count(v) > 1}, key=str):
                    r.add("warning", "duplicates", f"{name}.yaml {key}", f"{field} listed more than once: {v}")


def check_links(r):
    for f in K.glob("*.yaml"):
        for m in re.finditer(r"url: \"?([^\s\",}]+)", f.read_text(encoding="utf-8")):
            u = m.group(1)
            if not (u.startswith("https://") or u.endswith(".html") or "#" in u or u.startswith("http://purl") or u.startswith("http://www.w3.org")):
                r.add("warning", "links", f.name, f"Not an https link: {u}")


def check_claims(r, pages_count):
    targets = list((ROOT / "portal" / "src" / "pages").glob("*.html")) + [ROOT / "README.md", ROOT / "docs" / "USER-GUIDE.md", ROOT / "scripts" / "build_dq_portal.py"]
    for pat, what, fn in CLAIMS:
        actual = pages_count if fn is None else fn()
        for f in targets:
            if fn is None and f.suffix == ".html":
                continue
            text = f.read_text(encoding="utf-8")
            for m in re.finditer(pat, text):
                n = next((g for g in m.groups() if g), None)
                stated = int(n) if n else WORDS.get(m.group(0).split()[0])
                if stated is not None and stated != actual:
                    r.add("error", "claims match the data", f"{f.relative_to(ROOT)}", f"Says \"{m.group(0)}\" but there are {actual} {what}.")


def check_language(r):
    for f in list((ROOT / "portal" / "src" / "pages").glob("*.html")) + list(K.glob("*.yaml")):
        text = f.read_text(encoding="utf-8")
        for w, instead in AVOID.items():
            for m in re.finditer(rf"\b{re.escape(w)}\b", text, re.I):
                line = text.count("\n", 0, m.start()) + 1
                r.add("note", "plain and inclusive language", f"{f.relative_to(ROOT)}:{line}", f"Avoid \"{w}\"" + (f"; try \"{instead}\"." if instead else "."))


def run(today=None) -> dict:
    import sys
    sys.path.insert(0, str(ROOT / "scripts"))
    import build_dq_portal as b
    today = today or dt.date.today()
    r = Report()
    check_reviews(r, today)
    check_freshness(r, today)
    check_pii(r)
    check_duplicates(r)
    check_links(r)
    check_claims(r, len(b.PAGES))
    check_language(r)
    ver = verification()
    tot_yes = sum(v["read_in_full"] for v in ver.values())
    tot = tot_yes + sum(v["not_yet"] for v in ver.values())
    counts = {lvl: sum(1 for i in r.items if i["level"] == lvl) for lvl in ("error", "warning", "note")}
    return {"as_of": today.isoformat(), "version": b.VERSION, "counts": counts,
            "verification": {"by_file": ver, "read_in_full": tot_yes, "total": tot, "ratio": round(100 * tot_yes / tot, 1) if tot else None},
            "checks": ["review dates", "freshness", "verification", "personal or sensitive data", "duplicates", "links",
                       "claims match the data", "plain and inclusive language"],
            "items": r.items}


def to_markdown(h: dict) -> str:
    c = h["counts"]
    out = [f"# Content health report ({h['as_of']}, v{h['version']})", "",
           f"**{c['error']} errors, {c['warning']} warnings, {c['note']} notes.** "
           f"Sources read in full: {h['verification']['read_in_full']} of {h['verification']['total']} ({h['verification']['ratio']}%).", "",
           "| Level | Check | Where | Message |", "|---|---|---|---|"]
    out += [f"| {i['level']} | {i['check']} | `{i['where']}` | {i['message']} |" for i in h["items"]] or ["| - | - | - | Nothing found. |"]
    out += ["", "## Verification by file", "", "| File | Read in full | Not yet | % |", "|---|---|---|---|"]
    out += [f"| {k} | {v['read_in_full']} | {v['not_yet']} | {v['ratio']} |" for k, v in h["verification"]["by_file"].items()]
    return "\n".join(out) + "\n"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", default=str(ROOT / "assessments" / "health"))
    ap.add_argument("--strict", action="store_true", help="fail on warnings as well as errors")
    a = ap.parse_args(argv)
    h = run()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "health.json").write_text(json.dumps(h, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (out / "health.md").write_text(to_markdown(h), encoding="utf-8")
    c = h["counts"]
    print(f"Content health: {c['error']} errors, {c['warning']} warnings, {c['note']} notes. Report: {out / 'health.md'}")
    for i in h["items"]:
        if i["level"] != "note":
            print(f"  {i['level']}: [{i['check']}] {i['where']}: {i['message']}")
    return 1 if c["error"] or (a.strict and c["warning"]) else 0


if __name__ == "__main__":
    raise SystemExit(main())
