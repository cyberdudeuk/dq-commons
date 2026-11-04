"""The data quality portal builds from the pipeline results, with no placeholders left."""
import json
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from build_dq_portal import PAGES as _P  # noqa: E402
PAGES = [p[0] for p in _P]


class PortalBuild(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.out = Path(cls.tmp.name) / "dist"
        subprocess.run([sys.executable, str(ROOT / "scripts" / "build_dq_portal.py"), "--out", str(cls.out)],
                       check=True, capture_output=True, text=True)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_every_page_built_without_placeholders(self):
        for p in PAGES:
            text = (self.out / f"{p}.html").read_text(encoding="utf-8")
            self.assertTrue(text.startswith("<!doctype html>"), p)
            self.assertIsNone(re.search(r"__(DATA|PORTFOLIO|HISTORY|VOCAB|EXAMPLES|ENGINE|BUILD|BASE_CSS|DOWNLOADS|NDL_DATA|K_[A-Z]+)__", text), p)
            self.assertIn('class="dqp-bar"', text, p)
            self.assertRegex(text, rf'href="{re.escape(p)}\.html" data-t="[^"]+" aria-current="page"', p)
            self.assertIn('<symbol id="i-home"', text, p)  # the icon sprite is on every page
            self.assertIn('class="dqp-colo"', text, p)  # the colophon is on every page
        self.assertIn('class="dqp-prov"', (self.out / "commercial.html").read_text(encoding="utf-8"))  # provenance line

    def test_no_claude_ai_dependency(self):
        """D-GH-02: the portal must work for people without a claude.ai licence."""
        for p in PAGES:
            text = (self.out / f"{p}.html").read_text(encoding="utf-8")
            self.assertNotIn("claude.use(", text, p)
            self.assertNotIn("window.claude", text, p)

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


class Styles(unittest.TestCase):
    def test_hidden_attribute_is_enforced(self):
        # Page styles such as section{display:flex} override [hidden]; editor-only panels rely on it.
        for f in ("base.css", "shell.html"):
            self.assertIn("[hidden]{display:none!important}", (ROOT / "portal" / "src" / f).read_text(encoding="utf-8"), f)


if __name__ == "__main__":
    unittest.main()
