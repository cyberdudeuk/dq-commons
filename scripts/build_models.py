#!/usr/bin/env python3
"""Build every export of the enterprise data quality capability model from models/dq-capability.yaml.

Plain English: one YAML file describes the data model, the capability map and the workflows. This script
writes the same content in the formats that enterprise architecture, data modelling and process tools read:

  models/out/archimate/dq-capability.xml        ArchiMate 3.1 Open Exchange Format (Archi, BiZZdesign, Sparx EA, ADOIT, ...)
  models/out/archimate/csv/dq-*.csv             Archi CSV import set (elements, relations, properties)
  models/out/uml/dq-data-model.xmi              UML 2.5.1 XMI class model (Sparx EA, MagicDraw/Cameo, Visual Paradigm, Papyrus)
  models/out/sql/dq-data-model.sql              PostgreSQL DDL (also imports into erwin, ER/Studio, dbdiagram, DBeaver)
  models/out/json/dq-data-model.schema.json     JSON Schema 2020-12 (APIs, validation, data contracts)
  models/out/rdf/dq-data-model.ttl              OWL ontology in Turtle (Protege, TopBraid, knowledge graphs)
  models/out/dictionary/data-dictionary.csv     Data dictionary (spreadsheets, catalogues such as Purview or Collibra)
  models/out/dictionary/capability-guidance-matrix.csv   Capabilities against the government guidance
  models/out/erd/dq-data-model.mmd              Entity relationship diagram (Mermaid); --svg also renders it
  models/out/visio/dq-capability-process-map.vsdx  Visio process map: capability map overlaid with GDQF, 5 workflows, info model
  models/out/bpmn/P1..P5-*.bpmn                 BPMN 2.0 workflows with diagram layout (Camunda, Signavio, Bizagi, ARIS, bpmn.io)

Every output is deterministic, so `--check` can confirm the committed files match the YAML (used in CI).

Usage:  python3 scripts/build_models.py            write everything
        python3 scripts/build_models.py --check    fail if any committed export is out of date
        python3 scripts/build_models.py --svg      also render the ERD to SVG (needs mmdc)
        python3 scripts/build_models.py --render   also make a PDF of the process map and PNG previews (needs LibreOffice)
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
import re
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path
from xml.sax.saxutils import escape

import yaml

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "models" / "dq-capability.yaml"
OUT = ROOT / "models" / "out"

# Which GDQF principle a guidance code mostly serves, used to colour workflow steps (the "overlay").
GUIDANCE_PRINCIPLE = {
    "DAM": "GDQF-P1", "IDC": "GDQF-P1", "DOM": "GDQF-P1", "DQAP1": "GDQF-P1", "GDQF-P1": "GDQF-P1",
    "DQAP2": "GDQF-P2", "GDQF-P2": "GDQF-P2",
    "DQAP3": "GDQF-P3", "DQAP4": "GDQF-P3", "DQAP7": "GDQF-P3", "IF": "GDQF-P3", "GDQF-P3": "GDQF-P3",
    "DQAP6": "GDQF-P4", "MD": "GDQF-P4", "DQV": "GDQF-P4", "COP": "GDQF-P4", "GDQF-P4": "GDQF-P4",
    "DQAP5": "GDQF-P5", "QAAD": "GDQF-P5", "GDQF-P5": "GDQF-P5",
}


# ----------------------------------------------------------------------------------------------- helpers
def load() -> dict:
    m = yaml.safe_load(SRC.read_text(encoding="utf-8"))
    validate(m)
    return m


def validate(m: dict) -> None:
    """Stop early, in plain English, if the YAML refers to something that does not exist."""
    names = {e["name"] for e in m["entities"]}
    enums = set(m["enums"])
    codes = set(m["guidance"]) | {p["id"] for p in m["principles"]}
    problems = []
    allowed = {"entity": {"name", "group", "description", "guidance", "attributes"},
               "attribute": {"name", "type", "key", "required", "many", "description"},
               "capability": {"id", "name", "principle", "guidance", "entities", "children"},
               "process": {"id", "name", "capability", "lanes", "steps"},
               "step": {"id", "kind", "name", "lane", "guidance", "outputs", "inputs", "branches", "next"}}

    def keys_ok(kind: str, obj: dict, where: str) -> None:
        # A comma inside an unquoted value in {...} splits it into a stray key; catch that here.
        extra = set(obj) - allowed[kind]
        if extra:
            problems.append(f"{where} has unexpected fields {sorted(map(str, extra))} (put quotes round text that contains a comma)")

    for e in m["entities"]:
        keys_ok("entity", e, e["name"])
        for a in e["attributes"]:
            keys_ok("attribute", a, f"{e['name']}.{a['name']}")
    for c in m["capabilities"]:
        keys_ok("capability", c, c["id"])
    for p in m["processes"]:
        keys_ok("process", p, p["id"])
        for s in p["steps"]:
            keys_ok("step", s, f"{p['id']}.{s['id']}")

    def code_ok(c: str) -> bool:
        return c in codes or re.sub(r"\d+$", "", c) in codes or c in GUIDANCE_PRINCIPLE or c in {"GDQF-LC", "GDQF-D", "ISO8000", "DCAT", "DQV", "ODCS", "ICO"}

    for e in m["entities"]:
        keys = [a for a in e["attributes"] if a.get("key")]
        if len(keys) != 1:
            problems.append(f"{e['name']} needs exactly one key attribute")
        for a in e["attributes"]:
            t = a["type"]
            if t.startswith("ref:") and t[4:] not in names:
                problems.append(f"{e['name']}.{a['name']} refers to unknown entity {t[4:]}")
            if t.startswith("enum:") and t[5:] not in enums:
                problems.append(f"{e['name']}.{a['name']} uses unknown list {t[5:]}")
        for g in e.get("guidance", []):
            if not code_ok(g):
                problems.append(f"{e['name']} cites unknown guidance {g}")
    caps = {c["id"] for c in m["capabilities"]}
    for c in m["capabilities"]:
        for en in c.get("entities", []):
            if en not in names:
                problems.append(f"capability {c['id']} lists unknown entity {en}")
    for p in m["processes"]:
        if p["capability"] not in caps:
            problems.append(f"process {p['id']} has unknown capability")
        ids = {s["id"] for s in p["steps"]}
        for s in p["steps"]:
            if s["lane"] not in p["lanes"]:
                problems.append(f"{p['id']}.{s['id']} uses unknown lane {s['lane']}")
            for t in list((s.get("branches") or {}).values()) + ([s["next"]] if s.get("next") else []):
                if t not in ids:
                    problems.append(f"{p['id']}.{s['id']} goes to unknown step {t}")
            for en in s.get("outputs", []) + s.get("inputs", []):
                if en not in names:
                    problems.append(f"{p['id']}.{s['id']} uses unknown entity {en}")
            for g in s.get("guidance", []):
                if not code_ok(g):
                    problems.append(f"{p['id']}.{s['id']} cites unknown guidance {g}")
    if problems:
        sys.exit("The model has problems:\n  " + "\n  ".join(problems))


def snake(name: str) -> str:
    return re.sub(r"(?<!^)(?=[A-Z])", "_", name).lower()


def slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def uid(*parts: str) -> str:
    """Stable identifier, valid as an XML ID (starts with a letter)."""
    return "id-" + hashlib.sha1("|".join(parts).encode()).hexdigest()[:16]


def xa(s) -> str:
    return escape(str(s), {'"': "&quot;"})


def key_of(e: dict) -> dict:
    return next(a for a in e["attributes"] if a.get("key"))


def entity(m: dict, name: str) -> dict:
    return next(e for e in m["entities"] if e["name"] == name)


def flows(p: dict) -> list[tuple[str, str, str]]:
    """Sequence flows (source, target, label) for a process."""
    steps = p["steps"]
    out = []
    for i, s in enumerate(steps):
        if s["kind"] == "end":
            continue
        if s["kind"] == "gateway":
            for label, tgt in s["branches"].items():
                out.append((s["id"], tgt, str(label)))
        elif s.get("next"):
            out.append((s["id"], s["next"], ""))
        else:
            nxt = next((t for t in steps[i + 1:]), None)
            if nxt:
                out.append((s["id"], nxt["id"], ""))
    return out


def step_principle(s: dict) -> str | None:
    for g in s.get("guidance", []):
        if g in GUIDANCE_PRINCIPLE:
            return GUIDANCE_PRINCIPLE[g]
    return None


def csv_text(rows: list[list]) -> str:
    buf = io.StringIO()
    w = csv.writer(buf, quoting=csv.QUOTE_ALL, lineterminator="\n")
    w.writerows(rows)
    return buf.getvalue()


# ----------------------------------------------------------------------------------------------- data dictionary
def data_dictionary(m: dict) -> dict[str, str]:
    rows = [["entity", "group", "attribute", "type", "key", "required", "many", "references", "allowed_values", "description", "entity_guidance"]]
    for e in m["entities"]:
        for a in e["attributes"]:
            t = a["type"]
            ref = t[4:] if t.startswith("ref:") else ""
            allowed = "; ".join(m["enums"][t[5:]]) if t.startswith("enum:") else ""
            base = "reference" if ref else ("enum" if allowed else t)
            rows.append([e["name"], e["group"], a["name"], base, "yes" if a.get("key") else "", "yes" if a.get("required") or a.get("key") else "",
                         "yes" if a.get("many") else "", ref, allowed, a.get("description", ""), " ".join(e.get("guidance", []))])
    mat = [["capability_id", "capability", "gdqf_principle", "guidance", "entities", "sub_capabilities", "processes"]]
    for c in m["capabilities"]:
        procs = " ".join(p["id"] for p in m["processes"] if p["capability"] == c["id"])
        mat.append([c["id"], c["name"], c["principle"], " ".join(c["guidance"]), " ".join(c["entities"]), "; ".join(c["children"]), procs])
    return {"dictionary/data-dictionary.csv": csv_text(rows), "dictionary/capability-guidance-matrix.csv": csv_text(mat)}


# ----------------------------------------------------------------------------------------------- SQL
SQL_TYPES = {"string": "text", "text": "text", "integer": "integer", "decimal": "numeric", "boolean": "boolean",
             "date": "date", "datetime": "timestamptz", "url": "text"}


def table_order(m: dict) -> list[dict]:
    """Tables in an order where every table comes after the tables it refers to (YAML order breaks ties)."""
    names = [x["name"] for x in m["entities"]]
    deps = {e["name"]: {a["type"][4:] for a in e["attributes"]
                        if a["type"].startswith("ref:") and not a.get("many") and a["type"][4:] != e["name"]} for e in m["entities"]}
    done: list[str] = []
    while len(done) < len(names):
        ready = [n for n in names if n not in done and deps[n] <= set(done)]
        if not ready:
            sys.exit("The data model has a loop of required links between tables: " + ", ".join(n for n in names if n not in done))
        done.append(ready[0])
    return [entity(m, n) for n in done]


def sql(m: dict) -> dict[str, str]:
    out = [f"-- {m['name']}: logical data model as PostgreSQL DDL (model version {m['version']}).",
           "-- Generated by scripts/build_models.py from models/dq-capability.yaml. Do not edit by hand.",
           "-- Holds roles, not personal contact details: a named data owner is a role holder, and contact routes are forms.", ""]
    links = []
    for e in table_order(m):
        t = snake(e["name"])
        cols, comments = [], [f"COMMENT ON TABLE {t} IS '{e['description'].replace(chr(39), chr(39) * 2)}';"]
        for a in e["attributes"]:
            ty = a["type"]
            if a.get("many"):
                tgt = ty.split(":", 1)[1]
                links.append((e, a, tgt))
                continue
            if ty.startswith("ref:"):
                tgt = entity(m, ty[4:])
                col = f"  {a['name']} text REFERENCES {snake(tgt['name'])}({key_of(tgt)['name']})"
            elif ty.startswith("enum:"):
                vals = ", ".join("'" + v.replace("'", "''") + "'" for v in m["enums"][ty[5:]])
                col = f"  {a['name']} text CHECK ({a['name']} IN ({vals}))"
            else:
                col = f"  {a['name']} {SQL_TYPES[ty]}"
            if a.get("key"):
                col += " PRIMARY KEY"
            elif a.get("required"):
                col += " NOT NULL"
            cols.append(col)
            if a.get("description"):
                comments.append(f"COMMENT ON COLUMN {t}.{a['name']} IS '{a['description'].replace(chr(39), chr(39) * 2)}';")
        out.append(f"CREATE TABLE {t} (\n" + ",\n".join(cols) + "\n);")
        out.extend(comments)
        out.append("")
    for e, a, tgt in links:
        t = f"{snake(e['name'])}_{a['name']}"
        k = key_of(e)["name"]
        if tgt in m["enums"]:
            vals = ", ".join("'" + v.replace("'", "''") + "'" for v in m["enums"][tgt])
            other = f"  value text NOT NULL CHECK (value IN ({vals}))"
            pk = f"{k}, value"
        else:
            te = entity(m, tgt)
            tk = key_of(te)["name"]
            other = f"  {snake(tgt)}_{tk} text NOT NULL REFERENCES {snake(tgt)}({tk})"
            pk = f"{k}, {snake(tgt)}_{tk}"
        out.append(f"CREATE TABLE {t} (\n  {k} text NOT NULL REFERENCES {snake(e['name'])}({k}),\n{other},\n  PRIMARY KEY ({pk})\n);")
        out.append(f"COMMENT ON TABLE {t} IS 'Links {e['name']} to its {a['name'].replace('_', ' ')}.';")
        out.append("")
    return {"sql/dq-data-model.sql": "\n".join(out)}


# ----------------------------------------------------------------------------------------------- JSON Schema
JSON_TYPES = {"string": {"type": "string"}, "text": {"type": "string"}, "integer": {"type": "integer"},
              "decimal": {"type": "number"}, "boolean": {"type": "boolean"}, "date": {"type": "string", "format": "date"},
              "datetime": {"type": "string", "format": "date-time"}, "url": {"type": "string", "format": "uri"}}


def json_schema(m: dict) -> dict[str, str]:
    defs = {}
    for e in m["entities"]:
        props, req = {}, []
        for a in e["attributes"]:
            ty = a["type"]
            if ty.startswith("ref:"):
                p = {"type": "string", "$comment": f"Identifier of a {ty[4:]}"}
            elif ty.startswith("enum:"):
                p = {"enum": m["enums"][ty[5:]]}
            else:
                p = dict(JSON_TYPES[ty])
            if a.get("many"):
                p = {"type": "array", "items": p, "uniqueItems": True}
            if a.get("description"):
                p["description"] = a["description"]
            props[a["name"]] = p
            if a.get("key") or a.get("required"):
                req.append(a["name"])
        defs[e["name"]] = {"type": "object", "title": e["name"], "description": e["description"],
                           "properties": props, "required": req, "additionalProperties": False}
    schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": m["namespace"].rstrip("#") + "/dq-data-model.schema.json",
        "title": m["name"],
        "description": "A data set of records for the enterprise data quality capability. Each property holds a list of one kind of record. Generated from models/dq-capability.yaml.",
        "type": "object",
        "properties": {snake(e["name"]): {"type": "array", "items": {"$ref": f"#/$defs/{e['name']}"}} for e in m["entities"]},
        "additionalProperties": False,
        "$defs": defs,
    }
    return {"json/dq-data-model.schema.json": json.dumps(schema, indent=2, ensure_ascii=False) + "\n"}


# ----------------------------------------------------------------------------------------------- OWL / Turtle
XSD = {"string": "xsd:string", "text": "xsd:string", "integer": "xsd:integer", "decimal": "xsd:decimal", "boolean": "xsd:boolean",
       "date": "xsd:date", "datetime": "xsd:dateTime", "url": "xsd:anyURI"}


def tl(s: str) -> str:
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"@en'


def turtle(m: dict) -> dict[str, str]:
    L = ["@prefix dqm: <" + m["namespace"] + "> .", "@prefix owl: <http://www.w3.org/2002/07/owl#> .",
         "@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .", "@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .",
         "@prefix dct: <http://purl.org/dc/terms/> .", "@prefix skos: <http://www.w3.org/2004/02/skos/core#> .", "",
         f"<{m['namespace'].rstrip('#')}> a owl:Ontology ;", f"  rdfs:label {tl(m['name'])} ;",
         f"  owl:versionInfo \"{m['version']}\" ;", "  dct:license <https://opensource.org/licenses/MIT> ;",
         f"  rdfs:comment {tl('Logical data model of the enterprise data quality capability, generated from models/dq-capability.yaml.')} .", ""]
    for name, vals in m["enums"].items():
        cls = "".join(w.capitalize() for w in name.split("_")) + "Value"
        L += [f"dqm:{cls} a owl:Class ; rdfs:label {tl(name.replace('_', ' '))} ;",
              "  owl:oneOf ( " + " ".join(f"dqm:{cls}_{slug(v).replace('-', '_')}" for v in vals) + " ) ."]
        for v in vals:
            L.append(f"dqm:{cls}_{slug(v).replace('-', '_')} a dqm:{cls}, owl:NamedIndividual ; rdfs:label {tl(v)} .")
        L.append("")
    for e in m["entities"]:
        L += [f"dqm:{e['name']} a owl:Class ;", f"  rdfs:label {tl(e['name'])} ;", f"  rdfs:comment {tl(e['description'])} ;"]
        L += [f"  rdfs:seeAlso <{m['guidance'][g]['url']}> ;" for g in sorted({re.sub(r'\d+$', '', g) for g in e.get('guidance', [])}) if g in m["guidance"]]
        L.append(f"  skos:note {tl('Group: ' + e['group'])} .")
        for a in e["attributes"]:
            ty = a["type"]
            iri = f"dqm:{e['name']}_{a['name']}"
            if ty.startswith("ref:"):
                L.append(f"{iri} a owl:ObjectProperty ; rdfs:domain dqm:{e['name']} ; rdfs:range dqm:{ty[4:]} ;")
            elif ty.startswith("enum:"):
                cls = "".join(w.capitalize() for w in ty[5:].split("_")) + "Value"
                L.append(f"{iri} a owl:ObjectProperty ; rdfs:domain dqm:{e['name']} ; rdfs:range dqm:{cls} ;")
            else:
                L.append(f"{iri} a owl:DatatypeProperty ; rdfs:domain dqm:{e['name']} ; rdfs:range {XSD[ty]} ;")
            L.append(f"  rdfs:label {tl(a['name'].replace('_', ' '))}" + (f" ;\n  rdfs:comment {tl(a['description'])} ." if a.get("description") else " ."))
            if a.get("required") or a.get("key"):
                L.append(f"dqm:{e['name']} rdfs:subClassOf [ a owl:Restriction ; owl:onProperty {iri} ; owl:minCardinality \"1\"^^xsd:nonNegativeInteger ] .")
        L.append("")
    return {"rdf/dq-data-model.ttl": "\n".join(L)}


# ----------------------------------------------------------------------------------------------- Mermaid ERD
def mermaid(m: dict) -> dict[str, str]:
    L = ["%% Generated by scripts/build_models.py from models/dq-capability.yaml", "erDiagram"]
    for e in m["entities"]:
        L.append(f"  {e['name']} {{")
        for a in e["attributes"]:
            ty = a["type"]
            base = "ref" if ty.startswith("ref:") else ("enum" if ty.startswith("enum:") else ty)
            if a.get("many"):
                base += "_list"
            tag = " PK" if a.get("key") else (" FK" if ty.startswith("ref:") else "")
            L.append(f"    {base} {a['name']}{tag}")
        L.append("  }")
    for e in m["entities"]:
        for a in e["attributes"]:
            ty = a["type"]
            if ty.startswith("ref:"):
                card = "}o--o{" if a.get("many") else ("}o--||" if a.get("required") else "}o--o|")
                L.append(f"  {e['name']} {card} {ty[4:]} : \"{a['name']}\"")
    return {"erd/dq-data-model.mmd": "\n".join(L) + "\n"}


# ----------------------------------------------------------------------------------------------- ArchiMate
def archimate_elements(m: dict):
    """Elements and relationships shared by the exchange format and the CSV set."""
    els, rels, props = [], [], []

    def el(eid, typ, name, doc="", **p):
        els.append((eid, typ, name, doc))
        for k, v in p.items():
            props.append((eid, k, v))
        return eid

    def rel(typ, s, t, name="", **extra):
        rels.append((uid("rel", typ, s, t, name), typ, s, t, name, extra))

    for g, gd in m["guidance"].items():
        el(uid("req", g), "Requirement", gd["title"], f"Government guidance ({g}).", source=gd["url"], code=g)
    for p in m["principles"]:
        el(uid("prin", p["id"]), "Principle", p["name"], f"Government Data Quality Framework principle ({p['id']}).", code=p["id"])
    roles = sorted({lane for p in m["processes"] for lane in p["lanes"]})
    for r in roles:
        el(uid("role", r), "BusinessRole", r)
    for e in m["entities"]:
        el(uid("ent", e["name"]), "DataObject", e["name"], e["description"], group=e["group"], guidance=" ".join(e.get("guidance", [])))
    for a, e in [(a, e) for e in m["entities"] for a in e["attributes"] if a["type"].startswith("ref:") and a["type"][4:] != e["name"]]:
        rel("Association", uid("ent", e["name"]), uid("ent", a["type"][4:]), a["name"])
    for c in m["capabilities"]:
        cid = el(uid("cap", c["id"]), "Capability", c["name"], f"Capability {c['id']}.", code=c["id"], principle=c["principle"], guidance=" ".join(c["guidance"]))
        for ch in c["children"]:
            sid = el(uid("cap", c["id"], ch), "Capability", ch, f"Part of {c['name']}.")
            rel("Composition", cid, sid)
        rel("Association", cid, uid("prin", c["principle"]), "applies principle")
        for g in c["guidance"]:
            gg = re.sub(r"\d+$", "", g) if g not in m["guidance"] else g
            gg = "GDQF" if gg.startswith("GDQF") else gg
            if gg in m["guidance"]:
                rel("Realization", cid, uid("req", gg))
        for en in c["entities"]:
            rel("Association", cid, uid("ent", en), "manages")
    for p in m["processes"]:
        pid = el(uid("proc", p["id"]), "BusinessProcess", p["name"], f"Workflow {p['id']}. See models/out/bpmn.", code=p["id"])
        rel("Realization", pid, uid("cap", p["capability"]))
        for s in p["steps"]:
            if s["kind"] in ("start", "end", "gateway"):
                continue
            sid = el(uid("step", p["id"], s["id"]), "BusinessProcess", s["name"], "", process=p["id"], guidance=" ".join(s.get("guidance", [])),
                     automated="yes" if s["kind"] == "service" else "no")
            rel("Composition", pid, sid)
            rel("Assignment", uid("role", s["lane"]), sid)
            for en in s.get("outputs", []):
                rel("Access", sid, uid("ent", en), accessType="Write")
            for en in s.get("inputs", []):
                rel("Access", sid, uid("ent", en), accessType="Read")
    # de-duplicate relationships (same source, target, type)
    seen, uniq = set(), []
    for r in rels:
        if r[0] not in seen:
            seen.add(r[0])
            uniq.append(r)
    return els, uniq, props


def archimate_xml(m: dict) -> dict[str, str]:
    els, rels, props = archimate_elements(m)
    keys = sorted({k for _, k, _ in props})
    pdef = {k: f"propid-{i + 1}" for i, k in enumerate(keys)}
    by_el: dict[str, list] = {}
    for eid, k, v in props:
        by_el.setdefault(eid, []).append((k, v))
    X = ['<?xml version="1.0" encoding="UTF-8"?>',
         '<model xmlns="http://www.opengroup.org/xsd/archimate/3.0/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"',
         '       xsi:schemaLocation="http://www.opengroup.org/xsd/archimate/3.0/ http://www.opengroup.org/xsd/archimate/3.1/archimate3_Diagram.xsd"',
         f'       identifier="{uid("model")}">',
         f'  <name xml:lang="en">{xa(m["name"])}</name>',
         f'  <documentation xml:lang="en">Generated by scripts/build_models.py from models/dq-capability.yaml (model version {m["version"]}). MIT licence.</documentation>',
         "  <elements>"]
    for eid, typ, name, doc in els:
        X.append(f'    <element identifier="{eid}" xsi:type="{typ}">')
        X.append(f'      <name xml:lang="en">{xa(name)}</name>')
        if doc:
            X.append(f'      <documentation xml:lang="en">{xa(doc)}</documentation>')
        if eid in by_el:
            X.append("      <properties>")
            for k, v in by_el[eid]:
                X.append(f'        <property propertyDefinitionRef="{pdef[k]}"><value xml:lang="en">{xa(v)}</value></property>')
            X.append("      </properties>")
        X.append("    </element>")
    X.append("  </elements>")
    X.append("  <relationships>")
    for rid, typ, s, t, name, extra in rels:
        attrs = "".join(f' {k}="{xa(v)}"' for k, v in extra.items())
        X.append(f'    <relationship identifier="{rid}" source="{s}" target="{t}" xsi:type="{typ}"{attrs}>' + (f'<name xml:lang="en">{xa(name)}</name>' if name else "") + "</relationship>")
    X.append("  </relationships>")
    X.append("  <propertyDefinitions>")
    for k in keys:
        X.append(f'    <propertyDefinition identifier="{pdef[k]}" type="string"><name xml:lang="en">{xa(k)}</name></propertyDefinition>')
    X.append("  </propertyDefinitions>")
    # Views: capability map (grid) and information model (entities by group).
    X.append("  <views>\n    <diagrams>")
    X.append(f'      <view identifier="{uid("view", "cap")}" xsi:type="Diagram"><name xml:lang="en">Capability map with GDQF principles</name>')
    for i, c in enumerate(m["capabilities"]):
        x, y = 20 + (i % 4) * 300, 20 + (i // 4) * 260
        X.append(f'        <node identifier="{uid("vn", c["id"])}" elementRef="{uid("cap", c["id"])}" xsi:type="Element" x="{x}" y="{y}" w="280" h="240">')
        for j, ch in enumerate(c["children"]):
            X.append(f'          <node identifier="{uid("vn", c["id"], ch)}" elementRef="{uid("cap", c["id"], ch)}" xsi:type="Element" x="{x + 15}" y="{y + 50 + j * 60}" w="250" h="50"/>')
        X.append("        </node>")
    X.append("      </view>")
    X.append(f'      <view identifier="{uid("view", "info")}" xsi:type="Diagram"><name xml:lang="en">Information model</name>')
    groups = list(dict.fromkeys(e["group"] for e in m["entities"]))
    for gi, g in enumerate(groups):
        for j, e in enumerate([e for e in m["entities"] if e["group"] == g]):
            X.append(f'        <node identifier="{uid("vi", e["name"])}" elementRef="{uid("ent", e["name"])}" xsi:type="Element" x="{20 + gi * 200}" y="{20 + j * 70}" w="180" h="55"/>')
    X.append("      </view>")
    for p in m["processes"]:
        lay = layout(p)
        X.append(f'      <view identifier="{uid("view", p["id"])}" xsi:type="Diagram"><name xml:lang="en">{xa(p["id"] + " " + p["name"])}</name>')
        for s in p["steps"]:
            if s["kind"] in ("start", "end", "gateway"):
                continue
            x, y, w, h = lay["px"][s["id"]]
            X.append(f'        <node identifier="{uid("vp", p["id"], s["id"])}" elementRef="{uid("step", p["id"], s["id"])}" xsi:type="Element" x="{int(x)}" y="{int(y)}" w="{int(w)}" h="{int(h)}"/>')
        X.append("      </view>")
    X.append("    </diagrams>\n  </views>\n</model>")
    return {"archimate/dq-capability.xml": "\n".join(X) + "\n"}


ARCHI_REL = {"Association": "AssociationRelationship", "Composition": "CompositionRelationship", "Realization": "RealizationRelationship",
             "Assignment": "AssignmentRelationship", "Access": "AccessRelationship"}


def archi_csv(m: dict) -> dict[str, str]:
    els, rels, props = archimate_elements(m)
    e_rows = [["ID", "Type", "Name", "Documentation", "Specialization"], [uid("model"), "ArchimateModel", m["name"], "Generated from models/dq-capability.yaml", ""]]
    e_rows += [[eid, typ, name, doc, ""] for eid, typ, name, doc in els]
    r_rows = [["ID", "Type", "Name", "Documentation", "Source", "Target", "Specialization"]]
    r_rows += [[rid, ARCHI_REL[typ], name, "", s, t, ""] for rid, typ, s, t, name, _ in rels]
    p_rows = [["ID", "Key", "Value"]] + [[eid, k, v] for eid, k, v in props]
    p_rows += [[rid, "accessType", extra["accessType"].lower()] for rid, typ, s, t, name, extra in rels if "accessType" in extra]
    return {"archimate/csv/dq-elements.csv": csv_text(e_rows), "archimate/csv/dq-relations.csv": csv_text(r_rows),
            "archimate/csv/dq-properties.csv": csv_text(p_rows)}


# ----------------------------------------------------------------------------------------------- UML XMI
UML_PRIM = {"string": "String", "text": "String", "integer": "Integer", "decimal": "Real", "boolean": "Boolean",
            "date": "String", "datetime": "String", "url": "String"}


def xmi(m: dict) -> dict[str, str]:
    P = "http://www.omg.org/spec/UML/20161101/PrimitiveTypes.xmi#"
    X = ['<?xml version="1.0" encoding="UTF-8"?>',
         '<xmi:XMI xmlns:xmi="http://www.omg.org/spec/XMI/20131001" xmlns:uml="http://www.omg.org/spec/UML/20161101">',
         f'  <uml:Model xmi:type="uml:Model" xmi:id="{uid("uml-model")}" name="{xa(m["name"])}">',
         f'    <ownedComment xmi:type="uml:Comment" xmi:id="{uid("uml-c")}"><body>{xa("Generated by scripts/build_models.py from models/dq-capability.yaml. Dates are ISO 8601 strings.")}</body></ownedComment>',
         f'    <packagedElement xmi:type="uml:Package" xmi:id="{uid("pkg", "lists")}" name="Reference lists">']
    for name, vals in m["enums"].items():
        X.append(f'      <packagedElement xmi:type="uml:Enumeration" xmi:id="{uid("enum", name)}" name="{xa(name)}">')
        for v in vals:
            X.append(f'        <ownedLiteral xmi:type="uml:EnumerationLiteral" xmi:id="{uid("lit", name, v)}" name="{xa(v)}"/>')
        X.append("      </packagedElement>")
    X.append("    </packagedElement>")
    assocs = []
    for g in dict.fromkeys(e["group"] for e in m["entities"]):
        X.append(f'    <packagedElement xmi:type="uml:Package" xmi:id="{uid("pkg", g)}" name="{xa(g)}">')
        for e in [e for e in m["entities"] if e["group"] == g]:
            X.append(f'      <packagedElement xmi:type="uml:Class" xmi:id="{uid("cls", e["name"])}" name="{e["name"]}">')
            X.append(f'        <ownedComment xmi:type="uml:Comment" xmi:id="{uid("cc", e["name"])}"><body>{xa(e["description"])}</body></ownedComment>')
            for a in e["attributes"]:
                ty, aid = a["type"], uid("attr", e["name"], a["name"])
                lower = "1" if a.get("required") or a.get("key") else "0"
                upper = "*" if a.get("many") else "1"
                if ty.startswith("ref:"):
                    asid = uid("assoc", e["name"], a["name"])
                    X.append(f'        <ownedAttribute xmi:type="uml:Property" xmi:id="{aid}" name="{a["name"]}" type="{uid("cls", ty[4:])}" association="{asid}">')
                    assocs.append((asid, aid, e["name"], ty[4:], a["name"]))
                elif ty.startswith("enum:"):
                    X.append(f'        <ownedAttribute xmi:type="uml:Property" xmi:id="{aid}" name="{a["name"]}" type="{uid("enum", ty[5:])}"' + (' isID="true"' if a.get("key") else "") + ">")
                else:
                    X.append(f'        <ownedAttribute xmi:type="uml:Property" xmi:id="{aid}" name="{a["name"]}"' + (' isID="true"' if a.get("key") else "") + ">")
                    X.append(f'          <type href="{P}{UML_PRIM[ty]}"/>')
                X.append(f'          <lowerValue xmi:type="uml:LiteralInteger" xmi:id="{aid}-l" value="{lower}"/>')
                X.append(f'          <upperValue xmi:type="uml:LiteralUnlimitedNatural" xmi:id="{aid}-u" value="{upper}"/>')
                if a.get("description"):
                    X.append(f'          <ownedComment xmi:type="uml:Comment" xmi:id="{aid}-c"><body>{xa(a["description"])}</body></ownedComment>')
                X.append("        </ownedAttribute>")
            X.append("      </packagedElement>")
        X.append("    </packagedElement>")
    X.append(f'    <packagedElement xmi:type="uml:Package" xmi:id="{uid("pkg", "assoc")}" name="Associations">')
    for asid, aid, src, tgt, name in assocs:
        end = asid + "-src"
        X.append(f'      <packagedElement xmi:type="uml:Association" xmi:id="{asid}" name="{xa(name)}" memberEnd="{aid} {end}">')
        X.append(f'        <ownedEnd xmi:type="uml:Property" xmi:id="{end}" type="{uid("cls", src)}" association="{asid}">')
        X.append(f'          <lowerValue xmi:type="uml:LiteralInteger" xmi:id="{end}-l" value="0"/>')
        X.append(f'          <upperValue xmi:type="uml:LiteralUnlimitedNatural" xmi:id="{end}-u" value="*"/>')
        X.append("        </ownedEnd>")
        X.append("      </packagedElement>")
    X.append("    </packagedElement>\n  </uml:Model>\n</xmi:XMI>")
    return {"uml/dq-data-model.xmi": "\n".join(X) + "\n"}


# ----------------------------------------------------------------------------------------------- process layout (shared by BPMN and Visio)
COL_W, LANE_H, LANE_LABEL = 1.8, 1.75, 1.0   # inches
TASK_W, TASK_H, EVENT_D, GATE_D = 1.45, 0.82, 0.42, 0.62
PX = 100  # pixels per inch for BPMN diagram interchange


def layout(p: dict) -> dict:
    """Positions in inches with origin top-left, plus pixel boxes for BPMN/ArchiMate."""
    lanes = {l: i for i, l in enumerate(p["lanes"])}
    pos, px = {}, {}
    for col, s in enumerate(p["steps"]):
        cx = LANE_LABEL + 0.3 + col * COL_W + COL_W / 2
        cy = lanes[s["lane"]] * LANE_H + 0.75
        w, h = {"start": (EVENT_D, EVENT_D), "end": (EVENT_D, EVENT_D), "gateway": (GATE_D, GATE_D)}.get(s["kind"], (TASK_W, TASK_H))
        pos[s["id"]] = (cx, cy, w, h, col)
        px[s["id"]] = ((cx - w / 2) * PX, (cy - h / 2) * PX, w * PX, h * PX)
    width = LANE_LABEL + 0.6 + len(p["steps"]) * COL_W
    height = len(p["lanes"]) * LANE_H
    return {"pos": pos, "px": px, "width": width, "height": height, "lanes": lanes}


def route(lay: dict, s: str, t: str) -> list[tuple[float, float]]:
    """Orthogonal path in inches (top-left origin) between two steps."""
    sx, sy, sw, sh, sc = lay["pos"][s]
    tx, ty, tw, th, tc = lay["pos"][t]
    if tc > sc:
        x1, x2 = sx + sw / 2, tx - tw / 2
        if abs(sy - ty) < 1e-6:
            return [(x1, sy), (x2, ty)]
        xm = x2 - 0.2
        return [(x1, sy), (xm, sy), (xm, ty), (x2, ty)]
    # loop back: leave from the bottom, run along the bottom of the lower lane, come up into the target
    low = max(sy, ty)
    lane_bottom = (math.floor(low / LANE_H) + 1) * LANE_H - 0.12
    return [(sx, sy + sh / 2), (sx, lane_bottom), (tx, lane_bottom), (tx, ty + th / 2)]


# ----------------------------------------------------------------------------------------------- BPMN 2.0
def bpmn(m: dict) -> dict[str, str]:
    out = {}
    tag = {"start": "startEvent", "end": "endEvent", "gateway": "exclusiveGateway", "user": "userTask", "service": "serviceTask", "manual": "manualTask"}
    for p in m["processes"]:
        lay = layout(p)
        pid, cid = f"Process_{p['id']}", f"Collab_{p['id']}"
        fl = flows(p)
        fid = {(s, t, l): f"Flow_{p['id']}_{s}_{t}" for s, t, l in fl}
        incoming = {s["id"]: [fid[f] for f in fl if f[1] == s["id"]] for s in p["steps"]}
        outgoing = {s["id"]: [fid[f] for f in fl if f[0] == s["id"]] for s in p["steps"]}
        X = ['<?xml version="1.0" encoding="UTF-8"?>',
             '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" xmlns:bpmndi="http://www.omg.org/spec/BPMN/20100524/DI"',
             '  xmlns:dc="http://www.omg.org/spec/DD/20100524/DC" xmlns:di="http://www.omg.org/spec/DD/20100524/DI"',
             f'  id="Defs_{p["id"]}" targetNamespace="{xa(m["namespace"])}" exporter="dq-commons build_models.py" exporterVersion="{m["version"]}">',
             f'  <bpmn:collaboration id="{cid}">',
             f'    <bpmn:participant id="Part_{p["id"]}" name="{xa(p["id"] + " " + p["name"])}" processRef="{pid}"/>',
             "  </bpmn:collaboration>",
             f'  <bpmn:process id="{pid}" name="{xa(p["name"])}" isExecutable="false">',
             f'    <bpmn:documentation>{xa("Realises capability " + p["capability"] + ". Generated from models/dq-capability.yaml; guidance codes are explained in models/README.md.")}</bpmn:documentation>',
             f'    <bpmn:laneSet id="LaneSet_{p["id"]}">']
        for i, lane in enumerate(p["lanes"]):
            X.append(f'      <bpmn:lane id="Lane_{p["id"]}_{i}" name="{xa(lane)}">')
            X += [f'        <bpmn:flowNodeRef>{p["id"]}_{s["id"]}</bpmn:flowNodeRef>' for s in p["steps"] if s["lane"] == lane]
            X.append("      </bpmn:lane>")
        X.append("    </bpmn:laneSet>")
        data_refs = []
        for s in p["steps"]:
            nid = f'{p["id"]}_{s["id"]}'
            X.append(f'    <bpmn:{tag[s["kind"]]} id="{nid}" name="{xa(s["name"])}">')
            if s.get("guidance"):
                X.append(f'      <bpmn:documentation>{xa("Guidance: " + ", ".join(s["guidance"]))}</bpmn:documentation>')
            X += [f"      <bpmn:incoming>{f}</bpmn:incoming>" for f in incoming[s["id"]]]
            X += [f"      <bpmn:outgoing>{f}</bpmn:outgoing>" for f in outgoing[s["id"]]]
            for en in s.get("inputs", []):
                did = f"DataIn_{nid}_{en}"
                X.append(f'      <bpmn:dataInputAssociation id="{did}"><bpmn:sourceRef>DOR_{nid}_{en}</bpmn:sourceRef></bpmn:dataInputAssociation>')
                data_refs.append((nid, en, did, "in"))
            for en in s.get("outputs", []):
                did = f"DataOut_{nid}_{en}"
                X.append(f'      <bpmn:dataOutputAssociation id="{did}"><bpmn:targetRef>DOR_{nid}_{en}</bpmn:targetRef></bpmn:dataOutputAssociation>')
                data_refs.append((nid, en, did, "out"))
            X.append(f'    </bpmn:{tag[s["kind"]]}>')
        for (s, t, l), f in fid.items():
            X.append(f'    <bpmn:sequenceFlow id="{f}" sourceRef="{p["id"]}_{s}" targetRef="{p["id"]}_{t}"' + (f' name="{xa(l)}"' if l else "") + "/>")
        for en in sorted({en for _, en, _, _ in data_refs}):
            X.append(f'    <bpmn:dataObject id="DO_{p["id"]}_{en}" name="{xa(en)}"/>')
        for nid, en, did, _ in data_refs:
            X.append(f'    <bpmn:dataObjectReference id="DOR_{nid}_{en}" name="{xa(en)}" dataObjectRef="DO_{p["id"]}_{en}"/>')
        X.append("  </bpmn:process>")
        # Diagram interchange
        X.append(f'  <bpmndi:BPMNDiagram id="Diagram_{p["id"]}"><bpmndi:BPMNPlane id="Plane_{p["id"]}" bpmnElement="{cid}">')
        W, H = lay["width"] * PX, lay["height"] * PX
        X.append(f'    <bpmndi:BPMNShape id="Part_{p["id"]}_di" bpmnElement="Part_{p["id"]}" isHorizontal="true"><dc:Bounds x="0" y="0" width="{W:.0f}" height="{H:.0f}"/></bpmndi:BPMNShape>')
        for i, lane in enumerate(p["lanes"]):
            X.append(f'    <bpmndi:BPMNShape id="Lane_{p["id"]}_{i}_di" bpmnElement="Lane_{p["id"]}_{i}" isHorizontal="true"><dc:Bounds x="30" y="{i * LANE_H * PX:.0f}" width="{W - 30:.0f}" height="{LANE_H * PX:.0f}"/></bpmndi:BPMNShape>')
        for s in p["steps"]:
            x, y, w, h = lay["px"][s["id"]]
            X.append(f'    <bpmndi:BPMNShape id="{p["id"]}_{s["id"]}_di" bpmnElement="{p["id"]}_{s["id"]}"' + (' isMarkerVisible="true"' if s["kind"] == "gateway" else "") + f'><dc:Bounds x="{x:.0f}" y="{y:.0f}" width="{w:.0f}" height="{h:.0f}"/></bpmndi:BPMNShape>')
        per_task: dict[str, int] = {}
        for nid, en, did, _ in data_refs:
            step = nid.split("_", 1)[1]
            x, y, w, h = lay["px"][step]
            k = per_task.get(nid, 0)
            per_task[nid] = k + 1
            dx, dy = x + k * 34, y + h + 18
            X.append(f'    <bpmndi:BPMNShape id="DOR_{nid}_{en}_di" bpmnElement="DOR_{nid}_{en}"><dc:Bounds x="{dx:.0f}" y="{dy:.0f}" width="28" height="36"/></bpmndi:BPMNShape>')
            X.append(f'    <bpmndi:BPMNEdge id="{did}_di" bpmnElement="{did}"><di:waypoint x="{dx + 14:.0f}" y="{y + h:.0f}"/><di:waypoint x="{dx + 14:.0f}" y="{dy:.0f}"/></bpmndi:BPMNEdge>')
        for (s, t, l), f in fid.items():
            pts = route(lay, s, t)
            X.append(f'    <bpmndi:BPMNEdge id="{f}_di" bpmnElement="{f}">' + "".join(f'<di:waypoint x="{x * PX:.0f}" y="{y * PX:.0f}"/>' for x, y in pts) + "</bpmndi:BPMNEdge>")
        X.append("  </bpmndi:BPMNPlane></bpmndi:BPMNDiagram>\n</bpmn:definitions>")
        out[f"bpmn/{p['id']}-{slug(p['name'])}.bpmn"] = "\n".join(X) + "\n"
    return out


# ----------------------------------------------------------------------------------------------- Visio (.vsdx)
NS_V = "http://schemas.microsoft.com/office/visio/2012/main"
NS_R = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
GREY, INK, PAPER, LANE_FILL = "#505a5f", "#0b0c0c", "#ffffff", "#f3f2f1"


class Page:
    """Collects Visio shapes for one page. Coordinates in inches, origin bottom-left (Visio convention)."""

    def __init__(self, name: str, width: float, height: float):
        self.name, self.width, self.height = name, width, height
        self.shapes: list[str] = []
        self.connects: list[str] = []
        self.next_id = 1

    def _id(self) -> int:
        i = self.next_id
        self.next_id += 1
        return i

    @staticmethod
    def _char(size_pt: float, color: str, bold: bool) -> str:
        return (f'<Section N="Character"><Row IX="0"><Cell N="Font" V="1"/><Cell N="Size" V="{size_pt / 72:.4f}" U="PT"/>'
                f'<Cell N="Color" V="{color}"/><Cell N="Style" V="{1 if bold else 0}"/></Row></Section>')

    def box(self, x: float, y: float, w: float, h: float, text: str = "", fill: str | None = PAPER, line: str | None = INK,
            color: str = INK, size: float = 9, bold: bool = False, shape: str = "rect", rounding: float = 0.0,
            weight_pt: float = 1.0, align: int = 1, valign: int = 1, name: str = "Shape", data: dict | None = None) -> int:
        """x, y is the centre."""
        sid = self._id()
        cells = [f'<Cell N="PinX" V="{x:.4f}"/>', f'<Cell N="PinY" V="{y:.4f}"/>', f'<Cell N="Width" V="{w:.4f}"/>',
                 f'<Cell N="Height" V="{h:.4f}"/>', f'<Cell N="LocPinX" V="{w / 2:.4f}" F="Width*0.5"/>',
                 f'<Cell N="LocPinY" V="{h / 2:.4f}" F="Height*0.5"/>', f'<Cell N="Rounding" V="{rounding:.4f}"/>',
                 f'<Cell N="LineWeight" V="{weight_pt / 72:.4f}" U="PT"/>', f'<Cell N="VerticalAlign" V="{valign}"/>',
                 '<Cell N="LeftMargin" V="0.05"/>', '<Cell N="RightMargin" V="0.05"/>', '<Cell N="TopMargin" V="0.03"/>', '<Cell N="BottomMargin" V="0.03"/>']
        cells.append(f'<Cell N="FillForegnd" V="{fill}"/><Cell N="FillPattern" V="1"/>' if fill else '<Cell N="FillPattern" V="0"/>')
        cells.append(f'<Cell N="LineColor" V="{line}"/><Cell N="LinePattern" V="1"/>' if line else '<Cell N="LinePattern" V="0"/>')
        if shape == "ellipse":
            geo = (f'<Section N="Geometry" IX="0"><Cell N="NoFill" V="{0 if fill else 1}"/><Cell N="NoLine" V="{0 if line else 1}"/>'
                   f'<Row T="Ellipse" IX="1"><Cell N="X" V="{w / 2:.4f}"/><Cell N="Y" V="{h / 2:.4f}"/><Cell N="A" V="{w:.4f}"/>'
                   f'<Cell N="B" V="{h / 2:.4f}"/><Cell N="C" V="{w / 2:.4f}"/><Cell N="D" V="{h:.4f}"/></Row></Section>')
        else:
            pts = [(w / 2, 0), (w, h / 2), (w / 2, h), (0, h / 2), (w / 2, 0)] if shape == "diamond" else [(0, 0), (w, 0), (w, h), (0, h), (0, 0)]
            rows = "".join(f'<Row T="{"MoveTo" if i == 0 else "LineTo"}" IX="{i + 1}"><Cell N="X" V="{px:.4f}"/><Cell N="Y" V="{py:.4f}"/></Row>' for i, (px, py) in enumerate(pts))
            geo = f'<Section N="Geometry" IX="0"><Cell N="NoFill" V="{0 if fill else 1}"/><Cell N="NoLine" V="{0 if line else 1}"/>{rows}</Section>'
        para = f'<Section N="Paragraph"><Row IX="0"><Cell N="HorzAlign" V="{align}"/></Row></Section>'
        props = ""
        if data:
            rows = "".join(f'<Row N="{re.sub(r"[^A-Za-z0-9_]", "_", k)}"><Cell N="Value" V="{xa(v)}" U="STR"/><Cell N="Label" V="{xa(k)}"/></Row>' for k, v in data.items())
            props = f'<Section N="Property">{rows}</Section>'
        body = f"<Text>{escape(text)}</Text>" if text else ""
        self.shapes.append(f'<Shape ID="{sid}" NameU="{xa(name)}.{sid}" Name="{xa(name)}.{sid}" Type="Shape" LineStyle="0" FillStyle="0" TextStyle="0">'
                           + "".join(cells) + self._char(size, color, bold) + para + props + geo + body + "</Shape>")
        return sid

    def text(self, x: float, y: float, w: float, h: float, text: str, size: float = 9, bold: bool = False, color: str = INK, align: int = 1) -> int:
        return self.box(x, y, w, h, text, fill=None, line=None, color=color, size=size, bold=bold, align=align, name="Text")

    def connector(self, pts: list[tuple[float, float]], src: int | None = None, dst: int | None = None, label: str = "", color: str = GREY) -> int:
        """Orthogonal connector glued to the shapes at each end, drawn with the stored route."""
        sid = self._id()
        xs, ys = [p[0] for p in pts], [p[1] for p in pts]
        x0, y0 = min(xs), min(ys)
        w, h = max(max(xs) - x0, 0.01), max(max(ys) - y0, 0.01)
        (bx, by), (ex, ey) = pts[0], pts[-1]
        rows = "".join(f'<Row T="{"MoveTo" if i == 0 else "LineTo"}" IX="{i + 1}"><Cell N="X" V="{px - x0:.4f}"/><Cell N="Y" V="{py - y0:.4f}"/></Row>' for i, (px, py) in enumerate(pts))
        lx, ly = pts[len(pts) // 2 - 1] if len(pts) > 2 else ((bx + ex) / 2, (by + ey) / 2)
        cells = (f'<Cell N="PinX" V="{x0 + w / 2:.4f}"/><Cell N="PinY" V="{y0 + h / 2:.4f}"/><Cell N="Width" V="{w:.4f}"/><Cell N="Height" V="{h:.4f}"/>'
                 f'<Cell N="LocPinX" V="{w / 2:.4f}"/><Cell N="LocPinY" V="{h / 2:.4f}"/>'
                 f'<Cell N="BeginX" V="{bx:.4f}"/><Cell N="BeginY" V="{by:.4f}"/><Cell N="EndX" V="{ex:.4f}"/><Cell N="EndY" V="{ey:.4f}"/>'
                 f'<Cell N="ObjType" V="2"/><Cell N="ShapeRouteStyle" V="16"/><Cell N="ConLineRouteExt" V="1"/>'
                 f'<Cell N="LineColor" V="{color}"/><Cell N="LineWeight" V="{1.25 / 72:.4f}" U="PT"/><Cell N="LinePattern" V="1"/>'
                 f'<Cell N="EndArrow" V="4"/><Cell N="EndArrowSize" V="2"/><Cell N="FillPattern" V="0"/>'
                 f'<Cell N="TxtPinX" V="{lx - x0 + 0.05:.4f}"/><Cell N="TxtPinY" V="{ly - y0 + 0.09:.4f}"/><Cell N="TxtWidth" V="0.5"/><Cell N="TxtHeight" V="0.18"/>')
        self.shapes.append(f'<Shape ID="{sid}" NameU="Dynamic connector.{sid}" Name="Dynamic connector.{sid}" Type="Shape" LineStyle="0" FillStyle="0" TextStyle="0">'
                           + cells + self._char(7.5, INK, True)
                           + f'<Section N="Geometry" IX="0"><Cell N="NoFill" V="1"/>{rows}</Section>' + (f"<Text>{escape(label)}</Text>" if label else "") + "</Shape>")
        if src:
            self.connects.append(f'<Connect FromSheet="{sid}" FromCell="BeginX" FromPart="9" ToSheet="{src}" ToCell="PinX" ToPart="3"/>')
        if dst:
            self.connects.append(f'<Connect FromSheet="{sid}" FromCell="EndX" FromPart="12" ToSheet="{dst}" ToCell="PinX" ToPart="3"/>')
        return sid

    def xml(self) -> str:
        return (f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n<PageContents xmlns="{NS_V}" xmlns:r="{NS_R}" xml:space="preserve">'
                f'<Shapes>{"".join(self.shapes)}</Shapes>' + (f'<Connects>{"".join(self.connects)}</Connects>' if self.connects else "") + "</PageContents>")


def principle_colour(m: dict) -> dict[str, str]:
    return {p["id"]: p["colour"] for p in m["principles"]}


def visio_legend(m: dict, pg: Page, x: float, y: float) -> None:
    """GDQF principle colour key, top-right. x, y is the top-left corner."""
    pg.text(x + 1.4, y - 0.15, 2.8, 0.25, "Government Data Quality Framework principles", size=8, bold=True, align=0)
    for i, p in enumerate(m["principles"]):
        yy = y - 0.45 - i * 0.26
        pg.box(x + 0.12, yy, 0.18, 0.18, fill=p["colour"], line=None, name="Legend")
        pg.text(x + 1.55, yy, 2.7, 0.24, f'{p["id"].replace("GDQF-", "")} {p["name"]}', size=7.5, align=0)


def visio_capability_page(m: dict, W: float) -> Page:
    H = 11.69
    pg = Page("Capability map (GDQF overlay)", W, H)
    col = principle_colour(m)
    pg.text(W / 2 - 2, H - 0.45, W - 5, 0.5, m["name"] + ": capability map overlaid with the Government Data Quality Framework, DAM policy and DQAP guidance", size=14, bold=True, align=0)
    pg.text(W / 2 - 2, H - 0.85, W - 5, 0.3, "Colour shows the GDQF principle each capability mainly serves. Codes show the guidance it realises (key on the last page). Workflows P1 to P5 are on the following pages.", size=8.5, align=0)
    visio_legend(m, pg, W - 4.3, H - 0.25)
    gx, gy = 0.35, 0.3
    cw, ch = (W - 1.1 - 3 * gx) / 4, 2.45
    x0, ytop = 0.55, H - 2.0
    for i, c in enumerate(m["capabilities"]):
        cx = x0 + (i % 4) * (cw + gx) + cw / 2
        cy = ytop - (i // 4) * (ch + gy) - ch / 2
        procs = ", ".join(p["id"] for p in m["processes"] if p["capability"] == c["id"])
        pg.box(cx, cy, cw, ch, fill=PAPER, line=col[c["principle"]], weight_pt=2.25, name="Capability",
               data={"Capability": c["id"], "Principle": c["principle"], "Guidance": " ".join(c["guidance"]), "Entities": " ".join(c["entities"])})
        pg.box(cx, cy + ch / 2 - 0.27, cw, 0.54, f'{c["id"]} {c["name"]}', fill=col[c["principle"]], line=None, color="#ffffff", size=10, bold=True, name="Capability title")
        for j, child in enumerate(c["children"]):
            pg.box(cx, cy + ch / 2 - 0.85 - j * 0.4, cw - 0.35, 0.32, child, fill=LANE_FILL, line="#b1b4b6", size=8, rounding=0.05, name="Sub-capability")
        foot = "Guidance: " + " · ".join(c["guidance"]) + (f"   Workflow: {procs}" if procs else "")
        pg.text(cx, cy - ch / 2 + 0.2, cw - 0.2, 0.3, foot, size=7, color=GREY)
    # Lifecycle band (GDQF: assess quality throughout the lifecycle)
    stages = m["enums"]["lifecycle_stage"]
    bw = (W - 1.1) / len(stages)
    pg.text(W / 2, 0.95, W - 1, 0.25, "GDQF data lifecycle: quality is assessed and managed at every stage (principle 3)", size=8.5, bold=True)
    for i, s in enumerate(stages):
        pg.box(0.55 + i * bw + bw / 2, 0.55, bw - 0.1, 0.42, s, fill=col["GDQF-P3"], line=None, color="#ffffff", size=8, bold=True, name="Lifecycle stage")
    return pg


def visio_process_page(m: dict, p: dict, W: float) -> Page:
    lay = layout(p)
    top = 2.0
    H = lay["height"] + top + 0.9
    pg = Page(f'{p["id"]} {p["name"]}'[:31], W, H)
    col = principle_colour(m)
    cap = next(c for c in m["capabilities"] if c["id"] == p["capability"])
    pg.text(W / 2 - 2.2, H - 0.4, W - 5, 0.45, f'{p["id"]} {p["name"]}', size=14, bold=True, align=0)
    pg.text(W / 2 - 2.2, H - 0.8, W - 5, 0.3, f'Realises {cap["id"]} {cap["name"]}. Fill colour shows the GDQF principle; the line under each step shows its guidance and the records it creates (data model entities).', size=8.5, align=0)
    visio_legend(m, pg, W - 4.3, H - 0.15)

    def V(x: float, y: float) -> tuple[float, float]:  # layout (top-left origin) to Visio page coordinates
        return x + 0.2, H - top - y

    lanew = lay["width"]
    for name, i in lay["lanes"].items():
        cx, cy = V(lanew / 2, i * LANE_H + LANE_H / 2)
        pg.box(cx, cy, lanew, LANE_H, fill=PAPER if i % 2 else LANE_FILL, line="#b1b4b6", name="Swimlane")
        lx, ly = V(LANE_LABEL / 2, i * LANE_H + LANE_H / 2)
        pg.box(lx, ly, LANE_LABEL, LANE_H, name, fill="#dee0e2", line="#b1b4b6", size=8.5, bold=True, name="Lane label")
    ids = {}
    for s in p["steps"]:
        cx, cy, w, h, _ = lay["pos"][s["id"]]
        x, y = V(cx, cy)
        data = {"Step": f'{p["id"]}.{s["id"]}', "Role": s["lane"], "Guidance": " ".join(s.get("guidance", [])),
                "Records": " ".join(s.get("outputs", [])), "Automated": "yes" if s["kind"] == "service" else "no"}
        if s["kind"] == "start":
            ids[s["id"]] = pg.box(x, y, w, h, fill="#cce2d8", line="#005a30", weight_pt=1.5, shape="ellipse", name="Start", data=data)
            pg.text(x, y - h / 2 - 0.22, 1.6, 0.36, s["name"], size=7.5)
        elif s["kind"] == "end":
            ids[s["id"]] = pg.box(x, y, w, h, fill="#f4cdc6", line="#942514", weight_pt=3, shape="ellipse", name="End", data=data)
            pg.text(x, y - h / 2 - 0.22, 1.6, 0.36, s["name"], size=7.5)
        elif s["kind"] == "gateway":
            ids[s["id"]] = pg.box(x, y, w, h, "X", fill="#fff7bf", line="#594d00", weight_pt=1.5, shape="diamond", size=10, bold=True, name="Decision", data=data)
            pg.text(x, y + h / 2 + 0.2, 1.65, 0.36, s["name"], size=7.5, bold=True)
        else:
            pr = step_principle(s)
            fill = col.get(pr, "#1d70b8")
            label = ("⚙ " if s["kind"] == "service" else "") + s["name"]
            ids[s["id"]] = pg.box(x, y, w, h, label, fill=fill, line=None, color="#ffffff", size=7.5, bold=True, rounding=0.08, name="Task", data=data)
            info = " · ".join(s.get("guidance", []))
            if s.get("outputs"):
                info += "\n→ " + ", ".join(s["outputs"])
            pg.text(x, y - h / 2 - 0.27, COL_W - 0.05, 0.42, info, size=6.5, color=GREY)
    for s, t, label in flows(p):
        pts = [V(x, y) for x, y in route(lay, s, t)]
        pg.connector(pts, ids[s], ids[t], label)
    pg.text(W / 2, 0.35, W - 1, 0.3, "⚙ = automated step (Commons toolkit or scheduled job). Swimlanes are roles from the data ownership model and DQAP guide. Matching BPMN 2.0 file: models/out/bpmn/" + f'{p["id"]}-{slug(p["name"])}.bpmn', size=7.5, color=GREY)
    return pg


def visio_info_page(m: dict, W: float) -> Page:
    groups = list(dict.fromkeys(e["group"] for e in m["entities"]))
    H = 11.69
    pg = Page("Information model", W, H)
    pg.text(W / 2, H - 0.45, W - 1, 0.5, "Information architecture: the records the capability keeps, grouped by area, with the guidance each implements", size=14, bold=True)
    pg.text(W / 2, H - 0.85, W - 1, 0.3, "Full attributes, types and relationships: models/out/dictionary/data-dictionary.csv, the ERD, SQL, UML, JSON Schema and OWL exports.", size=8.5)
    gw = (W - 1) / len(groups)
    for gi, g in enumerate(groups):
        ents = [e for e in m["entities"] if e["group"] == g]
        gx = 0.5 + gi * gw + gw / 2
        pg.box(gx, H - 1.35, gw - 0.15, 0.4, g, fill="#0b0c0c", line=None, color="#ffffff", size=9.5, bold=True, name="Group")
        for j, e in enumerate(ents):
            y = H - 2.05 - j * 1.05
            pg.box(gx, y, gw - 0.3, 0.9, fill=PAPER, line="#1d70b8", weight_pt=1.5, name="Entity",
                   data={"Entity": e["name"], "Attributes": str(len(e["attributes"])), "Guidance": " ".join(e.get("guidance", []))})
            pg.text(gx, y + 0.25, gw - 0.4, 0.3, e["name"], size=9, bold=True)
            pg.text(gx, y - 0.13, gw - 0.4, 0.5, f'{len(e["attributes"])} attributes · ' + " ".join(e.get("guidance", [])), size=7, color=GREY)
    return pg


def visio_key_page(m: dict, W: float) -> Page:
    H = 11.69
    pg = Page("Guidance key", W, H)
    pg.text(W / 2, H - 0.45, W - 1, 0.5, "Guidance key: the codes used on every page", size=14, bold=True)
    rows = [(k, v["title"], v["url"]) for k, v in m["guidance"].items()]
    rows += [(f"DQAP{i}", f"DQAP implementation guide, step {i}", m["guidance"]["DQAP"]["url"]) for i in range(1, 8)]
    rows += [(p["id"], f"GDQF principle: {p['name']}", m["guidance"]["GDQF"]["url"]) for p in m["principles"]]
    rows += [("GDQF-LC", "GDQF data lifecycle", m["guidance"]["GDQF"]["url"]), ("GDQF-D", "GDQF data quality dimensions", m["guidance"]["GDQF"]["url"]),
             ("DCAT / DQV", "W3C Data Catalog Vocabulary 3 / Data Quality Vocabulary", "https://www.w3.org/TR/vocab-dcat-3/")]
    for i, (k, t, u) in enumerate(rows):
        y = H - 1.2 - i * 0.33
        pg.text(1.2, y, 1.4, 0.3, k, size=8.5, bold=True, align=0)
        pg.text(1.9 + 3.6, y, 7.2, 0.3, t, size=8.5, align=0)
        pg.text(9.4 + 0.5 * (W - 9.4), y, W - 9.6, 0.3, u, size=7, color="#1d70b8", align=0)
    pg.text(W / 2, 0.4, W - 1, 0.3, f'Generated by scripts/build_models.py from models/dq-capability.yaml, model version {m["version"]}, reviewed {m["review"]["last_reviewed"]}. MIT licence.', size=7.5, color=GREY)
    return pg


def vsdx(m: dict) -> dict[str, bytes]:
    # One width for every page so printed and PDF copies line up; Visio keeps each page's own height.
    W = max([16.54] + [layout(p)["width"] + 0.4 for p in m["processes"]])
    pages = [visio_capability_page(m, W)] + [visio_process_page(m, p, W) for p in m["processes"]] + [visio_info_page(m, W), visio_key_page(m, W)]
    n = len(pages)
    files: dict[str, str] = {}
    files["[Content_Types].xml"] = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/>'
        '<Override PartName="/visio/document.xml" ContentType="application/vnd.ms-visio.drawing.main+xml"/>'
        '<Override PartName="/visio/pages/pages.xml" ContentType="application/vnd.ms-visio.pages+xml"/>'
        + "".join(f'<Override PartName="/visio/pages/page{i + 1}.xml" ContentType="application/vnd.ms-visio.page+xml"/>' for i in range(n))
        + '<Override PartName="/visio/windows.xml" ContentType="application/vnd.ms-visio.windows+xml"/>'
        '<Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>'
        '<Override PartName="/docProps/app.xml" ContentType="application/vnd.openxmlformats-officedocument.extended-properties+xml"/></Types>')
    files["_rels/.rels"] = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" Type="http://schemas.microsoft.com/visio/2010/relationships/document" Target="visio/document.xml"/>'
        '<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/>'
        '<Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties" Target="docProps/app.xml"/></Relationships>')
    files["docProps/core.xml"] = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" '
        'xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dcterms="http://purl.org/dc/terms/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">'
        f'<dc:title>{xa(m["name"])}: process map</dc:title><dc:creator>Data Quality Commons</dc:creator>'
        f'<dc:description>Capability map overlaid with the Government Data Quality Framework, the DAM policy and DQAP guidance, with workflows P1 to P5.</dc:description>'
        f'<cp:keywords>data quality; GDQF; DAM policy; DQAP; critical data assets</cp:keywords>'
        f'<dcterms:modified xsi:type="dcterms:W3CDTF">{m["review"]["last_reviewed"]}T00:00:00Z</dcterms:modified></cp:coreProperties>')
    files["docProps/app.xml"] = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties">'
        '<Application>Microsoft Visio</Application><Template></Template></Properties>')
    files["visio/document.xml"] = (
        f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n<VisioDocument xmlns="{NS_V}" xmlns:r="{NS_R}" xml:space="preserve">'
        '<DocumentSettings TopPage="0" DefaultTextStyle="0" DefaultLineStyle="0" DefaultFillStyle="0" DefaultGuideStyle="0"><GlueSettings>9</GlueSettings><SnapSettings>295</SnapSettings></DocumentSettings>'
        '<Colors><ColorEntry IX="0" RGB="#000000"/><ColorEntry IX="1" RGB="#FFFFFF"/></Colors>'
        '<FaceNames><FaceName NameU="Calibri" UnicodeRanges="-536859905 -1073732485 9 0" CharSets="536871423 0" Panose="2 15 5 2 2 2 4 3 2 4" Flags="325"/>'
        '<FaceName NameU="Arial" UnicodeRanges="-536859905 -1073711037 9 0" CharSets="1073742335 -65536" Panose="2 11 6 4 2 2 2 2 2 4" Flags="325"/></FaceNames>'
        '<StyleSheets><StyleSheet ID="0" NameU="No Style" Name="No Style">'
        '<Cell N="EnableLineProps" V="1"/><Cell N="EnableFillProps" V="1"/><Cell N="EnableTextProps" V="1"/><Cell N="HideForApply" V="0"/>'
        '<Cell N="LineWeight" V="0.01041666666666667"/><Cell N="LineColor" V="0"/><Cell N="LinePattern" V="1"/><Cell N="Rounding" V="0"/>'
        '<Cell N="EndArrowSize" V="2"/><Cell N="BeginArrow" V="0"/><Cell N="EndArrow" V="0"/><Cell N="LineCap" V="0"/><Cell N="BeginArrowSize" V="2"/>'
        '<Cell N="LineColorTrans" V="0"/><Cell N="CompoundType" V="0"/><Cell N="FillForegnd" V="1"/><Cell N="FillBkgnd" V="0"/><Cell N="FillPattern" V="1"/>'
        '<Cell N="ShdwForegnd" V="0"/><Cell N="ShdwPattern" V="0"/><Cell N="FillForegndTrans" V="0"/><Cell N="FillBkgndTrans" V="0"/>'
        '<Cell N="LeftMargin" V="0.05"/><Cell N="RightMargin" V="0.05"/><Cell N="TopMargin" V="0.05"/><Cell N="BottomMargin" V="0.05"/>'
        '<Cell N="VerticalAlign" V="1"/><Cell N="TextBkgnd" V="0"/><Cell N="DefaultTabStop" V="0.5"/><Cell N="TextDirection" V="0"/>'
        '<Section N="Character"><Row IX="0"><Cell N="Font" V="1"/><Cell N="Color" V="0"/><Cell N="Style" V="0"/><Cell N="Case" V="0"/><Cell N="Pos" V="0"/>'
        '<Cell N="FontScale" V="1"/><Cell N="Size" V="0.1666666666666667"/><Cell N="DblUnderline" V="0"/><Cell N="Overline" V="0"/><Cell N="Strikethru" V="0"/>'
        '<Cell N="ColorTrans" V="0"/><Cell N="LangID" V="en-GB"/></Row></Section>'
        '<Section N="Paragraph"><Row IX="0"><Cell N="IndFirst" V="0"/><Cell N="IndLeft" V="0"/><Cell N="IndRight" V="0"/><Cell N="SpLine" V="-1.2"/>'
        '<Cell N="SpBefore" V="0"/><Cell N="SpAfter" V="0"/><Cell N="HorzAlign" V="1"/><Cell N="Bullet" V="0"/></Row></Section>'
        '</StyleSheet></StyleSheets></VisioDocument>')
    files["visio/_rels/document.xml.rels"] = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" Type="http://schemas.microsoft.com/visio/2010/relationships/pages" Target="pages/pages.xml"/>'
        '<Relationship Id="rId2" Type="http://schemas.microsoft.com/visio/2010/relationships/windows" Target="windows.xml"/></Relationships>')
    files["visio/windows.xml"] = (
        f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n<Windows xmlns="{NS_V}" xmlns:r="{NS_R}" ClientWidth="1600" ClientHeight="900" xml:space="preserve">'
        '<Window ID="0" WindowType="Drawing" WindowState="1073741824" ClientWidth="1600" ClientHeight="900" Page="0" ViewScale="-1" ViewCenterX="8.27" ViewCenterY="5.85">'
        '<ShowRulers>1</ShowRulers><ShowGrid>0</ShowGrid><ShowPageBreaks>0</ShowPageBreaks><ShowGuides>1</ShowGuides><ShowConnectionPoints>1</ShowConnectionPoints>'
        '<GlueSettings>9</GlueSettings><SnapSettings>295</SnapSettings></Window></Windows>')
    page_entries = []
    for i, pg in enumerate(pages):
        page_entries.append(
            f'<Page ID="{i}" NameU="{xa(pg.name)}" Name="{xa(pg.name)}" ViewScale="-1" ViewCenterX="{pg.width / 2:.2f}" ViewCenterY="{pg.height / 2:.2f}">'
            f'<PageSheet LineStyle="0" FillStyle="0" TextStyle="0"><Cell N="PageWidth" V="{pg.width:.4f}"/><Cell N="PageHeight" V="{pg.height:.4f}"/>'
            '<Cell N="ShdwOffsetX" V="0.125"/><Cell N="ShdwOffsetY" V="-0.125"/><Cell N="PageScale" V="1" U="IN_F"/><Cell N="DrawingScale" V="1" U="IN_F"/>'
            '<Cell N="DrawingSizeType" V="0"/><Cell N="DrawingScaleType" V="0"/><Cell N="InhibitSnap" V="0"/><Cell N="PageLockReplace" V="0" U="BOOL"/>'
            '<Cell N="PrintPageOrientation" V="2"/><Cell N="PageShapeSplit" V="1"/><Cell N="RouteStyle" V="16"/><Cell N="LineRouteExt" V="1"/></PageSheet>'
            f'<Rel r:id="rId{i + 1}"/></Page>')
        files[f"visio/pages/page{i + 1}.xml"] = pg.xml()
    files["visio/pages/pages.xml"] = f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n<Pages xmlns="{NS_V}" xmlns:r="{NS_R}" xml:space="preserve">' + "".join(page_entries) + "</Pages>"
    files["visio/pages/_rels/pages.xml.rels"] = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        + "".join(f'<Relationship Id="rId{i + 1}" Type="http://schemas.microsoft.com/visio/2010/relationships/page" Target="page{i + 1}.xml"/>' for i in range(n))
        + "</Relationships>")
    buf = io.BytesIO()
    date = tuple(int(x) for x in m["review"]["last_reviewed"].split("-")) + (0, 0, 0)
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for name in ["[Content_Types].xml"] + sorted(k for k in files if k != "[Content_Types].xml"):
            zi = zipfile.ZipInfo(name, date_time=date)
            zi.compress_type = zipfile.ZIP_DEFLATED
            zi.external_attr = 0o644 << 16
            z.writestr(zi, files[name].encode("utf-8"))
    return {"visio/dq-capability-process-map.vsdx": buf.getvalue()}


# ----------------------------------------------------------------------------------------------- main
def fingerprint(name: str, data: bytes) -> str:
    """Content hash. For zip packages (.vsdx) it hashes what is inside, because zlib versions compress differently."""
    if name.endswith(".vsdx"):
        z = zipfile.ZipFile(io.BytesIO(data))
        h = hashlib.sha256()
        for n in sorted(z.namelist()):
            h.update(n.encode() + b"\0" + z.read(n) + b"\0")
        return h.hexdigest()
    return hashlib.sha256(data).hexdigest()


def same(name: str, a: bytes, b: bytes) -> bool:
    return a == b or (name.endswith(".vsdx") and fingerprint(name, a) == fingerprint(name, b))


def build(m: dict) -> dict[str, bytes]:
    out: dict[str, bytes] = {}
    for fn in (data_dictionary, sql, json_schema, turtle, mermaid, archimate_xml, archi_csv, xmi, bpmn):
        for k, v in fn(m).items():
            out[k] = v.encode("utf-8")
    out.update(vsdx(m))
    manifest = ["# Generated model exports", "", f"Model version {m['version']}, from models/dq-capability.yaml. sha256 of each file:", ""]
    manifest += [f"- `{k}` {fingerprint(k, v)[:16]}" for k, v in sorted(out.items())]
    out["MANIFEST.md"] = ("\n".join(manifest) + "\n").encode()
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--check", action="store_true", help="fail if committed exports differ from the YAML")
    ap.add_argument("--svg", action="store_true", help="also render the ERD to SVG with mmdc")
    ap.add_argument("--render", action="store_true", help="also make a PDF of the Visio map and PNG previews (needs LibreOffice and pdftoppm)")
    a = ap.parse_args()
    m = load()
    files = build(m)
    if a.check:
        stale = [k for k, v in files.items() if not (OUT / k).exists() or not same(k, (OUT / k).read_bytes(), v)]
        if stale:
            print("These model exports are out of date. Run: python3 scripts/build_models.py\n  " + "\n  ".join(stale))
            return 1
        print(f"Model exports are up to date ({len(files)} files).")
        return 0
    for k, v in files.items():
        p = OUT / k
        p.parent.mkdir(parents=True, exist_ok=True)
        if not (p.exists() and same(k, p.read_bytes(), v)):  # leave identical files alone
            p.write_bytes(v)
    print(f"Wrote {len(files)} files to {OUT.relative_to(ROOT)}")
    if a.svg:
        mmdc = shutil.which("mmdc")
        if not mmdc:
            print("mmdc not found; skipped the SVG. Install with: npm install -g @mermaid-js/mermaid-cli")
        else:
            cfg = ROOT / "models" / "puppeteer.json"
            cmd = [mmdc, "-i", str(OUT / "erd/dq-data-model.mmd"), "-o", str(ROOT / "models/dq-data-model.svg"), "-b", "white"]
            if cfg.exists():
                cmd += ["-p", str(cfg)]
            mcfg = ROOT / "models" / "mermaid-config.json"  # plain SVG text, so the image works outside browsers too
            if mcfg.exists():
                cmd += ["-c", str(mcfg)]
            subprocess.run(cmd, check=True)
            print("Rendered models/dq-data-model.svg")
    if a.render:
        render_previews()
    return 0


def render_previews() -> None:
    """PDF of the Visio map for people without Visio, plus small PNG previews for the portal page."""
    import tempfile
    soffice, ppm = shutil.which("soffice"), shutil.which("pdftoppm")
    if not (soffice and ppm):
        print("LibreOffice or pdftoppm not found; skipped the PDF and previews.")
        return
    with tempfile.TemporaryDirectory() as tmp:
        src = Path(tmp) / "dq-capability-process-map.vsdx"
        shutil.copy(OUT / "visio/dq-capability-process-map.vsdx", src)
        subprocess.run([soffice, "--headless", "--convert-to", "pdf", "--outdir", tmp, str(src)], check=True, capture_output=True)
        pdf = Path(tmp) / "dq-capability-process-map.pdf"
        shutil.copy(pdf, ROOT / "models" / "dq-capability-process-map.pdf")
        prev = ROOT / "models" / "previews"
        prev.mkdir(parents=True, exist_ok=True)
        for old in prev.glob("map-*.png"):
            old.unlink()
        subprocess.run([ppm, "-r", "48", "-png", str(pdf), str(prev / "map")], check=True)
        for f in sorted(prev.glob("map-*.png")):  # pdftoppm pads page numbers; keep simple names
            n = int(f.stem.split("-")[-1])
            f.rename(prev / f"map-{n}.png")
    print("Wrote models/dq-capability-process-map.pdf and portal previews")


if __name__ == "__main__":
    sys.exit(main())
