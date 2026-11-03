"""Knowledge graph, ontology, events, training, releases and the build bundle."""
import collections
import re
import subprocess
import sys
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from dqkit import graph, mcp_server  # noqa: E402

K = ROOT / "knowledge"
load = lambda n: yaml.safe_load((K / f"{n}.yaml").read_text(encoding="utf-8"))


class KnowledgeGraph(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.g = graph.build()

    def test_no_dangling_links_and_one_connected_graph(self):
        self.assertEqual(self.g["stats"]["dangling"], 0, self.g["dangling"][:5])
        adj = collections.defaultdict(set)
        for e in self.g["edges"]:
            adj[e["s"]].add(e["o"])
            adj[e["o"]].add(e["s"])
        start = self.g["nodes"][0]["id"]
        seen, stack = {start}, [start]
        while stack:
            for y in adj[stack.pop()]:
                if y not in seen:
                    seen.add(y)
                    stack.append(y)
        self.assertEqual(len(seen), len(self.g["nodes"]), "the graph should be one connected whole")

    def test_every_relationship_and_type_is_declared(self):
        ont = load("ontology")
        props = {p["id"] for p in ont["properties"]}
        classes = {c["id"] for c in ont["classes"]}
        self.assertEqual({e["p"] for e in self.g["edges"]} - props, set())
        self.assertEqual({n["type"] for n in self.g["nodes"]} - classes, set())
        for p in ont["properties"]:
            self.assertIn(p["domain"], classes, p["id"])
            self.assertIn(p["range"], classes, p["id"])

    def test_every_node_has_a_source(self):
        for n in self.g["nodes"]:
            self.assertTrue(n.get("source"), n["id"])

    def test_terms_have_definitions_and_thesaurus_links_resolve(self):
        L, O = load("learning"), load("ontology")
        terms = {t["term"] for t in L["glossary"]} | {t["term"] for t in O["thesaurus"]}
        for t in O["thesaurus"]:
            for k in ("broader", "related"):
                for x in t.get(k, []):
                    self.assertIn(x, terms, (t["term"], k, x))
        for n in self.g["nodes"]:
            if n["type"] == "Term":
                self.assertTrue(n.get("definition") or n.get("alt"), n["id"])

    def test_find_path_and_exports(self):
        self.assertEqual(graph.find(self.g, "Jersey", 1)[0]["id"], "Jurisdiction:jersey")
        p = graph.path(self.g, "Term:accuracy", "Framework:uk-dam-policy")
        self.assertEqual(p[0], "Term:accuracy")
        self.assertEqual(p[-1], "Framework:uk-dam-policy")
        ttl = graph.to_turtle(self.g)
        self.assertIn("owl:ObjectProperty", ttl)
        self.assertIn("skos:Concept", ttl)
        self.assertNotRegex(ttl, r"<[^>]*\s[^>]*>", "IRIs must not contain spaces")

    def test_committed_exports_are_current(self):
        ttl = (ROOT / "vocab" / "knowledge-graph.ttl").read_text(encoding="utf-8")
        self.assertEqual(ttl, graph.to_turtle(self.g), "run python scripts/build_vocab.py")

    def test_mcp_explore(self):
        self.assertIn("explore_knowledge", {t["name"] for t in mcp_server.TOOLS})
        r = mcp_server.call_tool("explore_knowledge", {"from": "Data steward", "to": "ISO 8000"})
        self.assertTrue(r["path"])
        self.assertTrue(mcp_server.call_tool("explore_knowledge", {"query": "completeness"}))

    def test_lineage_flows_reference_their_own_stages(self):
        for f in load("ontology")["lineage"]:
            ids = {s["id"] for s in f["stages"]}
            for a, b in f["flows"]:
                self.assertIn(a, ids)
                self.assertIn(b, ids)


class EventsAndTraining(unittest.TestCase):
    def test_events_are_honest(self):
        E = load("events")
        for e in E["events"]:
            self.assertIn(e["checked"], ("yes", "listed"), e["id"])
            self.assertTrue(e["url"].startswith("https://"), e["id"])
            self.assertIn(e["kind"], E["kinds"])
            self.assertIn(e["format"], E["formats"])
            self.assertTrue(e.get("accessibility"), e["id"])
            self.assertLessEqual(e["start"][:10], e["end"][:10], e["id"])

    def test_training_links_skills_and_modules(self):
        T, L = load("training"), load("learning")
        skills, mods = {s["id"] for s in T["skills"]}, {m["id"] for m in L["modules"]}
        for s in T["skills"]:
            self.assertTrue(set(s["modules"]) <= mods, s["id"])
        for c in T["courses"]:
            self.assertTrue(set(c["skills"]) <= skills, c["id"])
            self.assertIn(c["level"], T["levels"])
            self.assertIn(c["cost_band"], ("free", "paid", "not stated"))
            self.assertIn(c["checked"], ("yes", "listed"))


class Releases(unittest.TestCase):
    def test_versions_are_semantic_descending_and_in_the_changelog(self):
        R = load("releases")["releases"]
        vs = [tuple(int(x) for x in r["version"].split(".")) for r in R]
        self.assertEqual(vs, sorted(vs, reverse=True))
        log = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
        for r in R:
            self.assertRegex(log, rf"## {re.escape(r['version'])} ", r["version"])
            for it in r["items"]:
                self.assertIn(it["type"], ("new", "changed", "fixed", "removed"))

    def test_portal_version_comes_from_releases(self):
        sys.path.insert(0, str(ROOT / "scripts"))
        import build_dq_portal as b
        self.assertEqual(b.VERSION, load("releases")["releases"][0]["version"])
        pages = {p[0] for p in b.PAGES}
        for r in load("releases")["releases"]:
            for p in r.get("pages_new", []) + r.get("pages_changed", []):
                self.assertIn(p, pages, (r["version"], p))

    def test_bundle_is_current(self):
        r = subprocess.run([sys.executable, str(ROOT / "scripts" / "build_bundle.py"), "--check"], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)


if __name__ == "__main__":
    unittest.main()
