"""Reconciliation of two versions of a dataset (Python side; parity with the browser is in parity_check)."""
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
import parity_check as pc  # noqa: E402
from dqkit.reconcile import reconcile  # noqa: E402


class Reconcile(unittest.TestCase):
    def test_finds_every_kind_of_difference(self):
        r = reconcile(pc.read_csv_text(pc.RECON_SRC), pc.read_csv_text(pc.RECON_TGT), ["id"])
        self.assertFalse(r["passed"])
        self.assertEqual((r["only_in_source"]["count"], r["only_in_target"]["count"]), (1, 1))
        self.assertEqual(r["duplicate_keys"]["source"], 1)
        self.assertEqual(r["columns_missing_in_target"], ["when"])
        self.assertEqual(r["mismatches"][0]["examples"][0], {"key": ["2"], "source": "Bo", "target": "Bob"})
        self.assertEqual({t["column"]: t["difference"] for t in r["totals"]}, {"amount": 7.0, "count": -1.0})

    def test_identical_files_pass(self):
        df = pc.read_csv_text("id,v\n1,a\n2,b\n")
        self.assertTrue(reconcile(df, df, "id")["passed"])

    def test_cli_exit_codes(self):
        with tempfile.TemporaryDirectory() as d:
            a, b = Path(d) / "a.csv", Path(d) / "b.csv"
            a.write_text(pc.RECON_SRC); b.write_text(pc.RECON_TGT)
            r = subprocess.run([sys.executable, "-m", "dqkit", "reconcile", str(a), str(b), "--key", "id"], cwd=ROOT, capture_output=True, text=True)
            self.assertEqual(r.returncode, 1)
            self.assertIn("DIFFERENCES FOUND", r.stderr)
            r = subprocess.run([sys.executable, "-m", "dqkit", "reconcile", str(a), str(a), "--key", "id,name"], cwd=ROOT, capture_output=True, text=True)
            self.assertEqual(r.returncode, 1)  # the source has a duplicate key, so even a self-comparison reports it


if __name__ == "__main__":
    unittest.main()
