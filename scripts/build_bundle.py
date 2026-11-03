"""Build the solution build and development bundle: every mandated document in one standalone, navigable page.

Usage:
    python scripts/build_bundle.py [--out docs/bundle/index.html] [--artifact FILE] [--check]

What it does, in plain English:
1. Reads the product, architecture and delivery documents from the repository (README, PRD, theory of change,
   user research, equality screening, architecture, FTIR spec, build manifest, operations, operating model,
   Metadata Weaver, assurance routines, charter, change log, decisions and build log).
2. Converts them from Markdown to HTML with a small built-in converter (no extra packages), adds a contents
   sidebar, a search box, the version and commit, and print styles.
3. Writes a complete web page (docs/bundle/index.html). With --artifact it also writes a copy without the
   <html> wrapper, for publishing as a claude.ai page. With --check it fails if the committed page is out of date.

It makes no network calls. It only presents the documents; it never changes them.
"""
from __future__ import annotations

import argparse
import html
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

DOCS = [  # (group, file, short title)
    ("Overview", "README.md", "README"),
    ("Product", "docs/PRD.md", "Product requirements (PRD)"),
    ("Product", "docs/THEORY-OF-CHANGE.md", "Theory of change"),
    ("Product", "docs/USER-RESEARCH-BUNDLE.md", "User research bundle"),
    ("Product", "docs/EQUALITY-AND-DATA-PROTECTION-SCREENING.md", "Equality and data protection screening"),
    ("Architecture", "docs/ARCHITECTURE.md", "Architecture: SAD, HLD and LLD"),
    ("Architecture", "docs/FTIR-SPEC.md", "Functional, technical and integration requirements"),
    ("Architecture", "docs/METADATA-WEAVER.md", "Metadata Weaver: assessment and design"),
    ("Delivery", "docs/BUILD-MANIFEST.md", "Build manifest"),
    ("Delivery", "docs/OPERATIONS.md", "Operations"),
    ("Delivery", "docs/OPERATING-MODEL.md", "Operating model"),
    ("Delivery", "docs/ASSURANCE-ROUTINES.md", "Assurance routines"),
    ("Delivery", "docs/DQ-MANAGEMENT-PLAYBOOK.md", "Data quality management playbook"),
    ("Delivery", "CHARTER.md", "Co-design and contribution charter"),
    ("Records", "CHANGELOG.md", "Change log"),
    ("Records", "docs/DECISIONS.md", "Decision log"),
    ("Records", "docs/BUILD-LOG.md", "Build log"),
]


def _inline(s: str) -> str:
    s = html.escape(s, quote=False)
    s = re.sub(r"`([^`]+)`", lambda m: f"<code>{m.group(1)}</code>", s)
    s = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"(?<![\w*])\*([^*\n]+)\*(?!\w)", r"<em>\1</em>", s)
    s = re.sub(r"(?<!\w)_([^_\n]+)_(?!\w)", r"<em>\1</em>", s)

    def link(m):
        text, url = m.group(1), m.group(2).replace("&amp;", "&")
        if not re.match(r"^(https?://|#|mailto:)", url):
            url = "https://github.com/cyberdudeuk/dq-commons/blob/main/" + url.lstrip("./")
        return f'<a href="{html.escape(url)}">{text}</a>'
    return re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)", link, s)


def md_to_html(md: str, prefix: str) -> tuple[str, list]:
    """A small Markdown converter: headings, paragraphs, lists, tables, code blocks, quotes. Returns (html, headings)."""
    out, heads, lines, i = [], [], md.replace("\r\n", "\n").split("\n"), 0
    para: list = []

    def flush():
        if para:
            out.append("<p>" + _inline(" ".join(x.strip() for x in para)) + "</p>")
            para.clear()
    while i < len(lines):
        ln = lines[i]
        if ln.startswith("```"):
            flush()
            lang, code = ln[3:].strip(), []
            i += 1
            while i < len(lines) and not lines[i].startswith("```"):
                code.append(lines[i])
                i += 1
            note = '<p class="note">Diagram source (Mermaid). The Knowledge map shows the live, interactive version.</p>' if lang == "mermaid" else ""
            out.append(f'{note}<pre><code class="lang-{html.escape(lang)}">' + html.escape("\n".join(code)) + "</code></pre>")
            i += 1
            continue
        m = re.match(r"^(#{1,6})\s+(.*)$", ln)
        if m:
            flush()
            lvl, text = len(m.group(1)), m.group(2).strip()
            hid = f"{prefix}-{len(heads)}"
            heads.append((lvl, re.sub(r"[`*]", "", text), hid))
            out.append(f'<h{min(lvl + 1, 6)} id="{hid}">{_inline(text)}</h{min(lvl + 1, 6)}>')
            i += 1
            continue
        if ln.strip().startswith("|") and i + 1 < len(lines) and re.match(r"^\s*\|?\s*:?-{2,}", lines[i + 1]):
            flush()
            cells = lambda r: [c.strip() for c in r.strip().strip("|").split("|")]
            hdr, rows = cells(ln), []
            i += 2
            while i < len(lines) and lines[i].strip().startswith("|"):
                rows.append(cells(lines[i]))
                i += 1
            out.append('<div class="tbl"><table><thead><tr>' + "".join(f'<th scope="col">{_inline(c)}</th>' for c in hdr) + "</tr></thead><tbody>" +
                       "".join("<tr>" + "".join(f"<td>{_inline(c)}</td>" for c in r) + "</tr>" for r in rows) + "</tbody></table></div>")
            continue
        m = re.match(r"^(\s*)([-*]|\d+\.)\s+(.*)$", ln)
        if m:
            flush()
            ordered = m.group(2)[0].isdigit()
            items = []
            while i < len(lines):
                m2 = re.match(r"^(\s*)([-*]|\d+\.)\s+(.*)$", lines[i])
                if m2:
                    items.append([len(m2.group(1)), m2.group(3)])
                elif lines[i].startswith("  ") and lines[i].strip() and items:
                    items[-1][1] += " " + lines[i].strip()
                else:
                    break
                i += 1
            tag = "ol" if ordered else "ul"
            out.append(f"<{tag}>" + "".join(f'<li{" class=\"sub\"" if ind >= 2 else ""}>{_inline(t)}</li>' for ind, t in items) + f"</{tag}>")
            continue
        if ln.startswith(">"):
            flush()
            q = []
            while i < len(lines) and lines[i].startswith(">"):
                q.append(lines[i].lstrip("> "))
                i += 1
            out.append("<blockquote>" + _inline(" ".join(q)) + "</blockquote>")
            continue
        if not ln.strip():
            flush()
        else:
            para.append(ln)
        i += 1
    flush()
    return "\n".join(out), heads


CSS = """
:root{--bg:#f5f7f7;--surface:#fff;--sunk:#eef2f2;--fg:#17212b;--muted:#56636e;--line:#d6dddf;--accent:#0d6b6e;--accent-soft:#e1f0ef;--gold:#ffbf47}
@media (prefers-color-scheme: dark){:root:not([data-theme="light"]){--bg:#10171c;--surface:#172129;--sunk:#0c1216;--fg:#e5ecef;--muted:#9aa9b3;--line:#2b3a44;--accent:#4fb8b4;--accent-soft:#16312f;color-scheme:dark}}
:root[data-theme="dark"]{--bg:#10171c;--surface:#172129;--sunk:#0c1216;--fg:#e5ecef;--muted:#9aa9b3;--line:#2b3a44;--accent:#4fb8b4;--accent-soft:#16312f;color-scheme:dark}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--fg);font:15px/1.6 "Public Sans",system-ui,-apple-system,"Segoe UI",sans-serif}
a{color:var(--accent)}
.skip{position:absolute;left:-9999px}.skip:focus{left:16px;top:8px;background:var(--gold);color:#0b0c0c;padding:8px 12px;z-index:10}
.top{background:#0b4f52;color:#f2f7f7;padding:14px max(16px,env(safe-area-inset-left,0px));display:flex;gap:12px;align-items:center;flex-wrap:wrap}
.top svg{flex:none}
.top b{font-size:16px}.top small{display:block;color:#b9d6d5;font-size:12px}
.lay{display:grid;grid-template-columns:280px minmax(0,1fr);max-width:1240px;margin:0 auto;gap:28px;padding:20px max(16px,env(safe-area-inset-right,0px)) 60px max(16px,env(safe-area-inset-left,0px))}
@media (max-width:900px){.lay{grid-template-columns:minmax(0,1fr)}}
nav.side{position:sticky;top:12px;align-self:start;max-height:calc(100vh - 24px);overflow:auto;background:var(--surface);border:1px solid var(--line);border-radius:10px;padding:12px}
@media (max-width:900px){nav.side{position:static;max-height:none}}
nav.side h2{font-size:11.5px;letter-spacing:.09em;text-transform:uppercase;color:var(--muted);margin:12px 0 4px}
nav.side a{display:block;text-decoration:none;padding:4px 6px;border-radius:4px;font-size:14px;color:var(--fg)}
nav.side a:hover{background:var(--accent-soft)}
nav.side input{width:100%;font:inherit;padding:8px;border:1px solid var(--muted);border-radius:6px;background:var(--surface);color:var(--fg)}
main{min-width:0}
.intro{background:var(--surface);border:1px solid var(--line);border-left:5px solid var(--gold);border-radius:10px;padding:16px 18px;margin-bottom:20px}
.intro h1{font-family:"Source Serif 4",Georgia,serif;margin:0 0 6px;font-size:clamp(1.6rem,3vw,2.2rem)}
.doc{background:var(--surface);border:1px solid var(--line);border-radius:10px;padding:6px 22px 18px;margin-bottom:22px}
.doc .src{font-size:12.5px;color:var(--muted);margin:10px 0 0}
.doc h2{font-family:"Source Serif 4",Georgia,serif;font-size:1.55rem;margin:18px 0 8px}
.doc h3{font-size:1.15rem;margin:18px 0 6px}.doc h4,.doc h5,.doc h6{font-size:1rem;margin:14px 0 4px}
.tbl{overflow-x:auto;border:1px solid var(--line);border-radius:8px;margin:10px 0}
table{border-collapse:collapse;width:100%;font-size:14px}th,td{padding:7px 10px;border-bottom:1px solid var(--line);text-align:left;vertical-align:top}
th{background:var(--sunk);font-size:12px;text-transform:uppercase;letter-spacing:.05em;color:var(--muted)}
pre{background:var(--sunk);border:1px solid var(--line);border-radius:8px;padding:12px;overflow:auto;font-size:13px}
code{font-family:"JetBrains Mono",ui-monospace,Menlo,Consolas,monospace;font-size:.88em}
li.sub{margin-left:1.4em;list-style:circle}
blockquote{border-left:4px solid var(--accent);margin:10px 0;padding:6px 14px;background:var(--accent-soft)}
.note{font-size:13px;color:var(--muted);margin-bottom:4px}
.hide{display:none}
:focus-visible{outline:3px solid var(--gold);outline-offset:2px}
@media print{nav.side,.top{display:none}.lay{display:block}.doc{border:0;page-break-before:always}body{background:#fff;color:#000}}
"""

MARK = ('<svg width="34" height="34" viewBox="0 0 64 64" aria-hidden="true"><g fill="none" stroke="currentColor" stroke-width="3.6">'
        '<circle cx="32" cy="24.5" r="13"/><circle cx="23.2" cy="39.5" r="13"/><circle cx="40.8" cy="39.5" r="13"/></g>'
        '<circle cx="32" cy="34.6" r="7.4" fill="#ffbf47"/><path d="M28.4 34.8l2.6 2.6 4.8-5.2" fill="none" stroke="#0b0c0c" '
        'stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"/></svg>')


def build(sha: str) -> tuple[str, str]:
    import build_dq_portal as b
    sections, nav, group = [], [], None
    for k, (g, f, title) in enumerate(DOCS):
        p = ROOT / f
        if not p.exists():
            continue
        body, heads = md_to_html(p.read_text(encoding="utf-8"), f"d{k}")
        if g != group:
            nav.append(f"<h2>{html.escape(g)}</h2>")
            group = g
        nav.append(f'<a href="#doc{k}" data-doc="doc{k}">{html.escape(title)}</a>')
        sections.append(f'<article class="doc" id="doc{k}" aria-labelledby="doc{k}-h"><p class="src">{html.escape(g)} · <code>{html.escape(f)}</code></p>'
                        f'<h2 id="doc{k}-h" class="sr">{html.escape(title)}</h2>{body}</article>')
    rel = b.releases()[0]
    frag = f"""<title>DQ Commons Build Bundle</title>
<link rel="icon" type="image/svg+xml" href="{b.FAVICON}">
<style>{CSS}</style>
<a class="skip" href="#main">Skip to the documents</a>
<header class="top" role="banner">{MARK}<div><b>{html.escape(b.BRAND)}</b><small>Solution build and development bundle · version {html.escape(b.VERSION)} · commit {html.escape(sha)}</small></div></header>
<div class="lay">
<nav class="side" aria-label="Documents"><label for="f" style="font-weight:600;font-size:13px">Find in the bundle</label><input type="search" id="f" placeholder="For example: weaver, DPIA, D-055">
<p id="fn" style="font-size:12px;color:var(--muted)" role="status" aria-live="polite"></p>{"".join(nav)}</nav>
<main id="main" tabindex="-1">
<section class="intro" aria-labelledby="bt"><h1 id="bt">Solution build and development bundle</h1>
<p>Every product, architecture and delivery document for version <b>{html.escape(b.VERSION)}</b> ({html.escape(rel['title'])}, {html.escape(rel['date'])}), generated from the repository so it always matches the build. Code MIT, content OGL v3.0. Not an official government document.</p>
<p style="font-size:13px">Source of truth: <a href="https://github.com/cyberdudeuk/dq-commons">github.com/cyberdudeuk/dq-commons</a>. Regenerate with <code>python scripts/build_bundle.py</code>.</p></section>
{"".join(sections)}
</main></div>
<script>
(function () {{
  var f = document.getElementById("f"), docs = [].slice.call(document.querySelectorAll(".doc")), fn = document.getElementById("fn");
  f.addEventListener("input", function () {{
    var q = f.value.trim().toLowerCase(), n = 0;
    docs.forEach(function (d) {{ var hit = !q || d.textContent.toLowerCase().indexOf(q) >= 0; d.classList.toggle("hide", !hit);
      var a = document.querySelector('[data-doc="' + d.id + '"]'); if (a) a.classList.toggle("hide", !hit); if (hit) n++; }});
    fn.textContent = q ? n + " of " + docs.length + " documents mention that." : "";
  }});
}})();
</script>
"""
    frag = frag.replace('class="sr"', 'style="position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0,0,0,0)"')
    doc = ('<!doctype html>\n<html lang="en-GB">\n<head>\n<meta charset="utf-8">\n<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">\n'
           + frag.split("<a class=\"skip\"", 1)[0] + "</head>\n<body>\n<a class=\"skip\"" + frag.split("<a class=\"skip\"", 1)[1] + "</body>\n</html>\n")
    return doc, frag


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", default=str(ROOT / "docs" / "bundle" / "index.html"))
    ap.add_argument("--artifact", help="also write a copy without the <html> wrapper, for a claude.ai page")
    ap.add_argument("--check", action="store_true", help="fail if the committed bundle is out of date (ignores the commit id)")
    a = ap.parse_args(argv)
    import build_dq_portal as b
    doc, frag = build(b.git_sha())
    out = Path(a.out)
    strip = lambda t: re.sub(r"commit [0-9a-f]{4,40}|commit unknown", "commit", t)
    if a.check:
        ok = out.exists() and strip(out.read_text(encoding="utf-8")) == strip(doc)
        print("Bundle is current." if ok else "Bundle is out of date: run python scripts/build_bundle.py")
        return 0 if ok else 1
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(doc, encoding="utf-8")
    print("Wrote", out)
    if a.artifact:
        Path(a.artifact).write_text(frag, encoding="utf-8")
        print("Wrote", a.artifact)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
