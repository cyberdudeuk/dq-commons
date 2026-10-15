"""The data quality portal builds from the pipeline results, with no placeholders left."""
import json
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PAGES = ["index", "pipeline", "check", "ndl-assurance", "baseline", "guidance", "tooling", "share"]


class PortalBuild(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.out, cls.art = Path(cls.tmp.name) / "dist", Path(cls.tmp.name) / "art"
        subprocess.run([sys.executable, str(ROOT / "scripts" / "build_dq_portal.py"), "--out", str(cls.out),
                        "--artifact", str(cls.art)], check=True, capture_output=True, text=True)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_every_page_built_without_placeholders(self):
        for p in PAGES:
            text = (self.out / f"{p}.html").read_text(encoding="utf-8")
            self.assertTrue(text.startswith("<!doctype html>"), p)
            self.assertIsNone(re.search(r"__(DATA|PORTFOLIO|HISTORY|VOCAB|EXAMPLES|ENGINE|BUILD|BASE_CSS|DOWNLOADS|NDL_DATA)__", text), p)
            self.assertIn('class="dqp-bar"', text, p)
            self.assertIn(f'href="{p}.html" aria-current="page"', text, p)

    def test_artifact_home_has_no_wrapper_and_links_to_repo(self):
        home = (self.art / "index.html").read_text(encoding="utf-8")
        self.assertFalse(home.lstrip().lower().startswith("<!doctype"))
        self.assertTrue(home.startswith("<title>"))
        pipe = (self.art / "pipeline.html").read_text(encoding="utf-8")
        self.assertIn("/blob/main/assessments/portfolio/", pipe)

    def test_embedded_results_match_the_pipeline(self):
        port = json.loads((ROOT / "assessments" / "portfolio" / "portfolio.json").read_text(encoding="utf-8"))
        text = (self.out / "pipeline.html").read_text(encoding="utf-8")
        m = re.search(r"const P = (\{.*?\}), H = ", text, re.S)
        self.assertIsNotNone(m)
        self.assertEqual(json.loads(m.group(1).replace("<\\/", "</")), port)

    def test_downloads_are_copied(self):
        for f in ("portfolio.json", "run-summary.md", "cda-return.csv", "catalogue.dqv.jsonld"):
            self.assertTrue((self.out / "downloads" / f).exists(), f)
        self.assertTrue(any((self.out / "downloads" / "assets").glob("*.DQAP.xlsx")))


if __name__ == "__main__":
    unittest.main()
