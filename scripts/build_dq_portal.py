"""Build the Public Sector Data Quality Commons portal from the pipeline's latest results and the knowledge base.

Usage:
    python scripts/build_dq_portal.py [--results assessments/portfolio] [--out portal/dist]
                                      [--repo https://github.com/OWNER/REPO] [--artifact DIR]

What it does, in plain English:
1. Reads the latest pipeline results (portfolio.json, metadata-assessment.json, each asset's
   results and history).
2. Fills the portal's page templates (portal/src/pages/*.html) with those results, so every
   number on the portal comes from the same run.
3. Adds the shared top bar, skip link and footer to every page.
4. Writes a complete static website to portal/dist (GitHub Pages publishes this), with the
   result files under downloads/.
5. Optionally (--artifact DIR) writes a copy for a claude.ai artifact: the home page without its
   own <html>/<head> wrapper, and download links pointing to the GitHub repository instead.

It makes no network calls. Nothing here changes the results; it only presents them.
"""
from __future__ import annotations

import argparse
import csv
import html
import json
import re
import shutil
import subprocess
from datetime import date
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "portal" / "src"
VERSION = "1.0.0"
BRAND = "Public Sector Data Quality Commons"

# Navigation groups, in order, and the pages in each: (file stem, short label, description).
GROUPS = [
    ("Start", [
        ("index", "Home", "Start here: what the Commons does and routes by role and task"),
        ("about", "About the Commons", "Mission, aims, objectives, priorities, roadmap and wishlist"),
        ("guide", "User guide", "How to use the portal, guided tours and frequently asked questions"),
    ]),
    ("Do", [
        ("check", "Check your data", "Run the toolkit in your browser on a CSV file. Nothing is uploaded"),
        ("maturity", "Maturity self-assessment", "Where you are on 8 themes, from Beginning to Mastering, and next steps"),
        ("assistant", "AI assistant", "Plain English to tested rules, explanations and framework look-ups"),
        ("pipeline", "Pipeline status", "The latest automated run: trust levels, issues and escalations"),
    ]),
    ("Know", [
        ("frameworks", "Frameworks and standards", "30 frameworks and standards, crosswalks, packs and clause-by-clause comparison"),
        ("learn", "Learn", "Pathways by role, modules, tutorials and glossary"),
        ("ai", "AI for data quality", "Principles, use cases, vendor questions, worked examples and the route to reuse"),
        ("guidance", "Issues framework", "Prioritise issues with the government method, and the guidance findings"),
        ("tooling", "Tooling", "Data quality tools, standards and open code across government"),
        ("library", "Library and knowledge base", "Curated resources, how-to articles and resources shared by members"),
    ]),
    ("Govern", [
        ("commercial", "Buying and suppliers", "Supplier obligations, model contract clauses, KPIs, tender questions and exit"),
        ("legacy", "Legacy and modernisation", "Data debt, migration gates, MoSCoW, self-assessment and a reconciliation tool"),
        ("interop", "Interoperability and standards", "Identifiers, formats, data contracts, guardrails, measures and related capabilities"),
    ]),
    ("Scenarios", [
        ("scenarios", "All scenarios", "Pick your policy, sector or platform: what applies and where to start"),
        ("ndl-assurance", "National Data Library", "84 NDL data pages tested against GOV.UK requirements"),
        ("baseline", "Critical data asset baseline", "Effort to report data quality for every critical data asset"),
    ]),
    ("Community", [
        ("community", "Community", "Contributions library, wishlist, networks and how to get involved"),
        ("media", "Media centre", "Blog, vlog and podcasts about data quality, from the Commons and members"),
        ("surveys", "Surveys and commissions", "Take or run a data quality survey, or ask the Commons for help"),
        ("share", "Case studies", "Case studies, the tooling survey review, and messages to other teams"),
        ("operate", "Operating model and support", "Support tiers, roles, how requests become features, GitHub, Jira and Confluence"),
    ]),
]
PAGES = [p for _, ps in GROUPS for p in ps]
GROUP_OF = {p[0]: g for g, ps in GROUPS for p in ps}
DOWNLOAD_FILES = ["portfolio.json", "run-summary.md", "cda-return.csv", "escalations.json", "catalogue.dqv.jsonld",
                  "metadata-assessment.json"]


def git_sha() -> str:
    try:
        return subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, capture_output=True, text=True,
                              check=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return "unknown"


def js_json(obj) -> str:
    """JSON safe to place inside a <script> element."""
    return json.dumps(obj, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/").replace("<!--", "<\\!--")


# ---------- data for each page ----------

def ndl_data(results_dir: Path, port: dict) -> dict:
    """The NDL assurance page's data, rebuilt from the pipeline outputs (same shape as before)."""
    m = json.loads((results_dir / "metadata-assessment.json").read_text(encoding="utf-8"))
    pages = [{"c": p["collection"], "s": p["slug"], "t": p["title"], "p": p["provider"], "sc": p["score"], "r": p["rag"],
              "cov": p["cda_metadata_coverage"], "ev": {c["id"]: c["evidence"] for c in p["checks"]},
              "f": [c["id"] for c in p["checks"] if c["status"] == "fail"],
              "pa": [c["id"] for c in p["checks"] if c["status"] == "partial"]} for p in m["pages"]]
    checks = [{k: c[k] for k in ("id", "label", "source", "dimension", "issue_type", "applicable", "pass", "partial", "fail",
                                 "performance")}
              | {"priority": c["assessment"]["priority"], "target": c["assessment"]["target"],
                 "resolution": c["assessment"]["resolution"]} for c in m["checks"]]
    charts = []
    for a in port["assets"]:
        res = json.loads((results_dir / a["files"]["results"]).read_text(encoding="utf-8"))
        charts.append({"id": a["id"], "t": a["title"].split(": ", 1)[-1].capitalize(), "url": a.get("iri", ""),
                       "rows": res["rows"], "met": res["rules_met"], "tot": res["rules_total"],
                       "trust": res["trust"]["level"], "share": res["trust"]["sharing"],
                       "res": [{"id": r["id"], "d": r["description"], "dim": r["dimension"], "p": r["performance"],
                                "tg": r["assessment"]["target"], "m": r["assessment"]["meets_target"],
                                "pr": r["assessment"]["priority"], "det": r["detail"]} for r in res["results"]]})
    return {"as_of": m["as_of"], "mean": m["mean_score"], "cov": m["mean_cda_coverage"], "rag": m["rag"],
            "collections": m["collections"], "props": m["cda_property_coverage"], "checks": checks, "pages": pages,
            "charts": charts}


def history_series(results_dir: Path, port: dict) -> dict:
    """Per asset: [[date, rules met, rules measured]], from the history CSVs."""
    hdir = results_dir / port.get("files", {}).get("history", "history")
    out = {}
    for a in port["assets"]:
        p = hdir / f"{a['id']}.history.csv"
        by_date: dict = {}
        if p.exists():
            with open(p, newline="", encoding="utf-8") as f:
                for row in csv.DictReader(f):
                    t = by_date.setdefault(row["date"], [0, 0])
                    t[1] += 1
                    t[0] += str(row["meets_target"]).lower() == "true"
        out[a["id"]] = [[d, v[0], v[1]] for d, v in sorted(by_date.items())]
    return out


def vocab() -> dict:
    """The same vocabulary the parity check gives the browser engine."""
    import sys
    sys.path.insert(0, str(ROOT))
    from dqkit import dqv, rules
    return {"issue_types": rules.ISSUE_TYPES, "dimensions": dqv._dimensions()}


def examples(port_file: Path) -> list:
    """The portfolio's assets as ready-to-run examples for the in-browser checker."""
    doc = yaml.safe_load(port_file.read_text(encoding="utf-8"))
    base = port_file.parent
    out = []
    for e in doc["assets"]:
        rules_text = (base / e["rules"]).read_text(encoding="utf-8")
        spec = yaml.safe_load(rules_text)
        out.append({"id": spec["asset"]["id"], "title": spec["asset"].get("title", spec["asset"]["id"]).split(": ", 1)[-1],
                    "rules": rules_text, "csv": (base / e["data"]).read_text(encoding="utf-8-sig"),
                    "csv_name": Path(e["data"]).name, "rules_name": Path(e["rules"]).name})
    return out


def knowledge() -> dict:
    """Every knowledge-base file as a page placeholder (__K_NAME__). Built lazily, only if a page uses it."""
    import sys
    sys.path.insert(0, str(ROOT))
    from dqkit import packs, rules
    K = ROOT / "knowledge"
    y = lambda n: yaml.safe_load((K / f"{n}.yaml").read_text(encoding="utf-8"))
    with open(K / "requirements.csv", newline="", encoding="utf-8") as f:
        reqs = list(csv.DictReader(f))
    library = {}
    for f in sorted((ROOT / "rules" / "library").glob("*.yaml")):
        library[f.stem] = {"text": f.read_text(encoding="utf-8"), "spec": yaml.safe_load(f.read_text(encoding="utf-8"))}
    valuesets = {}
    for f in sorted(rules.VALUESET_DIR.glob("*.csv")):
        with open(f, newline="", encoding="utf-8") as fh:
            valuesets[f.stem] = list(csv.DictReader(fh))
    return {
        "FRAMEWORKS": lambda: y("frameworks")["frameworks"],
        "REQUIREMENTS": lambda: reqs,
        "COMMUNITIES": lambda: y("communities")["communities"],
        "LEARNING": lambda: y("learning"),
        "MATURITY": lambda: y("maturity"),
        "SURVEYS": lambda: y("surveys"),
        "AI": lambda: y("ai-for-dq"),
        "PACKS": lambda: packs.list_packs(),
        "CROSSWALK": lambda: packs.crosswalk_matrix(),
        "LIBRARY": lambda: library,
        "VALUESETS": lambda: valuesets,
        "SCHEMES": lambda: list(rules.IDENTIFIER_SCHEMES),
        "COMMERCIAL": lambda: y("commercial"),
        "LEGACY": lambda: y("legacy"),
        "INTEROP": lambda: y("interop"),
        "MEDIA": lambda: y("media"),
        "ARTICLES": lambda: y("articles"),
        "INTEGRATIONS": lambda: yaml.safe_load((ROOT / "integrations" / "config.yaml").read_text(encoding="utf-8")),
    }


# ---------- page assembly ----------

def nav(active: str, long: bool) -> str:
    """Grouped navigation. Desktop: one disclosure per group. Menu (narrow screens): every group listed."""
    out = []
    for g, ps in GROUPS:
        cur_g = any(stem == active for stem, _, _ in ps)
        links = "".join(
            f'<a href="{stem}.html"{" aria-current=\"page\"" if stem == active else ""}>{html.escape(label)}'
            f'<small>{html.escape(desc)}</small></a>' for stem, label, desc in ps)
        if long:
            out.append(f'<div class="dqp-grp"><h2>{g}</h2>{links}</div>')
        else:
            out.append(f'<details class="dqp-g"{" data-current" if cur_g else ""}><summary>{g}</summary>'
                       f'<div class="dqp-panel">{links}</div></details>')
    return "".join(out)


def split_fragment(text: str) -> tuple[str, str]:
    """Split a page fragment into head part (title, links, styles) and body part."""
    m = re.search(r"\n<(div|header|main|section)\b", text)
    if not m:
        raise ValueError("page fragment has no body element")
    return text[:m.start()], text[m.start():]


def assemble(stem: str, fragment: str, build_label: str, footer: str) -> tuple[str, str]:
    """Return (full document, artifact fragment) for one page."""
    shell = (SRC / "shell.html").read_text(encoding="utf-8")
    shell = (shell.replace("{{NAV}}", nav(stem, False)).replace("{{NAV_LONG}}", nav(stem, True))
             .replace("{{BUILD}}", build_label).replace("{{BRAND}}", BRAND).replace("{{GROUP}}", GROUP_OF.get(stem, "")))
    head, body = split_fragment(fragment)
    shell_css, shell_body = shell.split("</style>", 1)
    shell_css += "</style>"
    frag = f"{head}\n{shell_css}\n{shell_body}\n{body}\n{footer}\n"
    doc = ("<!doctype html>\n<html lang=\"en-GB\">\n<head>\n<meta charset=\"utf-8\">\n"
           "<meta name=\"viewport\" content=\"width=device-width,initial-scale=1,viewport-fit=cover\">\n"
           f"{head}\n{shell_css}\n</head>\n<body style=\"margin:0\">\n{shell_body}\n{body}\n{footer}\n</body>\n</html>\n")
    return doc, frag


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--results", default=str(ROOT / "assessments" / "portfolio"))
    ap.add_argument("--portfolio", default=str(ROOT / "portfolio.ndl.yaml"))
    ap.add_argument("--out", default=str(ROOT / "portal" / "dist"))
    ap.add_argument("--repo", default="https://github.com/cyberdudeuk/ndl-dq-assurance",
                    help="repository web address (proposed name; not yet pushed), used for source links and (in --artifact mode) downloads")
    ap.add_argument("--artifact", help="also write a claude.ai artifact copy to this folder")
    a = ap.parse_args(argv)

    results_dir, out = Path(a.results), Path(a.out)
    port = json.loads((results_dir / "portfolio.json").read_text(encoding="utf-8"))
    sha = git_sha()
    build_label = f"v{VERSION} · data as of {port['as_of']}"
    data = {
        "__NDL_DATA__": js_json(ndl_data(results_dir, port)),
        "__PORTFOLIO__": js_json(port),
        "__HISTORY__": js_json(history_series(results_dir, port)),
        "__VOCAB__": js_json(vocab()),
        "__EXAMPLES__": js_json(examples(Path(a.portfolio))),
        "__BASE_CSS__": (SRC / "base.css").read_text(encoding="utf-8"),
        "__ENGINE__": (SRC / "js" / "engine.js").read_text(encoding="utf-8").replace("</script", "<\\/script"),
        "__SHEETS__": (SRC / "js" / "sheets.js").read_text(encoding="utf-8").replace("</script", "<\\/script"),
        "__BUILD__": js_json({"version": VERSION, "sha": sha, "built": date.today().isoformat(), "as_of": port["as_of"],
                              "repo": a.repo}),
    }

    kb, kcache = knowledge(), {}

    def render(target: Path, download_base: str, artifact: bool):
        if target.exists():
            shutil.rmtree(target)
        target.mkdir(parents=True)
        footer = (f'<footer class="dqp-foot"><span>{BRAND} v{VERSION}</span>'
                  f'<span>Results measured as of {port["as_of"]}; built {date.today().isoformat()} from commit {sha}</span>'
                  f'<span>Code MIT, content OGL v3.0</span><span>A prototype public good service. Not an official government product.</span><a href="operate.html">Get help</a><a href="guide.html#accessibility">Accessibility</a>'
                  f'<a href="{html.escape(a.repo)}">Source code</a></footer>')
        for stem, _, _ in PAGES:
            text = (SRC / "pages" / f"{stem}.html").read_text(encoding="utf-8")
            text = text.replace("__DATA__", data["__NDL_DATA__"]) if stem == "ndl-assurance" else text
            for k, v in data.items():
                text = text.replace(k, v)
            for name in set(re.findall(r"__K_([A-Z]+)__", text)):
                if name not in kcache:
                    kcache[name] = js_json(kb[name]())
                text = text.replace(f"__K_{name}__", kcache[name])
            text = text.replace("__DOWNLOADS__", download_base)
            doc, frag = assemble(stem, text, build_label, footer)
            (target / f"{stem}.html").write_text(frag if (artifact and stem == "index") else doc, encoding="utf-8")
        if not artifact:
            dl = target / "downloads"
            (dl / "assets").mkdir(parents=True)
            for f in DOWNLOAD_FILES:
                if (results_dir / f).exists():
                    shutil.copy2(results_dir / f, dl / f)
            for f in (results_dir / "assets").iterdir():
                if f.suffix in (".xlsx", ".docx", ".md", ".csv", ".jsonld", ".json"):
                    shutil.copy2(f, dl / "assets" / f.name)
            (target / ".nojekyll").write_text("", encoding="utf-8")
        print(f"Built {len(PAGES)} pages in {target}")

    render(out, "downloads/", artifact=False)
    if a.artifact:
        rel = results_dir.resolve().relative_to(ROOT).as_posix()
        render(Path(a.artifact), f"{a.repo.rstrip('/')}/blob/main/{rel}/", artifact=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
