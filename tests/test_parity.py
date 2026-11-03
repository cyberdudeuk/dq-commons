"""The browser engine (portal/src/js/engine.js) must give the same answers as the Python kit.

Runs scripts/parity_check.py, which compares the two on the NDL chart files, the test data in
test_dqkit.py, synthetic fixtures covering all 15 checks, the scoring grid, issue operations and
the exports. Skipped when Node.js is not installed.
"""
import shutil
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


@unittest.skipUnless(shutil.which("node"), "Node.js (node) is not on PATH")
class JavaScriptParity(unittest.TestCase):
    def test_engine_matches_python(self):
        out = subprocess.run([sys.executable, str(ROOT / "scripts" / "parity_check.py")], cwd=ROOT,
                             capture_output=True, text=True, timeout=600)
        self.assertEqual(out.returncode, 0, msg=out.stdout[-6000:] + out.stderr[-3000:])


if __name__ == "__main__":
    unittest.main()
