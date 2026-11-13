"""Checks for v2.10.0: the standards catalogue, the Weaver's DQV output and the three-portal ecosystem.

Plain English: every standard has a unique id, a known domain and status, a public https link and Rosetta
concepts that exist; the Rosetta has eleven standards with a value per concept; the Weaver writes valid DQV
for a sample record; and every cross-reference to the DAM capability playbooks uses ids that exist there
(checked against a copy of the playbooks' content when one is available next to this repository).
"""
import os
import re
import unittest
from pathlib import Path

import yaml

from dqkit import weaver

ROOT = Path(__file__).resolve().parent.parent
K = ROOT / "knowledge"
load = lambda n: yaml.safe_load((K / f"{n}.yaml").read_text(encoding="utf-8"))
SC, RO, ECO, WH, ST = load("standards-catalogue"), load("rosetta"), load("ecosystem"), load("dama-wheel"), load("stakeholders")
PAGES = {f.stem for f in (ROOT / "portal" / "src" / "pages").glob("*.html")}
PLAYBOOKS = Path(os.environ.get("DAM_PLAYBOOKS_DIR", ROOT.parent / "dam-capability-playbooks"))
CATALOGUE = Path(os.environ.get("CATALOGUE_DIR", ROOT.parent / "github-repos-asset-catalogue"))


class StandardsCatalogue(unittest.TestCase):
    def test_ids_unique_and_fields_valid(self):
        ids = [s["id"] for s in SC["standards"]]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertGreaterEqual(len(ids), 50)
        domains = {d["id"] for d in SC["domains"]}
        sources = {s["id"] for s in SC["sources"]}
        for s in SC["standards"]:
            with self.subTest(s["id"]):
                self.assertIn(s["domain"], domains)
                self.assertIn(s["status"], {"Mandated", "Recommended", "UK guidance", "Widely used"})
                self.assertIn(s["weaver"], {"both", "out", "in", "check", "none"})
                self.assertTrue(s["url"].startswith("https://"), s["url"])
                if "source" in s:
                    self.assertIn(s["source"], sources)

    def test_concepts_exist_in_rosetta(self):
        concepts = {c["id"] for c in RO["concepts"]}
        for s in SC["standards"]:
            for c in s.get("concepts", []):
                self.assertIn(c, concepts, s["id"])

    def test_dqv_is_present_and_written_by_the_weaver(self):
        dqv = next(s for s in SC["standards"] if s["id"] == "dqv")
        self.assertIn(dqv["weaver"], {"out", "both"})
        self.assertEqual(dqv["rosetta"], "DQV")

    def test_no_private_workbook_names(self):
        text = (K / "standards-catalogue.yaml").read_text(encoding="utf-8").lower()
        for banned in ("xlsx", "crosswalks", "classification_v5", "draft taxonomy"):
            self.assertNotIn(banned, text)

    def test_standards_count_claims_match_the_catalogue(self):
        # every "N-standard catalogue" claim in the comparison and gains must equal the catalogue's length
        text = (K / "ecosystem.yaml").read_text(encoding="utf-8")
        claims = [int(n) for n in re.findall(r"\b(\d+)-standard catalogue", text)]
        self.assertTrue(claims, "no standards count claim found")
        for n in claims:
            self.assertEqual(n, len(SC["standards"]))

    def test_tracked_by_the_catalogue_includes_croissant_and_linkml(self):
        names = {s.get("catalogue") for s in SC["standards"]}
        self.assertTrue({"Croissant", "LinkML"} <= names)


class Rosetta(unittest.TestCase):
    def test_eleven_standards_each_concept_complete(self):
        self.assertEqual(len(RO["standards"]), 11)
        for c in RO["concepts"]:
            for s in RO["standards"]:
                self.assertIn(s, c["standards"], f'{c["id"]} lacks {s}')


class WeaverDqv(unittest.TestCase):
    def test_weave_returns_dqv_quality_metadata(self):
        rec = {"@context": "https://schema.org", "@type": "Dataset", "name": "Main rivers",
               "description": "Rivers in England", "publisher": {"@type": "Organization", "name": "Environment Agency"},
               "license": "https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/"}
        out = weaver.weave(rec)
        q = out["quality"]
        self.assertIn("dqv", q["@context"])
        graph = q.get("@graph") or [q]
        types = {t for n in graph for t in ([n.get("@type")] if isinstance(n.get("@type"), str) else n.get("@type", []))}
        self.assertIn("dqv:QualityMetadata", types | {q.get("@type")})
        text = repr(q)
        self.assertIn("dqv:QualityMeasurement", text)
        self.assertIn("metric-cda-coverage", text)


class Ecosystem(unittest.TestCase):
    def test_three_portals(self):
        self.assertEqual({p["id"] for p in ECO["portals"]}, {"dqc", "dam", "cat"})

    def test_dama_map_matches_the_wheel(self):
        wheel = {a["id"] for a in WH["areas"]}
        rows = ECO["xref"]["dama"]
        self.assertEqual({r["dqc"] for r in rows}, wheel)
        for r in rows:
            self.assertRegex(r["dam"], r"^DM-[A-Z]+$")

    def test_role_map_uses_commons_roles(self):
        roles = {r["id"] for r in ST["roles"]}
        for r in ECO["xref"]["roles"]:
            self.assertIn(r["dqc"], roles)
            self.assertRegex(r["dam"], r"^[A-Z]{3}$")

    def test_commons_paths_exist(self):
        for key, items in ECO["placements"].items():
            self.assertIn(key, PAGES, key)
        for j in ECO["journeys"]:
            for step in j["steps"]:
                if step["portal"] == "dqc":
                    self.assertIn(step["path"].split("#")[0][:-5], PAGES, step["path"])
        for n in ECO["lineage"]["nodes"]:
            if n["portal"] == "dqc":
                self.assertIn(n["path"].split("#")[0][:-5], PAGES, n["path"])
        ids = {n["id"] for n in ECO["lineage"]["nodes"]}
        for e in ECO["lineage"]["edges"]:
            self.assertIn(e["from"], ids)
            self.assertIn(e["to"], ids)

    def _catalogue_paths(self):
        out = []
        def walk(x):
            if isinstance(x, dict):
                if x.get("portal") == "cat" and isinstance(x.get("path"), str):
                    out.append(x["path"])
                for k, v in x.items():
                    if k == "catalogue_views":
                        out.extend(view["path"] for view in v.values())
                    walk(v)
            elif isinstance(x, list):
                for v in x:
                    walk(v)
        walk(ECO)
        return out

    def test_catalogue_links_are_views_it_publishes(self):
        """Each link into the repos asset catalogue names a view in the catalogue's own manifest (data/xref.json)."""
        man = CATALOGUE / "dist" / "data" / "xref.json"
        if not man.exists():
            self.skipTest("repos asset catalogue not alongside")
        import json
        views = {v["id"] for v in json.loads(man.read_text(encoding="utf-8"))["keys"]["views"]}
        view = lambda p: re.match(r"#?([\w-]*)", p.split("#", 1)[-1]).group(1)
        bad = [p for p in self._catalogue_paths() if view(p) not in views]
        self.assertEqual(bad, [])
        self.assertNotIn("crosswalk", views)  # negative test: the old #crosswalk link would be caught

    def test_catalogue_paths_found(self):
        paths = self._catalogue_paths()
        self.assertGreater(len(paths), 8)
        self.assertNotIn("#crosswalk", paths)

    def test_deep_links_follow_address_changes(self):
        """The wheel and the role pages read #area-... and #role from the address on load and whenever it changes."""
        pages = ROOT / "portal" / "src" / "pages"
        for name in ("wheel", "roles"):
            src = (pages / f"{name}.html").read_text(encoding="utf-8")
            self.assertRegex(src, r"addEventListener\(\s*\"hashchange\"", name)

    def test_xref_manifest_built(self):
        p = ROOT / "portal" / "dist" / "api" / "xref.json"
        if not p.exists():
            self.skipTest("portal not built")
        import json
        x = json.loads(p.read_text(encoding="utf-8"))
        self.assertEqual(len(x["keys"]["dama_areas"]), 11)
        self.assertEqual(len(x["keys"]["standards"]), len(SC["standards"]))

    @unittest.skipUnless((PLAYBOOKS / "content" / "frameworks.yaml").exists(), "playbooks repo not alongside")
    def test_ids_exist_in_the_playbooks(self):
        fw = yaml.safe_load((PLAYBOOKS / "content" / "frameworks.yaml").read_text(encoding="utf-8"))
        pb = (PLAYBOOKS / "content" / "playbooks.yaml").read_text(encoding="utf-8")
        areas = {a["id"] for a in fw["dama"]["areas"]}
        for r in ECO["xref"]["dama"]:
            self.assertIn(r["dam"], areas)
        for r in ECO["xref"]["roles"]:
            self.assertRegex(pb, rf"\b{re.escape(r['dam'])}\b")


if __name__ == "__main__":
    unittest.main()
