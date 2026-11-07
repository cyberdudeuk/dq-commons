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
import urllib.parse
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
        ("map", "Data quality at a glance", "Pictures instead of tables: who does each step and how much it matters, the steps as a flow, how records connect, and how a rule travels"),
        ("github", "New to GitHub?", "What GitHub is, how the portal and its repository connect, and what you can do there"),
        ("about", "About the Commons", "Background, why it exists, purpose, aims, goals, objectives and desired outcomes"),
        ("guide", "User guide", "How to use the portal, guided tours, tutorials and frequently asked questions"),
        ("sitemap", "Site map", "Every page on one visual map, by menu group and level, with suggested routes to follow"),
        ("ask", "Ask the Commons", "Ask a question in plain English and get answers drawn from across the portal, with links to the source"),
        ("roles", "For your role", "What CDO Council, CDOs, data owners, stewards, quality leads and others need, decide and should watch, and the gap register"),
        ("accessibility", "Accessibility and privacy", "Accessibility statement, known problems, and what happens to anything you share"),
    ]),
    ("2 Learn", [
        ("learn", "Learn", "Pathways by role, modules, tutorials and glossary"),
        ("professions", "Across the professions", "Where data quality sits in every profession's capability framework, in the UK nations and internationally"),
        ("governance", "Governance boards and forums", "Who decides, advises, regulates and meets on government data: purpose, aims, outcomes, rules of engagement and terms of reference, and where your question should go"),
        ("training", "Skills and training", "Skills check against your role, a development plan and a catalogue of courses and qualifications"),
        ("knowledge", "Knowledge map", "Glossary, thesaurus, data dictionary, taxonomies, ontology and an interactive knowledge graph with lineage"),
        ("library", "Library and knowledge base", "Curated resources, how-to articles and resources shared by members"),
        ("media", "Media centre", "Blog, vlog and podcasts about data quality, from the Commons and members"),
        ("events", "Events", "Data quality conferences, workshops, courses and forums, with calendar downloads"),
    ]),
    ("3 Check", [
        ("check", "Check your data", "Run the toolkit in your browser on a CSV file. Nothing is uploaded"),
        ("maturity", "Maturity self-assessment", "Where you are on 8 themes, from Beginning to Mastering, and next steps"),
        ("wheel", "Data management wheel", "The 11 DAMA knowledge areas mapped to maturity, the DAM policy, the data and records lifecycle, and how professions join up"),
        ("guidance", "Issues framework", "Prioritise issues with the government method: a live calculator"),
        ("assistant", "Rules assistant", "Plain English to tested rules in your browser, plus framework and scoring look-ups"),
        ("baseline", "Critical data asset baseline", "Effort to report data quality for every critical data asset, to your own deadline"),
    ]),
    ("4 Improve", [
        ("playbook", "Data quality management playbook", "Eight stages to manage the quality of critical data assets: steps, checklists, roles, templates and the DAM policy, usable anywhere"),
        ("frameworks", "Frameworks and standards", "30 frameworks and standards, crosswalks, packs and clause-by-clause comparison"),
        ("tooling", "Tooling", "Data quality tools, standards and open code across government"),
        ("catalogues", "Catalogues and quality tools", "How data catalogues and quality tools connect, what to ask suppliers, and how to avoid lock-in and bundling traps"),
        ("connectors", "Connectors, weaves and AI", "Write rules once and weave them into 11 platforms' own formats; vendors from the Gartner and Forrester reports, their GitHub code, AI agents and MCP servers"),
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
        ("ecosystem", "Three portals, one journey", "How the Commons, the DAM capability playbooks and the GitHub Repos Asset Catalogue compare, connect and continue each other's journeys"),
        ("reuse", "Use the Commons your way", "Link, embed, white-label, open data API, intranets, enterprise content and collaboration tools, AI assistants, MCP, connectors and plugins"),
    ]),
    ("6 Contribute", [
        ("community", "Community", "Contributions library, wishlist, networks and how to get involved"),
        ("getinvolved", "Get involved", "Contribute, join a working group, champion the Commons in your organisation, a communications kit and badges"),
        ("share", "Case studies", "Draft case studies from measured results, to share what worked"),
        ("surveys", "Surveys and commissions", "Take or run a data quality survey, or ask the Commons for help"),
        ("research", "Take part in user research", "An introduction to the Commons for you and your team, the research panel, what we want to learn and what changed because of it"),
        ("build", "Help us build this", "Roadmap, backlog, wishlist, co-design charter, contributors and how to contact us"),
        ("roadmap", "Open roadmap and priorities", "How ideas, votes and research become the backlog and roadmap: scores, government strategy, capacity and decisions, in the open"),
        ("operate", "Operating model and support", "Support tiers, roles, how requests become features, GitHub, Jira and Confluence"),
    ]),
]
# Full group titles, shown in the menu panel and in each page's breadcrumb.
GROUP_TITLE = {"1 Start": "Get started", "2 Learn": "Learn and build skills", "3 Check": "Check and assess",
               "4 Improve": "Manage and improve", "5 Apply": "Apply to your context", "6 Contribute": "Contribute and get help"}
LEVEL = {**{s: "Beginner" for s in ["index", "map", "github", "about", "guide", "roles", "accessibility", "learn", "library", "media", "events",
                                    "check", "maturity", "scenarios", "community", "surveys", "operate", "sitemap", "ask", "research", "getinvolved"]},
         **{s: "Intermediate" for s in ["catalogues", "connectors", "professions", "training", "knowledge", "guidance", "assistant", "baseline", "playbook",
                                        "frameworks", "tooling", "ai", "commercial", "global", "share", "build", "reuse", "wheel", "ecosystem", "roadmap", "governance"]},
         **{s: "Advanced" for s in ["legacy", "interop", "weaver", "models", "pipeline", "ndl-assurance"]}}
PAGES = [p for _, ps in GROUPS for p in ps]
# Decorative icons from portal/src/icons.svg, for each menu group and page.
GROUP_ICON = {"1 Start": "compass", "2 Learn": "grad", "3 Check": "check", "4 Improve": "shield", "5 Apply": "map", "6 Contribute": "heart"}
PAGE_ICON = {"index": "home", "about": "info", "guide": "book", "accessibility": "access", "check": "check", "maturity": "gauge",
             "assistant": "sparkle", "weaver": "weave", "pipeline": "pulse", "frameworks": "layers", "learn": "grad", "ai": "cpu",
             "guidance": "flag", "tooling": "wrench", "library": "library", "commercial": "contract", "legacy": "history",
             "interop": "link", "scenarios": "map", "global": "globe", "ndl-assurance": "database", "baseline": "target",
             "community": "users", "media": "mic", "events": "calendar", "training": "grad", "knowledge": "globe", "surveys": "clipboard", "share": "quote", "build": "blocks", "operate": "lifebuoy", "playbook": "workflow", "roles": "users", "github": "repo", "professions": "blocks", "models": "steps", "catalogues": "handshake", "connectors": "link", "map": "map", "sitemap": "sitemap", "ask": "chat", "reuse": "share", "wheel": "wheel", "ecosystem": "network", "research": "message", "roadmap": "target", "governance": "scale", "getinvolved": "heart"}


def icon(name: str) -> str:
    return f'<svg class="dqi" aria-hidden="true" focusable="false"><use href="#i-{name}"/></svg>'


GROUP_OF = {p[0]: g for g, ps in GROUPS for p in ps}
# Colour key per menu group (v2.8.0): each group has its own accessible hue, used for signposting.
GROUP_KEY = {"1 Start": "start", "2 Learn": "learn", "3 Check": "check", "4 Improve": "improve", "5 Apply": "apply", "6 Contribute": "contribute"}
ORDER = [(stem, label, g) for g, ps in GROUPS for stem, label, _ in ps]
ACRONYMS = yaml.safe_load((ROOT / "knowledge" / "acronyms.yaml").read_text(encoding="utf-8"))["acronyms"]
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
    return json.dumps(obj, ensure_ascii=False, separators=(",", ":"), default=str).replace("</", "<\\/").replace("<!--", "<\\!--")


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
            "capabilities": m["capabilities"], "enums": m["enums"], "lanes": m.get("lanes", {}),
            "page_labels": {stem: label for stem, label, _ in PAGES},
            "stages": {s["id"]: f"Stage {s['n']}: {s['name']}" for s in yaml.safe_load((ROOT / "knowledge" / "playbook.yaml").read_text(encoding="utf-8"))["stages"]},
            "roles": {r["id"]: r["name"] for r in yaml.safe_load((ROOT / "knowledge" / "stakeholders.yaml").read_text(encoding="utf-8"))["roles"]},
            "entities": [{k: e[k] for k in ("name", "group", "description", "guidance")} | {"attributes": e["attributes"]} for e in m["entities"]],
            "processes": [{"id": p["id"], "name": p["name"], "capability": p["capability"], "lanes": p["lanes"],
                           "steps": [{k: s.get(k) for k in ("id", "kind", "name", "lane", "guidance", "outputs", "branches", "next", "page", "stage")} for s in p["steps"]]} for p in m["processes"]],
            "files": files, "previews": previews,
            "extras": [f for f in ("dq-data-model.svg", "dq-capability-process-map.pdf") if (ROOT / "models" / f).exists()]}


def models_nav() -> dict:
    """A light version of the capability model for pages that link into it (home, roles, playbook)."""
    m = yaml.safe_load((ROOT / "models" / "dq-capability.yaml").read_text(encoding="utf-8"))
    return {"principles": m["principles"], "lanes": m.get("lanes", {}),
            "capabilities": [{k: c.get(k) for k in ("id", "name", "principle", "children", "pages")} for c in m["capabilities"]],
            "processes": [{"id": p["id"], "name": p["name"], "capability": p["capability"],
                           "steps": [{k: s.get(k) for k in ("id", "kind", "name", "lane", "page", "stage")} for s in p["steps"] if s["kind"] not in ("start", "end")]}
                          for p in m["processes"]]}


def knowledge() -> dict:
    """Every knowledge-base file as a page placeholder (__K_NAME__). Built lazily, only if a page uses it."""
    import sys
    sys.path.insert(0, str(ROOT))
    from dqkit import packs, rules, weaves
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
        "CATALOGUES": lambda: y("catalogue-integration"),
        "REUSE": lambda: y("reuse"),
        "WHEEL": lambda: y("dama-wheel"),
        "CHANGE": lambda: y("change-delivery"),
        "FEEDBACK": lambda: y("feedback"),
        "STANDARDS": lambda: y("standards-catalogue"),
        "ECO": lambda: y("ecosystem"),
        "CODE": lambda: y("code-evidence"),
        "VENDORS": lambda: {**y("vendors"), "crosswalk": weaves.crosswalk()},
        "PROVENANCE": lambda: provenance_feed(),
        "GOVBODIES": lambda: y("governance-bodies"),
        "PARTICIPATION": lambda: y("participation"),
        "RESEARCH": lambda: {**y("research"), "email_text": research_email()[1]},
        "ROADMAP": lambda: {**y("roadmap"), "backlog": y("build")["backlog"], "github_live": github_live()},
        "SITEMAP": lambda: site_map(),
        "MCPTOOLS": lambda: mcp_tools(),
        "MODELS": lambda: models_summary(),
        "MODELNAV": lambda: models_nav(),
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
SEARCH_SOURCES = {"provenance": "build", "vendors": "connectors", "participation": "getinvolved", "governance-bodies": "governance", "research": "research", "roadmap": "roadmap", "standards-catalogue": "interop", "ecosystem": "ecosystem", "reuse": "reuse", "dama-wheel": "wheel", "change-delivery": "roles", "feedback": "build", "frameworks": "frameworks", "professions": "professions", "learning": "learn", "playbook": "playbook",
                  "training": "training", "ontology": "knowledge", "articles": "library", "events": "events", "media": "media",
                  "ai-for-dq": "ai", "commercial": "commercial", "legacy": "legacy", "interop": "interop", "global": "global",
                  "communities": "community", "maturity": "maturity", "rosetta": "weaver", "build": "build", "stakeholders": "roles", "catalogue-integration": "catalogues"}
NAME_KEYS = ("name", "title", "term", "label", "question")
DESC_KEYS = ("summary", "description", "definition", "what", "why", "answer", "desc", "purpose", "note", "text", "do", "how", "detail", "for", "needs", "decides", "watch", "goal")
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


PASSAGES: list = []  # original-case text for Ask the Commons and the API, filled by search_index()


def site_map() -> list:
    """The menu as data: groups, pages, levels and icons (site map page and api/pages.json)."""
    return [{"group": g, "key": GROUP_KEY[g], "title": GROUP_TITLE[g], "icon": GROUP_ICON[g],
             "pages": [{"stem": st, "label": lb, "desc": d, "level": LEVEL.get(st, "Beginner"), "icon": PAGE_ICON.get(st, "arrow"),
                        "url": f"{st}.html"} for st, lb, d in ps]} for g, ps in GROUPS]


def mcp_tools() -> list:
    """The toolkit's MCP tools, read from the server itself so the page can never drift from the code."""
    import sys
    sys.path.insert(0, str(ROOT))
    from dqkit import mcp_server
    return [{"name": t["name"], "title": t.get("title", ""), "description": t.get("description", "")} for t in mcp_server.TOOLS]


def feedback_docx(path: Path) -> None:
    """The Microsoft Form question set as a Word document, ready for Microsoft Forms' Quick import (v2.9.0)."""
    from docx import Document
    d = Document()
    d.core_properties.title = FEEDBACK["microsoft_form"]["title"]
    d.core_properties.author = BRAND
    d.add_heading(FEEDBACK["microsoft_form"]["title"], 0)
    d.add_paragraph("Tell us what is wrong, missing or hard to use in the Public Sector Data Quality Commons, or what worked well. "
                    "Please don't include names, contact details, personal data or anything official-sensitive. "
                    "We may publish feedback in summary form, without anything that identifies you.")
    for q in FEEDBACK["questions"]:
        d.add_paragraph().add_run(f'{q["n"]}. {q["text"]}' + (" (required)" if q.get("required") else "")).bold = True
        if q.get("hint"):
            d.add_paragraph(q["hint"])
        for o in q.get("options", []):
            d.add_paragraph(o, style="List Bullet")
        if q.get("scale"):
            d.add_paragraph(f'Rating: {q["scale"]}')
    d.add_heading("Settings for the form owner", 1)
    for x in FEEDBACK["microsoft_form"]["settings"]:
        d.add_paragraph(x, style="List Bullet")
    path.parent.mkdir(parents=True, exist_ok=True)
    d.save(str(path))


PORTAL_URL = "https://cyberdudeuk.github.io/dq-commons/"


def research_email(base: str = PORTAL_URL) -> tuple:
    """The invitation email (v2.11.0): (subject, plain text). Used on research.html, in the .eml file and the Word pack.
    No sender, no recipients, no tracking: the person sending it adds those."""
    R = yaml.safe_load((ROOT / "knowledge" / "research.yaml").read_text(encoding="utf-8"))
    subject = "Help shape DQ Commons: a free data quality portal for the public sector"
    who = "\n".join(f"- {w['who']}: {w['gets'][0].lower() + w['gets'][1:]}" for w in R["intro"]["for_whom"])
    ways = "\n".join(f"- {w['how']}: {w['detail']}" for w in R["intro"]["ways_to_use"])
    methods = ", ".join(m["name"].lower() for m in R["methods"] if m["id"] != "benchmark")
    body = f"""[Add a line from you here, so colleagues know why you are sending this.]

DQ Commons is a free, open portal for anyone in the UK public sector who looks after, uses or relies on data. You can check a data file in your browser (nothing is uploaded), find the data quality frameworks for your nation and sector, describe a dataset once in every metadata standard, and learn from peers. It needs no account and works on a phone, with a screen reader and offline.

Open it: {base}

What it offers your team
{who}

Ways to use it
{ways}

Help decide what it does next
The Commons is built in the open with the people who use it. We are opening a user research panel to find out what teams need, what gets in the way and what to build next. You can choose {methods}. Many take ten minutes in your own time.

- Taking part is voluntary and you can stop at any time.
- Your contact details stay with the Commons team and are never published.
- Findings are published as themes and totals, never with names.
- We arrange and pay for captions, British Sign Language, Welsh-language sessions and other support.

Find out more and sign up: {base}research.html
See the open roadmap and vote on ideas: {base}roadmap.html

The Commons is a community project, not an official GOV.UK service. Questions go through the contact form on the portal ({base}build.html#contact); the team doesn't publish an email address.
"""
    return subject, body


def research_bundle(folder: Path, base: str = PORTAL_URL) -> None:
    """The user research bundle for email and download (v2.11.0): invitation pack, participant information and
    consent, sign-up questions for Microsoft Forms, session guides, an .eml invitation and one zip with a read-me."""
    import zipfile
    from email.message import EmailMessage
    from docx import Document
    from docx.shared import Pt
    R = yaml.safe_load((ROOT / "knowledge" / "research.yaml").read_text(encoding="utf-8"))
    folder.mkdir(parents=True, exist_ok=True)
    subject, body = research_email(base)

    def doc(title):
        d = Document()
        d.core_properties.title, d.core_properties.author = title, BRAND
        d.styles["Normal"].font.name, d.styles["Normal"].font.size = "Arial", Pt(12)
        d.add_heading(title, 0)
        return d

    def bullets(d, xs):
        for x in xs:
            d.add_paragraph(x, style="List Bullet")

    # 1. Introducing the Commons and invitation
    d = doc("Introducing DQ Commons, and an invitation to help shape it")
    d.add_paragraph(R["intro"]["what"])
    d.add_paragraph(f"Open it: {base}")
    d.add_heading("What it offers your team", 1)
    t = d.add_table(rows=1, cols=2); t.style = "Table Grid"
    t.rows[0].cells[0].text, t.rows[0].cells[1].text = "If you are", "You get"
    for w in R["intro"]["for_whom"]:
        r = t.add_row().cells; r[0].text, r[1].text = w["who"], w["gets"]
    d.add_heading("Ways to use it", 1)
    bullets(d, [f'{w["how"]}: {w["detail"]} ({base}{w["link"]})' for w in R["intro"]["ways_to_use"]])
    d.add_heading("Why we are asking for your help", 1)
    d.add_paragraph(R["why_research"])
    d.add_heading("Ways to take part", 1)
    t = d.add_table(rows=1, cols=3); t.style = "Table Grid"
    for c, h in zip(t.rows[0].cells, ("Method", "Time", "What happens")):
        c.text = h
    for m in R["methods"]:
        r = t.add_row().cells; r[0].text, r[1].text, r[2].text = m["name"], m["time"], m["what"]
    d.add_heading("Research rounds", 1)
    bullets(d, [f'{x["name"]} ({x["when"]}): {x["participants"]}' for x in R["rounds"]])
    d.add_heading("Our promise", 1)
    bullets(d, R["sign_up"]["promise"])
    d.add_heading("How to take part", 1)
    d.add_paragraph(f"Sign up on the research page: {base}research.html#join. {R['sign_up']['team_route']}")
    d.add_paragraph(f"See the open roadmap, vote on ideas and suggest your own: {base}roadmap.html")
    d.add_paragraph("The Commons is a community project, not an official GOV.UK service. It has no tracking or analytics. "
                    f"Questions go through the contact form ({base}build.html#contact); the team doesn't publish an email address.")
    d.save(str(folder / "dq-commons-research-invitation.docx"))

    # 2. Participant information and consent
    c = R["consent"]
    d = doc(c["title"])
    for sct in c["sections"]:
        d.add_heading(sct["h"], 1); d.add_paragraph(sct["p"])
    d.add_heading("Consent", 1)
    d.add_paragraph("Please tick each statement you agree to. You can take part without agreeing to a recording.")
    for x in c["statements"]:
        d.add_paragraph("\u2610  " + x)
    d.add_paragraph("Session code (filled in by the researcher, never your name): ____________    Date: ____________")
    d.save(str(folder / "dq-commons-participant-information-and-consent.docx"))

    # 3. Sign-up questions for Microsoft Forms Quick import
    d = doc(R["sign_up"]["form_title"])
    d.add_paragraph("Thank you for your interest in helping shape DQ Commons. " + " ".join(R["sign_up"]["promise"][:3]))
    for q in R["screener"]:
        d.add_paragraph().add_run(f'{q["n"]}. {q["text"]}' + (" (required)" if q.get("required") else "") + (" (choose any)" if q.get("multi") else "")).bold = True
        bullets(d, q["options"])
    d.add_heading("Settings for the form owner", 1)
    bullets(d, ["Create the form in the Commons team's Microsoft 365 tenant, not a personal account.",
                "Who can respond: anyone can respond. Record name: off. One response per person: off.",
                "Only question 10 collects contact details. Restrict access to the responses to the research team.",
                "Export responses monthly, delete people who leave the panel at once, and delete everyone after 12 months without contact.",
                "Paste the form's share link into knowledge/research.yaml (sign_up.form_url) so the portal shows the Join button.",
                "Record protected characteristics only as totals, never against a person."])
    d.save(str(folder / "dq-commons-research-screener.docx"))

    # 4. Session guides
    d = doc("Research session guides")
    d.add_paragraph("Guides for each kind of session. Check access needs and consent first, every time. We test the portal, not the person.")
    for g in R["sessions"]:
        d.add_heading(g["title"], 1)
        t = d.add_table(rows=1, cols=3); t.style = "Table Grid"
        for cell, h in zip(t.rows[0].cells, ("Minutes", "Part", "What to do")):
            cell.text = h
        for st in g["steps"]:
            r = t.add_row().cells; r[0].text, r[1].text, r[2].text = str(st["min"]), st["part"], st["detail"]
        if g.get("note"):
            d.add_paragraph(g["note"])
    bm = R["benchmark"]
    d.add_heading(f'Usability benchmark: {bm["name"]}', 1)
    d.add_paragraph("Ask at the end of every usability and accessibility session. Answers: " + ", ".join(f"{i + 1} {x}" for i, x in enumerate(bm["scale"])) + ".")
    for i, x in enumerate(bm["items"], 1):
        d.add_paragraph(f"{i}. {x}   1  2  3  4  5")
    d.add_paragraph(bm["scoring"]); d.add_paragraph(bm["reading"]); d.add_paragraph(bm["credit"])
    d.add_heading("Who to recruit (minimums per round)", 1)
    bullets(d, [f'{q["group"]}: at least {q["min"]}' for q in R["quotas"]])
    d.add_heading("Turning sessions into findings", 1)
    for i, x in enumerate(R["synthesis"]["steps"], 1):
        d.add_paragraph(f"{i}. {x}")
    d.save(str(folder / "dq-commons-research-session-guides.docx"))

    # 5. Email file: no sender, no recipients; opens as a draft in Outlook or Mail
    m = EmailMessage()
    m["Subject"] = subject
    m["X-Unsent"] = "1"
    m.set_content(body)
    html_body = "".join(f"<p>{html.escape(p).replace(chr(10), '<br>')}</p>" for p in body.strip().split("\n\n"))
    m.add_alternative(f'<!doctype html><html lang="en"><body style="font-family:Arial,sans-serif;font-size:16px;line-height:1.5;max-width:40em">{html_body}</body></html>', subtype="html")
    (folder / "dq-commons-research-invitation.eml").write_bytes(bytes(m))

    # 6. One zip with a read-me
    readme = f"""DQ Commons user research bundle (version {VERSION})

What is in this bundle
- dq-commons-research-invitation.docx: introduces the Commons to your team and invites them to take part
- dq-commons-research-invitation.eml: the same invitation as an email; open it, add recipients and a line from you, send
- dq-commons-participant-information-and-consent.docx: what happens in a session, what is kept, and people's rights
- dq-commons-research-screener.docx: sign-up questions, ready for Microsoft Forms Quick import
- dq-commons-research-session-guides.docx: interview, usability, accessibility and co-design guides

How to use it
1. Send the email (or attach the invitation) to colleagues who might use the Commons.
2. People sign up on the research page: {base}research.html#join
3. Everyone sees the participant information before a session.
4. Findings are published on the research page and change the open roadmap: {base}roadmap.html

Nothing in this bundle names anyone. It has no tracking. Licence: Open Government Licence v3.0.
"""
    (folder / "README.txt").write_text(readme, encoding="utf-8")
    with zipfile.ZipFile(folder / "dq-commons-research-bundle.zip", "w", zipfile.ZIP_DEFLATED) as z:
        for f in sorted(folder.iterdir()):
            if f.suffix != ".zip":
                z.write(f, f"dq-commons-research-bundle/{f.name}")


def ambassador_kit(folder: Path, base: str = PORTAL_URL) -> None:
    """The champion and ambassador kit (v2.12.0): every message in the communications kit as text and Word, the
    introduction email as an .eml draft, role descriptions, working group terms, badge rules and snippets, in one zip."""
    import zipfile
    from email.message import EmailMessage
    from docx import Document
    from docx.shared import Pt
    P = yaml.safe_load((ROOT / "knowledge" / "participation.yaml").read_text(encoding="utf-8"))
    folder.mkdir(parents=True, exist_ok=True)
    fill = lambda t: t.replace("{link}", base)
    d = Document()
    d.core_properties.title, d.core_properties.author = "DQ Commons champion and ambassador kit", BRAND
    d.styles["Normal"].font.name, d.styles["Normal"].font.size = "Arial", Pt(12)
    d.add_heading("DQ Commons champion and ambassador kit", 0)
    d.add_paragraph(P["intro"])
    d.add_heading("Roles", 1)
    for r in P["champions"]["roles"]:
        d.add_heading(f'{r["name"]} ({r["for"]}, {r["time"]})', 2)
        for x in r["do"]:
            d.add_paragraph(x, style="List Bullet")
    d.add_heading("What you get", 1)
    for x in P["champions"]["get"]:
        d.add_paragraph(x, style="List Bullet")
    d.add_heading("What we ask", 1)
    for x in P["champions"]["ask"]:
        d.add_paragraph(x, style="List Bullet")
    d.add_heading("How to start", 1)
    for i, x in enumerate(P["champions"]["start"], 1):
        d.add_paragraph(f"{i}. {x}")
    d.add_heading("Messages to send in your organisation", 1)
    for k in P["kit"]:
        d.add_heading(k["channel"], 2)
        if k["subject"]:
            d.add_paragraph(f'Subject: {k["subject"]}')
        for para in fill(k["text"]).strip().split("\n\n"):
            d.add_paragraph(para)
        (folder / f'{k["id"]}.txt').write_text((f'Subject: {k["subject"]}\n\n' if k["subject"] else "") + fill(k["text"]), encoding="utf-8")
    d.add_heading("Working groups", 1)
    for g in P["working_groups"]:
        d.add_paragraph().add_run(f'{g["name"]} ({g["status"]})').bold = True
        d.add_paragraph(g["purpose"])
    d.add_heading("How working groups run", 2)
    for x in P["working_group_terms"]:
        d.add_paragraph(x, style="List Bullet")
    d.add_heading("Badges", 1)
    for bd in P["badges"]:
        d.add_paragraph(f'{bd["name"]}: {bd["criteria"]} ({"self-declared" if bd["confirm"] == "self" else "confirmed by a maintainer"})', style="List Bullet")
    for x in P["badge_rules"]:
        d.add_paragraph(x)
    d.add_paragraph(f"Badge images and copy-and-paste code for GitHub, social media and email signatures: {base}getinvolved.html#badges")
    d.save(str(folder / "dq-commons-ambassador-kit.docx"))
    em = next(k for k in P["kit"] if k["id"] == "email")
    m = EmailMessage()
    m["Subject"] = em["subject"]
    m["X-Unsent"] = "1"
    m.set_content(fill(em["text"]))
    (folder / "dq-commons-introduction.eml").write_bytes(bytes(m))
    (folder / "README.txt").write_text(f"""DQ Commons champion and ambassador kit (version {VERSION})

- dq-commons-ambassador-kit.docx: roles, what you get and what we ask, every message, working groups and badges
- dq-commons-introduction.eml: the introduction email as a draft; open it, add recipients and send
- email.txt, teams.txt, slack.txt, engage.txt, intranet.txt, newsletter.txt, talk.txt, update.txt: each message as plain text
Badges: {base}getinvolved.html#badges

Nothing here names anyone and nothing tracks who opens it. Licence: Open Government Licence v3.0.
""", encoding="utf-8")
    with zipfile.ZipFile(folder / "dq-commons-ambassador-kit.zip", "w", zipfile.ZIP_DEFLATED) as z:
        for f in sorted(folder.iterdir()):
            if f.suffix != ".zip":
                z.write(f, f"dq-commons-ambassador-kit/{f.name}")


def PLAYBOOK_STAGES() -> list:
    return yaml.safe_load((ROOT / "knowledge" / "playbook.yaml").read_text(encoding="utf-8"))["stages"]


def xref_manifest(base: str) -> dict:
    """Shared keys and their addresses, in the same shape as the DAM playbooks' data/xref.json (v2.10.0). Ids only, no copied text."""
    st = yaml.safe_load((ROOT / "knowledge" / "stakeholders.yaml").read_text(encoding="utf-8"))
    sc = yaml.safe_load((ROOT / "knowledge" / "standards-catalogue.yaml").read_text(encoding="utf-8"))
    dm = {x["dqc"]: x for x in ECO["xref"]["dama"]}
    rc = {x["dqc"]: x["dam"] for x in ECO["xref"]["roles"]}
    return {"portal": BRAND, "id": "dqc", "version": VERSION, "as_of": date.today().isoformat(), "url": base,
            "status": "Community project", "licence": "Code MIT; content Open Government Licence v3.0",
            "keys": {
                "dama_areas": [{"id": v["dam"], "commons_id": k, "name": v["name"], "url": f"{base}wheel.html#area-{k}"} for k, v in dm.items()],
                "roles": [{"id": r["id"], "code": rc.get(r["id"], ""), "name": r["name"], "group": r.get("group", "everyday"), "url": f"{base}roles.html#{r['id']}"} for r in st["roles"]],
                "standards": [{"id": x["id"], "name": x["name"], "status": x["status"], "domain": x["domain"], "url": f"{base}interop.html#std-{x['id']}"} for x in sc["standards"]],
                "pages": [{"id": stem, "name": label, "url": f"{base}{stem}.html"} for stem, label, _ in PAGES],
                "dam_requirements": [{"id": r["id"], "strength": r["strength"], "commons_stages": [st["id"] for st in PLAYBOOK_STAGES() if r["id"] in st.get("dam_playbooks", [])],
                                      "url": f"{base}playbook.html#stages"} for r in ECO["xref"]["requirements"]]},
            "related": [{k: p[k] for k in ("id", "name", "url", "status", "licence")} for p in ECO["portals"] if p["id"] != "dqc"]}


def write_api(target: Path, repo: str, base: str) -> None:
    """Read-only open data API (v2.8.0): fixed JSON addresses, a releases feed and a sitemap. No keys, no tracking."""
    api = target / "api"
    (api / "knowledge").mkdir(parents=True, exist_ok=True)
    dump = lambda p, o: p.write_text(json.dumps(o, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    eps = [("api/xref.json", "Cross-reference manifest: the Commons' shared keys (DAMA areas, roles, standards, pages) and where each lives, for sister portals", xref_manifest(base)),
           ("api/pages.json", "Every page by menu group, with level, description and address", site_map()),
           ("api/search.json", "The search index: pages, sections and named knowledge items", search_index()),
           ("api/passages.json", "Every section and knowledge item with readable text and a link, for assistants and reuse", PASSAGES),
           ("api/releases.json", "Every release with what is new, changed and fixed", releases()),
           ("api/acronyms.json", "Acronyms and their meanings in plain English", ACRONYMS),
           ("api/mcp-tools.json", "The toolkit's MCP tools for AI assistants", mcp_tools())]
    for path, _, obj in eps:
        dump(target / path, obj)
    kfiles = []
    for f in sorted((ROOT / "knowledge").glob("*.yaml")):
        obj = yaml.safe_load(f.read_text(encoding="utf-8"))
        dump(api / "knowledge" / f"{f.stem}.json", obj)
        r = (obj or {}).get("review", {}) if isinstance(obj, dict) else {}
        kfiles.append({"path": f"api/knowledge/{f.stem}.json", "source": f"knowledge/{f.name}",
                       "last_reviewed": str(r.get("last_reviewed", "")), "owner_role": r.get("owner_role", "")})
    dump(api / "index.json", {
        "name": BRAND, "version": VERSION, "generated": date.today().isoformat(), "licence": "Code MIT; content Open Government Licence v3.0 except where stated", "source": repo,
        "website": base, "how_to_use": "Read-only JSON at fixed addresses. No key or sign-in. Show the source and version next to anything you reuse.",
        "endpoints": [{"path": p, "description": d} for p, d, _ in eps] + [{"path": "feed.xml", "description": "Atom feed of releases"},
                                                                        {"path": "sitemap.xml", "description": "Sitemap for search engines"}],
        "knowledge": kfiles})
    # Ask the Commons loads this as a script, so it also works when the portal is opened from files with no web server.
    (target / "ask-index.js").write_text("window.DQP_PASSAGES=" + json.dumps(PASSAGES, ensure_ascii=False, separators=(",", ":")) + ";\n", encoding="utf-8")
    from xml.sax.saxutils import escape as xe
    entries = []
    for r in releases()[:20]:
        body = "".join(f"<li>{xe(i.get('type', '').capitalize())}: {xe(_plain(str(i.get('text', ''))))}</li>" for i in r.get("items", []))
        entries.append(f"<entry><title>Version {xe(str(r['version']))}: {xe(str(r.get('title', '')))}</title><id>{xe(base)}#v{xe(str(r['version']))}</id>"
                       f"<updated>{xe(str(r.get('date', date.today().isoformat())))}T00:00:00Z</updated><link href=\"{xe(base)}index.html\"/>"
                       f"<content type=\"html\">{xe('<ul>' + body + '</ul>')}</content></entry>")
    (target / "feed.xml").write_text('<?xml version="1.0" encoding="utf-8"?>\n<feed xmlns="http://www.w3.org/2005/Atom">'
                                     f"<title>{xe(BRAND)}: releases</title><id>{xe(base)}</id><link href=\"{xe(base)}\"/>"
                                     f"<updated>{date.today().isoformat()}T00:00:00Z</updated><author><name>{xe(BRAND)}</name></author>"
                                     + "".join(entries) + "</feed>\n", encoding="utf-8")
    urls = "".join(f"<url><loc>{xe(base)}{st}.html</loc></url>" for st, _, _ in PAGES)
    (target / "sitemap.xml").write_text('<?xml version="1.0" encoding="utf-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
                                        + urls + "</urlset>\n", encoding="utf-8")


def search_index() -> list:
    """Everything worth finding: pages, their headings, and named items from the knowledge base."""
    idx, seen = [], set()
    PASSAGES.clear()
    def add(title, kind, url, text="", page=""):
        title = _plain(str(title))[:140]
        key = (title.lower(), url)
        if title and key not in seen:
            seen.add(key)
            idx.append({"t": title, "k": kind, "u": url, "p": page, "x": _plain(str(text)).lower()[:400]})
            PASSAGES.append({"t": title, "k": kind, "u": url, "p": page, "x": _plain(str(text))[:700]})
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
    # The capability model: capabilities, records and workflow steps open at the right place on the models page.
    mf = ROOT / "models" / "dq-capability.yaml"
    if mf.exists() and "models" in labels:
        mm = yaml.safe_load(mf.read_text(encoding="utf-8"))
        for c in mm["capabilities"]:
            add(f"{c['name']} (capability {c['id']})", "Capability", f"models.html#cap-{c['id']}", "; ".join(c["children"]) + " " + " ".join(c["guidance"]), labels["models"])
        for e in mm["entities"]:
            add(f"{e['name']} (record)", "Record", f"models.html#ent-{e['name']}", e["description"] + " " + " ".join(a["name"] for a in e["attributes"]), labels["models"])
        for pr in mm["processes"]:
            add(f"{pr['id']} {pr['name']} (workflow)", "Workflow", f"models.html#wf-{pr['id']}", " ".join(pr["lanes"]), labels["models"])
            for s in pr["steps"]:
                if s["kind"] not in ("start", "end"):
                    add(s["name"], f"Workflow step · {pr['id']}", f"models.html#wf-{pr['id']}-{s['id']}", f"{s['lane']} " + " ".join(s.get("guidance", [])), labels["models"])
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
            out.append(f'<div class="dqp-grp" data-g="{GROUP_KEY[g]}"><h2>{g[0]}. {GROUP_TITLE[g]}</h2>{links}</div>')
        else:
            out.append(f'<details class="dqp-g" data-g="{GROUP_KEY[g]}"{" data-current" if cur_g else ""}><summary>{icon(GROUP_ICON[g])}{g}</summary>'
                       f'<div class="dqp-panel{" dqp-wide" if len(ps) > 6 else ""}"><p class="dqp-gt">{GROUP_TITLE[g]}</p>{links}</div></details>')
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


FEEDBACK = yaml.safe_load((ROOT / "knowledge" / "feedback.yaml").read_text(encoding="utf-8"))


ECO = yaml.safe_load((ROOT / "knowledge" / "ecosystem.yaml").read_text(encoding="utf-8"))


def related_elsewhere(stem: str) -> str:
    """'Related elsewhere': the right page of a sister portal at the point of need, naming the portal and its status (v2.10.0)."""
    items = (ECO.get("placements") or {}).get(stem) or []
    if not items:
        return ""
    P = {p["id"]: p for p in ECO["portals"]}
    lis = "".join(
        f'<li data-p="{it["portal"]}"><a href="{html.escape(P[it["portal"]]["url"] + it["path"])}" rel="noopener">{html.escape(it["title"])}</a> '
        f'<span class="dqp-relp">in {html.escape(P[it["portal"]]["name"])} · {html.escape(P[it["portal"]]["status"])}</span>'
        f'<br><span class="dqp-relw">{html.escape(it["why"])}</span></li>' for it in items)
    return (f'<aside class="dqp-rel" aria-labelledby="dqp-rel-h">{icon("network")}<div><h2 id="dqp-rel-h">Related elsewhere</h2>'
            f'<p>Sister open projects, each with its own owner and status. <a href="ecosystem.html">How the three portals fit together</a>.</p>'
            f'<ul>{lis}</ul></div></aside>')


def feedback_strip(stem: str, label: str) -> str:
    """'Tell us about this page' at the end of every page: the Microsoft Form (when set up) and the GitHub form (v2.9.0)."""
    mf = FEEDBACK["microsoft_form"]
    links = []
    if mf.get("prefill_url") and "PAGE" in mf["prefill_url"]:
        links.append((mf["prefill_url"].replace("PAGE", urllib.parse.quote(label)), "Microsoft Form", True))
    elif mf.get("url"):
        links.append((mf["url"], "Microsoft Form", True))
    links.append((f"build.html#contact", "GitHub contact form", False))
    links.append(("build.html#feedback", "other ways to give feedback", False))
    items = " · ".join(f'<a href="{html.escape(u)}"' + (' target="_blank" rel="noopener"' if ext else "") + f'>{html.escape(t)}'
                       + ('<span class="dqp-sr"> (opens in a new tab)</span>' if ext else "") + "</a>" for u, t, ext in links)
    return (f'<aside class="dqp-fb" aria-label="Feedback about this page">{icon("feedback")}<p><b>Is something wrong, missing or hard to use on this page?</b> '
            f'Tell us: {items}. Please don\'t include personal data. '
            f'<span class="dqp-fbx">Is it really about the <a href="{html.escape(FEEDBACK["sister_routes"]["dam"])}" rel="noopener">DAM capability playbooks</a> or the '
            f'<a href="{html.escape(FEEDBACK["sister_routes"]["cat"])}" rel="noopener">GitHub repos asset catalogue</a>? Tell them directly, or tell us and we\'ll pass it on.</span></p></aside>')


def prev_next(stem: str) -> str:
    """Previous and next page in menu order, so people can move through the Commons like a book (v2.8.0)."""
    stems = [o[0] for o in ORDER]
    if stem not in stems:
        return ""
    i = stems.index(stem)
    g = GROUP_OF[stem]
    in_g = [o for o in ORDER if o[2] == g]
    pos = [o[0] for o in in_g].index(stem) + 1

    def link(o, cls, arrow, word):
        s2, label, gg = o
        return (f'<a class="dqp-pn-{cls}" href="{s2}.html" rel="{cls}" data-g="{GROUP_KEY[gg]}">'
                f'<small>{arrow} {word} · {html.escape(GROUP_TITLE[gg])}</small><b>{icon(PAGE_ICON.get(s2, "arrow"))}{html.escape(label)}</b></a>')
    prev = link(ORDER[i - 1], "prev", "←", "Previous") if i > 0 else '<span class="dqp-pn-prev" aria-hidden="true"></span>'
    nxt = link(ORDER[i + 1], "next", "→", "Next") if i < len(ORDER) - 1 else '<span class="dqp-pn-next" aria-hidden="true"></span>'
    dots = "".join(f'<a href="{o[0]}.html" class="dqp-pn-dot"{" aria-current=\"page\"" if o[0] == stem else ""} data-tip="{html.escape(o[1])}">'
                   f'<span class="dqp-sr">{html.escape(o[1])}</span></a>' for o in in_g)
    return (f'<nav class="dqp-pn" aria-label="Previous and next page" data-g="{GROUP_KEY[g]}">{prev}'
            f'<div class="dqp-pn-mid"><span>Page {pos} of {len(in_g)} in <b>{html.escape(GROUP_TITLE[g])}</b></span>'
            f'<span class="dqp-pn-dots">{dots}</span></div>{nxt}</nav>')


def assemble(stem: str, fragment: str, build_label: str, footer: str) -> tuple[str, str]:
    """Return (full document, artifact fragment) for one page."""
    shell = (SRC / "shell.html").read_text(encoding="utf-8")
    shell = (shell.replace("{{NAV}}", nav(stem, False)).replace("{{NAV_LONG}}", nav(stem, True))
             .replace("{{BUILD}}", build_label).replace("{{BRAND}}", BRAND).replace("{{GROUP}}", GROUP_OF.get(stem, ""))
             .replace("{{ICONS}}", (SRC / "icons.svg").read_text(encoding="utf-8").strip())
             .replace("{{VERSION}}", VERSION).replace("{{RELEASES}}", js_json(releases()[:5]))
             .replace("{{SECTION_FLAGS}}", js_json(SECTION_FLAGS.get(stem, {})))
             .replace("{{REPO}}", html.escape(REPO[0]))
             .replace("{{ACRONYMS}}", js_json(ACRONYMS)))
    fragment = fragment.replace("{{REPO}}", html.escape(REPO[0]))  # pages may use the repository placeholder too
    # every page's eyebrow gets that page's icon
    fragment = re.sub(r'<span class="eyebrow">[^<·]*·', lambda m: f'<span class="eyebrow">{GROUP_TITLE.get(GROUP_OF.get(stem, ""), "Commons")} ·', fragment, count=1)
    fragment = fragment.replace('<span class="eyebrow">', f'<span class="eyebrow">{icon(PAGE_ICON.get(stem, "arrow"))}', 1)
    # WCAG 2.1.1 Keyboard: tables scroll sideways on small screens, so every table
    # wrapper must be reachable and scrollable by keyboard, and named for screen readers.
    fragment = re.sub(r'<div class="tbl"(?![^>]*tabindex)',
                      '<div class="tbl" tabindex="0" role="region" aria-label="Table, scrolls sideways on small screens"',
                      fragment)
    fragment = add_easy_read(stem, fragment)
    # group colour key for signposting (v2.8.0)
    fragment = fragment.replace('<div class="wrap"', f'<div class="wrap" data-group="{GROUP_KEY.get(GROUP_OF.get(stem, ""), "start")}"', 1)
    head, body = split_fragment(fragment)
    body += "\n" + related_elsewhere(stem) + "\n" + feedback_strip(stem, dict((p[0], p[1]) for p in PAGES).get(stem, stem)) + "\n" + prev_next(stem)
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
           "EVENTS": "events", "TRAINING": "training", "ONTOLOGY": "ontology", "GRAPH": "ontology", "RELEASES": "releases", "PLAYBOOK": "playbook", "EFFORT": "effort", "STAKEHOLDERS": "stakeholders", "PROFESSIONS": "professions", "REUSE": "reuse", "WHEEL": "dama-wheel", "CHANGE": "change-delivery", "FEEDBACK": "feedback", "STANDARDS": "standards-catalogue", "ECO": "ecosystem", "RESEARCH": "research", "ROADMAP": "roadmap", "CODE": "code-evidence", "GOVBODIES": "governance-bodies", "PARTICIPATION": "participation", "VENDORS": "vendors", "PROVENANCE": "provenance"}


def provenance_feed() -> dict:
    """The content provenance register plus counts per class, for the build page."""
    reg = yaml.safe_load((ROOT / "knowledge" / "provenance.yaml").read_text(encoding="utf-8"))
    counts: dict = {}
    for i in reg["items"]:
        counts[i["class"]] = counts.get(i["class"], 0) + 1
    return {**reg, "counts": counts}


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
<li>{icon("sitemap")} <a href="sitemap.html">Site map</a> · <a href="ask.html">Ask the Commons</a></li>
<li>{icon("share")} <a href="reuse.html">Reuse it</a>: <a href="api/index.json">open data API</a>, <a href="feed.xml">releases feed</a>, embedding and white-label</li>
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
        "__DIAGRAMS__": (SRC / "js" / "diagrams.js").read_text(encoding="utf-8").replace("</script", "<\\/script"),
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
        feedback_docx(dl / "dq-commons-feedback-form-questions.docx")
        if (ROOT / "portal" / "src" / "badges").exists():
            shutil.copytree(ROOT / "portal" / "src" / "badges", target / "badges", dirs_exist_ok=True)
        ambassador_kit(dl / "getinvolved", f"https://{(a.repo.rstrip('/').split('/')[-2:] + ['', ''])[0]}.github.io/{(a.repo.rstrip('/').split('/')[-2:] + ['', ''])[1]}/")
        # Weaver to the UK cross-government metadata model, for review (BL-12): one row per Rosetta concept.
        ro = yaml.safe_load((ROOT / "knowledge" / "rosetta.yaml").read_text(encoding="utf-8"))
        with open(dl / "weaver-uk-mem-mapping.csv", "w", newline="", encoding="utf-8") as fh:
            w = csv.writer(fh)
            w.writerow(["concept_id", "concept", "definition", "DCAT v3", "UK MEM / x-gov", "DQV", "status"])
            for c in ro["concepts"]:
                st = c.get("standards", {})
                w.writerow([c["id"], c["name"], c.get("definition", ""), st.get("DCAT v3", ""), st.get("UK MEM / x-gov", ""), st.get("DQV", ""),
                            "Draft for review by the Data Standards Authority peer review route"])
        research_bundle(dl / "research", f"https://{(a.repo.rstrip('/').split('/')[-2:] + ['', ''])[0]}.github.io/{(a.repo.rstrip('/').split('/')[-2:] + ['', ''])[1]}/")
        owner, name = (a.repo.rstrip("/").split("/")[-2:] + ["", ""])[:2]
        write_api(target, a.repo, f"https://{owner}.github.io/{name}/")
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
