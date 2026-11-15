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



def release_workflow_problems(wf):
    """What stops release.yml working with immutable releases (D-REL-05)."""
    problems = []
    if "--json isDraft" not in wf:
        problems.append("does not check whether an existing release is still a draft")
    if "--draft=false" not in wf:
        problems.append("does not publish the draft after attaching the files")
    if "immutable" not in wf.lower() or "exit 1" not in wf:
        problems.append("does not stop with a reason when the release is already published")
    return problems

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

    def test_assistant_escapes_every_value_in_its_explanations(self):
        # Alert 125: words typed by the user reach innerHTML through add(); every ${...} in an
        # explanation (the `<b>... HTML strings passed to push) must go through esc().
        src = read("portal", "src", "pages", "assistant.html")
        found = 0
        for m in re.finditer(r"`(<b>[^`]*)`\)", src):
            found += 1
            for expr in re.findall(r"\$\{([^}]*)\}", m.group(1)):
                self.assertTrue(expr.startswith("esc(") or ".map(esc)" in expr, f"unescaped ${{{expr}}} in explanation: {m.group(1)[:60]}")
        self.assertGreater(found, 3)

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
                self.assertIn(r"</script\b[^>]*>", line, f"{path}: closing tag must allow anything up to >")
                self.assertIn("re.I", line, f"{path}: tag match must ignore case")

    def test_pattern_behaviour(self):
        pat = re.compile(r"<script\b.*?</script\b[^>]*>|<style\b.*?</style\b[^>]*>", re.S | re.I)
        self.assertEqual(pat.sub("", "a<SCRIPT>x</script >b<style>y</STYLE>c"), "abc")
        # D-found-in-review: browsers also close on </script\t\n bar>, which \s*> missed.
        self.assertEqual(pat.sub("", "a<script>x</script\t\n bar>b"), "ab")


class Workflows(unittest.TestCase):
    def test_ci_has_least_privilege_permissions(self):
        # Alert 135: the tests workflow had no permissions block, so it ran with the default token scope.
        self.assertRegex(read(".github", "workflows", "ci.yml"), r"(?m)^permissions:\s*\n\s+contents:\s*read")

    def test_ci_runs_the_fuzzer_with_dev_mode(self):
        # OpenSSF dynamic_analysis: the parsers are fuzzed on every change, with warnings as errors.
        ci = read(".github", "workflows", "ci.yml")
        self.assertIn("python -X dev -W error -m unittest tests.test_fuzz", ci)

    def test_release_workflow_accepts_a_release_made_on_the_website(self):
        # D-REL-01: a release drafted on GitHub creates the tag first, and `gh release create`
        # then failed because the release already existed. The workflow now attaches to it.
        wf = read(".github", "workflows", "release.yml")
        self.assertIn('gh release view "${GITHUB_REF_NAME}"', wf)
        self.assertIn("gh release upload", wf)

    def test_release_workflow_respects_immutable_releases(self):
        # Defect D-REL-05: immutable releases are on, so a release published on the website can't take files
        # afterwards; the D-REL-01 path uploaded to it anyway and would fail half-way. Files may only go to a draft,
        # which is then published; a published release stops the run with a reason.
        self.assertEqual(release_workflow_problems(read(".github", "workflows", "release.yml")), [])

    def test_release_workflow_check_catches_upload_to_a_published_release(self):
        # Negative test for D-REL-05: the 2.16.0 workflow, which uploaded to any existing release.
        old = ('if gh release view "${GITHUB_REF_NAME}" > /dev/null 2>&1; then\n'
               '  gh release upload "${GITHUB_REF_NAME}" $FILES --clobber\n'
               '  gh release edit "${GITHUB_REF_NAME}" --title "${GITHUB_REF_NAME}" --notes-file notes.md\n')
        self.assertEqual(len(release_workflow_problems(old)), 3)

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
