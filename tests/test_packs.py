"""Framework packs, the framework registry and crosswalk conversion."""
import csv
import json
import unittest
from pathlib import Path

from dqkit import packs

ROOT = Path(__file__).resolve().parent.parent
RES = ROOT / "assessments" / "portfolio" / "assets" / "ndl-environment-air-quality-chart.results.json"


class Registry(unittest.TestCase):
    def test_every_framework_maps_every_dimension_to_kit_dimensions(self):
        kit = {r["id"] for r in csv.DictReader(open(ROOT / "vocab" / "dimensions.csv", encoding="utf-8"))}
        ids = set()
        for f in packs.registry():
            self.assertNotIn(f["id"], ids)
            ids.add(f["id"])
            self.assertEqual(set(f["map"]), set(f["dimensions"]), f["id"])
            for v in f["map"].values():
                self.assertLessEqual(set(v), kit, f["id"])
            self.assertIn(f["verified"], ("yes", "partly", "unpublished"), f["id"])
            for k in ("name", "publisher", "jurisdiction", "sector", "type", "status"):
                self.assertTrue(f.get(k), (f["id"], k))
        self.assertGreaterEqual(len(ids), 25)

    def test_matrix_covers_all(self):
        m = packs.crosswalk_matrix()
        self.assertEqual(set(m), {f["id"] for f in packs.registry()})
        self.assertIn("Currentness", m["iso-iec-25012"]["timeliness"])


class Packs(unittest.TestCase):
    def setUp(self):
        self.res = json.loads(RES.read_text(encoding="utf-8"))

    def test_all_packs_load_and_assess(self):
        ps = packs.list_packs()
        self.assertGreaterEqual(len(ps), 10)
        for p in ps:
            out = packs.assess(p, self.res)
            self.assertEqual(len(out["requirements"]), len(p["requirements"]))
            for r in out["requirements"]:
                self.assertIn(r["status"], ("met", "partly", "not met", "manual", "not applicable"))

    def test_evidence_rules(self):
        a = packs.assess("uk-dam-cda", self.res)
        by = {r["id"]: r for r in a["requirements"]}
        self.assertEqual(by["DAM-1"]["status"], "met")      # owner recorded
        self.assertEqual(by["DAM-3"]["status"], "not met")  # no DQAP link on NDL charts
        self.assertEqual(by["DQAP-5"]["status"], "manual")
        self.res["asset"]["dqap"] = "https://example.org/dqap"
        self.assertEqual({r["id"]: r for r in packs.assess("uk-dam-cda", self.res)["requirements"]}["DAM-3"]["status"], "met")

    def test_unknown_pack_and_path_traversal(self):
        for bad in ("nope", "../packs/uk-gdqf"):
            with self.assertRaises(ValueError):
                packs.load_pack(bad)

    def test_dqmi_style_index(self):
        res = {"results": [
            {"dimension": "completeness", "columns": ["a"], "performance": 90.0},
            {"dimension": "validity", "columns": ["a"], "performance": 80.0},
            {"dimension": "completeness", "columns": ["b"], "performance": 100.0}]}
        out = packs.dqmi_style(res, 0.5)
        self.assertEqual(out["items"], {"a": 80.0, "b": 100.0})
        self.assertEqual(out["index"], 45.0)

    def test_convert(self):
        out = packs.convert(self.res, "iso-iec-25012")
        rows = {r["dimension"]: r for r in out["dimensions"]}
        self.assertEqual(len(rows), 15)
        self.assertEqual(rows["Currentness"]["score"], self.res["dimensions"]["timeliness"]["mean_performance"])
        self.assertEqual(rows["Confidentiality"]["status"], "not measured by data rules")
        with self.assertRaises(ValueError):
            packs.convert(self.res, "not-a-framework")


if __name__ == "__main__":
    unittest.main()
