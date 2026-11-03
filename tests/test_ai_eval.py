"""The AI rule-drafting evaluation harness scores drafts correctly (no model is called)."""
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import eval_rule_drafting as ev  # noqa: E402


class Harness(unittest.TestCase):
    def test_perfect_partial_and_invalid(self):
        with tempfile.TemporaryDirectory() as d:
            Path(d, "E01.yaml").write_text(
                "asset: {id: claims}\nrules:\n- {id: R1, check: identifier, column: ni_number, scheme: nino}\n"
                "- {id: R2, check: unique, columns: [claim_month, ni_number]}\n")
            Path(d, "E02.yaml").write_text(
                "asset: {id: p}\nrules:\n- {id: R1, check: identifier, column: nhs_number, scheme: nhs_number}\n"
                "- {id: R2, check: not_null, column: made_up_column}\n")
            Path(d, "E03.yaml").write_text("asset: {id: x}\nrules:\n- {id: R1, check: magic}\n")
            out = ev.evaluate(d)
        by = {r["id"]: r for r in out["cases"]}
        self.assertEqual(by["E01"]["recall"], 1.0)
        self.assertAlmostEqual(by["E02"]["recall"], 0.333, places=3)
        self.assertEqual(by["E02"]["extra"], ["made_up_column"])
        self.assertFalse(by["E03"]["valid"])
        self.assertEqual(by["E04"]["error"], "no draft")
        self.assertGreater(out["overall"], 0)


if __name__ == "__main__":
    unittest.main()
