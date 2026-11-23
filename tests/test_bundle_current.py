"""The offline bundle (docs/bundle/index.html) matches its sources.

Defect, 23 November 2026: a docs-only commit changed the status and changelog
pages without regenerating the bundle, so Content health failed on main
("Bundle is out of date"). Only the weekly Content health job ran that check;
this test puts it in the ordinary test run that every change goes through.
"""

import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


class BundleIsCurrent(unittest.TestCase):
    def test_bundle_matches_sources(self):
        r = subprocess.run([sys.executable, "scripts/build_bundle.py", "--check"], cwd=ROOT, capture_output=True, text=True, check=False)
        self.assertEqual(r.returncode, 0, "docs/bundle/index.html is out of date: run python scripts/build_bundle.py\n" + r.stdout + r.stderr)


if __name__ == "__main__":
    unittest.main()
