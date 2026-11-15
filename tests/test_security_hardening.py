"""Regression tests for the code-scanning fixes of 15 November 2026 (OpenSSF Best Practices "static_analysis_fixed").

Each test names the CodeQL alert it guards and fails if that defect is put back.
Run: python -m unittest tests.test_security_hardening
"""
import ast
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PAGES = ROOT / "portal" / "src" / "pages"


def read(*parts):
    return ROOT.joinpath(*parts).read_text(encoding="utf-8")


class HostChecks(unittest.TestCase):
    def test_no_suffix_host_check(self):
        # Alert 144: hostname.endsWith("github.io") also matches hosts such as evilgithub.io.
        for page in PAGES.glob("*.html"):
            self.assertNotRegex(page.read_text(encoding="utf-8"), r'hostname\.endsWith\(\s*["\']github\.io',
                                f"{page.name}: compare the whole host name, not a suffix")


class Escaping(unittest.TestCase):
    def test_guidance_escape_covers_quotes(self):
        # Alert 103: esc() output goes inside href="...", so it must escape double and single quotes.
        m = re.search(r"const esc=s=>String\(s\)\.replace\(/\[([^\]]+)\]/g", read("portal", "src", "pages", "guidance.html"))
        self.assertIsNotNone(m, "guidance.html esc() not found")
        for ch in "&<>\"'":
            self.assertIn(ch, m.group(1), f"esc() does not escape {ch!r}")

    def test_assistant_escapes_file_name(self):
        # Alert 125: a file name chosen by the user was written into innerHTML unescaped.
        src = read("portal", "src", "pages", "assistant.html")
        self.assertNotIn("drafted from ${fileName}", src)
        self.assertIn("drafted from ${esc(fileName)}", src)

    def test_tab_panels_looked_up_by_id(self):
        # Alerts 63, 64: panel ids from aria-controls went through the selector helper $(); use getElementById.
        for name in ("media.html", "library.html"):
            src = read("portal", "src", "pages", name)
            self.assertNotIn('$(x.getAttribute("aria-controls"))', src, name)


class HtmlStripping(unittest.TestCase):
    def test_script_and_style_stripping_is_robust(self):
        # Alerts 112, 113, 114: the pattern missed upper-case tags and closing tags with spaces (</script >).
        for path in ("scripts/build_dq_portal.py", "scripts/export_strings.py"):
            src = read(path)
            for m in re.finditer(r're\.sub\(r"<script\\b[^"]*"', src):
                line = src[m.start():src.index("\n", m.start())]
                self.assertIn(r"</script\s*>", line, f"{path}: closing tag must allow spaces")
                self.assertIn("re.I", line, f"{path}: tag match must ignore case")

    def test_pattern_behaviour(self):
        pat = re.compile(r"<script\b.*?</script\s*>|<style\b.*?</style\s*>", re.S | re.I)
        self.assertEqual(pat.sub("", "a<SCRIPT>x</script >b<style>y</STYLE>c"), "abc")


class Workflows(unittest.TestCase):
    def test_ci_has_least_privilege_permissions(self):
        # Alert 135: the tests workflow had no permissions block, so it ran with the default token scope.
        self.assertRegex(read(".github", "workflows", "ci.yml"), r"(?m)^permissions:\s*\n\s+contents:\s*read")

    def test_ci_runs_the_linter(self):
        # OpenSSF "warnings": CI must fail on linter warnings.
        self.assertIn("ruff check .", read(".github", "workflows", "ci.yml"))


class Files(unittest.TestCase):
    def test_files_are_closed(self):
        # Alerts 79 to 85: open() outside a with-block leaves the file open until garbage collection.
        bad = []
        for folder in ("dqkit", "scripts"):
            for path in (ROOT / folder).rglob("*.py"):
                tree = ast.parse(path.read_text(encoding="utf-8"))
                in_with = {id(item.context_expr) for node in ast.walk(tree) if isinstance(node, (ast.With, ast.AsyncWith))
                           for item in node.items}
                for node in ast.walk(tree):
                    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "open" and id(node) not in in_with:
                        bad.append(f"{path.relative_to(ROOT)}:{node.lineno}")
        self.assertEqual(bad, [], "use 'with open(...) as f:'")

    def test_id_hash_marked_not_for_security(self):
        # Alert 136: SHA-1 mints persistent ids (changing it would change every id); it must say it is not for security.
        self.assertIn("usedforsecurity=False", read("scripts", "build_models.py"))


if __name__ == "__main__":
    unittest.main()
