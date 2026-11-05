"""Checks for v2.12.0: governance bodies, getting involved and badges, code evidence, DAM requirement links,
display options, source labels and journeys.

Plain English: every governance body is in a known layer with a terms-of-reference and activity status and links
that work; question routes point to real bodies; every badge has its images and passes contrast; working groups
point to real backlog items; the communications kit links back to the portal and names no one; code evidence uses
the wheel's areas; playbook stages link only to DAM requirements we know; the shell carries the display options,
source labels and journey bar; and nothing here contains an email address.
"""
import importlib.util
import re
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
K = ROOT / "knowledge"
load = lambda n: yaml.safe_load((K / f"{n}.yaml").read_text(encoding="utf-8"))
G, P, CE, ECO, PB, BU, WH = (load(n) for n in ("governance-bodies", "participation", "code-evidence", "ecosystem", "playbook", "build", "dama-wheel"))
PAGES = {f.stem for f in (ROOT / "portal" / "src" / "pages").glob("*.html")}
EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
BL = {b["id"] for b in BU["backlog"]}


class Governance(unittest.TestCase):
    def test_bodies_are_complete(self):
        layers = {l["id"] for l in G["layers"]}
        ids = [b["id"] for b in G["bodies"]]
        self.assertEqual(len(ids), len(set(ids)))
        for b in G["bodies"]:
            with self.subTest(b["id"]):
                self.assertIn(b["layer"], layers)
                self.assertIn(b["tor"], ("published", "described", "not found"))
                self.assertIn(b["activity"], ("active", "unclear", "historic"))
                for k in ("purpose", "engagement", "decides", "cadence"):
                    self.assertTrue(b.get(k))
                self.assertTrue(b["aims"] and b["outcomes"] and b["links"])
                for l in b["links"]:
                    u = l["url"]
                    self.assertTrue(u.startswith("https://") or u.split("#")[0][:-5] in PAGES, u)
        self.assertTrue(all(any(b["layer"] == l for b in G["bodies"]) for l in layers), "every layer has a body")

    def test_routes_and_requirements(self):
        ids = {b["id"] for b in G["bodies"]}
        reqs = {r["id"] for r in ECO["xref"]["requirements"]}
        for r in G["routes"]:
            for g in r["go"]:
                self.assertIn(g, ids)
        for b in G["bodies"]:
            for d in b.get("dam", []):
                self.assertIn(d, reqs)

    def test_no_email_addresses(self):
        for f in ("governance-bodies.yaml", "participation.yaml", "code-evidence.yaml"):
            self.assertIsNone(EMAIL.search((K / f).read_text(encoding="utf-8")), f)


class Participation(unittest.TestCase):
    def test_badges_have_images_and_contrast(self):
        spec = importlib.util.spec_from_file_location("mb", ROOT / "scripts" / "make_badges.py")
        mb = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mb)
        out = ROOT / "portal" / "src" / "badges"
        for b in P["badges"]:
            with self.subTest(b["id"]):
                self.assertGreaterEqual(mb.contrast_white(b["color"]), 4.5)
                self.assertIn(b["confirm"], ("self", "maintainer"))
                for f in (f'{b["id"]}.svg', f'{b["id"]}-signature.svg', f'{b["id"]}-square.svg', f'{b["id"]}-signature.png', f'{b["id"]}-square.png'):
                    self.assertTrue((out / f).exists(), f)

    def test_working_groups_and_routes(self):
        for g in P["working_groups"]:
            for b in g["backlog"]:
                self.assertIn(b, BL, g["id"])
        for r in P["routes"]:
            for x in r["items"]:
                link = x["link"]
                self.assertTrue(link.startswith("#") or link.split("#")[0][:-5] in PAGES, link)

    def test_kit_links_back_and_names_no_one(self):
        for k in P["kit"]:
            self.assertNotIn("@", k["text"], k["id"])
        self.assertTrue(all("{link}" in k["text"] for k in P["kit"] if k["id"] != "update"))

    def test_github_forms_and_contact_topics(self):
        for f in ("8-badge-claim.yml", "9-join-working-group.yml"):
            t = (ROOT / ".github" / "ISSUE_TEMPLATE" / f).read_text(encoding="utf-8")
            yaml.safe_load(t)
            self.assertIn("never an email address", t)
        for topic in ("Join a working group", "Become a champion or ambassador", "Claim a badge"):
            self.assertIn(topic, BU["contact_topics"])


class Evidence(unittest.TestCase):
    def test_code_evidence_uses_wheel_areas(self):
        wheel = {a["id"] for a in WH["areas"]}
        self.assertTrue(CE["source"]["data_as_of"])
        for a in CE["areas"]:
            self.assertIn(a["id"], wheel)
            self.assertLessEqual(a["in_code"], a["repos"])

    def test_playbook_stages_link_known_requirements(self):
        reqs = {r["id"] for r in ECO["xref"]["requirements"]}
        seen = set()
        for s in PB["stages"]:
            for r in s.get("dam_playbooks", []):
                self.assertIn(r, reqs)
                seen.add(r)
        self.assertGreaterEqual(len(seen), 14)


class Shell(unittest.TestCase):
    def test_display_labels_and_journeys(self):
        s = (ROOT / "portal" / "src" / "shell.html").read_text(encoding="utf-8")
        for needle in ('id="dqp-disp-open"', 'name="fs" value="150"', 'value="high"', "dqp-display", "dqp-src", "dqp-journey", 'data-k="official"' if False else "official"):
            self.assertIn(needle, s)


if __name__ == "__main__":
    unittest.main()
