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

    def test_no_values_lost_to_unquoted_commas(self):
        """A comma inside an unquoted flow-mapping value silently creates a key with a null value."""
        files = list(K.glob("*.yaml")) + list((ROOT / "packs").glob("*.yaml")) + list((ROOT / "rules" / "library").glob("*.yaml"))
        def walk(o, where):
            if isinstance(o, dict):
                for k, v in o.items():
                    self.assertIsNotNone(v, f"{where}: key {k!r} has no value (unquoted comma?)")
                    walk(v, where)
            elif isinstance(o, list):
                for v in o:
                    walk(v, where)
        for f in files:
            walk(yaml.safe_load(f.read_text(encoding="utf-8")), f.name)

    def test_internal_links_resolve(self):
        """Every portal link in the knowledge base (link, where, related, try, cta targets) points to a built page."""
        pages = {p.stem for p in (ROOT / "portal" / "src" / "pages").glob("*.html")}
        articles = {a["id"] for a in load("articles")["articles"]}
        found = []

        def walk(o):
            if isinstance(o, dict):
                for v in o.values():
                    walk(v)
            elif isinstance(o, list):
                for v in o:
                    walk(v)
            elif isinstance(o, str) and re.fullmatch(r"[a-z0-9-]+\.html(#[\w-]+)?", o):
                found.append(o)
        for f in K.glob("*.yaml"):
            walk(yaml.safe_load(f.read_text(encoding="utf-8")))
        self.assertGreater(len(found), 50)
        for u in found:
            self.assertIn(u.split("#")[0][:-5], pages, u)
        for a in load("articles")["articles"]:
            for r in a.get("related", []):
                if not r.endswith(".html") and "#" not in r and not r.startswith("http"):
                    self.assertIn(r, articles, (a["id"], r))

    def test_every_knowledge_file_has_a_current_review(self):
        """Each file names an owning role and was reviewed in the last 12 months, so nothing goes quietly stale."""
        import datetime as dt
        today = dt.date.today()
        for f in K.glob("*.yaml"):
            r = (yaml.safe_load(f.read_text(encoding="utf-8")) or {}).get("review")
            self.assertTrue(r and r.get("owner_role"), f.name)
            age = (today - dt.date.fromisoformat(str(r["last_reviewed"]))).days
            self.assertLessEqual(age, 365, f"{f.name} not reviewed for {age} days")

    def test_media_honesty(self):
        m = load("media")
        for s in m["slides"]:
            self.assertTrue(s.get("source") or s["kind"] in ("data",) or s["label"] == "From the Commons" or s.get("own"), s["id"])
        for x in m["library"] + m["podcasts"] + m["videos"]:
            self.assertIn(x["checked"], ("yes", "listed"), x["title"])
            self.assertTrue(x["url"].startswith("https://"), x["title"])

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


class Playbook(unittest.TestCase):
    """The data quality management playbook is complete, consistent and its document is current."""

    def test_playbook(self):
        import subprocess
        import sys as _sys
        pb = load("playbook")
        clauses = {r["clause"] for r in csv.DictReader(open(K / "requirements.csv", encoding="utf-8"))}
        fws = {f["id"] for f in load("frameworks")["frameworks"]}
        roles = {r["id"] for r in pb["roles"]}
        self.assertEqual([s["n"] for s in pb["stages"]], list(range(1, 9)))
        for s in pb["stages"]:
            self.assertEqual(set(s["raci"]), roles, s["id"])
            self.assertEqual(list(s["raci"].values()).count("A"), 1, f"{s['id']}: exactly one accountable role")
            for c in s["dam"]:
                self.assertIn(c, clauses, s["id"])
            self.assertTrue(s["checklist"] and s["inclusion"], s["id"])
            self.assertTrue((ROOT / "portal" / "src" / "pages" / s["toolkit"]["link"]).exists(), s["toolkit"]["link"])
        for j in pb["jurisdictions"]:
            for f in j["frameworks"]:
                self.assertIn(f, fws, j["where"])
        for t in pb["templates"]:
            self.assertTrue(all(isinstance(x, str) and x for x in t["fields"]), t["id"])
        r = subprocess.run([_sys.executable, str(ROOT / "scripts" / "build_playbook_doc.py"), "--check"], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stdout)
