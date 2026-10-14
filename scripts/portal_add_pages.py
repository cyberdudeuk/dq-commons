"""Add the DQ assurance pages to the Unified Data Asset Portal artifact (audited, repeatable).

Usage: python scripts/portal_add_pages.py PORTAL_DIR ASSURANCE_HTML ATLAS_HTML EFFORT_HTML
- adds 'NDL collections assurance' (Explore) and 'Public sector DQ tooling atlas' (Reference)
  to the shared menu on every page, and as tiles on the hub
- builds the two new pages inside the portal shell (menu, breadcrumb, skip link)
- refreshes the CDA quality baseline page content with the starter-kit version
"""
import re
import sys
from pathlib import Path

portal, assurance, atlas, effort = map(Path, sys.argv[1:5])

NEW = {
    "GDS_NDL_Assurance.html": dict(src=assurance, area="Explore", area_id="area-explore", ic="🛡️",
        name="NDL collections assurance", blurb="All 84 NDL pages tested against DAM policy and DQ guidance.",
        after="GDS_NDL_Benchmark.html", pill="Analysis", acc="#5aa9ff", roles="cdo sro steward reviewer architect"),
    "GDS_DQ_Tooling_Atlas.html": dict(src=atlas, area="Reference", area_id="area-reference", ic="🔎",
        name="Public sector DQ tooling atlas", blurb="Data quality tools, standards and open code across government.",
        after="GDS_Solutions_Register.html", pill="Research", acc="#9b8cff", roles="architect steward cdo"),
}


def menu_link(fn, d):
    return (f'<a href="{fn}"><span class="ic" aria-hidden="true">{d["ic"]}</span><span><strong>{d["name"]}</strong>'
            f'<small>{d["blurb"]}</small></span></a>\n')


def add_menu(html):
    for fn, d in NEW.items():
        if f'href="{fn}"' in html.split('<nav class="up-menu"', 1)[-1].split("</nav>", 1)[0]:
            continue
        html = re.sub(r'(<a href="' + re.escape(d["after"]) + r'"[^>]*>.*?</a>\n)', lambda m: m.group(1) + menu_link(fn, d), html, count=1)
    return html


def add_tiles(html):
    for fn, d in NEW.items():
        if f'class="tile" href="{fn}"' in html:
            continue
        tile = (f'<a class="tile" href="{fn}" style="--acc:{d["acc"]}" data-roles="{d["roles"]}" data-text="{d["name"].lower()} '
                f'{d["blurb"].lower()} {d["pill"].lower()}"><span class="top"><span class="ic" aria-hidden="true">{d["ic"]}</span>'
                f'<span> <span class="pill">{d["pill"]}</span></span></span><h3>{d["name"]}</h3><p>{d["blurb"]}</p>'
                f'<span class="go" aria-hidden="true">Open ›</span></a>')
        html = re.sub(r'(<a class="tile" href="' + re.escape(d["after"]) + r'".*?</a>)', lambda m: m.group(1) + tile, html, count=1, flags=re.S)
    return html.replace("Showing all 17 pages.", "Showing all 19 pages.")


base = (portal / "GDS_Quality_Baseline.html").read_text(encoding="utf-8")
SHELL_START = base.index("<!--UP-SHELL-->")
SHELL_END = base.index("<!--UP-SHELL-->", SHELL_START + 1) + len("<!--UP-SHELL-->")
JS_START = base.index('<script id="up-shell-js">')


def page_from_shell(fn, d, content):
    head_and_shell = base[:SHELL_END]
    head_and_shell = head_and_shell.replace(' aria-current="page"', "").replace(' class="up-cur"', "")
    head_and_shell = add_menu(head_and_shell)
    head_and_shell = head_and_shell.replace(f'<a href="{fn}">', f'<a href="{fn}" aria-current="page">', 1)
    head_and_shell = re.sub(r'(<button type="button" aria-expanded="false")(>' + re.escape(d["area"].replace("&", "&amp;")) + "</button>)",
                            r'\1 class="up-cur"\2', head_and_shell, count=1)
    crumbs = (f'<div class="up-crumbs"><div class="up-in"><nav aria-label="Breadcrumb"><ol><li><a href="index.html">Portal home</a></li>'
              f'<li><a href="index.html#{d["area_id"]}">{d["area"]}</a></li><li aria-current="page">{d["name"]}</li></ol></nav></div></div>')
    head_and_shell = re.sub(r'<div class="up-crumbs">.*?</div></div>', lambda m: crumbs, head_and_shell, count=1, flags=re.S)
    return head_and_shell + "\n\n" + content + "\n\n" + base[JS_START:]


for fn, d in NEW.items():
    (portal / fn).write_text(page_from_shell(fn, d, d["src"].read_text(encoding="utf-8")), encoding="utf-8")

# refresh baseline page content, keeping its shell
new_base = base[:SHELL_END] + "\n\n" + effort.read_text(encoding="utf-8") + "\n\n" + base[JS_START:]
(portal / "GDS_Quality_Baseline.html").write_text(new_base, encoding="utf-8")

changed = []
for f in sorted(portal.glob("*.html")):
    t = f.read_text(encoding="utf-8")
    u = add_menu(t)
    if f.name == "index.html":
        u = add_tiles(u)
    if u != t or f.name in NEW or f.name == "GDS_Quality_Baseline.html":
        f.write_text(u, encoding="utf-8")
        changed.append(f.name)
print("changed:", ", ".join(changed))
