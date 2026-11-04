"""The Commons knowledge graph: every concept in the knowledge base, linked, explainable and exportable.

In plain English:
- It reads the knowledge base (frameworks, packs, the issue and dimension vocabulary, check types, the Metadata
  Rosetta, roles, modules, skills, courses, events, jurisdictions, partners, the glossary and thesaurus, and the
  lineage flows in knowledge/ontology.yaml) and builds one graph of nodes (things) and edges (relationships).
- Every relationship is named by a property in the ontology (knowledge/ontology.yaml), with a domain and range,
  so the graph is self-describing.
- It writes the graph as JSON (for the portal), JSON-LD and Turtle (SKOS and OWL, for other tools), and answers
  questions: find a concept, list its neighbours, or trace the path that links two concepts.

Nothing is invented: every node and edge comes from a knowledge file, and each node records which file.
"""
from __future__ import annotations

import csv
import json
import re
from collections import deque
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
K = ROOT / "knowledge"
NS = "https://cyberdudeuk.github.io/ndl-dq-assurance/vocab#"


def _y(name):
    return yaml.safe_load((K / f"{name}.yaml").read_text(encoding="utf-8"))


def slug(s) -> str:
    return re.sub(r"[^a-z0-9]+", "-", str(s).lower()).strip("-")


class Graph:
    def __init__(self):
        self.nodes, self.edges, self._seen = {}, [], set()

    def node(self, type_, key, label, **kw):
        nid = f"{type_}:{slug(key)}"
        if nid not in self.nodes:
            self.nodes[nid] = {"id": nid, "type": type_, "label": str(label), **{k: v for k, v in kw.items() if v not in (None, "", [])}}
        else:
            for k, v in kw.items():
                if v not in (None, "", []) and k not in self.nodes[nid]:
                    self.nodes[nid][k] = v
        return nid

    def edge(self, s, p, o, note=None):
        if s == o or (s, p, o) in self._seen:
            return
        self._seen.add((s, p, o))
        e = {"s": s, "p": p, "o": o}
        if note:
            e["note"] = str(note)
        self.edges.append(e)

    def to_dict(self):
        return {"nodes": list(self.nodes.values()), "edges": self.edges}


def build() -> dict:
    """Build the whole graph. Returns {nodes, edges, ontology, stats}."""
    from . import packs, rules
    ont = _y("ontology")
    g = Graph()

    # quality dimensions and issue types (vocab/)
    with open(ROOT / "vocab" / "dimensions.csv", newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            g.node("Dimension", r["id"], r["label"], definition=r["definition"], source="vocab/dimensions.csv")
    with open(ROOT / "vocab" / "issue-types.csv", newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            i = g.node("IssueType", r["id"], r["label"], definition=r["definition"], source="vocab/issue-types.csv")
            g.edge(i, "inDimension", f"Dimension:{slug(r['dimension'])}")

    # check types: default issue type and dimension
    issue_dim = {n["id"]: e["o"] for e in g.edges if e["p"] == "inDimension" for n in [g.nodes[e["s"]]]}
    for c in sorted(set(rules.CHECKS) | {"in_valueset"}):
        cid = g.node("Check", c, c, source="dqkit/rules.py")
        it = rules.DEFAULT_ISSUE.get(c) or ("invalid-category" if c == "in_valueset" else None)
        if it:
            g.edge(cid, "defaultIssue", f"IssueType:{slug(it)}")
            if f"IssueType:{slug(it)}" in issue_dim:
                g.edge(cid, "checksDimension", issue_dim[f"IssueType:{slug(it)}"])

    # frameworks, jurisdictions
    for f in _y("frameworks")["frameworks"]:
        fid = g.node("Framework", f["id"], f["name"], definition=f.get("status", ""), url=f.get("url"), source="knowledge/frameworks.yaml",
                     detail=f"{f.get('publisher', '')} · {f.get('sector', '')} · {f.get('year', '')}")
        j = g.node("Jurisdiction", f["jurisdiction"], f["jurisdiction"], source="knowledge/frameworks.yaml")
        g.edge(fid, "appliesIn", j)
        for fd, dims in (f.get("map") or {}).items():
            for d in dims:
                g.edge(fid, "mapsTo", f"Dimension:{slug(d)}", note=fd)

    # policy clauses (clause-by-clause breakdown)
    with open(K / "requirements.csv", newline="", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            cid = g.node("PolicyClause", f"{r['source']}-{r['clause']}", f"{r['clause']}: {r['requirement']}",
                         definition=f"Area: {r['area']}. Strength: {r['strength']}. Toolkit: {r['kit_support']}",
                         source="knowledge/requirements.csv")
            g.edge(cid, "clauseOf", f"Framework:{slug(r['source'])}")

    # packs and requirements
    for p in packs.list_packs():
        pid = g.node("Pack", p["id"], p["name"], definition=p.get("summary", ""), source=f"packs/{p['id']}.yaml")
        for fw in p.get("frameworks", []):
            g.edge(pid, "implements", f"Framework:{slug(fw)}")
        for r in p["requirements"]:
            rid = g.node("Requirement", f"{p['id']}-{r['id']}", f"{r['id']}: {r['text']}", source=f"packs/{p['id']}.yaml")
            g.edge(pid, "requires", rid)
            ev = r.get("evidence", {})
            for c in ev.get("checks", []) + ev.get("any_checks", []):
                g.edge(rid, "evidencedBy", f"Check:{slug(c)}")
            for d in ev.get("dimensions", []) + ev.get("any_dimension", []):
                g.edge(rid, "evidencedBy", f"Dimension:{slug(d)}")

    # Metadata Rosetta
    ro = _y("rosetta")
    for s in ro["standards"]:
        g.node("MetadataStandard", s, s, source="knowledge/rosetta.yaml")
    for c in ro["concepts"]:
        cid = g.node("MetadataConcept", c["id"], c["name"], definition=c.get("definition", ""), lineage=c.get("lineage", ""),
                     source="knowledge/rosetta.yaml")
        mapped = False
        for s, term in (c.get("standards") or {}).items():
            if term and term not in ("-", "–"):
                g.edge(cid, "expressedIn", f"MetadataStandard:{slug(s)}", note=term)
                mapped = True
        if not mapped:  # open standards and policy concepts with no per-standard term: they are about metadata
            g.edge(cid, "about", "Term:metadata")

    # roles, modules, skills, courses
    L, T = _y("learning"), _y("training")
    for r in L["roles"]:
        g.node("Role", r["id"], r["name"], definition=r.get("needs", ""), detail=r.get("ddat", ""), source="knowledge/learning.yaml")
    for m in L["modules"]:
        mid = g.node("Module", m["id"], f"{m['id'].upper()}: {m['title']}", definition=m.get("capability", ""), url=f"learn.html#{m['id']}",
                     source="knowledge/learning.yaml")
        for r in m.get("roles", []):
            g.edge(mid, "forRole", f"Role:{slug(r)}")
    for s in T["skills"]:
        sid = g.node("Skill", s["id"], s["name"], definition=s["what"], detail=s.get("ddat", ""), url=f"training.html#{s['id']}",
                     source="knowledge/training.yaml")
        for m in s.get("modules", []):
            g.edge(f"Module:{slug(m)}", "teaches", sid)
        for r in L["roles"]:
            if set(s.get("modules", [])) & {m["id"] for m in L["modules"] if r["id"] in m.get("roles", [])}:
                g.edge(f"Role:{slug(r['id'])}", "needsSkill", sid)
    for c in T["courses"]:
        cid = g.node("Course", c["id"], c["title"], definition=f"{c['provider']} · {c['format']} · {c['cost']}", url=c["url"],
                     source="knowledge/training.yaml")
        for s in c.get("skills", []):
            g.edge(cid, "teaches", f"Skill:{slug(s)}")

    # jurisdictions and partners
    G = _y("global")
    cds = g.node("Jurisdiction", "Crown Dependencies", "Crown Dependencies", source="knowledge/global.yaml")
    ots = g.node("Jurisdiction", "UK Overseas Territories", "UK Overseas Territories", source="knowledge/global.yaml")
    for c in G["crown_dependencies"]:
        j = g.node("Jurisdiction", c["name"], c["name"], definition=f"Statistics: {c['stats_body']}. Data protection: {c['dp']}.",
                   url=c.get("stats_url"), source="knowledge/global.yaml")
        g.edge(j, "partOf", cds)
    for t in G["overseas_territories"]:
        j = g.node("Jurisdiction", t["name"], t["name"], definition=f"{t['region']}" + (f" · ISO {t['iso']}" if t.get("iso") else ""),
                   source="knowledge/global.yaml")
        g.edge(j, "partOf", ots)
    for p in G["partners"]:
        oid = g.node("Organisation", p["id"], p["name"], definition=p["use"], url=p["url"], source="knowledge/global.yaml")
        g.edge(oid, "appliesIn", g.node("Jurisdiction", p["level"], p["level"], source="knowledge/global.yaml"))
        if p.get("pack"):
            g.edge(f"Pack:{slug(p['pack'])}", "implements", oid)

    # events
    for e in _y("events")["events"]:
        eid = g.node("Event", e["id"], e["title"], definition=f"{e['start'][:10]} · {e['format']} · {e['location']}", url=e["url"],
                     source="knowledge/events.yaml")
        g.edge(eid, "heldIn", g.node("Jurisdiction", e["region"], e["region"], source="knowledge/events.yaml"))

    # glossary and thesaurus
    terms = {}
    for t in L["glossary"]:
        terms[t["term"]] = {"definition": t["definition"], "source": "knowledge/learning.yaml"}
    for t in ont["thesaurus"]:
        d = terms.setdefault(t["term"], {"source": "knowledge/ontology.yaml"})
        if t.get("definition"):
            d.setdefault("definition", t["definition"])
        for k in ("alt", "broader", "related"):
            d[k] = t.get(k, [])
    for name, d in terms.items():
        g.node("Term", name, name, definition=d.get("definition", ""), alt=d.get("alt", []), source=d["source"])
    for name, d in terms.items():
        for b in d.get("broader", []):
            if b in terms:
                g.edge(f"Term:{slug(name)}", "broader", f"Term:{slug(b)}")
        for r in d.get("related", []):
            if r in terms:
                g.edge(f"Term:{slug(name)}", "related", f"Term:{slug(r)}")
    # terms that name a dimension, role or metadata standard are the same concept
    for name in terms:
        for t in ("Dimension", "Role", "MetadataStandard"):
            for n in g.nodes.values():
                if n["type"] == t and n["label"].lower() in (name.lower(), name.lower() + " v3"):
                    g.edge(f"Term:{slug(name)}", "sameAs", n["id"])

    # event topics that are glossary terms
    for e in _y("events")["events"]:
        for t in e.get("topics", []):
            if f"Term:{slug(t)}" in g.nodes:
                g.edge(f"Event:{slug(e['id'])}", "about", f"Term:{slug(t)}")

    # lineage
    for flow in ont["lineage"]:
        for s in flow["stages"]:
            g.node("Stage", s["id"], s["label"], definition=s["what"], detail=flow["title"], source="knowledge/ontology.yaml")
        for a, b in flow["flows"]:
            g.edge(f"Stage:{slug(a)}", "flowsTo", f"Stage:{slug(b)}", note=flow["title"])
        for s in flow["stages"]:
            for target in s.get("links", []):
                g.edge(f"Stage:{slug(s['id'])}", "involves", target)

    # the places the Commons serves
    scope = g.node("Jurisdiction", "Commons scope", "Places the Commons serves", definition="The UK and its nations, the Crown Dependencies, the Overseas Territories, the Commonwealth and international partners.",
                   source="knowledge/global.yaml")
    for j in ("UK", "England", "Scotland", "Wales", "Northern Ireland", "Crown Dependencies", "UK Overseas Territories", "International", "Supranational", "National"):
        if f"Jurisdiction:{slug(j)}" in g.nodes:
            g.edge(f"Jurisdiction:{slug(j)}", "inScope", scope)

    # the capability model (models/dq-capability.yaml): capabilities, workflows and record types
    mf = ROOT / "models" / "dq-capability.yaml"
    if mf.exists():
        import re as _re
        mm = yaml.safe_load(mf.read_text(encoding="utf-8"))
        fw = {"DAM": "uk-dam-policy", "IDC": "uk-identify-cda", "MD": "uk-cda-metadata", "DOM": "uk-data-ownership-model", "DQAP": "uk-dqap",
              "IF": "uk-dqap", "GDQF": "uk-gdqf", "COP": "uk-code-of-practice-3", "QAAD": "uk-qaad", "ICO": "uk-ico-accuracy"}
        def guide(code):
            base = _re.sub(r"\d+$", "", code).split("-")[0]
            return f"Framework:{slug(fw[base])}" if base in fw else None
        for e in mm["entities"]:
            rid = g.node("RecordType", e["name"], e["name"], definition=e["description"], detail=e["group"], source="models/dq-capability.yaml")
            for gcode in e.get("guidance", []):
                if guide(gcode):
                    g.edge(rid, "guidedBy", guide(gcode))
        for e in mm["entities"]:
            for a in e["attributes"]:
                if a["type"].startswith("ref:") and a["type"][4:] != e["name"]:
                    g.edge(f"RecordType:{slug(e['name'])}", "linksTo", f"RecordType:{slug(a['type'][4:])}", note=a["name"])
        for c in mm["capabilities"]:
            cid = g.node("Capability", c["id"], f"{c['id']} {c['name']}", definition="; ".join(c["children"]), source="models/dq-capability.yaml")
            for gcode in c["guidance"]:
                if guide(gcode):
                    g.edge(cid, "guidedBy", guide(gcode))
            for en in c["entities"]:
                g.edge(cid, "keepsRecord", f"RecordType:{slug(en)}")
        for pr in mm["processes"]:
            wid = g.node("Workflow", pr["id"], f"{pr['id']} {pr['name']}", definition=f"{len(pr['steps'])} steps across: " + ", ".join(pr["lanes"]), source="models/dq-capability.yaml")
            g.edge(f"Capability:{slug(pr['capability'])}", "realisedBy", wid)
            for lane in pr["lanes"]:
                lr = (mm.get("lanes", {}).get(lane) or {}).get("learning")
                if lr:
                    g.edge(wid, "performedBy", f"Role:{slug(lr)}")
            for en in sorted({en for s in pr["steps"] for en in s.get("outputs", [])}):
                g.edge(wid, "createsRecord", f"RecordType:{slug(en)}")

    # keep only edges whose ends exist
    d = g.to_dict()
    ids = set(g.nodes)
    dangling = [e for e in d["edges"] if e["s"] not in ids or e["o"] not in ids]
    d["edges"] = [e for e in d["edges"] if e["s"] in ids and e["o"] in ids]
    types = {}
    for n in d["nodes"]:
        types[n["type"]] = types.get(n["type"], 0) + 1
    d["stats"] = {"nodes": len(d["nodes"]), "edges": len(d["edges"]), "types": types, "dangling": len(dangling)}
    d["dangling"] = dangling
    return d


# ---------- questions ----------

def _index(g):
    adj = {}
    for e in g["edges"]:
        adj.setdefault(e["s"], []).append((e["p"], e["o"], "out"))
        adj.setdefault(e["o"], []).append((e["p"], e["s"], "in"))
    return adj


def find(g: dict, q: str, limit: int = 20) -> list:
    """Nodes whose label, id, alternative labels or definition match the words in q (best first)."""
    words = [w for w in q.lower().split() if w]
    out = []
    for n in g["nodes"]:
        hay = " ".join([n["label"], n["id"], " ".join(n.get("alt", [])), n.get("definition", "")]).lower()
        score = sum(w in hay for w in words) + (3 if n["label"].lower() == q.lower() else 0) + (1 if q.lower() in n["label"].lower() else 0)
        if score >= len(words) and words:
            out.append((score, n))
    out.sort(key=lambda x: (-x[0], x[1]["label"]))
    return [n for _, n in out[:limit]]


def neighbours(g: dict, node_id: str) -> list:
    adj, nodes = _index(g), {n["id"]: n for n in g["nodes"]}
    return [{"property": p, "direction": d, "node": nodes[o]} for p, o, d in adj.get(node_id, [])]


def path(g: dict, a: str, b: str, max_len: int = 8) -> list:
    """The shortest chain of relationships from a to b (either direction), as [node, property, node, ...]."""
    adj = _index(g)
    prev, q = {a: None}, deque([a])
    while q:
        x = q.popleft()
        if x == b:
            break
        for p, o, d in adj.get(x, []):
            if o not in prev:
                prev[o] = (x, p, d)
                q.append(o)
    if b not in prev:
        return []
    chain, x = [b], b
    while prev[x]:
        px, p, d = prev[x]
        chain[:0] = [px, f"{p}" if d == "out" else f"{p} (inverse)"]
        x = px
    return chain if len(chain) // 2 <= max_len else []


# ---------- exports ----------

def _iri(nid):
    return NS + "k/" + nid.replace(":", "/")


def to_jsonld(g: dict) -> dict:
    ont = _y("ontology")
    ctx = {"dqc": NS, "skos": "http://www.w3.org/2004/02/skos/core#", "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
           "owl": "http://www.w3.org/2002/07/owl#", "label": "rdfs:label", "definition": "skos:definition",
           "altLabel": "skos:altLabel", "seeAlso": {"@id": "rdfs:seeAlso", "@type": "@id"}}
    graph = []
    for c in ont["classes"]:
        graph.append({"@id": f"dqc:{c['id']}", "@type": "owl:Class", "label": c["label"], "definition": c["definition"]})
    for p in ont["properties"]:
        graph.append({"@id": f"dqc:{p['id']}", "@type": "owl:ObjectProperty", "label": p["label"], "definition": p["definition"],
                      "rdfs:domain": {"@id": f"dqc:{p['domain']}"}, "rdfs:range": {"@id": f"dqc:{p['range']}"}})
    by = {}
    for e in g["edges"]:
        by.setdefault(e["s"], []).append(e)
    for n in g["nodes"]:
        o = {"@id": _iri(n["id"]), "@type": [f"dqc:{n['type']}"] + (["skos:Concept"] if n["type"] in ("Term", "Dimension", "IssueType", "MetadataConcept") else []),
             "label": n["label"]}
        if n.get("definition"):
            o["definition"] = n["definition"]
        if n.get("alt"):
            o["altLabel"] = n["alt"]
        if n.get("url", "").startswith("http"):
            o["seeAlso"] = n["url"]
        if n["type"] in ("Dimension", "IssueType"):  # same concept as the published quality vocabulary (vocab/dq-vocab.ttl)
            key = n["id"].split(":", 1)[1]
            o["owl:sameAs"] = [{"@id": NS + (key if n["type"] == "Dimension" else "issue/" + key)}]
        for e in by.get(n["id"], []):
            key = {"broader": "skos:broader", "related": "skos:related"}.get(e["p"], f"dqc:{e['p']}")
            o.setdefault(key, []).append({"@id": _iri(e["o"])})
        graph.append(o)
    return {"@context": ctx, "@graph": graph}


def _lit(s):
    return '"' + str(s).replace("\\", "\\\\").replace('"', '\\"').replace("\n", " ") + '"@en'


def to_turtle(g: dict) -> str:
    """SKOS/OWL Turtle of the ontology and the graph."""
    doc = to_jsonld(g)
    lines = ["@prefix dqc: <" + NS + "> .", "@prefix skos: <http://www.w3.org/2004/02/skos/core#> .",
             "@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .", "@prefix owl: <http://www.w3.org/2002/07/owl#> .", ""]
    ref = lambda i: i if i.startswith("dqc:") or i.startswith("skos:") or i.startswith("owl:") else f"<{i}>"
    for o in doc["@graph"]:
        types = o["@type"] if isinstance(o["@type"], list) else [o["@type"]]
        parts = [f"{ref(o['@id'])} a {', '.join(types)}", f"  rdfs:label {_lit(o['label'])}"]
        if o.get("definition"):
            parts.append(f"  skos:definition {_lit(o['definition'])}")
        for a in o.get("altLabel", []):
            parts.append(f"  skos:altLabel {_lit(a)}")
        if o.get("seeAlso"):
            parts.append(f"  rdfs:seeAlso <{o['seeAlso']}>")
        for k, v in o.items():
            if k.startswith(("dqc:", "skos:broader", "skos:related", "rdfs:domain", "rdfs:range", "owl:sameAs")):
                vs = v if isinstance(v, list) else [v]
                parts.append(f"  {k} " + ", ".join(ref(x["@id"]) for x in vs))
        lines.append(" ;\n".join(parts) + " .")
    return "\n".join(lines) + "\n"
