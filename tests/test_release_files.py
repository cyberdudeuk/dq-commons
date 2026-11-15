"""Release files must declare one version, once, and carry no merge leftovers.

Defect D-REL-02 (15 November 2026): merging main into the 2.16.0 branch kept both sides of every conflict, so
pyproject.toml declared `version` twice (a TOML error that stopped Ruff and failed CI on main), dqkit/__init__.py set
__version__ twice, and the README, build log and bundle described two "latest" releases. The existing check in
test_playbook.py only asked whether the right line was present, so a duplicate passed. These checks parse the files
and count, and each has a negative test that feeds it the broken shape.
"""
import re
import subprocess
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent

try:
    import tomllib
except ModuleNotFoundError:  # Python 3.10
    tomllib = None


def version_problems(pyproject_text, init_text):
    out = []
    if tomllib is not None:
        try:
            data = tomllib.loads(pyproject_text)
        except tomllib.TOMLDecodeError as e:
            return [f"pyproject.toml does not parse: {e}"]
        v = data.get("project", {}).get("version")
    else:
        found = re.findall(r'^version\s*=\s*"([^"]+)"', pyproject_text, re.M)
        if len(found) != 1:
            return [f"pyproject.toml declares version {len(found)} times"]
        v = found[0]
    inits = re.findall(r'^__version__\s*=\s*"([^"]+)"', init_text, re.M)
    if len(inits) != 1:
        out.append(f"dqkit/__init__.py sets __version__ {len(inits)} times")
    elif inits[0] != v:
        out.append(f"__version__ {inits[0]} differs from pyproject {v}")
    return out


MARKER = re.compile(r"^(<{7}|={7}|>{7})( |$)", re.M)


def marker_problems(files):
    return [str(f) for f, text in files if MARKER.search(text)]


def release_problems(releases, changelog_text):
    out = []
    vs = [r["version"] for r in releases]
    if len(vs) != len(set(vs)):
        out.append("releases.yaml lists a version twice")
    key = lambda v: tuple(int(x) for x in v.split("."))
    if vs != sorted(vs, key=key, reverse=True):
        out.append("releases.yaml is not newest first")
    heads = re.findall(r"^## (\d+\.\d+\.\d+)", changelog_text, re.M)
    if len(heads) != len(set(heads)):
        out.append("CHANGELOG.md has a version heading twice")
    if heads and vs and heads[0] != vs[0]:
        out.append(f"newest CHANGELOG entry {heads[0]} differs from newest release {vs[0]}")
    return out


def readme_latest_problems(readme_text):
    n = len(re.findall(r"The latest release \(", readme_text))
    return [] if n == 1 else [f"README names a latest release {n} times"]


class ReleaseFiles(unittest.TestCase):
    def test_one_version_declared_once(self):
        self.assertEqual(version_problems((ROOT / "pyproject.toml").read_text(encoding="utf-8"),
                                          (ROOT / "dqkit" / "__init__.py").read_text(encoding="utf-8")), [])

    def test_no_merge_markers_in_tracked_text(self):
        files = subprocess.run(["git", "ls-files"], cwd=ROOT, capture_output=True, text=True, check=True).stdout.split()
        texts = []
        for f in files:
            if f.endswith((".py", ".md", ".yaml", ".yml", ".toml", ".html", ".json", ".txt", ".cff")):
                try:
                    texts.append((f, (ROOT / f).read_text(encoding="utf-8")))
                except (UnicodeDecodeError, FileNotFoundError):
                    pass
        self.assertEqual(marker_problems(texts), [])

    def test_release_lists_agree(self):
        rel = yaml.safe_load((ROOT / "knowledge" / "releases.yaml").read_text(encoding="utf-8"))["releases"]
        self.assertEqual(release_problems(rel, (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")), [])

    def test_readme_names_one_latest_release(self):
        self.assertEqual(readme_latest_problems((ROOT / "README.md").read_text(encoding="utf-8")), [])


class NegativeTests(unittest.TestCase):
    """Each check must fail on the broken shape D-REL-02 produced."""

    def test_duplicate_version_is_caught(self):
        p = '[project]\nname = "x"\nversion = "2.16.0"\nversion = "2.15.2"\n'
        self.assertTrue(version_problems(p, '__version__ = "2.16.0"\n'))

    def test_duplicate_dunder_version_is_caught(self):
        p = '[project]\nname = "x"\nversion = "2.16.0"\n'
        self.assertTrue(version_problems(p, '__version__ = "2.16.0"\n__version__ = "2.15.2"\n'))

    def test_markers_are_caught(self):
        self.assertTrue(marker_problems([("a.md", "x\n<<<<<<< HEAD\ny\n=======\nz\n>>>>>>> abc\n")]))

    def test_out_of_order_or_repeated_releases_are_caught(self):
        self.assertTrue(release_problems([{"version": "2.15.2"}, {"version": "2.16.0"}], "## 2.15.2\n"))
        self.assertTrue(release_problems([{"version": "2.16.0"}], "## 2.16.0\n## 2.16.0\n"))

    def test_two_latest_releases_are_caught(self):
        self.assertTrue(readme_latest_problems("The latest release (2.16.0) a.\nThe latest release (2.15.2) b.\n"))


if __name__ == "__main__":
    unittest.main()
