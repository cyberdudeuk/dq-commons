"""Export the portal's words for translators (Welsh, issue #6; community languages, issue #23).

Writes one CSV per language with every piece of visible text from the page sources and the plain English
summaries: an id, the page, the English text, an empty translation column, and a note. Translators fill the
translation column; scripts can then build translated pages. Machine translation must never be published
without review by a qualified translator.

Usage:
    python scripts/export_strings.py --lang cy            # Welsh: translation/cy.csv
    python scripts/export_strings.py --lang cy --stats    # just count words, for a quote
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import html
import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from build_dq_portal import PAGES  # noqa: E402

BLOCK = re.compile(r"<(h[1-6]|p|li|th|td|label|summary|button|figcaption|dt|dd|caption|legend|option)\b[^>]*>(.*?)</\1>", re.S)


def page_strings(stem: str) -> list:
    src = (ROOT / "portal" / "src" / "pages" / f"{stem}.html").read_text(encoding="utf-8")
    src = re.sub(r"<script\b.*?</script>|<style\b.*?</style>|<pre\b.*?</pre>|<code\b.*?</code>", " ", src, flags=re.S)
    out = []
    for m in BLOCK.finditer(src):
        inner = m.group(2)
        if re.search(r"<(p|li|h[1-6]|table|ul|ol)\b", inner):
            continue  # a container: its children are exported on their own
        text = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", "", inner))).strip()
        if len(text) > 1 and not re.fullmatch(r"[\d\W_]+", text) and "__" not in text and "${" not in text:
            out.append((m.group(1), text))
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--lang", required=True, help="language tag, e.g. cy (Welsh), pa (Punjabi), ur (Urdu), pl (Polish)")
    ap.add_argument("--out", default="")
    ap.add_argument("--stats", action="store_true")
    a = ap.parse_args(argv)
    rows, seen = [], set()
    easy = yaml.safe_load((ROOT / "knowledge" / "easy-read.yaml").read_text(encoding="utf-8"))["pages"]
    for stem, label, desc in PAGES:
        items = [("menu", label), ("menu", desc)] + page_strings(stem) + [("in-short", x) for x in easy.get(stem, [])]
        for kind, text in items:
            key = hashlib.sha1(f"{stem}|{text}".encode()).hexdigest()[:10]
            if key in seen:
                continue
            seen.add(key)
            rows.append({"id": f"{stem}.{key}", "page": stem, "kind": kind, "en": text, a.lang: "", "note": ""})
    words = sum(len(r["en"].split()) for r in rows)
    print(f"{len(rows)} strings, {words} words, {len(PAGES)} pages")
    if a.stats:
        return 0
    out = Path(a.out or ROOT / "translation" / f"{a.lang}.csv")
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["id", "page", "kind", "en", a.lang, "note"])
        w.writeheader()
        w.writerows(rows)
    print(f"Written {out.relative_to(ROOT) if out.is_relative_to(ROOT) else out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
