"""Checks for the capability model exports (scripts/build_models.py).

Plain English: the model is one YAML file turned into ArchiMate, UML, SQL, JSON Schema, OWL, CSV, Visio and BPMN.
These tests rebuild everything in memory and check each format holds together, so a tool that imports a file
will find every element, link and shape it refers to.
"""
import csv
import io
import json
import re
import sqlite3
import sys
import unittest
import zipfile
from pathlib import Path

from lxml import etree

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import build_models as bm  # noqa: E402

M = bm.load()
FILES = bm.build(M)
BPMN = "{http://www.omg.org/spec/BPMN/20100524/MODEL}"
BPMNDI = "{http://www.omg.org/spec/BPMN/20100524/DI}"
AM = "{http://www.opengroup.org/xsd/archimate/3.0/}"
XSI = "{http://www.w3.org/2001/XMLSchema-instance}"
V = "{http://schemas.microsoft.com/office/visio/2012/main}"


class ModelSource(unittest.TestCase):
    def test_committed_exports_match_the_yaml(self):
        stale = [k for k, v in FILES.items() if not (bm.OUT / k).exists() or (bm.OUT / k).read_bytes() != v]
        self.assertEqual(stale, [], "run python3 scripts/build_models.py")

    def test_build_is_deterministic(self):
        self.assertEqual(bm.build(M), FILES)

    def test_every_capability_and_entity_cites_guidance(self):
        for c in M["capabilities"]:
            self.assertTrue(c["guidance"], c["id"])
        for e in M["entities"]:
            self.assertTrue(e.get("guidance"), e["name"])

    def test_every_dqap_step_and_gdqf_principle_is_covered(self):
        codes = {g for p in M["processes"] for s in p["steps"] for g in s.get("guidance", [])}
        for i in range(1, 8):
            self.assertIn(f"DQAP{i}", codes, f"no workflow step carries out DQAP step {i}")
        principles = {c["principle"] for c in M["capabilities"]}
        self.assertEqual(principles, {p["id"] for p in M["principles"]})

    def test_dam_policy_metadata_properties_are_in_the_asset_record(self):
        # The 13 critical data asset properties (Recording metadata for CDAs) map onto these fields.
        fields = {a["name"] for a in bm.entity(M, "DataAsset")["attributes"]} | {a["name"] for a in bm.entity(M, "Distribution")["attributes"]}
        for f in ["title", "alternative_title", "description", "creator", "date_created", "expires", "superseded_by", "temporal_coverage",
                  "conforms_to", "access_rights", "licence", "asset_id", "media_type"]:
            self.assertIn(f, fields)

    def test_no_personal_contact_fields(self):
        for e in M["entities"]:
            for a in e["attributes"]:
                self.assertNotRegex(a["name"], r"email|phone|telephone|(^|_)address($|_)", f"{e['name']}.{a['name']}")

    def test_stray_keys_are_caught(self):
        broken = json.loads(json.dumps(M))
        broken["processes"][0]["steps"][1]["oops"] = None
        with self.assertRaises(SystemExit):
            bm.validate(broken)


class DataFormats(unittest.TestCase):
    def test_sql_runs(self):
        ddl = FILES["sql/dq-data-model.sql"].decode()
        ddl = "\n".join(line for line in ddl.splitlines() if not line.startswith("COMMENT ON")).replace("timestamptz", "text")
        con = sqlite3.connect(":memory:")
        con.execute("PRAGMA foreign_keys=ON")
        con.executescript(ddl)
        tables = {r[0] for r in con.execute("select name from sqlite_master where type='table'")}
        for e in M["entities"]:
            self.assertIn(bm.snake(e["name"]), tables)
        con.execute("insert into organisation(organisation_id, name) values ('dept', 'A department')")
        with self.assertRaises(sqlite3.IntegrityError):  # allowed values are enforced
            con.execute("insert into data_asset(asset_id,title,description,creator,is_critical,date_created,access_rights,security_classification,licence)"
                        " values ('a','t','d','dept',1,'2026-01-01','Secret','OFFICIAL','x')")

    def test_json_schema_is_valid_and_accepts_a_record(self):
        import jsonschema
        schema = json.loads(FILES["json/dq-data-model.schema.json"])
        jsonschema.Draft202012Validator.check_schema(schema)
        doc = {"issue": [{"issue_id": "I1", "rule": "R1", "raised_on": "2026-11-01", "priority": "High", "status": "Open"}]}
        jsonschema.Draft202012Validator(schema).validate(doc)
        bad = {"issue": [{"issue_id": "I1", "rule": "R1", "raised_on": "2026-11-01", "priority": "Urgent", "status": "Open"}]}
        self.assertFalse(jsonschema.Draft202012Validator(schema).is_valid(bad))

    def test_turtle_is_balanced_and_prefixed(self):
        ttl = FILES["rdf/dq-data-model.ttl"].decode()
        body = re.sub(r'"(?:[^"\\]|\\.)*"', '""', ttl)  # ignore text inside literals
        self.assertEqual(body.count("["), body.count("]"))
        self.assertEqual(body.count("("), body.count(")"))
        declared = set(re.findall(r"@prefix (\w+):", ttl))
        used = set(re.findall(r"(?<![\w/#<])([a-z]+):[A-Za-z_]", body)) - {"http", "https"}
        self.assertLessEqual(used, declared)
        for e in M["entities"]:
            self.assertIn(f"dqm:{e['name']} a owl:Class", ttl)

    def test_data_dictionary_has_every_field(self):
        rows = list(csv.DictReader(io.StringIO(FILES["dictionary/data-dictionary.csv"].decode())))
        self.assertEqual(len(rows), sum(len(e["attributes"]) for e in M["entities"]))

    def test_uml_references_resolve(self):
        x = etree.fromstring(FILES["uml/dq-data-model.xmi"])
        ns = "{http://www.omg.org/spec/XMI/20131001}"
        ids = [e.get(f"{ns}id") for e in x.iter() if e.get(f"{ns}id")]
        self.assertEqual(len(ids), len(set(ids)), "duplicate xmi:id")
        idset = set(ids)
        for e in x.iter():
            for attr in ("type", "association"):
                if e.get(attr):
                    self.assertIn(e.get(attr), idset)
            if e.get("memberEnd"):
                for r in e.get("memberEnd").split():
                    self.assertIn(r, idset)


class ArchiMate(unittest.TestCase):
    def setUp(self):
        self.x = etree.fromstring(FILES["archimate/dq-capability.xml"])
        self.els = {e.get("identifier"): e.get(f"{XSI}type") for e in self.x.iter(f"{AM}element")}

    def test_relationships_point_at_elements_and_are_allowed(self):
        allowed = {("Composition", "Capability", "Capability"), ("Composition", "BusinessProcess", "BusinessProcess"),
                   ("Realization", "Capability", "Requirement"), ("Realization", "BusinessProcess", "Capability"),
                   ("Assignment", "BusinessRole", "BusinessProcess"), ("Access", "BusinessProcess", "DataObject")}
        for r in self.x.iter(f"{AM}relationship"):
            s, t, typ = r.get("source"), r.get("target"), r.get(f"{XSI}type")
            self.assertIn(s, self.els)
            self.assertIn(t, self.els)
            if typ != "Association":
                self.assertIn((typ, self.els[s], self.els[t]), allowed)

    def test_views_reference_elements(self):
        for n in self.x.iter(f"{AM}node"):
            self.assertIn(n.get("elementRef"), self.els)

    def test_csv_set_matches(self):
        els = list(csv.DictReader(io.StringIO(FILES["archimate/csv/dq-elements.csv"].decode())))
        rels = list(csv.DictReader(io.StringIO(FILES["archimate/csv/dq-relations.csv"].decode())))
        ids = {e["ID"] for e in els}
        self.assertEqual(els[0]["Type"], "ArchimateModel")
        self.assertEqual(len(els) - 1, len(self.els))
        for r in rels:
            self.assertIn(r["Source"], ids)
            self.assertIn(r["Target"], ids)


class Workflows(unittest.TestCase):
    def test_bpmn_is_complete(self):
        for p in M["processes"]:
            name = next(k for k in FILES if k.startswith(f"bpmn/{p['id']}-"))
            x = etree.fromstring(FILES[name])
            ids = {e.get("id") for e in x.iter() if e.get("id")}
            nodes = [e for e in x.iter() if e.tag in {f"{BPMN}{t}" for t in ("startEvent", "endEvent", "userTask", "serviceTask", "manualTask", "exclusiveGateway")}]
            self.assertEqual(len(nodes), len(p["steps"]))
            self.assertEqual(len(list(x.iter(f"{BPMN}startEvent"))), 1)
            for f in x.iter(f"{BPMN}sequenceFlow"):
                self.assertIn(f.get("sourceRef"), ids)
                self.assertIn(f.get("targetRef"), ids)
            drawn = {s.get("bpmnElement") for s in x.iter(f"{BPMNDI}BPMNShape")} | {s.get("bpmnElement") for s in x.iter(f"{BPMNDI}BPMNEdge")}
            for e in nodes + list(x.iter(f"{BPMN}sequenceFlow")) + list(x.iter(f"{BPMN}lane")) + list(x.iter(f"{BPMN}dataObjectReference")):
                self.assertIn(e.get("id"), drawn, f"{name}: {e.get('id')} has no diagram layout")
            for lane in x.iter(f"{BPMN}lane"):
                for ref in lane.iter(f"{BPMN}flowNodeRef"):
                    self.assertIn(ref.text, ids)

    def test_every_step_can_reach_the_end(self):
        for p in M["processes"]:
            out = {}
            for s, t, _ in bm.flows(p):
                out.setdefault(s, []).append(t)
            ends = {s["id"] for s in p["steps"] if s["kind"] == "end"}
            for s in p["steps"]:
                seen, todo = set(), [s["id"]]
                while todo:
                    n = todo.pop()
                    if n not in seen:
                        seen.add(n)
                        todo += out.get(n, [])
                self.assertTrue(seen & ends, f"{p['id']}.{s['id']} never reaches an end")


class Visio(unittest.TestCase):
    def test_package_parts_and_glue(self):
        z = zipfile.ZipFile(io.BytesIO(FILES["visio/dq-capability-process-map.vsdx"]))
        names = set(z.namelist())
        for part in ["[Content_Types].xml", "_rels/.rels", "visio/document.xml", "visio/pages/pages.xml", "visio/pages/_rels/pages.xml.rels"]:
            self.assertIn(part, names)
        pages = etree.fromstring(z.read("visio/pages/pages.xml"))
        n = len(pages.findall(f"{V}Page"))
        self.assertEqual(n, 1 + len(M["processes"]) + 2)
        ct = z.read("[Content_Types].xml").decode()
        for i in range(1, n + 1):
            self.assertIn(f"/visio/pages/page{i}.xml", ct)
            page = etree.fromstring(z.read(f"visio/pages/page{i}.xml"))
            ids = {s.get("ID") for s in page.iter(f"{V}Shape")}
            self.assertTrue(ids)
            for c in page.iter(f"{V}Connect"):
                self.assertIn(c.get("FromSheet"), ids)
                self.assertIn(c.get("ToSheet"), ids)

    def test_every_step_is_on_its_page_with_guidance(self):
        z = zipfile.ZipFile(io.BytesIO(FILES["visio/dq-capability-process-map.vsdx"]))
        for i, p in enumerate(M["processes"]):
            xml = z.read(f"visio/pages/page{i + 2}.xml").decode()
            for s in p["steps"]:
                self.assertIn(f'V="{p["id"]}.{s["id"]}"', xml)


if __name__ == "__main__":
    unittest.main()
