"""Owner rules and DPG gaps closed in 2.16.1, each with a negative test that feeds the check the broken shape.

Decision D-LIC-01 (15 November 2026): the owner states the repository holds no Open Government Licence content.
Documentation and content are CC BY 4.0 and code stays MIT. Third-party data keeps its source's licence.

Defect D-PRIV-01: the privacy notice said the data controller "will be named here".
Defect D-NAME-01: the README, the Rosetta and two knowledge files used the former directorate name and named a team
the owner does not want named.
Defect D-FONT-01: the charter said "Fonts are the only external request", but the portal loads no web fonts.
Defect D-DOC-01: the README gave status v2.0.0, 131 tests, 8 dimensions, 43 issue types and 28 other frameworks.
Defect D-REL-04: D-REL-02 was fixed in PR #50 with tests, but was not named in CHANGELOG.md or docs/BUILD-LOG.md.
"""
import csv
import re
import subprocess
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
TESTS = ROOT / "tests"


def read(rel):
    return (ROOT / rel).read_text(encoding="utf-8")


def tracked():
    return subprocess.run(["git", "ls-files"], cwd=ROOT, capture_output=True, text=True, check=True).stdout.split()


TEXT = (".py", ".md", ".yaml", ".yml", ".toml", ".html", ".json", ".jsonld", ".ttl", ".txt", ".cff", ".csv", ".js", ".css")

# ---------------------------------------------------------------- licence (D-LIC-01)

OGL = re.compile(r"\bOGL\b|Open Government Licen[cs]e|open-government-licence|Crown copyright", re.I)
# Files that describe this project's own content. History (CHANGELOG, build log, decision log) records past states
# and is not scanned; generated outputs are scanned through the sources they are built from.
LICENCE_SCOPE = re.compile(r"^(README\.md|CHARTER\.md|CONTRIBUTING\.md|SECURITY\.md|CODE_OF_CONDUCT\.md|CONTRIBUTORS\.md|"
                           r"CITATION\.cff|\.zenodo\.json|pyproject\.toml|LICENSE|"
                           r"docs/(?!BUILD-LOG\.md|DECISIONS\.md|bundle/)[^/]+\.md|knowledge/.+|portal/src/.+|scripts/.+\.py)$")
# Lines that name the OGL because they describe someone else's data or project, never this project's content.
ALLOW = [
    ("knowledge/ecosystem.yaml", "licence: Code MIT; content Open Government Licence v3.0",
     "the DAM capability playbooks, a separate repository with its own licence"),
    ("knowledge/ecosystem.yaml", "licence: Code MIT; content and data Open Government Licence v3.0",
     "the GitHub Repos Asset Catalogue, a separate repository with its own licence"),
    ("knowledge/code-evidence.yaml", "licence: Open Government Licence v3.0", "the source licence of imported third-party data"),
    ("scripts/import_code_evidence.py", '"licence": "Open Government Licence v3.0"', "writes that source licence"),
    ("knowledge/professions.yaml", "Open Government Licence.", "a third-party framework's own licence"),
    ("portal/src/pages/weaver.html", "open-government-licence", "real public catalogue records used as examples"),
    ("portal/src/pages/weaver.html", "OGL-UK-3.0", "real public catalogue records used as examples"),
    ("scripts/parity_check.py", "OGL-UK-3.0", "test fixtures of public catalogue records"),
    ("scripts/parity_check.py", "open-government-licence", "test fixtures of public catalogue records"),
    ("portal/src/pages/weaver.html", '"uk-ogl"', "a real CKAN record's licence id"),
    ("scripts/parity_check.py", '"uk-ogl"', "a CKAN record's licence id in a test fixture"),
]


def licence_problems(files):
    """files: (path, text) pairs. Returns 'path:line' for every OGL mention in scope that is not allow-listed."""
    out = []
    for path, text in files:
        if not LICENCE_SCOPE.match(path):
            continue
        for n, line in enumerate(text.splitlines(), 1):
            if OGL.search(line) and not any(path == p and needle in line for p, needle, _ in ALLOW):
                out.append(f"{path}:{n}")
    return out


CC_BY = "https://creativecommons.org/licenses/by/4.0/"


def content_licence_problems(text):
    out = []
    if "CC BY 4.0" not in text or CC_BY not in text:
        out.append("does not name and link CC BY 4.0")
    if "Creative Commons Attribution 4.0 International" not in text:
        out.append("does not give the licence's full name")
    if "MIT" not in text:
        out.append("does not say code stays MIT")
    if "Third-party data keeps its source's licence" not in text or "assessments/ndl/" not in text:
        out.append("no third-party data note naming the assessments folder")
    return out


class Licence(unittest.TestCase):
    def test_no_ogl_wording_for_this_projects_content(self):
        files = [(f, (ROOT / f).read_bytes().decode("utf-8", errors="replace")) for f in tracked()
                 if f.endswith(TEXT) or f in ("LICENSE",)]
        self.assertEqual(licence_problems(files), [])

    def test_allow_list_entries_still_exist(self):
        for path, needle, why in ALLOW:
            self.assertIn(needle, read(path), f"stale allow-list entry ({why})")

    def test_content_licence_file(self):
        self.assertEqual(content_licence_problems(read("docs/CONTENT-LICENCE.md")), [])

    def test_readme_and_footer_name_cc_by(self):
        self.assertIn(CC_BY, read("README.md"))
        self.assertIn(CC_BY, read("scripts/build_dq_portal.py"))

    def test_citation_files_declare_both_licences(self):
        cff = yaml.safe_load(read("CITATION.cff"))
        self.assertEqual(cff["license"], ["MIT", "CC-BY-4.0"])


class LicenceNegative(unittest.TestCase):
    def test_ogl_content_line_is_caught(self):
        self.assertTrue(licence_problems([("README.md", "Code MIT, content OGL v3.0.\n")]))
        self.assertTrue(licence_problems([("portal/src/pages/x.html", "<li>Open Government Licence v3.0</li>\n")]))

    def test_allow_list_is_per_file(self):
        line = "    licence: Code MIT; content Open Government Licence v3.0\n"
        self.assertFalse(licence_problems([("knowledge/ecosystem.yaml", line)]))
        self.assertTrue(licence_problems([("knowledge/reuse.yaml", line)]))

    def test_old_content_licence_file_fails(self):
        old = ("Documentation and data are available under the [Open Government Licence v3.0](https://www.nationalarchives"
               ".gov.uk/doc/open-government-licence/version/3/), except where otherwise stated. Code is MIT.")
        self.assertTrue(content_licence_problems(old))


# ---------------------------------------------------------------- ownership (DPG G3)

EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}")


def holder(cff):
    a = cff["authors"][0]
    return a.get("name") or f"{a['given-names']} {a['family-names']}"


def ownership_problems(readme, licence, name):
    out = []
    m = re.search(r"^## Ownership\n(.*?)(?=^## |\Z)", readme, re.M | re.S)
    if not m:
        return ["README has no Ownership section"]
    sec = m.group(1)
    for need in (name, "cyberdudeuk", "personal project", "No public body owns or endorses it"):
        if need not in sec:
            out.append(f"Ownership section does not say {need!r}")
    first = next((ln for ln in licence.splitlines() if ln.startswith("Copyright")), "")
    if name not in first:
        out.append(f"LICENSE holder line {first!r} does not name {name}")
    return out


class Ownership(unittest.TestCase):
    def test_readme_and_licence_name_the_citation_holder(self):
        name = holder(yaml.safe_load(read("CITATION.cff")))
        self.assertEqual(ownership_problems(read("README.md"), read("LICENSE"), name), [])

    def test_no_email_addresses(self):
        for f in ("README.md", "LICENSE", "CITATION.cff", ".zenodo.json", "docs/CONTENT-LICENCE.md",
                  "docs/THEORY-OF-CHANGE.md", "portal/src/pages/accessibility.html"):
            self.assertIsNone(EMAIL.search(read(f)), f)


class OwnershipNegative(unittest.TestCase):
    def test_missing_section_or_old_holder_is_caught(self):
        self.assertTrue(ownership_problems("# X\n", "Copyright (c) 2026 A B\n", "A B"))
        ok = "## Ownership\n- A B owns it; cyberdudeuk is theirs; a personal project. No public body owns or endorses it.\n"
        self.assertFalse(ownership_problems(ok, "Copyright (c) 2026 A B and contributors\n", "A B"))
        self.assertTrue(ownership_problems(ok, "Copyright (c) 2026 cyberdudeuk and contributors\n", "A B"))

    def test_email_pattern_catches_an_address(self):
        self.assertIsNotNone(EMAIL.search("write to someone@example.org"))


# ---------------------------------------------------------------- privacy notice (D-PRIV-01, DPG G4)

def privacy_problems(page, name, screening):
    m = re.search(r'<section id="privacy".*?</section>', page, re.S)
    if not m:
        return ["no privacy section"]
    sec = m.group(0)
    out = []
    if "will be named here" in sec:
        out.append("controller still a placeholder")
    if not re.search(r"Data controller:</b>\s*" + re.escape(name), sec):
        out.append(f"controller is not {name}")
    if 'href="build.html#contact"' not in sec or "issues/new/choose" not in sec:
        out.append("contact route is not the contact form and GitHub issue form")
    if EMAIL.search(sec):
        out.append("an email address is shown")
    if "a full DPIA is not needed for this repository" in screening and "a full DPIA is not needed" not in sec:
        out.append("DPIA status does not match the screening")
    if "none has been completed" not in sec:
        out.append("does not say that no DPIA has been completed")
    return out


class Privacy(unittest.TestCase):
    def test_controller_named_and_dpia_status_from_screening(self):
        self.assertEqual(privacy_problems(read("portal/src/pages/accessibility.html"),
                                          holder(yaml.safe_load(read("CITATION.cff"))),
                                          read("docs/EQUALITY-AND-DATA-PROTECTION-SCREENING.md")), [])


class PrivacyNegative(unittest.TestCase):
    def test_placeholder_notice_fails(self):
        old = ('<section id="privacy"><p><b>Status:</b> the organisation that runs it will be named here as the data '
               'controller, and a data protection impact assessment will be completed.</p></section>')
        self.assertTrue(privacy_problems(old, "A B", "a full DPIA is not needed for this repository"))


# ---------------------------------------------------------------- SDG statement (DPG G5)

def sdg_problems(text):
    m = re.search(r"^## Sustainable Development Goals\n(.*?)(?=^## |\Z)", text, re.M | re.S)
    if not m:
        return ["no Sustainable Development Goals section"]
    sec, out = m.group(1), []
    for need in ("17.18", "16.6", "not_unknown", "group_disparity", "un-nqaf", "imf-dqaf", "ISO 8000", "owner", "DQV",
                 "developing countries", "UK-first", "not to its official indicators"):
        if need not in sec:
            out.append(f"SDG section does not mention {need!r}")
    return out


class Sdg(unittest.TestCase):
    def test_sdg_section(self):
        self.assertEqual(sdg_problems(read("docs/THEORY-OF-CHANGE.md")), [])

    def test_sdg_features_exist(self):
        rules_src = read("dqkit/rules.py")
        for check in ("not_unknown", "group_disparity"):
            self.assertIn(check, rules_src)
        for pack in ("un-nqaf", "imf-dqaf", "iso-8000-8"):
            self.assertTrue((ROOT / "packs" / f"{pack}.yaml").exists(), pack)
        self.assertTrue((ROOT / "dqkit" / "dqv.py").exists())


class SdgNegative(unittest.TestCase):
    def test_claim_without_limits_fails(self):
        self.assertTrue(sdg_problems("## Sustainable Development Goals\nWe support 17.18 and 16.6.\n"))
        self.assertTrue(sdg_problems("# Theory of change\n"))


# ---------------------------------------------------------------- owner vocabulary (D-NAME-01)

BANNED = re.compile(r"\bOCDO\b|Office of the Chief Data Officer|Data Management Team", re.I)


def naming_problems(files):
    return [f"{p}:{n}" for p, text in files for n, line in enumerate(text.splitlines(), 1) if BANNED.search(line)]


class Naming(unittest.TestCase):
    def test_no_former_directorate_name_or_team_name(self):
        files = [(f, (ROOT / f).read_bytes().decode("utf-8", errors="replace")) for f in tracked()
                 if f.endswith(TEXT) and f != "tests/test_owner_rules.py"]
        self.assertEqual(naming_problems(files), [])


class NamingNegative(unittest.TestCase):
    def test_each_banned_form_is_caught(self):
        for line in ("GDS/OCDO DAM portal", "the Office of the Chief Data Officer", "the GDS Data Management Team's survey"):
            self.assertTrue(naming_problems([("x.md", line)]), line)
        self.assertFalse(naming_problems([("x.md", "the Government Data Directorate; a chief data officer")]))


# ---------------------------------------------------------------- fonts (D-FONT-01)

WEB_FONT = re.compile(r"@font-face|fonts\.googleapis|fonts\.gstatic|use\.typekit|\.woff2?\b", re.I)


def font_problems(portal_files, claims):
    out = [p for p, text in portal_files if WEB_FONT.search(text)]
    out += [p for p, text in claims if "Fonts are the only external request" in text]
    return out


class Fonts(unittest.TestCase):
    def test_no_web_fonts_and_no_claim_that_fonts_are_requested(self):
        portal = [(str(f), f.read_text(encoding="utf-8")) for f in (ROOT / "portal" / "src").rglob("*")
                  if f.suffix in (".html", ".css", ".js")]
        portal.append(("scripts/build_dq_portal.py", read("scripts/build_dq_portal.py")))
        claims = [(f, read(f)) for f in ("CHARTER.md", "knowledge/build.yaml", "portal/src/pages/accessibility.html")]
        self.assertEqual(font_problems(portal, claims), [])
        self.assertIn("no web fonts", read("portal/src/pages/accessibility.html"))
        self.assertIn("no web fonts", read("CHARTER.md"))


class FontsNegative(unittest.TestCase):
    def test_web_font_or_old_claim_is_caught(self):
        self.assertTrue(font_problems([("a.css", "@font-face{font-family:X;src:url(x.woff2)}")], []))
        self.assertTrue(font_problems([], [("CHARTER.md", "No trackers. Fonts are the only external request.")]))


# ---------------------------------------------------------------- README facts (D-DOC-01)

def count_tests():
    """The number `python -m unittest discover -s tests` reports with every test dependency installed. The fuzz tests
    are only defined when Hypothesis is installed (CI installs it after the main run), so they are added back here."""
    n = unittest.TestLoader().discover(str(TESTS), top_level_dir=str(TESTS)).countTestCases()
    try:
        import hypothesis  # noqa: F401
    except ImportError:
        n += len(re.findall(r"^\s+def test_", (TESTS / "test_fuzz.py").read_text(encoding="utf-8"), re.M))
    return n


def readme_fact_problems(readme, version, tests, dims, issue_types, frameworks):
    out = []
    if f"**Status:** prototype (v{version})" not in readme:
        out.append("status line does not give the current version")
    m = re.search(r"\((\d+) tests at the time of writing\)", readme)
    if not m or int(m.group(1)) != tests:
        out.append(f"test count {m.group(1) if m else None} is not {tests}")
    if f"{dims} quality dimensions and {issue_types} cross-government issue types" not in readme:
        out.append("vocabulary counts are stale")
    if f"maps {frameworks}\npublished frameworks" not in readme:
        out.append("framework count is stale")
    if "https://www.bestpractices.dev/projects/16716/badge" not in readme or "(https://www.bestpractices.dev/projects/16716)" not in readme:
        out.append("no OpenSSF Best Practices badge")
    return out


def rows(rel):
    with open(ROOT / rel, encoding="utf-8", newline="") as fh:
        return len(list(csv.DictReader(fh)))


class ReadmeFacts(unittest.TestCase):
    def test_readme_facts_match_the_repository(self):
        rel = yaml.safe_load(read("knowledge/releases.yaml"))["releases"]
        fw = yaml.safe_load(read("knowledge/frameworks.yaml"))["frameworks"]
        self.assertEqual(readme_fact_problems(read("README.md"), rel[0]["version"], count_tests(),
                                              rows("vocab/dimensions.csv"), rows("vocab/issue-types.csv"), len(fw)), [])


class ReadmeFactsNegative(unittest.TestCase):
    def test_old_readme_fails(self):
        old = ("**Status:** prototype (v2.0.0).\n(131 tests at the time of writing)\n"
               "8 quality dimensions and 43 cross-government issue types\nmaps 28 other\npublished frameworks\n")
        self.assertEqual(len(readme_fact_problems(old, "2.16.1", 300, 11, 45, 30)), 5)


# ---------------------------------------------------------------- defects are named where the repo records them (D-REL-04)

def unrecorded_defects(test_texts, changelog, build_log):
    ids = sorted({i for t in test_texts for i in re.findall(r"\bDefect (D-[A-Z]+-\d+)", t)})
    return [i for i in ids if i not in changelog or i not in build_log]


class DefectsRecorded(unittest.TestCase):
    def test_every_defect_named_in_a_test_is_in_changelog_and_build_log(self):
        texts = [f.read_text(encoding="utf-8") for f in TESTS.glob("test_*.py")]
        self.assertEqual(unrecorded_defects(texts, read("CHANGELOG.md"), read("docs/BUILD-LOG.md")), [])

    def test_d_rel_02_is_under_2_16_0(self):
        cl = read("CHANGELOG.md")
        sec = re.search(r"^## 2\.16\.0 .*?(?=^## )", cl, re.M | re.S).group(0)
        self.assertRegex(sec, r"### Fixed\n(- .*\n)*- .*D-REL-02")


class DefectsRecordedNegative(unittest.TestCase):
    def test_unrecorded_defect_is_caught(self):
        self.assertEqual(unrecorded_defects(['"""Defect D-REL-02: merge kept both sides."""'], "## 2.16.0\n", "log"),
                         ["D-REL-02"])


if __name__ == "__main__":
    unittest.main()
