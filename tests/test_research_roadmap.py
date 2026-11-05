"""Checks for v2.11.0: user research with prospective consumers, the email bundle and the open roadmap.

Plain English: research questions, rounds and findings point to methods, questions and backlog items that exist;
the sign-up never asks for contact details anywhere public; every open backlog item is scored, and its MoSCoW
priority matches the band of its score (so the roadmap, the build page and GitHub milestones agree); objectives
and assessments name strategy anchors that exist; and the bundle builds with no email addresses in it.
"""
import re
import tempfile
import unittest
import zipfile
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
K = ROOT / "knowledge"
load = lambda n: yaml.safe_load((K / f"{n}.yaml").read_text(encoding="utf-8"))
R, RM, BU = load("research"), load("roadmap"), load("build")
BL = {b["id"]: b for b in BU["backlog"]}
PAGES = {f.stem for f in (ROOT / "portal" / "src" / "pages").glob("*.html")}
EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")


def score(a):
    w = {c["id"]: c["weight"] for c in RM["criteria"]}
    return sum(w[k] * a[k] for k in w) / sum(w.values()) * RM["effort_factor"][a["effort"]]


class Research(unittest.TestCase):
    def test_questions_rounds_findings_link_up(self):
        methods = {m["id"] for m in R["methods"]}
        qids = {q["id"] for q in R["questions"]}
        for q in R["questions"]:
            self.assertIn(q["horizon"], ("tactical", "strategic"))
            for m in q["methods"]:
                self.assertIn(m, methods, q["id"])
            for b in q["backlog"]:
                self.assertIn(b, BL, q["id"])
        for r in R["rounds"]:
            for m in r["methods"]:
                self.assertIn(m, methods)
            for q in r["questions"]:
                self.assertIn(q, qids)
        for f in R["findings"]:
            self.assertIn(f["source"], ("research", "feedback", "secondary"))
            self.assertIn(f["link"].split("#")[0][:-5], PAGES)
            for b in f["backlog"]:
                self.assertIn(b, BL)

    def test_both_horizons_covered(self):
        self.assertEqual({q["horizon"] for q in R["questions"]}, {"tactical", "strategic"})

    def test_contact_details_only_in_the_private_form(self):
        contact = [q for q in R["screener"] if q.get("contact")]
        self.assertEqual(len(contact), 1, "exactly one question collects contact details")
        self.assertIn("never published", contact[0]["text"])
        self.assertIn("public GitHub issues", R["sign_up"]["status_when_empty"])
        self.assertIn("Take part in user research", BU["contact_topics"])

    def test_no_email_addresses(self):
        for f in ("research.yaml", "roadmap.yaml"):
            self.assertIsNone(EMAIL.search((K / f).read_text(encoding="utf-8")), f)


class Roadmap(unittest.TestCase):
    def test_every_open_item_is_scored(self):
        assessed = {a["id"] for a in RM["assessments"]}
        for b in BU["backlog"]:
            if b["status"] != "done":
                self.assertIn(b["id"], assessed, f'{b["id"]} has no assessment')
        for a in RM["assessments"]:
            self.assertIn(a["id"], BL)

    def test_moscow_matches_score_band(self):
        for a in RM["assessments"]:
            s = score(a)
            band = next(x["moscow"] for x in RM["bands"] if s >= x["min"])
            self.assertEqual(BL[a["id"]]["moscow"], band, f'{a["id"]} scores {s:.2f}, so it should be {band}')

    def test_scores_in_range_and_anchors_exist(self):
        anchors = {a["id"] for a in RM["anchors"]}
        crit = [c["id"] for c in RM["criteria"]]
        evid = {q["id"] for q in R["questions"]} | {f["id"] for f in R["findings"]}
        for a in RM["assessments"]:
            for c in crit:
                self.assertIn(a[c], (0, 1, 2, 3), a["id"])
            self.assertIn(a["effort"], RM["effort_factor"])
            for x in a["anchors"]:
                self.assertIn(x, anchors, a["id"])
            for e in a["evidence"]:
                self.assertIn(e, evid, a["id"])
        for o in RM["objectives"]:
            self.assertIn(o["horizon"], ("tactical", "strategic"))
            for x in o["anchors"]:
                self.assertIn(x, anchors)
            for i in o["items"]:
                self.assertIn(i, BL, o["id"])
        for a in RM["anchors"]:
            self.assertTrue(a["url"].startswith("https://"))
            self.assertIn(a["status"], ("published", "committed", "ongoing"))

    def test_pipeline_links_exist(self):
        for p in RM["pipeline"]:
            self.assertIn(p["link"].split("#")[0][:-5], PAGES, p["link"])


class Bundle(unittest.TestCase):
    def test_bundle_builds_without_addresses(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location("bdp", ROOT / "scripts" / "build_dq_portal.py")
        bdp = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(bdp)
        with tempfile.TemporaryDirectory() as t:
            out = Path(t) / "research"
            bdp.research_bundle(out)
            names = sorted(p.name for p in out.iterdir())
            for n in ("README.txt", "dq-commons-research-bundle.zip", "dq-commons-research-invitation.docx", "dq-commons-research-invitation.eml",
                      "dq-commons-participant-information-and-consent.docx", "dq-commons-research-screener.docx", "dq-commons-research-session-guides.docx"):
                self.assertIn(n, names)
            eml = (out / "dq-commons-research-invitation.eml").read_text(encoding="utf-8")
            self.assertNotRegex(eml, r"(?im)^(to|from|cc|bcc):")
            self.assertIsNone(EMAIL.search(eml))
            with zipfile.ZipFile(out / "dq-commons-research-bundle.zip") as z:
                self.assertEqual(len(z.namelist()), 6)


if __name__ == "__main__":
    unittest.main()
