"""Checks for v2.8.0: site map, Ask the Commons, reuse routes, the open data API, sharing and reading aids.

Plain English: every page is on the site map with an easy read summary and previous / next links; the API,
feed and sitemap are built and readable; every reuse route says how to do it; acronyms have meanings; and no
new page shows an email address.
"""
import json
import re
import subprocess
import sys
import tempfile
import unittest
import xml.dom.minidom
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import build_dq_portal as B  # noqa: E402

REUSE = yaml.safe_load((ROOT / "knowledge" / "reuse.yaml").read_text(encoding="utf-8"))
ACR = yaml.safe_load((ROOT / "knowledge" / "acronyms.yaml").read_text(encoding="utf-8"))["acronyms"]
EASY = yaml.safe_load((ROOT / "knowledge" / "easy-read.yaml").read_text(encoding="utf-8"))["pages"]
SRC = ROOT / "portal" / "src"


class Navigation(unittest.TestCase):
    def test_every_page_has_a_group_level_icon_and_summary(self):
        for stem, label, desc in B.PAGES:
            self.assertTrue((SRC / "pages" / f"{stem}.html").exists(), stem)
            self.assertIn(stem, B.LEVEL, stem)
            self.assertIn(stem, B.PAGE_ICON, stem)
            self.assertIn(stem, EASY, f"{stem} has no easy read summary")
            self.assertIn(f'id="i-{B.PAGE_ICON[stem]}"', (SRC / "icons.svg").read_text(encoding="utf-8"), stem)

    def test_prev_next_follows_menu_order(self):
        order = [s for s, _, _ in B.PAGES]
        first, last = B.prev_next(order[0]), B.prev_next(order[-1])
        self.assertNotIn('rel="prev"', first)
        self.assertIn(f'href="{order[1]}.html" rel="next"', first)
        self.assertNotIn('rel="next"', last)
        mid = B.prev_next(order[5])
        self.assertIn(f'href="{order[4]}.html" rel="prev"', mid)
        self.assertIn(f'href="{order[6]}.html" rel="next"', mid)
        self.assertIn('aria-current="page"', mid)

    def test_site_map_covers_every_page_once(self):
        stems = [p["stem"] for g in B.site_map() for p in g["pages"]]
        self.assertEqual(sorted(stems), sorted(s for s, _, _ in B.PAGES))
        self.assertEqual(len(stems), len(set(stems)))

    def test_every_group_has_a_colour_key(self):
        for g, _ in B.GROUPS:
            self.assertIn(g, B.GROUP_KEY)
            self.assertIn(f'[data-group="{B.GROUP_KEY[g]}"]', (SRC / "shell.html").read_text(encoding="utf-8"))


class Knowledge(unittest.TestCase):
    def test_reuse_routes_are_complete(self):
        for r in REUSE["routes"]:
            for k in ("id", "name", "for", "effort", "upkeep", "control", "it", "status", "summary", "steps", "icon"):
                self.assertTrue(r.get(k), f"route {r.get('id')} missing {k}")
            self.assertGreaterEqual(len(r["steps"]), 2, r["id"])
        self.assertTrue(REUSE["ai"] and REUSE["guardrails"] and REUSE["customise"])

    def test_mcp_command_in_reuse_matches_the_server(self):
        cmd = next(a["command"] for a in REUSE["ai"] if a["id"] == "mcp")
        self.assertEqual(cmd, "python -m dqkit.mcp_server")
        self.assertTrue((ROOT / "dqkit" / "mcp_server.py").exists())
        self.assertGreaterEqual(len(B.mcp_tools()), 10)

    def test_acronyms_are_short_and_uppercase(self):
        for k, v in ACR.items():
            self.assertRegex(k, r"^[A-Z]{2,6}s?$")
            self.assertTrue(10 <= len(v) <= 120, k)


class BuiltOutput(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.out = Path(cls.tmp.name) / "dist"
        subprocess.run([sys.executable, str(ROOT / "scripts" / "build_dq_portal.py"), "--out", str(cls.out)],
                       check=True, capture_output=True, cwd=ROOT)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_api_index_lists_files_that_exist(self):
        ix = json.loads((self.out / "api" / "index.json").read_text(encoding="utf-8"))
        self.assertEqual(ix["version"], B.VERSION)
        for e in ix["endpoints"]:
            self.assertTrue((self.out / e["path"]).exists(), e["path"])
        for k in ix["knowledge"]:
            self.assertTrue((self.out / k["path"]).exists(), k["path"])
        passages = json.loads((self.out / "api" / "passages.json").read_text(encoding="utf-8"))
        self.assertGreater(len(passages), 500)
        self.assertTrue((self.out / "ask-index.js").read_text(encoding="utf-8").startswith("window.DQP_PASSAGES="))

    def test_feed_and_sitemap_are_valid(self):
        feed = xml.dom.minidom.parse(str(self.out / "feed.xml"))
        self.assertGreater(len(feed.getElementsByTagName("entry")), 0)
        sm = (self.out / "sitemap.xml").read_text(encoding="utf-8")
        xml.dom.minidom.parseString(sm)
        for stem, _, _ in B.PAGES:
            self.assertIn(f"/{stem}.html</loc>", sm)

    def test_every_page_has_share_aids_and_page_navigation(self):
        for stem, _, _ in B.PAGES:
            h = (self.out / f"{stem}.html").read_text(encoding="utf-8")
            self.assertIn('class="dqp-pn"', h, stem)
            self.assertIn('id="dqp-top"', h, stem)
            self.assertIn("Share this page", h, stem)
            self.assertIn('id="dqp-acr"', h, stem)
            self.assertRegex(h, r'<div class="wrap" data-group="[a-z]+"', stem)

    def test_no_email_addresses_on_new_pages(self):
        for stem in ("sitemap", "ask", "reuse"):
            h = (self.out / f"{stem}.html").read_text(encoding="utf-8")
            self.assertIsNone(re.search(r"[\w.+-]+@[\w-]+\.[\w.]+", re.sub(r"@\d", "", h)), stem)


if __name__ == "__main__":
    unittest.main()
