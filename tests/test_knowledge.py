"""The knowledge base loads, its links are well formed, and cross-references resolve."""
import csv
import re
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
K = ROOT / "knowledge"


def load(name):
    return yaml.safe_load((K / f"{name}.yaml").read_text(encoding="utf-8"))


def urls(obj):
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k == "url" and v:
                yield v
            else:
                yield from urls(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from urls(v)


class Knowledge(unittest.TestCase):
    def test_external_links_are_https(self):
        for name in ("frameworks", "communities", "learning", "ai-for-dq"):
            for u in urls(load(name)):
                if not u.endswith(".html") and "#" not in u:
                    self.assertTrue(u.startswith("https://"), (name, u))

    def test_requirements_reference_known_frameworks(self):
        ids = {f["id"] for f in load("frameworks")["frameworks"]}
        rows = list(csv.DictReader(open(K / "requirements.csv", encoding="utf-8")))
        self.assertGreaterEqual(len(rows), 30)
        for r in rows:
            self.assertIn(r["source"], ids)

    def test_maturity_model_is_complete(self):
        m = load("maturity")
        self.assertEqual([l["name"] for l in m["levels"]], ["Beginning", "Emerging", "Learning", "Developing", "Mastering"])
        for t in m["themes"]:
            self.assertEqual(len(t["statements"]), 5, t["id"])
            self.assertEqual(len(t["next"]), 5, t["id"])

    def test_surveys_never_ask_for_names_or_emails(self):
        s = load("surveys")
        for sv in s["surveys"]:
            for q in sv["questions"]:
                self.assertIsNone(re.search(r"\b(your name|email address|date of birth)\b", q["q"], re.I), q["q"])
        self.assertIn("don't ask for your name", s["privacy_notice"])

    def test_learning_links_point_to_portal_pages_or_https(self):
        pages = {p.stem for p in (ROOT / "portal" / "src" / "pages").glob("*.html")}
        for m in load("learning")["modules"]:
            for r in m["resources"]:
                u = r["url"]
                if not u.startswith("https://"):
                    self.assertIn(u.split("#")[0].removesuffix(".html"), pages, u)

    def test_ai_guidance(self):
        a = load("ai-for-dq")
        self.assertEqual([s["n"] for s in a["route_to_toolkit"]["stages"]], list(range(1, 8)))
        for c in a["case_studies"]:
            if c["id"] != "C2":
                self.assertTrue(c["sources"], c["id"])  # real case studies must cite sources
        for w in a["worked_examples"]:
            self.assertTrue(w.get("illustrative"), w["id"])


if __name__ == "__main__":
    unittest.main()
