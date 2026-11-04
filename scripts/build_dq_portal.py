"""Build the Public Sector Data Quality Commons portal from the pipeline's latest results and the knowledge base.

Usage:
    python scripts/build_dq_portal.py [--results assessments/portfolio] [--out portal/dist]
                                      [--repo https://github.com/OWNER/REPO]

What it does, in plain English:
1. Reads the latest pipeline results (portfolio.json, metadata-assessment.json, each asset's
   results and history).
2. Fills the portal's page templates (portal/src/pages/*.html) with those results, so every
   number on the portal comes from the same run.
3. Adds the shared top bar, skip link and footer to every page.
4. Writes a complete static website to portal/dist (GitHub Pages publishes this), with the
   result files under downloads/.
5. Reads public GitHub issue data once (issue numbers, states, votes, published contributions, survey and
   maturity totals) so the portal works on GitHub alone, with no other service (D-GH-01, D-GH-02).

Apart from that one read of GitHub, it makes no network calls; offline it falls back to links. Nothing here changes the results; it only presents them.
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
# The version comes from the latest entry in knowledge/releases.yaml (the single source for releases).
VERSION = str(yaml.safe_load((ROOT / "knowledge" / "releases.yaml").read_text(encoding="utf-8"))["releases"][0]["version"])
BRAND = "Public Sector Data Quality Commons"

# Navigation groups in journey order: how people typically explore, from first visit to contributing.
# Each page also carries a level (Beginner, Intermediate, Advanced) shown as a badge in the menu.
GROUPS = [
    ("1 Start", [
        ("index", "Home", "Start here: what the Commons does, with routes by role and task"),
        ("github", "New to GitHub?", "What GitHub is, how the portal and its repository connect, and what you can do there"),
        ("about", "About the Commons", "Background, why it exists, purpose, aims, goals, objectives and desired outcomes"),
        ("guide", "User guide", "How to use the portal, guided tours and frequently asked questions"),
        ("roles", "For your role", "What CDO Council, CDOs, data owners, stewards, quality leads and others need, decide and should watch, and the gap register"),
        ("accessibility", "Accessibility and privacy", "Accessibility statement, known problems, and what happens to anything you share"),
    ]),
    ("2 Learn", [
        ("learn", "Learn", "Pathways by role, modules, tutorials and glossary"),
        ("professions", "Across the professions", "Where data quality sits in every profession's capability framework, in the UK nations and internationally"),
        ("training", "Skills and training", "Skills check against your role, a development plan and a catalogue of courses and qualifications"),
        ("knowledge", "Knowledge map", "Glossary, thesaurus, data dictionary, taxonomies, ontology and an interactive knowledge graph with lineage"),
        ("library", "Library and knowledge base", "Curated resources, how-to articles and resources shared by members"),
        ("media", "Media centre", "Blog, vlog and podcasts about data quality, from the Commons and members"),
        ("events", "Events", "Data quality conferences, workshops, courses and forums, with calendar downloads"),
    ]),
    ("3 Check", [
        ("check", "Check your data", "Run the toolkit in your browser on a CSV file. Nothing is uploaded"),
        ("maturity", "Maturity self-assessment", "Where you are on 8 themes, from Beginning to Mastering, and next steps"),
        ("guidance", "Issues framework", "Prioritise issues with the government method: a live calculator"),
        ("assistant", "Rules assistant", "Plain English to tested rules in your browser, plus framework and scoring look-ups"),
        ("baseline", "Critical data asset baseline", "Effort to report data quality for every critical data asset, to your own deadline"),
    ]),
    ("4 Improve", [
        ("playbook", "Data quality management playbook", "Eight stages to manage the quality of critical data assets: steps, checklists, roles, templates and the DAM policy, usable anywhere"),
        ("frameworks", "Frameworks and standards", "30 frameworks and standards, crosswalks, packs and clause-by-clause comparison"),
        ("tooling", "Tooling", "Data quality tools, standards and open code across government"),
        ("ai", "AI for data quality", "Principles, use cases, vendor questions, worked examples and the route to reuse"),
        ("commercial", "Buying and suppliers", "Supplier obligations, model contract clauses, KPIs, tender questions and exit"),
        ("legacy", "Legacy and modernisation", "Data debt, migration gates, MoSCoW, self-assessment and a reconciliation tool"),
        ("interop", "Interoperability and standards", "Identifiers, formats, data contracts, guardrails, measures and related capabilities"),
        ("weaver", "Metadata Weaver", "Turn one metadata record into DCAT, schema.org, CKAN, ODCS and CDA, and see the gaps"),
        ("models", "Capability and data models", "The data quality capability as data models, a Visio process map and BPMN workflows, for enterprise architecture tools"),
        ("pipeline", "Pipeline status", "The latest automated run: trust levels, issues and escalations"),
    ]),
    ("5 Apply", [
        ("scenarios", "All scenarios", "Pick your policy, sector or platform: what applies and where to start"),
        ("global", "UK and the world", "Crown Dependencies, Overseas Territories, the Commonwealth and international partners"),
        ("ndl-assurance", "National Data Library", "84 NDL data pages tested against GOV.UK requirements"),
    ]),
    ("6 Contribute", [
        ("community", "Community", "Contributions library, wishlist, networks and how to get involved"),
        ("share", "Case studies", "Draft case studies from measured results, to share what worked"),
        ("surveys", "Surveys and commissions", "Take or run a data quality survey, or ask the Commons for help"),
        ("build", "Help us build this", "Roadmap, backlog, wishlist, co-design charter, contributors and how to contact us"),
        ("operate", "Operating model and support", "Support tiers, roles, how requests become features, GitHub, Jira and Confluence"),
    ]),
]
# Full group titles, shown in the menu panel and in each page's breadcrumb.
GROUP_TITLE = {"1 Start": "Get started", "2 Learn": "Learn and build skills", "3 Check": "Check and assess",
               "4 Improve": "Manage and improve", "5 Apply": "Apply to your context", "6 Contribute": "Contribute and get help"}
LEVEL = {**{s: "Beginner" for s in ["index", "github", "about", "guide", "roles", "accessibility", "learn", "library", "media", "events",
                                    "check", "maturity", "scenarios", "community", "surveys", "operate"]},
         **{s: "Intermediate" for s in ["professions", "training", "knowledge", "guidance", "assistant", "baseline", "playbook",
                                        "frameworks", "tooling", "ai", "commercial", "global", "share", "build"]},
         **{s: "Advanced" for s in ["legacy", "interop", "weaver", "models", "pipeline", "ndl-assurance"]}}
PAGES = [p for _, ps in GROUPS for p in ps]
# Decorative icons from portal/src/icons.svg, for each menu group and page.
GROUP_ICON = {"1 Start": "compass", "2 Learn": "grad", "3 Check": "check", "4 Improve": "shield", "5 Apply": "map", "6 Contribute": "heart"}
PAGE_ICON = {"index": "home", "about": "info", "guide": "book", "accessibility": "access", "check": "check", "maturity": "gauge",
             "assistant": "sparkle", "weaver": "weave", "pipeline": "pulse", "frameworks": "layers", "learn": "grad", "ai": "cpu",
             "guidance": "flag", "tooling": "wrench", "library": "library", "commercial": "contract", "legacy": "history",
             "interop": "link", "scenarios": "map", "global": "globe", "ndl-assurance": "database", "baseline": "target",
             "community": "users", "media": "mic", "events": "calendar", "training": "grad", "knowledge": "globe", "surveys": "clipboard", "share": "quote", "build": "blocks", "operate": "lifebuoy", "playbook": "workflow", "roles": "users", "github": "repo", "professions": "blocks", "models": "steps"}


def icon(name: str) -> str:
    return f'<svg class="dqi" aria-hidden="true" focusable="false"><use href="#i-{name}"/></svg>'


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


def stakeholders() -> dict:
    """Roles, key dates and the gap register for the For your role page."""
    return yaml.safe_load((ROOT / "knowledge" / "stakeholders.yaml").read_text(encoding="utf-8"))


def knowledge_graph() -> dict:
    """The knowledge graph (dqkit/graph.py) for the Knowledge map page: nodes, edges and counts."""
    import sys
    sys.path.insert(0, str(ROOT))
    from dqkit import graph
    g = graph.build()
    return {"nodes": g["nodes"], "edges": g["edges"], "stats": g["stats"]}


def weaver_fields() -> list:
    import sys
    sys.path.insert(0, str(ROOT))
    from dqkit import weaver
    return weaver.fields()


def health_summary() -> dict:
    """The content health report's summary (scripts/self_check.py), for the portal."""
    import sys
    sys.path.insert(0, str(ROOT / "scripts"))
    import self_check
    h = self_check.run()
    return {"as_of": h["as_of"], "counts": h["counts"], "verification": {k: h["verification"][k] for k in ("read_in_full", "total", "ratio")},
            "checks": h["checks"], "open": [i for i in h["items"] if i["level"] != "note"][:20]}


def models_summary() -> dict:
    """The capability model (models/dq-capability.yaml) for the Capability and data models page."""
    m = yaml.safe_load((ROOT / "models" / "dq-capability.yaml").read_text(encoding="utf-8"))
    files = sorted(p.relative_to(ROOT / "models" / "out").as_posix() for p in (ROOT / "models" / "out").rglob("*") if p.is_file())
    previews = sorted(p.name for p in (ROOT / "models" / "previews").glob("map-*.png")) if (ROOT / "models" / "previews").exists() else []
    return {"name": m["name"], "version": m["version"], "review": m["review"], "guidance": m["guidance"], "principles": m["principles"],
            "capabilities": m["capabilities"], "enums": m["enums"],
            "entities": [{k: e[k] for k in ("name", "group", "description", "guidance")} | {"attributes": e["attributes"]} for e in m["entities"]],
            "processes": [{"id": p["id"], "name": p["name"], "capability": p["capability"], "lanes": p["lanes"],
                           "steps": [{k: s.get(k) for k in ("id", "kind", "name", "lane", "guidance", "outputs", "branches", "next")} for s in p["steps"]]} for p in m["processes"]],
            "files": files, "previews": previews,
            "extras": [f for f in ("dq-data-model.svg", "dq-capability-process-map.pdf") if (ROOT / "models" / f).exists()]}


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
        "MODELS": lambda: models_summary(),
        "MEDIA": lambda: y("media"),
        "ROSETTA": lambda: y("rosetta"),
        "ARTICLES": lambda: y("articles"),
        "GLOBAL": lambda: y("global"),
        "COMMUNITY": lambda: {**github_live()["community"], "read": github_live()["read"]},
        "BUILD": lambda: (lambda b: {**b, "roadmap": roadmap(b["backlog"]), "github_live": github_live()})(y("build")),
        "HEALTH": lambda: health_summary(),
        "EVENTS": lambda: y("events"),
        "PLAYBOOK": lambda: y("playbook"),
        "EFFORT": lambda: y("effort"),
        "STAKEHOLDERS": lambda: stakeholders(),
        "PROFESSIONS": lambda: y("professions"),
        "RELEASES": lambda: y("releases"),
        "TRAINING": lambda: y("training"),
        "GRAPH": lambda: knowledge_graph(),
        "ONTOLOGY": lambda: {**{k: v for k, v in y("ontology").items() if k != "review"}, "weaver_fields": weaver_fields()},
        "INTEGRATIONS": lambda: yaml.safe_load((ROOT / "integrations" / "config.yaml").read_text(encoding="utf-8")),
    }


# ---------- live GitHub data, read at build time (D-GH-01) ----------
# The portal never calls GitHub from a visitor's browser (D-POL-01). The build reads public issue data once,
# so the backlog shows each item's issue, state and votes (thumbs-up reactions), and the wishlist works on
# GitHub Pages too. If GitHub can't be reached (offline builds), the portal links to searches instead.
_GH_CACHE: dict = {}


def github_live() -> dict:
    if "v" in _GH_CACHE:
        return _GH_CACHE["v"]
    import os
    import urllib.request
    repo = REPO[0].replace("https://github.com/", "")
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    def get(path):
        req = urllib.request.Request(f"https://api.github.com/repos/{repo}/{path}", headers={
            "Accept": "application/vnd.github+json", "User-Agent": "dq-commons-portal-build", **({"Authorization": f"Bearer {token}"} if token else {})})
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.loads(r.read())
    out = {"backlog": {}, "wishes": [], "read": "", "community": community([])}
    try:
        extra = []
        for label in ("published", "survey-response", "maturity-share"):
            for page in range(1, 11):
                rows = get(f"issues?labels={label}&state=all&per_page=100&page={page}")
                extra += rows
                if len(rows) < 100:
                    break
        out["community"] = community(extra)
        for label in ("backlog", "wishlist"):
            for i in get(f"issues?labels={label}&state=all&per_page=100"):
                if i.get("pull_request"):
                    continue
                row = {"n": i["number"], "state": i["state"], "votes": (i.get("reactions") or {}).get("+1", 0),
                       "comments": i.get("comments", 0), "milestone": (i.get("milestone") or {}).get("title", "")}
                if label == "backlog" and i["title"].startswith("[BL-"):
                    out["backlog"][i["title"][1:].split("]")[0]] = row
                elif label == "wishlist" and i["state"] == "open":
                    out["wishes"].append({**row, "title": re.sub(r"^\[Wish\]\s*", "", i["title"])})
        out["wishes"].sort(key=lambda w: (-w["votes"], w["n"]))
        out["read"] = date.today().isoformat()
    except Exception as e:  # noqa: BLE001 - offline or rate-limited: the portal falls back to links
        print(f"GitHub data not read ({type(e).__name__}); the portal will link to GitHub instead.")
    _GH_CACHE["v"] = out
    return out


# ---------- community data from GitHub issue forms (D-GH-02) ----------
# Everything people send through the portal arrives as a GitHub issue form. At build time the portal reads:
#  - contributions, events and media a moderator has labelled "published" (and not "withdrawn");
#  - survey answers ("survey-response") and maturity levels ("maturity-share"), counted into totals with any
#    count under 5 hidden. Only structured answers are counted; nothing personal is read or kept.
SUPPRESS = 5
NO_RESPONSE = ("_No response_", "None of these")


def parse_form(body: str) -> dict:
    """GitHub renders an issue form as '### Label' then the answer. Returns {label: answer}."""
    out, cur = {}, None
    for line in (body or "").splitlines():
        if line.startswith("### "):
            cur = line[4:].strip()
            out[cur] = []
        elif cur is not None:
            out[cur].append(line)
    return {k: "\n".join(v).strip() for k, v in out.items()}


def form_labels(template: str) -> dict:
    """label -> field id for one issue form."""
    f = ROOT / ".github" / "ISSUE_TEMPLATE" / template
    if not f.exists():
        return {}
    return {b["attributes"]["label"]: b["id"] for b in yaml.safe_load(f.read_text(encoding="utf-8"))["body"] if b.get("id")}


def details(text: str) -> dict:
    d = {}
    for line in (text or "").splitlines():
        k, sep, v = line.partition(":")
        if sep and v.strip() and v.strip().lower() != "not stated":
            d[k.strip().lower()] = v.strip()
    return d


def community(issues: list) -> dict:
    """Published contributions, survey totals and the maturity benchmark, from issue data."""
    contrib_ids = form_labels("5-contribution.yml")
    items, surveys, shares = [], {}, []
    S = yaml.safe_load((ROOT / "knowledge" / "surveys.yaml").read_text(encoding="utf-8"))
    M = yaml.safe_load((ROOT / "knowledge" / "maturity.yaml").read_text(encoding="utf-8"))
    for i in issues:
        labels = {l["name"] for l in i.get("labels", [])}
        if "withdrawn" in labels or i.get("pull_request"):
            continue
        f = parse_form(i.get("body"))
        if "published" in labels and "contribution" in labels:
            v = {contrib_ids.get(k, k): ("" if a in NO_RESPONSE else a) for k, a in f.items()}
            d = details(v.get("details", ""))
            link = v.get("link", "")
            items.append({"n": i["number"], "type": v.get("kind", "Resource or link"), "title": re.sub(r"^\[[^\]]+\]\s*", "", i["title"]),
                          "summary": v.get("summary", "")[:2000], "link": link if link.startswith("https://") else "",
                          "org": d.get("credit as", ""), "sector": d.get("sector") or d.get("topics", ""), "nation": d.get("nation or region", ""),
                          "licence": d.get("licence", ""), "published": (i.get("closed_at") or i.get("updated_at") or "")[:10],
                          "start": d.get("starts", ""), "end": d.get("ends", ""), "where": d.get("where", ""), "cost": d.get("cost", ""),
                          "accessibility": d.get("accessibility", ""), "access": d.get("captions or transcript", "")})
        if "survey-response" in labels:
            sid = next((l.split(":", 1)[1] for l in labels if l.startswith("survey:")), None)
            sv = next((x for x in S["surveys"] if x["id"] == sid), None)
            if sv:
                ids = {q["q"]: q for q in sv["questions"]}
                surveys.setdefault(sid, []).append({ids[k]["id"]: a for k, a in f.items() if k in ids and a not in NO_RESPONSE[:1]})
        if "maturity-share" in labels:
            names = {t["name"]: t["id"] for t in M["themes"]}
            row = {"org_type": f.get(S["shared"]["org_type"]["q"], ""), "nation": f.get(S["shared"]["nation"]["q"], ""), "levels": {}}
            for k, a in f.items():
                if k in names and a[:1].isdigit():
                    row["levels"][names[k]] = int(a[:1])
            if len(row["levels"]) == len(M["themes"]):
                shares.append(row)
    out_s = {}
    for sv in S["surveys"]:
        rows = surveys.get(sv["id"], [])
        agg = {"n": len(rows), "q": {}}
        for q in sv["questions"]:
            if q["type"] in ("text", "long"):
                continue
            c: dict = {}
            for r in rows:
                for val in ([x.strip() for x in r.get(q["id"], "").split(",")] if q["type"] == "multi" else [r.get(q["id"], "")]):
                    val = "None" if val == "None of these" else val
                    if val and val != "Don't know":
                        c[val] = c.get(val, 0) + 1
            agg["q"][q["id"]] = {k: (None if v < SUPPRESS else v) for k, v in c.items()}
        out_s[sv["id"]] = agg
    def avg(rs):
        return {t["id"]: round(sum(r["levels"][t["id"]] for r in rs) / len(rs), 1) for t in M["themes"]}
    bench = {"n": len(shares), "groups": {}}
    if len(shares) >= SUPPRESS:
        bench["groups"]["all"] = {"label": "All organisations", "n": len(shares), "themes": avg(shares)}
    for key, prefix in (("org_type", "org:"), ("nation", "nation:")):
        g: dict = {}
        for r in shares:
            g.setdefault(r[key], []).append(r)
        for k, rs in g.items():
            if k and len(rs) >= SUPPRESS:
                bench["groups"][prefix + k] = {"label": k, "n": len(rs), "themes": avg(rs)}
    items.sort(key=lambda x: x["published"], reverse=True)
    return {"contributions": items, "surveys": out_s, "maturity": bench}


def roadmap(backlog: list) -> list:
    """The roadmap, worked out from backlog statuses with the same rule as the GitHub milestones
    (scripts/backlog_to_issues.py stage()), so the two can never disagree."""
    def stage(b):
        if b["status"] == "done":
            return "Done"
        if b["status"] == "in-progress":
            return "Now"
        return "Next" if b["moscow"] in ("must", "should") else "Later"
    labels = {"Now": "Being built, or prepared and waiting on people", "Next": "Must and should items", "Later": "Could items",
              "Done": f"Delivered by v{VERSION}"}
    return [{"stage": st, "label": labels[st], "items": [{"id": b["id"], "title": b["title"], "needs_people": "needs" in str(b.get("done", "")).lower() and st == "Now"}
                                                       for b in backlog if stage(b) == st]}
            for st in ("Now", "Next", "Later", "Done")]


# ---------- releases and versioning (knowledge/releases.yaml is the single source) ----------

def releases() -> list:
    return yaml.safe_load((ROOT / "knowledge" / "releases.yaml").read_text(encoding="utf-8"))["releases"]


def flags() -> tuple[set, set]:
    """Pages to flag in the menu: new or updated in the latest release or the one before (newest wins)."""
    new, upd = set(), set()
    for r in reversed(releases()[:2]):
        for p in r.get("pages_new", []):
            new.add(p)
            upd.discard(p)
        for p in r.get("pages_changed", []):
            if p not in new:
                upd.add(p)
    return new, upd


FAVICON = ("data:image/svg+xml," + __import__("urllib.parse", fromlist=["quote"]).quote(
    (SRC / "logo.svg").read_text(encoding="utf-8").replace("\n", "").strip(), safe=":/=,#()'"))


# ---------- section change flags and portal search ----------
# Knowledge files that feed the search index, and the page each one is shown on.
SEARCH_SOURCES = {"frameworks": "frameworks", "professions": "professions", "learning": "learn", "playbook": "playbook",
                  "training": "training", "ontology": "knowledge", "articles": "library", "events": "events", "media": "media",
                  "ai-for-dq": "ai", "commercial": "commercial", "legacy": "legacy", "interop": "interop", "global": "global",
                  "communities": "community", "maturity": "maturity", "rosetta": "weaver", "build": "build", "stakeholders": "roles"}
NAME_KEYS = ("name", "title", "term", "label", "question")
DESC_KEYS = ("summary", "description", "definition", "what", "why", "answer", "desc", "purpose", "note")
SECTION_FLAGS: dict = {}
REPO = ["https://github.com/cyberdudeuk/dq-commons"]  # set from --repo in main()
BASELINE = ROOT / "portal" / "section-baseline.json"


def _plain(fragment: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", fragment))).strip()


def section_slug(text: str) -> str:
    """Must match slug() in shell.html: the page drawer looks flags up by this key."""
    s = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:60]
    return "s-" + (s or "section")


def page_sections(src: str) -> dict:
    """Each static <h2> on a page source and a fingerprint of everything up to the next <h2>."""
    import hashlib
    src = re.sub(r"<script\b.*?</script>|<style\b.*?</style>", "", src, flags=re.S)
    parts = re.split(r"(<h2\b[^>]*>.*?</h2>)", src, flags=re.S)
    out = {}
    for i in range(1, len(parts), 2):
        head = _plain(parts[i])
        if head:
            body = _plain(parts[i + 1] if i + 1 < len(parts) else "")
            out[section_slug(head)] = hashlib.sha1(body.encode()).hexdigest()[:12]
    return out


def section_flags() -> dict:
    """Per page: sections new or changed since the baseline release (portal/section-baseline.json).
    Regenerate the baseline at each release with scripts/section_baseline.py."""
    base = json.loads(BASELINE.read_text(encoding="utf-8")) if BASELINE.exists() else {"since": None, "pages": {}}
    flags_by_page = {}
    for stem, _, _ in PAGES:
        old = base["pages"].get(stem)
        now = page_sections((SRC / "pages" / f"{stem}.html").read_text(encoding="utf-8"))
        f = {"_since": base.get("since")}
        if old is not None:
            for k, h in now.items():
                if k not in old:
                    f[k] = "new"
                elif old[k] != h:
                    f[k] = "upd"
        flags_by_page[stem] = f
    return flags_by_page


def search_index() -> list:
    """Everything worth finding: pages, their headings, and named items from the knowledge base."""
    idx, seen = [], set()
    def add(title, kind, url, text="", page=""):
        title = _plain(str(title))[:140]
        key = (title.lower(), url)
        if title and key not in seen:
            seen.add(key)
            idx.append({"t": title, "k": kind, "u": url, "p": page, "x": _plain(str(text)).lower()[:400]})
    labels = {stem: label for stem, label, _ in PAGES}
    for stem, label, desc in PAGES:
        add(label, "Page", f"{stem}.html", desc + " " + GROUP_TITLE[GROUP_OF[stem]], GROUP_TITLE[GROUP_OF[stem]])
    for stem, label, _ in PAGES:
        src = re.sub(r"<script\b.*?</script>|<style\b.*?</style>", "", (SRC / "pages" / f"{stem}.html").read_text(encoding="utf-8"), flags=re.S)
        for m in re.finditer(r"<h([23])\b([^>]*)>(.*?)</h\1>(.{0,600})", src, flags=re.S):
            head = _plain(m.group(3))
            if head:
                hid = re.search(r'\bid="([^"]+)"', m.group(2))
                anchor = hid.group(1) if hid else (section_slug(head) if m.group(1) == "2" else "")
                add(head, "Section", f"{stem}.html" + (f"#{anchor}" if anchor else ""), m.group(4), labels[stem])
    def walk(node, page, depth=0):
        if depth > 5:
            return
        if isinstance(node, dict):
            name = next((node[k] for k in NAME_KEYS if isinstance(node.get(k), str)), None)
            if name:
                desc = " ".join(str(node[k]) for k in DESC_KEYS if isinstance(node.get(k), str))
                add(name, labels[page], f"{page}.html", desc + " " + str(node.get("id", "")))
            for v in node.values():
                if isinstance(v, (dict, list)):
                    walk(v, page, depth + 1)
        elif isinstance(node, list):
            for v in node:
                walk(v, page, depth + 1)
    for f, page in SEARCH_SOURCES.items():
        path = ROOT / "knowledge" / f"{f}.yaml"
        if path.exists() and page in labels:
            walk(yaml.safe_load(path.read_text(encoding="utf-8")), page)
    return idx


# ---------- page assembly ----------

def nav(active: str, long: bool) -> str:
    """Grouped navigation. Desktop: one disclosure per group. Menu (narrow screens): every group listed."""
    out = []
    for g, ps in GROUPS:
        cur_g = any(stem == active for stem, _, _ in ps)
        new, upd = flags()
        flag = lambda s: ('<span class="dqp-navflag">New</span>' if s in new else '<span class="dqp-navflag upd">Updated</span>' if s in upd else "")
        links = "".join(
            f'<a href="{stem}.html" data-t="{html.escape(label)}"{" aria-current=\"page\"" if stem == active else ""}>'
            f'{icon(PAGE_ICON.get(stem, "arrow"))}<span>{html.escape(label)}{flag(stem)}</span>'
            f'<small><b class="dqp-lvl dqp-lvl-{LEVEL.get(stem, "Beginner").lower()}">{LEVEL.get(stem, "Beginner")}</b> {html.escape(desc)}</small></a>' for stem, label, desc in ps)
        if long:
            out.append(f'<div class="dqp-grp"><h2>{g[0]}. {GROUP_TITLE[g]}</h2>{links}</div>')
        else:
            out.append(f'<details class="dqp-g"{" data-current" if cur_g else ""}><summary>{icon(GROUP_ICON[g])}{g}</summary>'
                       f'<div class="dqp-panel"><p class="dqp-gt">{GROUP_TITLE[g]}</p>{links}</div></details>')
    return "".join(out)


EASY = yaml.safe_load((ROOT / "knowledge" / "easy-read.yaml").read_text(encoding="utf-8"))["pages"]


def add_easy_read(stem: str, fragment: str) -> str:
    """'In short': a plain English summary under the page title and introduction (issue #22)."""
    lines = EASY.get(stem)
    m = re.search(r"</h1>\s*(<p\b[^>]*>.*?</p>)?", fragment, flags=re.S)
    if not lines or not m:
        return fragment
    box = ('\n<details class="dqp-easy"><summary>' + icon("book") + 'In short: a plain English summary</summary><ul>'
           + "".join(f"<li>{html.escape(x)}</li>" for x in lines) + "</ul></details>\n")
    return fragment[:m.end()] + box + fragment[m.end():]


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
             .replace("{{BUILD}}", build_label).replace("{{BRAND}}", BRAND).replace("{{GROUP}}", GROUP_OF.get(stem, ""))
             .replace("{{ICONS}}", (SRC / "icons.svg").read_text(encoding="utf-8").strip())
             .replace("{{VERSION}}", VERSION).replace("{{RELEASES}}", js_json(releases()[:5]))
             .replace("{{SECTION_FLAGS}}", js_json(SECTION_FLAGS.get(stem, {})))
             .replace("{{REPO}}", html.escape(REPO[0])))
    # every page's eyebrow gets that page's icon
    fragment = re.sub(r'<span class="eyebrow">[^<·]*·', lambda m: f'<span class="eyebrow">{GROUP_TITLE.get(GROUP_OF.get(stem, ""), "Commons")} ·', fragment, count=1)
    fragment = fragment.replace('<span class="eyebrow">', f'<span class="eyebrow">{icon(PAGE_ICON.get(stem, "arrow"))}', 1)
    # WCAG 2.1.1 Keyboard: tables scroll sideways on small screens, so every table
    # wrapper must be reachable and scrollable by keyboard, and named for screen readers.
    fragment = re.sub(r'<div class="tbl"(?![^>]*tabindex)',
                      '<div class="tbl" tabindex="0" role="region" aria-label="Table, scrolls sideways on small screens"',
                      fragment)
    fragment = add_easy_read(stem, fragment)
    head, body = split_fragment(fragment)
    head += f'\n<link rel="icon" type="image/svg+xml" href="{FAVICON}">'
    shell_css, shell_body = shell.split("</style>", 1)
    shell_css += "</style>"
    frag = f"{head}\n{shell_css}\n{shell_body}\n{body}\n{footer}\n"
    doc = ("<!doctype html>\n<html lang=\"en-GB\">\n<head>\n<meta charset=\"utf-8\">\n"
           "<meta name=\"viewport\" content=\"width=device-width,initial-scale=1,viewport-fit=cover\">\n"
           f"{head}\n{shell_css}\n</head>\n<body style=\"margin:0\">\n{shell_body}\n{body}\n{footer}\n</body>\n</html>\n")
    return doc, frag


# Which knowledge file each __K_NAME__ placeholder comes from, for the per-page provenance line.
K_FILES = {"FRAMEWORKS": "frameworks", "COMMUNITIES": "communities", "LEARNING": "learning", "MATURITY": "maturity",
           "SURVEYS": "surveys", "AI": "ai-for-dq", "COMMERCIAL": "commercial", "LEGACY": "legacy", "INTEROP": "interop",
           "MEDIA": "media", "ROSETTA": "rosetta", "ARTICLES": "articles", "GLOBAL": "global", "BUILD": "build",
           "EVENTS": "events", "TRAINING": "training", "ONTOLOGY": "ontology", "GRAPH": "ontology", "RELEASES": "releases", "PLAYBOOK": "playbook", "EFFORT": "effort", "STAKEHOLDERS": "stakeholders", "PROFESSIONS": "professions"}


def provenance(names: set) -> str:
    """'Content last reviewed' line for a page: the oldest review date and the owning roles of the knowledge it shows."""
    rows = []
    for n in sorted(names):
        f = K_FILES.get(n)
        if not f:
            continue
        rv = (yaml.safe_load((ROOT / "knowledge" / f"{f}.yaml").read_text(encoding="utf-8")) or {}).get("review") or {}
        if rv.get("last_reviewed"):
            rows.append((str(rv["last_reviewed"]), rv.get("owner_role", ""), f))
    if not rows:
        return ""
    oldest = min(r[0] for r in rows)
    roles = sorted({r[1] for r in rows if r[1]})
    files = ", ".join(f"knowledge/{r[2]}.yaml" for r in rows)
    return (f'<p class="dqp-prov">{icon("calendar")} <b>Content last reviewed:</b> {html.escape(oldest)} '
            f'by {html.escape("; ".join(roles))}. Source: <code>{html.escape(files)}</code>. Review dates are checked automatically; '
            f'anything older than 12 months fails the build.</p>')


def page_history(stem: str, repo: str) -> str:
    """Who changed what, when (issue #21): the page's last change, and a link to every change on GitHub."""
    rel = f"portal/src/pages/{stem}.html"
    try:
        when = subprocess.run(["git", "log", "-1", "--format=%cs", "--", rel], cwd=ROOT, capture_output=True, text=True, timeout=20).stdout.strip()
    except Exception:  # noqa: BLE001 - no git (a copied folder): leave the line out
        when = ""
    if not when:
        return ""
    r = html.escape(repo.rstrip("/"))
    return (f'<p class="dqp-prov">{icon("history")} <b>Page last changed:</b> {html.escape(when)}. '
            f'<a href="{r}/commits/main/{rel}">Every change to this page</a> (what changed, when and why, on GitHub); '
            f'the knowledge it shows has its own history under <a href="{r}/commits/main/knowledge">knowledge</a>.</p>')


def page_footer(repo: str, as_of: str, sha: str) -> str:
    """Licences, disclaimers, transparency notices and the colophon. No personal details, by design."""
    r = html.escape(repo)
    built = date.today().isoformat()
    return f"""<footer class="dqp-foot" aria-label="About this site">
<div class="dqp-fcols">
<div><h2>Licences</h2><ul>
<li>{icon("code")} Code: <a href="{r}/blob/main/LICENSE">MIT licence</a></li>
<li>{icon("book")} Content: <a href="https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/">Open Government Licence v3.0</a>, except where stated</li>
<li>{icon("layers")} Standards and frameworks belong to their publishers. We summarise and link; we don't copy paid standards.</li>
<li>{icon("info")} Fonts: Public Sans, Source Serif 4 and JetBrains Mono, under the SIL Open Font Licence. Icons drawn for the Commons (MIT).</li>
<li>Third-party names and marks belong to their owners. Their use doesn't mean endorsement.</li>
</ul></div>
<div><h2>Notices</h2><ul>
<li>{icon("alert")} <b>Not an official government service.</b> A prototype public good, built in the open. Official guidance takes precedence; we link to it first.</li>
<li>{icon("scale")} Not legal, commercial or professional advice. Model contract clauses are illustrative and need review by your own legal and commercial teams.</li>
<li>{icon("sparkle")} <b>AI-assisted.</b> Parts of the code and content were drafted with AI and reviewed by people. Measuring is always done by rules, not models.</li>
<li>{icon("eye")} Every source in the knowledge base is read at source before it is cited. The few with no public document say so. Spotted something wrong? <a href="build.html#contact">Tell us</a>.</li>
<li>{icon("lock")} No cookies, analytics or trackers. Data you check stays in your browser. See <a href="accessibility.html#privacy">privacy</a>.</li>
<li>{icon("access")} <a href="accessibility.html">Accessibility statement</a> (aiming for WCAG 2.2 AA).</li>
</ul></div>
<div><h2>Get involved</h2><ul>
<li>{icon("message")} <a href="build.html#contact">Contact us</a> (by form; we never show an email address)</li>
<li>{icon("blocks")} <a href="build.html">Help us build this</a>: roadmap, backlog and co-design</li>
<li>{icon("shield")} <a href="{r}/blob/main/CHARTER.md">Charter</a> and <a href="{r}/blob/main/CODE_OF_CONDUCT.md">code of conduct</a></li>
<li>{icon("lifebuoy")} <a href="operate.html">Get help</a></li>
<li>{icon("repo")} <a href="{r}">Source code on GitHub</a></li>
<li>{icon("alert")} Security problem? <a href="{r}/security/advisories/new">Report it privately</a></li>
</ul></div>
</div>
<!--PROVENANCE-->
<p class="dqp-colo"><b>Colophon.</b> {BRAND} v{VERSION}. Built {built} from commit <code>{html.escape(sha)}</code>; pipeline results as of {html.escape(as_of)}.
Static HTML, CSS and JavaScript with no frameworks, generated by <code>scripts/build_dq_portal.py</code> from the open knowledge base and the dqkit toolkit (Python),
whose browser engine is checked case by case against Python. Set in Public Sans and Source Serif 4. Runs on GitHub alone: GitHub Pages, issue forms, discussions and Actions. Maintained by the Commons community.</p>
</footer>"""


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--results", default=str(ROOT / "assessments" / "portfolio"))
    ap.add_argument("--portfolio", default=str(ROOT / "portfolio.ndl.yaml"))
    ap.add_argument("--out", default=str(ROOT / "portal" / "dist"))
    ap.add_argument("--repo", default="https://github.com/cyberdudeuk/dq-commons",
                    help="repository web address, used for source links and to read issue data")
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
        # js-yaml 4.2.0 (MIT, portal/src/js/vendor/js-yaml.LICENSE), bundled so pages work with no CDN:
        # many government networks block CDNs, and a CDN sees every visitor (D-POL-01).
        "__JSYAML__": "/*! js-yaml 4.2.0 | MIT | https://github.com/nodeca/js-yaml */\n"
                      + (SRC / "js" / "vendor" / "js-yaml.min.js").read_text(encoding="utf-8").replace("</script", "<\\/script"),
        "__ENGINE__": (SRC / "js" / "engine.js").read_text(encoding="utf-8").replace("</script", "<\\/script"),
        "__SHEETS__": (SRC / "js" / "sheets.js").read_text(encoding="utf-8").replace("</script", "<\\/script"),
        "__BUILD__": js_json({"version": VERSION, "sha": sha, "built": date.today().isoformat(), "as_of": port["as_of"],
                              "repo": a.repo}),
    }

    kb, kcache = knowledge(), {}
    REPO[0] = a.repo.rstrip("/")
    SECTION_FLAGS.update(section_flags())

    def render(target: Path, download_base: str):
        if target.exists():
            shutil.rmtree(target)
        target.mkdir(parents=True)
        footer = page_footer(a.repo, port["as_of"], sha)
        for stem, _, _ in PAGES:
            text = (SRC / "pages" / f"{stem}.html").read_text(encoding="utf-8")
            prov = provenance(set(re.findall(r"__K_([A-Z]+)__", text)))
            text = text.replace("__DATA__", data["__NDL_DATA__"]) if stem == "ndl-assurance" else text
            for k, v in data.items():
                text = text.replace(k, v)
            for name in set(re.findall(r"__K_([A-Z]+)__", text)):
                if name not in kcache:
                    kcache[name] = js_json(kb[name]())
                text = text.replace(f"__K_{name}__", kcache[name])
            text = text.replace("__DOWNLOADS__", download_base)
            doc, frag = assemble(stem, text, build_label, footer.replace("<!--PROVENANCE-->", prov + page_history(stem, a.repo)))
            (target / f"{stem}.html").write_text(doc, encoding="utf-8")
        dl = target / "downloads"
        (dl / "assets").mkdir(parents=True)
        for f in DOWNLOAD_FILES:
            if (results_dir / f).exists():
                shutil.copy2(results_dir / f, dl / f)
        for f in (results_dir / "assets").iterdir():
            if f.suffix in (".xlsx", ".docx", ".md", ".csv", ".jsonld", ".json"):
                shutil.copy2(f, dl / "assets" / f.name)
        # Capability and data models: every export, the source YAML, the ERD image, the PDF map and one zip of the lot.
        md = ROOT / "models"
        if (md / "out").exists():
            import zipfile as _zf
            shutil.copytree(md / "out", dl / "models", dirs_exist_ok=True)
            for f in ["dq-capability.yaml", "README.md", "dq-data-model.svg", "dq-capability-process-map.pdf"]:
                if (md / f).exists():
                    shutil.copy2(md / f, dl / "models" / f)
            if (md / "previews").exists():
                shutil.copytree(md / "previews", dl / "models" / "previews", dirs_exist_ok=True)
            with _zf.ZipFile(dl / "models" / "dq-capability-models.zip", "w", _zf.ZIP_DEFLATED) as z:
                for f in sorted((dl / "models").rglob("*")):
                    if f.is_file() and f.suffix != ".zip" and "previews" not in f.parts:
                        z.write(f, f"dq-capability-models/{f.relative_to(dl / 'models').as_posix()}")
        (target / ".nojekyll").write_text("", encoding="utf-8")
        # Portal search: loaded only when someone opens search, so pages stay light.
        (target / "search-index.js").write_text("window.DQP_INDEX=" + json.dumps(search_index(), ensure_ascii=False, separators=(",", ":")) + ";\n", encoding="utf-8")
        # Offline copy (issue #24): the whole portal in one zip. Open index.html from the unzipped folder;
        # every page works without a connection because nothing loads from other sites.
        import zipfile
        with zipfile.ZipFile(dl / "dq-commons-offline.zip", "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
            for f in sorted(target.rglob("*")):
                if f.is_file() and f.name != "dq-commons-offline.zip":
                    z.write(f, f"dq-commons/{f.relative_to(target).as_posix()}")
        print(f"Built {len(PAGES)} pages in {target}")

    render(out, "downloads/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
