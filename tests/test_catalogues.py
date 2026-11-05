"""Checks for the catalogue and quality tool integration knowledge (knowledge/catalogue-integration.yaml).

Plain English: every lock-in risk must point to questions and contract clauses that exist, every product
claim must have a source and a date checked, and every link to another page must go somewhere real.
"""
import re
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
K = yaml.safe_load((ROOT / "knowledge" / "catalogue-integration.yaml").read_text(encoding="utf-8"))
CLAUSES = {c["id"] for c in yaml.safe_load((ROOT / "knowledge" / "commercial.yaml").read_text(encoding="utf-8"))["clauses"]}
PAGES = {f.stem for f in (ROOT / "portal" / "src" / "pages").glob("*.html")}
PAGE_HTML = (ROOT / "portal" / "src" / "pages" / "catalogues.html").read_text(encoding="utf-8")


class CatalogueKnowledge(unittest.TestCase):
    def test_risks_link_to_real_questions_and_clauses(self):
        qids = {q["id"] for q in K["rfx"]}
        for r in K["risks"]:
            self.assertTrue(r["check"] and r["ask"] and r["mitigation"], r["id"])
            for q in r["rfx"]:
                self.assertIn(q, qids, f"{r['id']} names missing question {q}")
            for c in r["clauses"]:
                self.assertIn(c, CLAUSES, f"{r['id']} names missing clause {c}")

    def test_every_product_claim_is_sourced_and_dated(self):
        for p in K["products"]:
            self.assertTrue(p["sources"], p["id"])
            for s in p["sources"]:
                self.assertRegex(s, r"^https://", p["id"])
            self.assertRegex(p["checked"], r"^\d{4}-\d{2}-\d{2}$")
            self.assertIn(p["native_dq"], {"yes", "partial", "no"})

    def test_questions_are_well_formed(self):
        ids = [q["id"] for q in K["rfx"]]
        self.assertEqual(len(ids), len(set(ids)))
        for q in K["rfx"]:
            self.assertIn(q["weight"], {"must", "should", "could"})
            self.assertIn(q["stage"], {"RFI", "RFP", "both"})
            self.assertTrue(q["good"] and q["evidence"])

    def test_patterns_and_depth(self):
        self.assertEqual(sorted(p["lockin"] for p in K["patterns"]), [1, 2, 3, 4, 5])
        self.assertEqual([d["level"] for d in K["depth"]], [0, 1, 2, 3, 4])

    def test_internal_links_resolve(self):
        links = [s["link"] for s in K["steps"]] + [r["link"] for r in K["related"]]
        for link in links:
            if link.startswith("#"):
                self.assertIn(f'id="{link[1:]}"', PAGE_HTML, link)
            else:
                self.assertIn(link.split(".html")[0], PAGES, link)
            m = re.search(r"#add=([A-Z0-9,]+)", link)
            if m:
                for c in m.group(1).split(","):
                    self.assertIn(c, CLAUSES)

    def test_review_date_is_set(self):
        self.assertRegex(K["review"]["last_reviewed"], r"^\d{4}-\d{2}-\d{2}$")


if __name__ == "__main__":
    unittest.main()
